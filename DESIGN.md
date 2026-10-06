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


Since this is for my own home-lab server, these are the things that I would like to check or pull information from and throw into some kind of dashboard.

Something I am wondering is if I could set it up to where this sends me an SMS or an email when the services are above a certain percentile