# Overview
A smart usb drive made from:
1. [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)
2. [Pimoroni InkyPHAT (red & black)](https://shop.pimoroni.com/products/inky-phat?variant=12549254217811)
3. 128Gb micro SD card
4. [Flirc Raspberry Pi Zero case](https://flirc.tv/products/flirc-raspberrypizero?variant=42687976833252) (hacked up a bit)

Borrowing from the ethernet and mass storage gadgets described here: https://github.com/thagrol/Guides using `libcomposite` you plug it in and it appears as:
* USB Ethernet
* USB Serial port
* USB storage

The display shows:
* Name of the device
* Space on the external storage
* When powered and connected:
  * network addresses (wifi & USB) 
  * any connections (TTY is com port, SSH is via network)
* When disconnected or unpowered (assuming the Pi was shut down cleanly)
  * owner details

The display checks device state every 30 seconds, if there are any changes it refreshes.

# Screen shots
![on](https://user-images.githubusercontent.com/225905/169946109-321233d4-dea4-4b42-9abe-ed2547084d6b.jpg)
![off](https://user-images.githubusercontent.com/225905/169946133-1ec556a2-a3d0-4a65-b5ab-6477758cf063.jpg)

The owner details can be stored in a file called `owner.json` the script folder, but the code also looks for `owner.json` on the root of the mass storage. 

Icons used are from [Font Awesome](https://fontawesome.com/icons)

# Setup
## Hardware
When installed in the case standard header pins stick out really far, I ended up soldering the pins upside down so the short pins were pointing up. I found the top of the pins were about level with the hole in the top of the Flirc case and it was pretty tidy. If you already have header pins on your pi you could trim them, or just let the inky phat sit a bit higher. To fit everything on nicely I cut out parts of the case top (see below)
![phat off](https://user-images.githubusercontent.com/225905/169948230-40e54025-1518-4301-ba9a-d1d421de4938.jpg)
![side view](https://user-images.githubusercontent.com/225905/169948231-e225a1cd-1dbb-46d0-a334-5428dd5d8405.jpg)

All this is optional, other cases would work just as well, but I really liked the final package.

## Software
### Assumptions
* You have the inkyPHAT and related software installed and it runs as root (i.e. `sudo ...`) the service will run as root, so it's good to test it
* The files for this are placed in `/home/pi/dev`. If you put them somewhere else you'll need to edit `GadgetPiStartup.service`. The latest version of the Raspberry Pi Imager ***does not*** default to using the `pi` user, so it's likely you'll have a different location.
* You can login to your pi via ssh etc. This doesn't cover headless pi setup.
* You have a basic understanding of doing stuff on a raspberry pi, particularly in headless mode

### Setup
You'll need the InkyPHAT ocd n the pi to verify all this actually works, also the `GadgetPiStartup.py` will probably fail if it's not plugged in.

### Basic prerequisites
1. Start with a clean install of Raspbian set up as per the above assumptions 
2. Enable usb gadget mode by editing `/boot/config.txt` at the end, under `[all]` add<br>
`dtoverlay=dwc2`<br>
`enable_uart=1`
3. Install and test the inkyPHAT libraries, their one liner should work <br>
`curl https://get.pimoroni.com/inky | bash`
    * *Optional:* you can test the install with the included examples
4. Reboot the Raspberry Pi<br>
`sudo shutdown -r now`
5. Install git<br>
`sudo apt install git`
6. Clone this repo<br>
`md dev;cd dev` # optional<br>
`git clone https://github.com/baralong/inky-gadget.git`<br>
`cd inky-gadget`
7. If you didn't clone to the `dev` directory: 
    1. Edit `GadgetPiStartup.service` so the `ExecStart` points to the full path of `GadgetPiStartup.py`
    2. Edit `GadgetPiStartup.service` so the `ExecStart` points to the full path of `usbGadget.sh`
### Set up the mass storage backing file and usb gadget
8. Install exfat support needed for the mass storage device<br>
`sudo apt-get install exfat-fuse exfat-utils`
9. Allocate space for the mass storage device (e.g. 32GB)<br>
*you can check the available disk space with `df -h` look for the `/` mount point*<br>
`sudo fallocate -l 32GB /usbdisk.img`
10. Format the image (volume name of `gadget-pi` is used here)<br>
`sudo mkfs.exfat -n gadget-pi /usbdisk.img`
### Create and run the `usbGadget` service
11. Copy the service configuration<br>
`sudo cp usbGadget.service /etc/systemd/system/`
12. Enable the service<br>
`sudo systemctl enable  usbGadget.service`
13. Start the service<br>
`sudo systemctl start  usbGadget.service`
14. Check for errors.<br>
`sudo journalctl --unit=usbGadget.service` 
    * At this point you should be able to plug the Raspberry Pi in and connect via the USB serial port or the USB ethernet port
    * **Note:** you may need to install additional CDC-ECM drivers for the ethernet port to work under windows
### Create and run the `GadgetPiStartup` service (used for the inky display)
15. Install extra python libraries used by the service<br>
`sudo pip3 install ifcfg "Pillow>=9.0" psutil`
16. Test the script:<br>
`sudo python3 GadgetPiStartup.py`<br>
You should see the InkyPHAT displaying the details as above. Terminate with `<ctrl>-C`
    * **Note** if you get an error `libopenjp2.so.7: cannot open shared object file: ...` then run<br>
`sudo apt-get install libopenjp2-7 `
17. Copy the service configuration<br>
`sudo cp GadgetPiStartup.service /etc/systemd/system/`
18. Enable the service<br>
`sudo systemctl enable  GadgetPiStartup.service`
19. Start the service<br>
`sudo systemctl start  GadgetPiStartup.service`
20. Check for errors.<br>
`sudo journalctl --unit=GadgetPiStartup.service` 
### You're all done!!
21. Reboot and make sure the services start up correctly<br>
`sudo shutdown -r now`

## Owner Details
These details are stored in a file called `owner.json` there's a sample stored in the repo.
```
{
    "name": "Unspecified User",
    "email": "fake@fake.com",
    "phone": "+61 # #### ####",
    "twitter": "@not a real thing"
}
```
You can edit the file in place, or, make a copy to the root of the mass storage device from a connected computer and use it there.

# Known issues
1. If you disconnect power or somehow shut the pi down abruptly it won't redraw the screen to show the owner info. The screen & pi need to be powered for it to change, but if you shut down cleanly it will.
2. If you run `sudo reboot` instead of `shutdown -r now` the service doesn't get time to finish redrawing the screen before exiting
3. You can only really shut down cleanly if you are connected to the pi via ssh or the USB-serial port
4. The mass storage device is pretty slow. Possibly a faster SD card would work, but I suspect the bottleneck is USB2 and the layers of software between the USB port and the image.

# Future changes:
The main thing I'd like is some way to interact with the Raspberry Pi, other than remoting into it. There's not a lot of room, but these are the options as I see them:
1. Buttons! There's some room to the left of the inky screen above the case cover. There are some [spare pins](https://pinout.xyz/pinout/inky_phat) though wiring them up could be tricky.
2. An accelerometer... it could detect taps and movement/orientation. I2C would probably be best, but, again, wiring it up would be hard
3. Dropping files onto the mass storage. No hardware required, but the drive is read only, so it'd need a way to detect changes.
4. Including the human interface device gadget mode, but I'm not sure what I'd use it for. If I had buttons and a menu system, it could be used for keyboard macros (probably) or mouse jiggling 

The other thing that I'd really like is faster screen refreshes. This would allow some kind of menu system. A bit like the [Pimoroni Badger](https://shop.pimoroni.com/products/badger-2040?variant=39752959852627)

One other thing would be to have scripts stored on the mass storage, that the pi could execute as required. Unfortunately there are some security issues there and working out when to run them would be challenging.


