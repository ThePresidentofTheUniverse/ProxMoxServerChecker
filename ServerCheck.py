#*****************************************************************************
# * Program......: ServerCheck
# * Programmer(s): Nolan Abbott
# * Date.........: 2026-10-06
# * GitHub Repo..: https://github.com/ThePresidentofTheUniverse/ServerChecker/tree/main
# * Description..: This is a program designed to grab the information of a ProxMox server
#                  running virtual machines and storing it in a log file as well as sending
#                  out an email to the individual that is running the server. This program
#                  can either be ran manually by just running the Python script in the
#                  server or can be set up with a SYSTEMD service.
# * NOTICE.......: Please look through the README.md prior to running this program,
#                  as some code will need to be altered for you to be able to run this
#                  program on your system.
# ******************************************************************************
#Module imports
import json #Used for the dump-json argument.
import argparse #Used for the different arguments added to the program.
import psutil as ps #Used to gather base system information
import socket as sock #Used to gather network information
import cpuinfo as cpuinfo #Used to grab the cpu information, like brand.
from pathlib import Path #This is used for the logging feature, allowing the program to verify if the path exists or not.
from datetime import datetime, date #Used to convert time information.
import re #Used to determine if there is a USB device on the VM
from usbmonitor import USBMonitor #Used to detect usb devices
from usbmonitor.attributes import ID_MODEL, ID_MODEL_ID, ID_VENDOR, ID_VENDOR_ID  #Pulls metadata information from the USB.
from proxmoxer import ProxmoxAPI #This can be used to do more monitoring.
from proxmoxer.core import ResourceException #In case information is not able to found for on reason or another.
#Modules for sending out an email.
import smtplib
import ssl
from getpass import getpass
from email.message import EmailMessage

#MAIN FUNCTIONS
#This pulls the information from the actual system
def core_server_info(verbose):
    #Create a null dict for info return
    server_info = []

    #grabs the name of the device
    if verbose:
        print("[VERBOSE] Grabbing Device Name")
    device_name = sock.gethostname()
    if verbose:
            print("[VERBOSE] Grabbing CPU Name")
    #grabs the name of the processor
    processor_name = cpuinfo.get_cpu_info()['brand_raw']
    if verbose:
            print("[VERBOSE] Grabbing total memory")
    #Grabs total memory amount
    memory_unrounded = (ps.virtual_memory().total / 1073741824) #quick equation to make number from bytes to gigbytes
    memory_total = round(memory_unrounded, 2)
    #Grabs the amount of memory being used
    if verbose:
            print("[VERBOSE] Converting total memory to percentile")
    memory_usage = ps.virtual_memory().percent
    #Grabs the amount of CPU being used
    if verbose:
            print("[VERBOSE] Grabbing CPU usage")
    cpu_usage = ps.cpu_percent(interval=1)
    #Grabs total storage and amount used
    if verbose:
            print("[VERBOSE] Determing total disk size")
    storage = ps.disk_usage('/')
    storage_total = round((storage.total / (2**30)), 2)
    if verbose:
            print("[VERBOSE] Determing amount of disk used")
    storage_used = round((storage.used / (2**30)), 2)

    #Throw all data together into the dictionary
    server_info.append({
         "device": device_name,
         "processor": processor_name,
         "mem_total": memory_total,
         "mem_usage": memory_usage,
         "cpu_usage": cpu_usage,
         "storage_tote": storage_total,
         "storage_used": storage_used,
    })

    #Returns a pretty design of the information
    pretty_list = ""
    for info in server_info:
        pretty_list += format_core(info)

    #returning all of the information
    return server_info, pretty_list

def state_of_vms(verbose, moxer):
    if verbose:
        print("[VERBOSE] Grabbing the state of each virtual machine")
     
    #Stores each state of the VM for JSON files
    vm_states = []
     
    #For-loop that checks the status of each VM
    guests = [g for g in moxer.cluster.resources.get(type="vm") if not g.get("template")]
    active = sum(1 for g in guests if g["status"] == "running")
    total = len(guests)
    deactive = total - active
     
    vm_states.append({
        "active_vms": active,
        "deactive_vms": deactive,
        "total_vms": total
        })
    #Returns a pretty design of the information
    pretty_list = ""
    for state in vm_states:
         pretty_list += format_vm_states(state)

    #Returning the state information
    return vm_states, pretty_list
    
