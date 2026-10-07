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
import platform as plat
import proxmoxmanager as pmm
import logging as log
import usbmonitor as monitor

#MAIN FUNCTIONS
#This pulls the information from the actual system
def core_server_info(active, deactive, device_name, processor, cpu_usage, memory, mem_usage, store_used, store_left):
    device_name = sock.gethostname
    

#This pulls the network information of the main system
def network_info():

#This grabs the information regarding the state of the systems current backup
def backup_info():

#This runs through each virtual machine and grabs their data.
def virtual_machine_info():

#This grabs some of the data from above and compiles it into a log file
def logging_file():


#HELPER FUNCTIONS
#This function is used with virtual_machine_info to verify if the usb in the vm is detected.
def usb_monitor():

#This is a function for scheduling the programs timing
def time_scheduler():

#This is a function used to check if a VM goes down or up
def vm_activity():

#This is a function that sends out emails.
def email_admin(subject):

# Sets everything up to run
def main():
    print("\n===================================================\nPOTU's SERVER CHECKER UTILITY\nUSE ONLY ON PROXMOX SERVICES\n===================================================")

# Lets the program run
if __name__ == "__main__":
    main()