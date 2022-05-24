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
You'll need the InkyPHAT in the pi to verify all this actually works, also the `GadgetPiStartup.py` will probably fail if it's not plugged in.

1. Start with a clean install of Raspbian set up as per the above assumptions 
2. Install and test the inkyPHAT libraries, their one liner should work
```
  curl https://get.pimoroni.com/inky | bash
```
3. Copy this repo to your chosen location
4. Edit `GadgetPiStartup.service` so the `ExecStart` points to the full path of `GadgetPiStartup.py`
5. `sudo cp usbGadget.sh /boot/`
6. Install exfat support
```
sudo apt-get install exfat-fuse
sudo apt-get install exfat-utils 
```
7. `sudo fallocate -l `  disk size ` /usbdisk.img`
8. `sudo mkfs.exfat -n ` volume name ` /usbdisk.img`
9. `sudo nano /boot.config.txt` at the end, under `[all]` add
```
dtoverlay=dwc2
enable_uart=1
```
10. `sudo python3 GadgetPiStartup.py` this should display stuff on the InkyPHAT
11. `sudo cp usbGadget.service /etc/systemd/system/`
12. `sudo systemctl enable  usbGadget.service`
13. `systemctl start  usbGadget.service`
14. `sudo journalctl --unit=usbGadget.service` check for errors. (Troubleshooting this is left as an exercise for the reader :wink:)
15. `sudo cp GadgetPiStartup.service /etc/systemd/system/`
16. `sudo systemctl enable  GadgetPiStartup.service`
17. `systemctl start  GadgetPiStartup.service`
18. `sudo journalctl --unit=GadgetPiStartup.service` check for errors. (Troubleshooting ...)
19. `sudo shutdown -r now`

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
2. You can only really shut down cleanly if you are connected to the pi via ssh or the USB-serial port.
3. The mass storage device is pretty slow

# Future changes:
The main thing I'd like is some way to interact with the Raspberry Pi, other than remoting into it. There's not a lot of room, but these are the options as I see them:
1. Buttons! There's some room to the left of the inky screen above the case cover. There are some [spare pins](https://pinout.xyz/pinout/inky_phat) though wiring them up could be tricky.
2. An accelerometer... it could detect taps and movement/orientation. I2C would probably be best, but, again, wiring it up would be hard
3. Dropping files onto the mass storage. No hardware required, but the drive is read only, so it'd need a way to detect changes.

The other thing that I'd really like is faster screen refreshes. This would allow some kind of menu system. A bit like the [Pimoroni Badger](https://shop.pimoroni.com/products/badger-2040?variant=39752959852627)

One other thing would be to have scripts stored on the mass storage, that the pi could execute as required. Unfortunately there are some security issues there and working out when to run them would be challenging.