#This pulls the network information of the main system
def network_info(hostname):
    #pulling local IPV4 address
    try:
        ipv4 = sock.gethostbyname(hostname)
    except sock.gaierror as e:
        ipv4 = f"lookup failed - {e}"

    #Attempting to pull the IPV6 address (decent chance that this usually does not work due to how the hostname is setup. Have not found a way to get around this yet.)
    try:
        results = sock.getaddrinfo(hostname, None, sock.AF_INET6)
        addrs = [r[4][0].split("%")[0] for r in results]
        ipv6 = [a for a in addrs if not a.startswith("fe80") and a != "::1"]
    except sock.gaierror as e:
        ipv6 = f"lookup failed - {e}"

    return ipv4, ipv6 if ipv6 else (addrs[0] if addrs else f"lookup failed - {e}")

#This grabs the information regarding the state of the systems current backup
def backup_info(moxer):
    #Initilize list to store backup information for log files.
    backup_list = []
    #The term 'get' is used because terminology between different versions of Proxmox vary.
    #run through each backup and pull is information
    for job in moxer.cluster.backup.get():
        next_run = job.get("next-run")

        #The if-else statement below grabs the scope of the virtual machines included in the backup. This is where different terminology is seen.
        if job.get("all"):
            scope = "All guests" + (f" (excluding {job['exclude']})" if job.get("exclude") else "")
        elif job.get("pool"):
            scope = f"Pool: {job['pool']}"
        else:
            scope = f"VMIDs: {job.get('vmid', 'none')}"

        backup_list.append({
             "id": job["id"],
             "enabled": bool(job.get("enabled", 1)), #pulls the data of if the backup is enabled
             "schedule": job.get("schedule") or f'{job.get("dow", "?")} {job.get("starttime", "?")}', #Grabs the data for occurence of backup.
             "retention": retention_amount(job),
             "next_run": datetime.fromtimestamp(next_run).isoformat() if next_run else "n/a", #Grabs the time of when the next run is going to occur
             "storage": job.get("storage"), #Grabs the storage location of the backup
             "scope": scope
        })
    #Returns a list of the information retreived from the backup loop
    pretty_list = ""
    for backup in backup_list:
         pretty_list += format_backup(backup)
    return backup_list , pretty_list

#This runs through each virtual machine and grabs their data.
def virtual_machine_info(devices, verbose, moxer):
    #Holds the list of virtual machines
    virtual_machine_list = []

    guests = moxer.cluster.resources.get(type="vm") #Grabs the information of all VMs
    for guest in guests: #For loop that prints out the information of each VM
        #Grabs a series of information that are used through-out the outputting process.
        node, vmid, vtype = guest["node"], guest["vmid"], guest["type"]
        if verbose:
            print(f"[VERBOSE] Grabbing virtual machine information[{vmid}]...")
        
        
        try: 
            #Attempts to grab the operating System information
            cfg = moxer.nodes(node).__getattr__(vtype)(vmid).config.get()#Designed to be used for VMs, does not work with containers.
        except:
            cfg = {}
        mem, maxmem = guest.get("mem", 0), guest.get("maxmem", 0)
        virtual_machine_list.append({
             "id": vmid,
             "name": guest.get("name"),
             "node": node,
             "status": guest["status"],
             "os": os_convert(str(cfg.get("ostype"))),
             "start_at_boot": bool(int(cfg.get("onboot", 0))),
             "cpu_percent": round(guest.get("cpu", 0) * 100, 2),
             "cores": cfg.get("cores"),
             "mem_percent": memory_percentage(guest),
             "mem_used_gb": round(mem / 1073741824, 2),
             "mem_allotted_gb": round(maxmem / 1073741824, 2),
             "usb": grab_usb_devices(cfg, devices),
        })

        pretty_list = ""
    for vm in virtual_machine_list:
         pretty_list += format_vm(vm)
    return virtual_machine_list, pretty_list

