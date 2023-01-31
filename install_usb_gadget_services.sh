#!/bin/bash
echo "set up and install the USB Gadget Service"
echo "You will be prompted for the amount of space to allocate for the mass storage gadget"
echo "this will appear as the USB drive, to create this file the packages exfat-fuse and exfat-utils will be installed "

# Check if the script is run with superuser privileges
if [ "$(id -u)" != "0" ]; then
  echo "This script must be run as root (with su privileges)"
  exit 1
fi

# Install exfat-fuse and exfat-utils
if ! apt-get install -y exfat-fuse exfat-utils; then
  echo "Installation of exfat-fuse and exfat-utils failed, exiting."
  exit 1
fi

# Get the available space in the root partition
available_space=$(df / --output=avail | tail -n 1)
available_space_gb=$((available_space / 1024 / 1024 /1024))

# Prompt the user for the desired size of the file
read -p "Enter the desired size of the mass storage gadget (in GB, less than $available_space_gb GB): " size

# Loop until the user enters a valid size
while [ $size -gt $available_space_gb ]; do
  echo "The size you entered is too big, please enter a smaller size."
  read -p "Enter the desired size of the mass storage gadget (in GB, less than $available_space_gb GB): " size
done

# Create the /usbdisk.img file with the desired size
if ! fallocate -l $size"G" /usbdisk.img; then
  echo "Creation of /usbdisk.img failed, exiting."
  exit 1
fi

# format /usbdisk.img as exfat
if ! mkfs.exfat -n gadget-pi /usbdisk.img; then
echo "Formatting of /usbdisk.img as exfat failed, exiting."
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

# finish up 
echo "USB Gadget service is setup. Displaying log output to check for errors"
journalctl --unit=usbGadget.service
