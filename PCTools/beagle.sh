sudo iptables -A POSTROUTING -t nat -j MASQUERADE
sudo echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward > /dev/null

ssh-keygen -R 192.168.7.2
ssh root@192.168.7.2