#This grabs some of the data from above and compiles it into a log file
def logging_file(pretty_core, pretty_states, backup_pretty, vm_pretty, prevent_log):
    log_file = Path(__file__).resolve().parent / "server_checker_log_file.txt"

    #The central log file
    log_data = f"\nLog for Server Checker\n----------------------------------------------------\nLOG DATE: {date.today()}\n----------------------------------------------------\nCORE SERVER INFO\n{pretty_states}\n{pretty_core}\n---------------------------------------------------\nSERVER BACKUP INFORMATION\n---------------------------------------------------\n"
    log_data += backup_pretty
    #Appends to log_data
    log_data += f"\n----------------------------------------------------\nVIRTUAL MACHINES INFORMATION\n----------------------------------------------------"
    #Appends list of virtual machines to log data
    log_data += vm_pretty
    #Appends to log_data
    log_data += f"----------------------------------------------------\n\n()()()()()()()()()()()()()()()()()()()()()()()()()()\nEND OF LOG\n()()()()()()()()()()()()()()()()()()()()()()()()()()\n\n"

    #Does it here specifically because the user might still want to get an email.
    if prevent_log == False:
        if log_file.is_file(): #If the file exists
            with open(log_file, "a") as logging:
                        logging.write(log_data)

        else: #If the file does not exist
            with open(log_file, "w+") as new_file:
                new_file.write(f"\n====================================================\nPOTU's SERVER CHECKER UTILITY\nUSE ONLY ON PROXMOX SERVICES\n==================================================={log_data}")

    return log_data

#This function collects the data from the system live
def data_collector(moxer, verbose):
    #Grab core server information

    server_info, pretty_core = core_server_info(verbose)
    #Grabs USB devices
    devices = usb_monitor()
    #Grabs the VM state information
    vm_states, pretty_states = state_of_vms(verbose, moxer)
    #Grabs the backup information
    backup_list, backup_pretty = backup_info(moxer)
    #Grabs network information
    ipv4, ipv6 = network_info(server_info[0]["device"])
    #Grabs list of VMs
    virtual_machine_list, vm_pretty = virtual_machine_info(devices, verbose, moxer)
    #returning all of the information that got pulled from above
    return{
      "server_info": server_info,
      "pretty_core": pretty_core,
      "devices": devices,
      "vm_states": vm_states,
      "pretty_states": pretty_states,
      "backup_list": backup_list,
      "backup_pretty": backup_pretty,
      "ipv4": ipv4,
      "ipv6": ipv6,
      "virtual_machine_list": virtual_machine_list,
      "vm_pretty": vm_pretty
    }

#-------------------------
# USB Monitoring Functions
#-------------------------
#This function is used to determine what kind of USB devices are detected on the machine.
def usb_monitor():   
    # Create the USBMonitor instance
    monitor = USBMonitor()

    # Get the current devices
    devices_dict = monitor.get_available_devices()

    return devices_dict

#This function is used to parse the host information
def parse_usb(val):
    host = next((p.split("=", 1)[1] for p in val.split(",") if p.startswith("host=")), None) #Finding the raw host name
    if host and ":" in host:
        vid, pid = host.lower().split(":") #Converting it something usable to relate the name to the USB device
        return vid.zfill(4), pid.zfill(4)
    return None, None # If nothing is found

def find_usb_name(vid, pid, monitor_devices):
    for dev in monitor_devices.values():
        #Associating the name of the device to the information parsed in parse_usb
        dev_vid = str(dev.get(ID_VENDOR_ID, "")).lower().replace("0x", "").zfill(4)
        dev_pid = str(dev.get(ID_MODEL_ID, "")).lower().replace("0x", "").zfill(4)
        if dev_vid == vid and dev_pid == pid:
            return dev.get(ID_MODEL) or dev.get(ID_VENDOR) or f"{vid}:{pid}"
    return f"{vid}:{pid}" #In-case the above fails, this just attempts to return raw.

#This is a function used to combine the other functions above and show-off the usb-devices.
def grab_usb_devices(cfg, monitor_devices):
    devices = [] #in-case there are multiple devices
    for key, val in cfg.items():
        if re.match(r"^usb\d+$", key):
            vid, pid = parse_usb(val)
            devices.append(find_usb_name(vid, pid, monitor_devices) if vid else val) #This should return something like 3=4 or 1=2
    if not devices:
        return "No Devices Detected"
    else:
        return devices

