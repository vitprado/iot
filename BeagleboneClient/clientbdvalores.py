#!/usr/bin/env python 
# -*- coding: utf-8 -*-
#
# Author: Vitor Hugo Prado Cardoso (10/11/2015)
#
#
# Servidor Socket para receber dados via ethernet e registrar
# os dados em arquivo txt.
#
#

import sys
import socket 
import time
import math

# apt-get install python-psycopg2
import psycopg2
import psycopg2.extras

host = '192.168.1.105'
tipo = 1 # Beaglebone Wifi

#host = 'beaglebone'
#tipo = 2 # Beaglebone cabo

#port = int(sys.argv[1])
port = 5000
size = 1024 
#delay = 1


def ExecutaQuery(query):
    # Tenta conectar ao banco de dados
        try:
            conn=psycopg2.connect("dbname='iot' user='postgres' password='postgres'")
            conn.autocommit = True

            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                print query
                cur.execute(query)
                return True
           
            except:
                print "Erro ao executar a query."
                return False
    
        except:
            print "Nao foi possivel estabelecer a conexao."
            return False


while True:
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    try:
        tempo_inicio = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.connect((host,port))
        s.send('leitura') 
        query = s.recv(size) 
        s.close()

        tempo_fim = time.time()
        deltat = tempo_fim - tempo_inicio


        # Faz consulta no intervalo de 3s
        if deltat < 3:
            delay = 3 - deltat
            time.sleep(delay)
        
        if ExecutaQuery(query):
            print "Gravado com sucesso."

    except:
        query = "INSERT INTO medicao VALUES (DEFAULT, '{}', '{}', 0, 0, 0);".format(tipo, timestamp)
        ExecutaQuery(query)

