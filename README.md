# POTU's Server Checker

## Summary
This program is designed to allow home-labbers to quickly check a homelab running Proxmox, including pulling main server statistics, virtual machine statistics and writing some of the core information to a log file once per week. Also sends out emails based on things like usb detections and virtual machine activity.

**NOTICE:** This program was built off of the idea that you are only running Virtual Machines on your device, if containers are being ran, this could cause issues with the program attempting to run.

## Maintainer(s)
Nolan Abbott - https://github.com/ThePresidentofTheUniverse

## Modules to Install & Requirements
There are several modules that need to be installed for this program to function. Please install the following modules shown below:
- psutil - https://psutil.readthedocs.io/stable/
- cpuinfo - https://pypi.org/project/py-cpuinfo/
- usb-monitor 1.23 - https://pypi.org/project/usb-monitor/
- proxmoxer - https://github.com/proxmoxer/proxmoxer
- aiosmtpd - https://aiosmtpd.aio-libs.org/en/latest/
The aiosmtpd module above is so you can test the email system locally. To conduct local testing, find the debug in the main function and set it to *True*.
**NOTCE:** To setup the aiosmtpd service, type in the following command first in your terminal. It will print out all of the prospective emails into the terminal: *python -m aiosmtpd -n -c aiosmtpd.handlers.Debugging -l localhost:8025*

## Program Features
This is a large script that essentially pulls a large amount of information from a home-lab running ProxMox that is using virtual machines. The program will pull the following information:
- Device Name
- Processor
- CPU Usage
- Memory
- Memory Usage
- Storage Usage
- IPv4 Address
- IPv6 Address
- List of Detected USB Devices
- Backup Information like ID, Enabled, Schedule, Retention, Storage Location and VMs Included
- VM information like ID, Name, Node, Operating System, Start at Boot, Status, Processor Usage, Memory Usage, Memory Allotted and whether or not a USB Device is detected.

Besides pulling the information, it will also create/write a log file in the root's user directory as well, containing information that changes at regular intervals, like CPU usage, VM information and Backup information. It also has the capabilities to send the log file out as an email to you, as long as you set it up. The steps to set up the email system is listed in another section lower down.

**NOTICE:** This is only seen in the raw output, the log output saves less information that will most likely not change over a long period of time.

# Configuring the Email SMTP Service
If you are wanting to see the SMTP service fully functional instead of running it in debug, do the following steps below:
1. Add Email Addresses
The system uses two different email addresses, one of them is the sender email and the other is the receiving email. Those are passed into the Email_admin function at the bottom of main.

2. Setup Sender Email Authentication
In my case, I ended up using Gmail to allow my emails to be sent out. To do this, you will need to configure the sender email with the following:
* Sign into the google account that will send the emails out.
* Enable two-step verification with the email account.
* Generate an App Password for the email account.
* Paste the App Password into *email_admin* function at the variable labeled "password" in the try-catch statement.

3. Configuring the Email Information in the Code
The program requires some code altercations for the email to be sent out to you, here are the lines of code that you need to change:
- In the *email_admin* function, this is where you paste the password you got from step 2.
- In the *main* function, this is where you paste the sender email.
- In the *main* function, this is where you paste the receiver email.

## Arguments
This is a list of the current arguments available in the program.

### debug-email
This argument temporarily sets the email debug function to *True*. While you will still need to enable the aiosmtpd service, this prevents you from having to manually change the debug mode in the code from *False* to *True*.

### dump-json
This argument creates a dump file of all relevant ProxMox information that this program uses, allowing you to dry-run this program or use the data gathered from the JSON file into whatever you want to use it for.

**NOTICE:** This argument is not able to run with the *dry-run* argument. Doing this will cause the program to stop itself from continuing.

### dry-run
This is an argument that allows you to dry-run the JSON dump file that was created with the *dump-json* arguement. This is designed primarily for testing purposes, allowing you to see how the program runs and what its capabilities are. Please note that a dry-run will still attempt to send out an email and will send info to the log file.

**NOTICE:** This argument is not able to run with the *dump-json* argument. Doing this will cause the program to stop itself from continuing.

### prevent-log
This argument will stop the script from creating and/or updating the log file.

**NOTICE:** This will not prevent the log data from getting sent in the email still.

### prevent-email
This stops the email with log data from getting sent to the receiver.

### silent-run
The standard output is not shown in the terminal; verbose will still be shown if ran with this command.

### verbose
This argument displays additional, more detailed information while the program runs. This additional information does not get stored in the log files or in the emails but is present in the terminal output.