#----------
#FORMATTING
#----------
#Formats how the backup report looks.
def format_backup(b):
    line = "/\\" * 20
    return (f"\n{line}\nBackup ID: {b['id']}\nEnabled: {b['enabled']}\n"
            f"Scheduled: {b['schedule']}\nBackup Retention: {b['retention']}\n"
            f"Next Run: {b['next_run']}\nStorage Location: {b['storage']}\n"
            f"Selection of VMs Included: {b['scope']}\n{line}\n")
#Format how each virtual machine looks
def format_vm(v):
    line="/\\" * 20
    return (f"\n{line}\nID: {v['id']}\nVM Name: {v['name']}\nNode: {v['node']}\n\nOperating System: {v['os']}"
            f"\nStart at Boot: {v['start_at_boot']}\nStatus: {v['status']}\nProcessor Usage: {v['cpu_percent']}"
            f"\nTotal Processors: {v['cores']}\nMemory Usage Percentage: {v['mem_percent']}%\nMemory Usage Technical: {v['mem_used_gb']}GB"
            f"\nMemory Allotted: {v['mem_allotted_gb']}GB\nUSB Device Detected: {v['usb']}\n{line}\n")
#format how core server info looks
def format_core(c):
    return(f"\nDevice Name: {c['device']}\nProcessor: {c['processor']}\nOverall CPU Usage: {c['cpu_usage']}%\nMemory: {c['mem_total']}GB\nOverall Memory Usage: {c['mem_usage']}"
           f"\nOverall Storage Usage {c['storage_used']}GB out of {c['storage_tote']}\nLeft-Over Storage: {round((c['storage_tote'] - c['storage_used']), 2)}GB")
#Format how the vm states look
def format_vm_states(vm):
    return(f"\nActive VMs: {vm['active_vms']}\nDeactive VMs: {vm['deactive_vms']}\nTotal VMs: {vm['total_vms']}\n")

#Returns a pretty_looking report that is used for the standard output
def report_builder(report, verbose):
     #Making it look pretty
    print("\n====================================================\nPOTU's SERVER CHECKER UTILITY\nUSE ONLY ON PROXMOX SERVICES\n====================================================")
    #Core server information
    print("\nCORE SERVER INFORMATION\n----------------------------------------------------")
    #Print out the report information
    print(report["pretty_core"])
    #Prints out the VM States
    print(report["pretty_states"])
    #USB Information
    if verbose:
        print("[VERBOSE] Grabbing USB Devices")
    print(f"/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\\")
    print("\nList of Detected USB Devices\n")
    # Print the USB devices
    for device_id, device_info in report["devices"].items():
        print(f"{device_id} -- {device_info[ID_MODEL]} ({device_info[ID_MODEL_ID]} - {device_info[ID_VENDOR_ID]})")
    print(f"/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\\")
    #Prints out the Backup Information
    print("\nBACKUP INFORMATION\n----------------------------------------------------\n")
    if verbose:
        print("[VERBOSE] Acquring Backup Information")
    print(report["backup_pretty"])
    #Prints out network information
    print("\nNETWORK SYSTEM INFORMATION\n----------------------------------------------------")
    if verbose:
            print("[VERBOSE] Determining the Local IP Addresses")
    print(f"IPV4 Address: {report['ipv4']}")
    print(f"IPV6 Address: {report['ipv6']}")
    #Print out the VM information
    print("\nVIRTUAL MACHINES TECHNICAL INFORMATION\n----------------------------------------------------")
    print(report["vm_pretty"])

#----------------
#HELPER FUNCTIONS
#----------------
#This is a function for reading wthe retention for backups
def retention_amount(job):
    #Depending on which version of Proxmox you are using, the retention is either stored as prune or as max. Max is the older version.
    retention = job.get("prune-backups")
    if retention:
        keep_last = int(retention.get("keep-last", 0))
        #Certain versions will return a dictionary of data to work with
        if isinstance(retention, str):
            retention = dict(r.split("=") for r in retention.split(","))
            return retention
        #returns the amount of backups stored.
        return keep_last
    if "maxfiles" in job:
        return {"keep-last": int(job["maxfiles"])}
    return None #Falls back to default storage if nothing is returned

