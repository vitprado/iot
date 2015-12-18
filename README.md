# iot
Projeto de Internet das Coisas (Internet of Things) usando CoAP (by OpenWSN protocol stacks) e Beaglebone Black via Socket Python.

- BeagleboneClient: Contém os arquivos que devem ser executados no computador.
- BeagleboneMote: Contém os arquivos que devem ser executados na Beaglebone.
- OpenWSNClient: Contém os arquivos que devem ser executados no client CoAP OpenWSN (computador). 
- PCTools: Contém arquivos para configuração e leitura do banco de dados PostgreSQL.

### BeagleboneBlack

Primeiros passos para preparar o microcontrolador (utilizando LINUX):

#### 1- Ativar a porta SPI:

Para ativar a porta SPI na Beaglebone, copie o arquivo:
iot/BeagleboneMote/scripts/BB-SPI0-01-00A0.dtbo para a Beaglebone e execute
os comandos a seguir.
```sh
cp BB-SPI0-01-00A0.dtbo /lib/firmware/
echo BB-SPI0-01 > /sys/devices/bone_capemgr.*/slots
ls -al /dev/spidev*
```

ou pode-se utilizar este tutorial, de onde foram tirados os passos mostrados anteriormente:
- http://elinux.org/BeagleBone_Black_Enable_SPIDEV

### 2- Instalar o PostgreSQL

Caso esteja utilizando a beaglebone via USB, para habilitar o uso da internet
é necessário executar os comandos a seguir:
```sh
sudo iptables -A POSTROUTING -t nat -j MASQUERADE
sudo echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward > /dev/null
```

Caso haja conflito nas credenciais SSH, utilizar o comando abaixo:
```sh
ssh-keygen -R 192.168.7.2
```

Em seguida estabelecer conexão com a Beaglebone conectava via USB (por padrão com IP 192.168.7.2, usuário root e sem senha)
```sh
ssh root@192.168.7.2
```

No terminal da Beaglebone, executar
```sh
/sbin/route add default gw 192.168.7.1
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
```