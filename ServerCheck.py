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
import proxmoxmanager as pmm #even though this is for managing, keeping it in just in-case
import platform as plat
import logging as log
import usbmonitor as monitor
from proxmoxer import ProxmoxAPI #This can be used to do more monitoring.

#Create global var that allows this program to access the backend of ProxMox server locally.
moxer = ProxmoxAPI(backend='local')

#MAIN FUNCTIONS
#This pulls the information from the actual system
def core_server_info():
    #grabs the name of the device
    device_name = sock.gethostname
    #grabs the name of the processor
    processor_name = plat.processor
    #Grabs total memory amount
    memory_unrounded = (ps.virtual_memory().total / 1073741824) #quick equation to make number from bytes to gigbytes
    memory_total = round(memory_unrounded, 2)
    #Grabs the amount of memory being used
    memory_usage = ps.virtual_memory().percent
    #Grabs the amount of CPU being used
    cpu_usage = ps.cpu_percent(interval=1)
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

    return device_name, processor_name, memory_total, memory_usage, cpu_usage, active, deactive, total
    

#This pulls the network information of the main system
#def network_info():

#This grabs the information regarding the state of the systems current backup
#def backup_info():

#This runs through each virtual machine and grabs their data.
#def virtual_machine_info():

#This grabs some of the data from above and compiles it into a log file
#def logging_file():


#HELPER FUNCTIONS

#This function is used with virtual_machine_info to verify if the usb in the vm is detected.
#def usb_monitor():

#This is a function for scheduling the programs timing
#def time_scheduler():

#This is a function used to check if a VM goes down or up
#def vm_activity():

#This is a function that sends out emails.
#def email_admin(subject):

# Sets everything up to run
def main():

    #Making it look pretty
    print("\n===================================================\nPOTU's SERVER CHECKER UTILITY\nUSE ONLY ON PROXMOX SERVICES\n===================================================")
    device_name, processor_name, memory_total, memory_usage, cpu_usage, active, deactive, total = core_server_info()

    print(f"DataCenter: ")
    print(f"Node: ")

    print(f"Active VMs: {active}")
    print(f"Deactivated VMs: {deactive}")
    print(f"Total VMs: {total}")

    print(f"Device Name: {device_name}")
    print(f"Processor: {processor_name}")
    print(f"Overall CPU Usage: {cpu_usage}")
    print(f"Memory: {memory_total}")
    print(f"Overall Memory Usage: {memory_usage}%")
    print(f"Overall Storage Usage: out of used")
    print(f"Left-Over Storage: left")

# Lets the program run
if __name__ == "__main__":
    main()