#This is a function designed to grab the operating system information from a virtual machine
def grab_os_information(moxer, node, vmid, vtype, cfg):
    if vtype == "qemu":
        try:
            info = moxer.nodes(node).qemu(vmid).agent("get-osinfo").get()
            return info["result"].get("pretty-name")
        except ResourceException:
            pass
    return cfg.get("ostype") #Fallback to the coarse config value.

#This function is used to grab the memory percentage of the virtual machines
def memory_percentage(guest):
    max = guest.get("maxmem", 0)
    if not max:
        return 0.0
    return round(guest.get("mem", 0) / max * 100, 2)

#This is a function that sends out emails.
def email_admin(subject, sender_email, debug):
    #Designed to test locally.
    if debug:
        smtp_server = "localhost"
        port = 8025
        with smtplib.SMTP(smtp_server, port) as server:
            server.send_message(subject)

    #designed to run in prod
    try:
        smtp_server = "smtp.gmail.com"
        port = 465 #define the standard secure SMTP port
        password = "Insert Password here" #The password used from my gmail account to allow emails to be sent.

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            smtp_server, port, context=context,
        ) as server:
            server.login(sender_email, password)
            server.send_message(subject)
    except (smtplib.SMTPException, OSError) as e:
        print(f"Email failed to send: {e}")
        raise

#---------------
#JSON FILE STUFF
#---------------

#This is a function that allows the statistics from this program to be stored in a JSON file.
def dump_json(report, path):
    with open(path, "w") as file:
          json.dump(report, file, indent=2, default=str)
    print(f"Proxmox data written to {path}")
#Keys from the JSON file
REQUIRED_KEYS = {"server_info", "devices", "vm_states", "backup_list", "ipv4", "ipv6", "virtual_machine_list"}
#Function used to load the JSON file.
def load_json(path):
    try:
          with open(path) as file:
               report = json.load(file)
    except FileNotFoundError:
         raise SystemExit(f"The following path was not found: {path}. Please verify that you have typed in the path correctly.")
    except json.JSONDecodeError as e:
         raise SystemExit(f"The following file that you have provieded is not valid: {path}. Invalid JSON: {e}")

    missing = REQUIRED_KEYS - report.keys()
    if missing:
         raise SystemExit(f"The Dry-Run file created is missing the following sections: {', '.join(sorted(missing))}")
    return report

#-------------
#OS Dictionary
#-------------
# This is essentially a dictionary used to convert the terms that are printed out by default with the OS stuff and makes them look pretty.
OS_DICT = {
    "l26": "Linux (2.6+ kernel)",
    "l24": "Linux (2.4 kernel)",
    "win11": "Windows 11 / Server 2022 / 2025",
    "win10": "Windows 10 / Server 2016 / 2019",
    "win8": "Windows 8 / Server 2012 / 2012 R2",
    "win7": "Windows 7 / Server 2008 R2",
    "wvista": "Windows Vista",
    "w2k8": "Windows Server 2008",
    "w2k3": "Windows Server 2003",
    "wxp": "Windows XP",
    "w2k": "Windows 2000",
    "solaris": "Solaris",
    "other": "Other",
}
#Function that converts the os name to a pretty name with the help of the dictionary above
def os_convert(os):
    raw = os
    if raw is None: # If there is no info
        return "Unknown Operating System"
    return OS_DICT.get(raw, raw) # Returns if there is info.

