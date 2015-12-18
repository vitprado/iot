# Comandos para serem executados no Linux para permitir o compartilhamento
# da internet pela porta USB

sudo iptables -A POSTROUTING -t nat -j MASQUERADE
sudo echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward > /dev/null

# Quando se usa mais do que uma beaglebone no mesmo computador, pode haver
# conflito nas credenciais do SSH, este comando limpa as credenciais no
# computador.

ssh-keygen -R 192.168.7.2

# Comando para estabelecer conexão com a Beaglebone conectava via USB 
# (por padrão com IP 192.168.7.2, usuário root e sem senha)
ssh root@192.168.7.2

