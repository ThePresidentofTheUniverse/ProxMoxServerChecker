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
from usbmonitor import USBMonitor
from usbmonitor.attributes import ID_MODEL, ID_MODEL_ID, ID_VENDOR_ID #Pulls metadata information from the USB.
from proxmoxer import ProxmoxAPI #This can be used to do more monitoring.
#Modules for sending out an email.
import smtplib
import ssl
from getpass import getpass
from email.message import EmailMessage

#Create global var that allows this program to access the backend of ProxMox server locally.
#moxer = ProxmoxAPI(backend='local')

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
  #  for vm in moxer.nodes('pve').qemu.get():
   #     if vm['status'] == 'stopped':
   #         deactive += 1
   #     else:
    #       active += 1
    #    total += 1

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
#def backup_info():

#This runs through each virtual machine and grabs their data.
#def virtual_machine_info():

#This grabs some of the data from above and compiles it into a log file
#def logging_file():


#HELPER FUNCTIONS

#This function is used with virtual_machine_info to verify if the usb in the vm is detected.
def usb_monitor():
    # Create the USBMonitor instance
    monitor = USBMonitor()

    # Get the current devices
    devices_dict = monitor.get_available_devices()

    # Print them
    for device_id, device_info in devices_dict.items():
     print(f"{device_id} -- {device_info[ID_MODEL]} ({device_info[ID_MODEL_ID]} - {device_info[ID_VENDOR_ID]})")
   
    

#This is a function for scheduling the programs timing
#def time_scheduler():

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
        password = "wbba sxrt xqri gdxi" #The password used from my gmail account to allow emails to be sent.

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

    print("\nBACKUP INFORMATION\n----------------------------------------------------")
    print(f"Enabled: ")
    print(f"Scheduled: ")
    print(f"Total Backups that can be Stored: ")
    print(f"Next Run: ")
    print(f"Storage Location: ")
    print(f"Selection of VMs Included: ")

    print("\nNETWORK SYSTEM INFORMATION\n----------------------------------------------------")
    ipv4, ipv6 = network_info(device_name)
    print(f"IPV4 Address: {ipv4}")
    print(f"IPV6 Address: {ipv6}")

    print("\nVIRTUAL MACHINES TECHNICAL INFORMATION\n----------------------------------------------------")
    usb_monitor()

    sender_email = "njabbott0126@gmail.com"
    receiver_email = "njabbott2005@gmail.com"

    #All this stuff here is to send out an email
    message = EmailMessage()
    message["to"] = receiver_email
    message["from"] = sender_email
    message["subject"] = "test message"
    message.set_content("This is a test message")

    debug = False
    email_admin(message, sender_email, debug)

# Lets the program run
if __name__ == "__main__":
    main()