# Sets everything up to run
def main():
    debug = False #Call up here so the argument for debug can change this
    no_email = False #Call up here so the argument for email prevention can change this.
    log_prevention = False #Call up here so the argument for log file prevention can change this.
    silence = False #Call up here so the argument for the silent output can be enabled.
    #This here is used to work with the different possible arguments applied in the program
    parser = argparse.ArgumentParser(
    description="ProxMox Server Checker Tool"
    )
    #Used to temporarily change if you are wanting to test out the email mode locally on your machine.
    parser.add_argument(
    "--debug-email",
    help="Used to temporarily change if you are wanting to test out the email mode locally on your machine."
    )
    parser.add_argument(
    "--verbose",
    action="store_true",
    help="Displays highly detailed processing information."
    )
    parser.add_argument(
    "--prevent-email",
    action="store_true",
    help="Prevents the email functionality from sending out the log file to the receiver's email address."
    )
    parser.add_argument(
    "--prevent-log",
    action="store_true",
    help="Prevents the log file from storing its data."
    )
    parser.add_argument(
    "--silent-run",
    action="store_true",
    help="Standard output is not shown in the terminal"
    )
    parser.add_argument(
    "--dump-json", nargs="?", const="proxmox_dump.json", metavar="FILE",
    help="Writes the collected Proxmox data to a JSON file"
    )
    parser.add_argument(
    "--dry-run", nargs="?", const="proxmox_dump.json", metavar="FILE",
    help="This uses the information from a JSON file to allow the program to run the ProxMox utilities without using ProxMox."
    )

    #Below connects the args to their functions or intended purposes, some arguments may be scattered below.
    args = parser.parse_args()
    if args.verbose:
        print("[VERBOSE] Server Checker has started.")
    #Prevent dry-run and json-dump from working together, which would result in errors
    if args.dry_run and args.dump_json:
            parser.error("--dry-run & --dump-json cannot be used together.")

    if args.dry_run:
        report = load_json(args.dry_run)
        print(f"[DRY RUN] Using data from {args.dry_run}")
        print(f"(collected {report.get('generated', 'unknown time')})")
    else:
        #Create global var that allows this program to access the backend of ProxMox server locally.
        moxer = ProxmoxAPI(backend='local')
        report = data_collector(moxer, args.verbose)

    if args.silent_run:
        if args.verbose:
            print("[VERBOSE] Running program without showing output.")
        silence = True

    if silence == False:
        report_builder(report, args.verbose)

    #Create the dictionary to store ProxMox information above.
    if args.dump_json:
            if args.verbose:
                print("[VERBOSE] Creating dictionary report of info dump...")
            #Create the report
            dump_report = {
                 "generated": datetime.now().isoformat(timespec="seconds"),
                 "server_info": report["server_info"],
                 "devices": report["devices"],
                 "vm_states": report["vm_states"],
                 "backup_list": report["backup_list"],
                 "ipv4": report["ipv4"],
                 "ipv6": report["ipv6"],
                 "virtual_machine_list": report["virtual_machine_list"],
            }
            #Call function to dump information to json
            dump_json(dump_report, args.dump_json)

    #Store that as a log file.
    if args.dump_json:
        if args.verbose:
            print("[VERBOSE] Writing raw information to JSON...")
        dump_json(report, args.dump_json)

    
    if args.prevent_log:
        if args.verbose:
            print("[VERBOSE] This run will not be written to the log file.")
        log_prevention = True

    #Sneakily run the log file here
    if log_prevention == False:
        if args.verbose:
            print("[VERBOSE] Creating a log file.")
    log_data = logging_file(report["pretty_core"], report["pretty_states"], report["backup_pretty"], report["vm_pretty"], log_prevention)
    if log_prevention == False:
        if args.verbose:
            print("[VERBOSE] Log file created successfully.")

    #Argument for email debug.
    if args.debug_email:
            if args.verbose:
                print("[VERBOSE] Debug for email temporarily set True.")
            debug = True #Sets emails to debug mode.

    sender_email = "sends out email"
    receiver_email = "receives the email"
    valid_email = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}" #This is used to at least validate the email to make sure it is correctly written.


    if args.prevent_email:
        if args.verbose:
              print("[VERBOSE] Email will not be sent to receiver.")
        no_email = True

    if no_email == False:
        if re.fullmatch(valid_email, sender_email) and re.fullmatch(valid_email, receiver_email): #Validates email is correctly formatted at least.
            #All this stuff here is to send out an email
            message = EmailMessage()
            message["to"] = receiver_email
            message["from"] = sender_email
            message["subject"] = "Server Checker"
            message.set_content(f"The server checker has been ran! Here is the information gathered from the log file:\n{log_data}")
            if args.verbose:
                print("[VERBOSE] Sending out the log email...")
            email_admin(message, sender_email, debug)
            if args.verbose:
                print("[VERBOSE] successfully sent log email.")
        else:
            print("Either the receiver_email or the sender_email failed the validation check. Please review the emails you have entered.")

    if args.verbose:
        print(f"\n[VERBOSE] Server Checker has completed.")

# Lets the program run
if __name__ == "__main__":
    main()