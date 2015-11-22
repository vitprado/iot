#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Author: Vitor Hugo Prado Cardoso (10/11/2015)
#
#
# Servidor Socket para receber dados via ethernet e registrar
# os dados em arquivo txt.
#

import sys
import socket
import time
import psycopg2
import psycopg2.extras

# Parametros de configuracao
HOST = '' 
PORT = int(sys.argv[1])
backlog = 5 
SIZE = 1024 
DELAY = 0.1 # Intervalo de varredura

tipo = 1 # Beaglebone Wifi

# Configuracao da conexao Ethernet
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
s.bind((HOST,PORT))
s.listen(backlog) 


def CapturaMedicao():
    # Tenta conectar ao banco de dados
    try:
        conn=psycopg2.connect("dbname='postgres' user='postgres' password='mypass'")

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute("""SELECT m.sensor0, m.sensor1, m.sensor2, m.sensor3, m.sensor4, m.sensor5 from medicao as m order by m.id_medicao DESC limit 1""")
            rows = cur.fetchall()
            #print rows
            return rows
        
        except:
            print "Erro ao executar a query."
            return False

    except:
        print "Nao foi possivel estabelecer a conexao."
        return False


# Loop de leitura
while True:
    client, address = s.accept()
    read = client.recv(SIZE) # Recebe a mensagem do client
    #timestamp = time.strftime("[%H:%M:%S]")
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    # Finaliza servidor socket
    if (read == 'close'):
        print 'Comando \'close\' recebido. Finalizando o programa.'
        client.close()
        s.close()
        break

    # Verifica mensagem recebida
    if (read == 'leitura'):
        
        data = CapturaMedicao()

        # Formata a mensagem para salvar no arquivo de texto
        query = "INSERT INTO medicao VALUES (DEFAULT, '{}', '{}', {}, {}, {});".format(tipo, timestamp, *data[0])
        #leitura_data =  '{} - {}, {}, {}, {}, {}, {}'.format(timestamp, *data[0])
        
        # Envia aviso de recebimento para o cliente
        client.send(query)        

    	print 'Enviado: ', query
        
    else:
	    print 'Comando invalido: ', data

    client.close()

    time.sleep(DELAY)

