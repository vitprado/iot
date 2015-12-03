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

# Parametros de configuracao
OUTFILE = 'logdata.txt'

host = '192.168.1.105'
tipo = 1 # Beaglebone Wifi
codigo = 0

#host = 'beaglebone'
#tipo = 2 # Beaglebone cabo

#port = int(sys.argv[1])
port = 5000
size = 1024 
#delay = 1


def GravaTempo(tempo):
    # Tenta conectar ao banco de dados
        try:
            conn=psycopg2.connect("dbname='iot' user='postgres' password='postgres'")
            conn.autocommit = True

            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                query = "INSERT INTO resultados VALUES (DEFAULT, DEFAULT, {}, '{}', '{}');".format(tempo, tipo, codigo)
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
    try:
        tempo_inicio = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.connect((host,port))
        s.send('leitura') 
        data = s.recv(size) 
        s.close()
        tempo_fim = time.time()
        tempo = tempo_fim - tempo_inicio
        if GravaTempo(tempo):
            print "Gravado com sucesso."

    except:
        GravaTempo(0)

