Should check for the following in the server:
- Check the state of each VM (up or down)
The state of the VMs matter to me, so I can make sure that they are running. I would also like to include additional information below each VM so I can see how well each one is functioning (just basic things like their virtual memory, cores and CPU usage)
- Check memory usage 
I would like to know how much memory is being used, as if the memory starts to spike or suddenly decreases, something is probably happening that shouldn't be.
- Check CPU usage
CPU is usually not that much of an issue, but if something does spike, then I would like to know about that as well.
- Check total storage (would be nice if it showed total then per VM) and show remaining disk space.
I am kind of strapped for storage right now, so this would be a good way for me to make sure I am not over-doing it with VMs.
- Send information to a log file like twice a week
The log files should be scheduled to release information to a log file, so I keeo track of things. I would also be interested in trying to set it up to where if the space for the log files detects if too much storage is being taken up by the log files and to begin deleting them slowly to maintain continuous space.
- Verify if external hard-drive is detected
My home-lab is kind of jank and using an external hard-drive to store some large set of information. Every once in a while it disconnects and I would like to not be suprised when I suddenly figure it out a day later.

For the currently planned modules, I will use the following:
- socket (https://docs.python.org/3/library/socket.html)
- platform (https://docs.python.org/3/library/platform.html)
- psutil (https://psutil.readthedocs.io/stable/)
- ProxmoxManager (https://pypi.org/project/proxmoxmanager/)
- usb-monitor 1.23 (https://pypi.org/project/usb-monitor/)
- logging (https://docs.python.org/3/library/logging.html)

For the warnings, here is the kind of warnings I would want:
- I would like to be notified if CPU increases to 25% or higher
- I would like to be notified if the Memory goes past 80% and also check 60% as well.
- I would like to be notified if a VM is started and stopped.
- I would like to know when the external hard-drive has disconnected itself.
- I would like a warning when the log files are getting above a certain storage amount.

Here is the planned concept I have for a report I want to get printed out to a log file:

```
===================================================
POTU's SERVER CHECKER UTILITY
USE ONLY ON PROXMOX SERVICES
===================================================

CORE SERVER INFORMATION
---------------------------------------------------
DataCenter: Datacenter

Active Virtual Machines: 8
Deactivated Virtual Mahcines: 2
Total Virtal Machines: 10

Device Name: homelab
Processor: AMD what-ever its called
Overall CPU Usage: 10%
Memory: 32GB
Overall Memory Usage: 70%
Overall Storage Usage: 20GB out of 50GB used
Left-Over Storage: 30GB left

BACKUP INFORMATION
---------------------------------------------------
Enabled: Yes
Scheduled: Monthly
Next Run: 2026-11-01
Storage Location: local
Selection of VMs included: 100,101,102,103,105

NETWORK SYSTEM INFORMATION
---------------------------------------------------
Name: vmbr0
IPV4 Address: 127.0.0.1
IPV6 Address: hexa-decimal stuff I don't feel like writing out
State: Up

VIRTUAL MACHINES TECHNICAL INFORMATION
---------------------------------------------------

/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
ID: 103
Virtual Machine Name: NGINXReverseProxy
Node: pve

Operating System: Ubuntu Linux
Start at Boot: Yes
Status: Running
IP Address: 192.168.1.203

Processors Usage: 0.15%
Total Processors: 4
Memory Usage Percentage: 63%
Memory Usage Technical: 1.26GB 
Memory Amount Technical: 2GB
Storage Usage: 1GB
Total Storage: 10GB

USB Device Detected - No
\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

```

Since this is for my own home-lab server, these are the things that I would like to check or pull information from and throw into some kind of dashboard.

Something I am wondering is if I could set it up to where this sends me an SMS or an email when the services are above a certain percentile