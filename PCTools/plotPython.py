import numpy as np
import scipy.stats as stats
import time
import psycopg2
import psycopg2.extras
from decimal import *
import matplotlib.patches as mpatches
import matplotlib.pyplot as pl

queryResultados1 = """select ceil(r.tempo*1000)::int from resultados as r where r.codigo = '3' and r.tempo < 1 order by r.tempo ;"""
queryResultados2 = """select ceil(r.tempo*1000)::int from resultados as r where r.codigo = '5' and r.tempo < 1 order by r.tempo ;"""
queryResultados3 = """select ceil(r.tempo*1000)::int from resultados as r where r.codigo = '6' and r.tempo < 1 order by r.tempo ;"""
queryResultados4 = """select ceil(r.tempo*1000)::int from resultados as r where r.codigo = '7' and r.tempo < 1 order by r.tempo ;"""
queryResultados5 = """select ceil(r.tempo*1000)::int from resultados as r where r.codigo = '10' and r.tempo < 1 order by r.tempo ;"""
queryMedia1 = """select ceil(avg(r.tempo*1000))::int from resultados as r where r.codigo = '3' and r.tempo < 1;"""
queryMedia2 = """select ceil(avg(r.tempo*1000))::int from resultados as r where r.codigo = '5' and r.tempo < 1;"""
queryMedia3 = """select ceil(avg(r.tempo*1000))::int from resultados as r where r.codigo = '6' and r.tempo < 1;"""
queryMedia4 = """select ceil(avg(r.tempo*1000))::int from resultados as r where r.codigo = '7' and r.tempo < 1;"""
queryMedia5 = """select ceil(avg(r.tempo*1000))::int from resultados as r where r.codigo = '10' and r.tempo < 1;"""

def CapturaMedicao(query):
    # Tenta conectar ao banco de dados
    try:
        conn=psycopg2.connect("dbname='iot' user='postgres' password='postgres'")

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute(query)
            rows = cur.fetchall()
            return rows
        
        except:
            print "Erro ao executar a query."
            return False

    except:
        print "Nao foi possivel estabelecer a conexao."
        return False

dados = CapturaMedicao(queryResultados1)
fit = stats.norm.pdf(dados, np.mean(dados), np.std(dados))
pl.plot(dados,fit,'--')
media = CapturaMedicao(queryMedia1)
pl.axvline(media)

dados = CapturaMedicao(queryResultados2)
fit = stats.norm.pdf(dados, np.mean(dados), np.std(dados))
pl.plot(dados,fit,'--')
media = CapturaMedicao(queryMedia2)
pl.axvline(media)

dados = CapturaMedicao(queryResultados3)
fit = stats.norm.pdf(dados, np.mean(dados), np.std(dados))
pl.plot(dados,fit,'--')
media = CapturaMedicao(queryMedia3)
pl.axvline(media)

dados = CapturaMedicao(queryResultados4)
fit = stats.norm.pdf(dados, np.mean(dados), np.std(dados))
pl.plot(dados,fit,'--')
media = CapturaMedicao(queryMedia4)
pl.axvline(media)

dados = CapturaMedicao(queryResultados5)
fit = stats.norm.pdf(dados, np.mean(dados), np.std(dados))
pl.plot(dados,fit,'--')
media = CapturaMedicao(queryMedia5)
pl.axvline(media)

pl.xlabel('Tempo (ms)')
pl.ylabel('Distribuicao Gaussiana')
pl.title('Tempo de resposta')
pl.show()














