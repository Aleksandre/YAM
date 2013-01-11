
unzip 2012-12-16-wheezy-raspbian.zip
sudo dd bs=1M if=2012-12-16-wheezy-raspbian.img of=/dev/sdc
diskutil eject /dev/sdc