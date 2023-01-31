#!/bin/bash
echo "set up and install the inky display service"

# Check if the script is run with superuser privileges
if [ "$(id -u)" != "0" ]; then
  echo "This script must be run as root (with su privileges)"
  exit 1
fi

if [ ! -e "/usbdisk.img" ]; then
  echo "File /usbdisk.img does not exist. Please install the USB Gadget Service first."
  exit 1
fi

# Get the path of the script's folder
script_dir=$(dirname "$0")

# Copy usbGadget.service to /etc/systemd/system/
cp "$script_dir/usbGadget.service" "/etc/systemd/system/"

# Replace the string $PATH with the full path of the install folder
sed -i "s|\$PATH|$script_dir|g" "/etc/systemd/system/usbGadget.service"

# enable the service
systemctl enable  usbGadget.service

# start the service
systemctl start  usbGadget.service

# Copy GadgetPiStartup.service to /etc/systemd/system/
cp "$script_dir/GadgetPiStartup.service" "/etc/systemd/system/"

# Replace the string $PATH with the full path of the install folder
sed -i "s|\$PATH|$script_dir|g" "/etc/systemd/system/GadgetPiStartup.service"

# enable the service
systemctl enable  GadgetPiStartup.service

# Start the service<br>
systemctl start  GadgetPiStartup.service

# finish up 
echo "USB Gadget service is setup. Displaying log output to check for errors"
journalctl --unit=usbGadget.service
