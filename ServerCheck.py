#*****************************************************************************
# * Program......: ServerCheck
# * Programmer(s): Nolan Abbott
# * Date.........: 2026-10-06
# * GitHub Repo..: https://github.com/ThePresidentofTheUniverse/ServerChecker/tree/main
# * Description..: 
# ******************************************************************************/
#Module imports
import psutil as ps
import socket as sock 
import cpuinfo as cpuinfo #Used to grab the cpu information, like brand.
import platform as plat
import logging as log
from datetime import datetime
import re #Used to determine if there is a USB device on the VM
from usbmonitor import USBMonitor #Used to detect usb devices
from usbmonitor.attributes import ID_MODEL, ID_MODEL_ID, ID_VENDOR, ID_VENDOR_ID #Pulls metadata information from the USB.
from proxmoxer import ProxmoxAPI #This can be used to do more monitoring.
from proxmoxer.core import ResourceException #In case information is not able to found for on reason or another.
#Modules for sending out an email.
import smtplib
import ssl
from getpass import getpass
from email.message import EmailMessage

#Create global var that allows this program to access the backend of ProxMox server locally.
moxer = ProxmoxAPI(backend='local')

#MAIN FUNCTIONS
#This pulls the information from the actual system
def core_server_info():
    #grabs the name of the device
    device_name = sock.gethostname()
    #grabs the name of the processor
    processor_name = cpuinfo.get_cpu_info()['brand_raw']
    #Grabs total memory amount
    memory_unrounded = (ps.virtual_memory().total / 1073741824) #quick equation to make number from bytes to gigbytes
    memory_total = round(memory_unrounded, 2)
    #Grabs the amount of memory being used
    memory_usage = ps.virtual_memory().percent
    #Grabs the amount of CPU being used
    cpu_usage = ps.cpu_percent(interval=1)
    #Grabs total storage and amount used
    storage = ps.disk_usage('/')
    storage_total = round((storage.total / (2**30)), 2)
    storage_used = round((storage.used / (2**30)), 2)

    # Grabs the active and deactive VMs
    active = 0
    deactive = 0
    total = 0
    #For-loop that checks the status of each VM
    for vm in moxer.nodes('pve').qemu.get():
        if vm['status'] == 'stopped':
            deactive += 1
        else:
           active += 1
        total += 1

    #returning all of the information
    return device_name, processor_name, memory_total, memory_usage, cpu_usage, active, deactive, total, storage_total, storage_used
    
#This pulls the network information of the main system
def network_info(hostname):
    #pulling local IPV4 address
    try:
        ipv4 = sock.gethostbyname(hostname)
    except sock.gaierror as e:
        ipv4 = f"lookup failed - {e}"

    #Attempting to pull the IPV6 address
    try:
        results = sock.getaddrinfo(
            hostname,
            None,
            family=sock.AF_INET6,
            type=sock.SOCK_STREAM
        )
        ipv6 = list({
            result[4][0] for result in results
        })
    except sock.gaierror as e:
        ipv6 = f"lookup failed - {e}"

    return ipv4, ipv6

#This is code that can probably work to get the IPV6 address, but it uses the name of the interface, which I would like to grab dynamically instead.
#def network_info():
    #interface = "vmbr0"
    #ipv4 = None
    #ipv6 = []

    #addresses = psutil.net_if_addrs().get(interface, [])

    #for addr in addresses:
    #    if addr.family == socket.AF_INET:
    #        ipv4 = addr.address
     #   elif addr.family == socket.AF_INET6:
            # Remove the scope suffix if present
      #      address = addr.address.split("%")[0]
       #     if address not in ipv6:
        #        ipv6.append(address)

    #return ipv4, ipv6

#This grabs the information regarding the state of the systems current backup
def backup_info():
    #The term 'get' is used because terminology between different versions of Proxmox vary.

    #run through each backup and pull is information
    for job in moxer.cluster.backup.get():
        enabled = bool(job.get("enabled", 1)) #pulls the data of if the backup is enabled
        schedule = job.get("schedule") or f'{job.get("dow", "?")} {job.get("starttime", "?")}' #Grabs the data for occurence of backup.
        storage = job.get("storage") #Grabs the storage location of the backup

        #Grabs the time of when the next run is going to occur
        next_run = job.get("next-run")
        next_run = datetime.fromtimestamp(next_run).isoformat() if next_run else "n/a"

        #The if-else statement below grabs the scope of the virtual machines included in the backup. This is where different terminology is seen.
        if job.get("all"):
            scope = "All guests" + (f" (excluding {job['exclude']})" if job.get("exclude") else "")
        elif job.get("pool"):
            scope = f"Pool: {job['pool']}"
        else:
            scope = f"VMIDs: {job.get('vmid', 'none')}"
        
        retention = retention_amount(job)

        print(f"/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\\")
        print(f"Backup ID: {job['id']}")
        print(f"Enabled: {enabled}")
        print(f"Scheduled: {schedule}")
        print(f"Backup Retention: {retention}")
        print(f"Next Run: {next_run}")
        print(f"Storage Location: {storage}")
        print(f"Selection of VMs Included: {scope}")
        print(f"/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\\")

