# POTU's Server Checker

## Summary
This program is designed to allow home-labbers to quickly check a homelab running Proxmox, including pulling main server statistics, virtual machine statistics and writing some of the core information to a log file once per week. Also sends out emails based on things like usb detections and virtual machine activity.

## Maintainer(s)
Nolan Abbott - https://github.com/ThePresidentofTheUniverse

## Modules to Install
There are several modules that need to be installed for this program to function. Please install the following modules shown below:
- psutil - https://psutil.readthedocs.io/stable/
- cpuinfo - https://pypi.org/project/py-cpuinfo/
- usb-monitor 1.23 - https://pypi.org/project/usb-monitor/
- proxmoxer - https://github.com/proxmoxer/proxmoxer
- aiosmtpd - https://aiosmtpd.aio-libs.org/en/latest/
The aiosmtpd module above is so you can test the email system locally. To conduct local testing, find the debug in the main function and set it to *True*.

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

## Artificial Intelligence Usage