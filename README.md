# POTU's Server Checker

## Summary
This program is designed to allow home-labbers to quickly check a homelab running Proxmox, including pulling main server statistics, virtual machine statistics and writing some of the core information to a log file once per week. Also sends out emails based on things like usb detections and virtual machine activity.

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

**NOTICE:** This program was built off of the idea that you are only running Virtual Machines on your device, if containers are being ran, this could cause issues with the program attempting to run.

## Program Features
This is a large script that essentially pulls a large amount of information from a home-lab running ProxMox

# Configuring the Email SMTP Service
If you are wanting to see the SMTP service fully functional instead of running it in debug, do the following steps below:
1. Add Email Addresses
The system uses two different email addresses, one of them is the sender email and the other is the receiving email. Those are passed into the Email_admin function at the bottom of main.

2. Setup Sender Email Authentication
In my case, I ended up using Gmail to allow my emails to be sent out. To do this, you will need to configure the sender email with the following:
A. Sign into the google account that will send the emails out.
B. Enable two-step verification with the email account.
C. Generate an App Password for the email account.
D. Paste the App Password into email_admin function at the variable labeled "password" in the try-catch statement.

## Example output
### Log output
Below is an example of the output you will receive in the log files:

```
Currently null
```

### Raw output
Here is the raw information that can be outputted when this program is ran:
```
null
```

## Problems & Solutions

**USB is Pulling Host and Not Name:** If you are seeing the output of the *USB Devices Detected* showing something along the lines of *['Host : 4-3']*, this is most likely due to how you have your USB device connected to the VM in ProxMox. To setup your USB device properly, do the following below in the *Hardware* section of the VM:
1. Remove the old USB Device connection if not already done.
2. Select *Add* then select *USB Device*
3. Select the *Use USB Vendor/Device ID*
4. Select the relevant USB device you want to connect and select the *Add* option.

## Artificial Intelligence Usage