#This runs through each virtual machine and grabs their data.
def virtual_machine_info(devices):
    guests = moxer.cluster.resources.get(type="vm") #Grabs the information of all VMs
    for guest in guests: #For loop that prints out the information of each VM
        #Grabs a series of information that are used through-out the outputting process.
        vmid = guest["vmid"] #Declare ID here because of OS information
        node = guest["node"] #Declare Node here because of OS information
        status = guest["status"]#Declares status here because of OS information
        vtype = guest["type"] #Only used to grab os information.

        print(f"/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\\")
        print(f"ID: {vmid}")
        print(f"VM Name: {guest.get("name")}")
        print(f"Node: {node}\n")
        try: 
            #Attempts to grab the operating System information
            cfg = moxer.nodes(node).__getattr__(vtype)(vmid).config.get()#Designed to be used for VMs, does not work with containers.
        except:
            cfg = "I am broken."
        print(f"Operating System: {grab_os_information(moxer, node, vmid, vtype, cfg) if status == "running" else cfg.get("ostype")}")
        print(f"Start at Boot: {cfg.get("onboot", 0)}")
        print(f"Status: {status}")
        print(f"Processor Usage: {round((guest["cpu"] * 100), 2)}") #Math equation to get CPU usage
        print(f"Total Processors: {cfg.get("cores")}")
        print(f"Memory Usage Percentage: {memory_percentage(guest)}%") #Weird equation to get memory in percentage.
        print(f"Memory Usage Technical: {round((guest["mem"] / 1073741824), 2)}GB") #bytes to gb conversion
        print(f"Memory Allotted: {round((guest["maxmem"] / 1073741824), 2)}GB") #bytes to gb conversion
        print(f"USB Device Detected: {grab_usb_devices(cfg, devices)}")
        print(f"/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\\")
        print(f"\n")

#This grabs some of the data from above and compiles it into a log file
#def logging_file():

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

#This is a function used to check if a VM goes down or up
#def vm_activity():

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

# Sets everything up to run
def main():

    #Making it look pretty
    print("\n====================================================\nPOTU's SERVER CHECKER UTILITY\nUSE ONLY ON PROXMOX SERVICES\n===================================================")

    print("\nCORE SERVER INFORMATION\n----------------------------------------------------")
    device_name, processor_name, memory_total, memory_usage, cpu_usage, active, deactive, total, storage_total, storage_used = core_server_info()
    print(f"DataCenter: ")

    print(f"Active VMs: {active}")
    print(f"Deactivated VMs: {deactive}")
    print(f"Total VMs: {total}")

    print(f"Device Name: {device_name}")
    print(f"Processor: {processor_name}")
    print(f"Overall CPU Usage: {cpu_usage}")
    print(f"Memory: {memory_total}GB")
    print(f"Overall Memory Usage: {memory_usage}%")
    print(f"Overall Storage Usage: {storage_used}GB out of {storage_total}GB used")
    print(f"Left-Over Storage: {round((storage_total - storage_used), 2)}GB left")

    print(f"/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\\")
    print("\nList of Detected USB Devices\n")
    devices = usb_monitor()
    # Print the USB devices
    for device_id, device_info in devices.items():
        print(f"{device_id} -- {device_info[ID_MODEL]} ({device_info[ID_MODEL_ID]} - {device_info[ID_VENDOR_ID]})")

    print(f"/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\\")

    print("\nBACKUP INFORMATION\n----------------------------------------------------\n")
    backup_info()

    print("\nNETWORK SYSTEM INFORMATION\n----------------------------------------------------")
    ipv4, ipv6 = network_info(device_name)
    print(f"IPV4 Address: {ipv4}")
    print(f"IPV6 Address: {ipv6}")

    print("\nVIRTUAL MACHINES TECHNICAL INFORMATION\n----------------------------------------------------")

    virtual_machine_info(devices)

    sender_email = "sends out email"
    receiver_email = "receives the email"

    #All this stuff here is to send out an email
    message = EmailMessage()
    message["to"] = receiver_email
    message["from"] = sender_email
    message["subject"] = "test message"
    message.set_content("This is a test message")

    debug = False
    #email_admin(message, sender_email, debug)

# Lets the program run
if __name__ == "__main__":
    main()