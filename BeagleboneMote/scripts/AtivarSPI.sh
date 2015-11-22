echo "Ativando SPI..."
cp BB-SPI0-01-00A0.dtbo /lib/firmware/
echo BB-SPI0-01 > /sys/devices/bone_capemgr.*/slots

ls -al /dev/spidev*