## Example output
### Log output
Below is an example of the output you will receive in the log files and receive via email:

```
Log for Server Checker
----------------------------------------------------
LOG DATE: 2026-10-13
----------------------------------------------------
CORE SERVER INFO
Active Virtual Machines: 6
Deactive Virtual Machines: 2
 Total Virtual Machines: 8

Overall CPU Usage: 0.9
Overall Memory Usage: 71.1%
Storage Usage 44.03GB out of 67.73GB

---------------------------------------------------
SERVER BACKUP INFORMATION
----------------------------------------------------
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
Backup ID: backup-c763cbde-e4ae
Enabled: True
Scheduled: monthly
Backup Retention: 2
Next Run: 2026-11-01T00:00:00
Storage Location: local
Selection of VMs Included: VMIDs: 100,101,102,103,105,109
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
----------------------------------------------------
VIRTUAL MACHINES INFORMATION
----------------------------------------------------
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
ID: 100
VM Name: MyCoolWebsite
Node: pve

Operating System: Linux (2.6+ kernel)
Start at Boot: 1
Status: running
Processor Usage: 0.39
Total Processors: 1
Memory Usage Percentage: 46.63%
Memory Usage Technical: 1.87GB
Memory Allotted: 4.0GB
USB Device Detected: No Devices Detected
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
----------------------------------------------------

()()()()()()()()()()()()()()()()()()()()()()()()()()
END OF LOG
()()()()()()()()()()()()()()()()()()()()()()()()()()
```

*Please note that the virtual machine list was cut short to preserve space. The program iterates through each VM's information. It also iterates through backup information as well.*

### Raw output
Here is the raw information that can be outputted when this program is ran:
```
====================================================
POTU's SERVER CHECKER UTILITY
USE ONLY ON PROXMOX SERVICES
===================================================

CORE SERVER INFORMATION
----------------------------------------------------
Active VMs: 6
Deactivated VMs: 2
Total VMs: 8
Device Name: pve
Processor: AMD Ryzen 5 3600 6-Core Processor
Overall CPU Usage: 0.9
Memory: 31.29GB
Overall Memory Usage: 71.1%
Overall Storage Usage: 44.03GB out of 67.73GB used
Left-Over Storage: 23.7GB left
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

List of Detected USB Devices

/dev/bus/usb/004/003 -- Expansion_SW (203b - 0bc2)
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

BACKUP INFORMATION
----------------------------------------------------

/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
Backup ID: backup-c763cbde-e4ae
Enabled: True
Scheduled: monthly
Backup Retention: 2
Next Run: 2026-11-01T00:00:00
Storage Location: local
Selection of VMs Included: VMIDs: 100,101,102,103,105,109
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

NETWORK SYSTEM INFORMATION
----------------------------------------------------
IPV4 Address: 127.0.0.1
IPV6 Address: lookup failed - [Errno -2] Name or service not known

VIRTUAL MACHINES TECHNICAL INFORMATION
----------------------------------------------------
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
ID: 100
VM Name: MyCoolWebsite
Node: pve

Operating System: Linux (2.6+ kernel)
Start at Boot: 1
Status: running
Processor Usage: 0.39
Total Processors: 1
Memory Usage Percentage: 46.63%
Memory Usage Technical: 1.87GB
Memory Allotted: 4.0GB
USB Device Detected: No Devices Detected
/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
```
*Please note that the virtual machine list was cut short to preserve space. The program iterates through each VM's information. It also iterates through backup information as well.*
## Problems & Solutions

**USB is Pulling Host and Not Name:** If you are seeing the output of the *USB Devices Detected* showing something along the lines of *['Host : 4-3']*, this is most likely due to how you have your USB device connected to the VM in ProxMox. To setup your USB device properly, do the following below in the *Hardware* section of the VM:
1. Remove the old USB Device connection if not already done.
2. Select *Add* then select *USB Device*
3. Select the *Use USB Vendor/Device ID*
4. Select the relevant USB device you want to connect and select the *Add* option.

## Known Bugs, Issues and Problems
This is a list containing information of known bugs and problems with this program.
* IPV6 Address Frequently not pulling.
* Verbose mode does not output alongside program running.

## Artificial Intelligence Usage
*Please note that artificial intelligence was used during the process of creating this code. Down below is how it was used for this project.*

To help me better understand how the proxmoxer module functions, I ended up having artificial intelligence coach/teach me how the information was being pulled and called upon with the module as well as having it list off the information that can be called and how it could be called. I also had it generated the list of operating systems for the *OS_DICT* dictionary.