# POTU's Server Checker

## Summary
This program is designed to allow home-labbers to quickly check a homelab running Proxmox, including pulling main server statistics, virtual machine statistics and writing some of the core information to a log file once per week. Also sends out emails based on things like usb detections and virtual machine activity.

## Maintainer(s)
Nolan Abbott - https://github.com/ThePresidentofTheUniverse

## Modules to Install
There are several modules that need to be installed for this program to function. Please install the following modules shown below:
- psutil - https://psutil.readthedocs.io/stable/
- cpuinfo - https://pypi.org/project/py-cpuinfo/
- proxmoxmanager - https://pypi.org/project/proxmoxmanager/
- usb-monitor 1.23 - https://pypi.org/project/usb-monitor/
- proxmoxer - https://github.com/proxmoxer/proxmoxer

## Example output
Below is an example of the output you will receive in the log files.

```
Currently null
```