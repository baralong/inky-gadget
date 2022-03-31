# inky-gadget
Scripts etc for the pi zero with inkyPhat

This displays:
1) The name of Raspberry Pi
2) The IP address from wifi and/or USB ethernet gadget
3) Any connected sessions: tty, if connected via the USB, or the ip if a different connection

This requires things are setup similarly to the ethernet and mass storage gadgets as described here https://github.com/thagrol/Guides, also that the backing file for the USB gadget is `/usbdisk.img` mounted at `/usbdisk.d`
