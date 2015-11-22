# leitor de mensagens coap 
# Author: Marcelo B. Almeida 06/11/14
# - O programa inicialmente le o profile do mote atraves do comando /d. 
# Entao descobre quantos parametros tem configurado e entao começa a ler
# o profile de cada um dos parametros, descobrindo datatype e nome do parametro
# entao ele fica ciclicamente (configurado a cada 2 segundos) lendo todos 
# os parametros do mote.
# Este programa salva dados em arquivo txt definido na variavel OUTFILE  
# para configurar o modulo coap :
# 1) IPDEFAULT - alterar para o IP do seu respctivo mote (ou na tela apos inicializacao)
# 2) OUTFILE - contem o nome do arquivo de log que eh salvo na pasta do arquivo *.py
# 3) Ele esta fixo para 6 parametros de leitura - caso configurar um nr menor de parametros 
#    deve ser alterado as linhas com flag PARAMLEITURA
# Para rodar programa:
# 1) abrir este arquivo .py dentro da interface do python (pythongui)
# 2) mandar rodar o programa (F5)
# 3) na janela criada clicar em add.
# 4) enquanto estiver aparecendo na tela estara tambem salvando em arquivo as informacoes geradas
# 5) fechar o programa clicando no botao fechar (X) da tela. Isto fará com que o arquivo seja fechado tambem.
 


import os
import sys
from Tkinter import *
import tkMessageBox
import re
import threading
import struct
from pydispatch import dispatcher
import time
import json

p = os.path.dirname(sys.argv[0])
p = os.path.join(p,'..','..','..','..','coap')
p = os.path.abspath(p)
sys.path.insert(0,p)
#IPDEFAULT = '00:12:4b:00:04:0e:fc:87'
IPDEFAULT = 'bbbb::12:4b00:40e:fc87'
OUTFILE =  'logdata.txt'

contador = 0

from coap import coap
from coap import coapDefines as d
import copy
import random
from Queue import Queue


# Conexao com o Postgresql
# apt-get install python-psycopg2
import psycopg2
import psycopg2.extras

# Configuracoes do banco de dados e coleta dos tempos de conexao
tipo = 3 # OpenWSN

def GravaValores(query):
    # Tenta conectar ao banco de dados
        try:
            conn=psycopg2.connect("dbname='iot' user='postgres' password='postgres'")
            conn.autocommit = True

            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                #query = "INSERT INTO resultados VALUES (DEFAULT, {}, {}, {}, {});".format(timestamp, val1, val2, val3)
                print query
                cur.execute(query)
                return True
           
            except:
                print "Erro ao executar a query."
                return False
    
        except:
            print "Nao foi possivel estabelecer a conexao."
            return False



class WorkerThread(threading.Thread):
    
    RANDOM_MAX_STARTUP_TIME = 10
    BRD_DESC_STATE, PT_DESC_STATE, SCAN_STATE = range(0,3)
    #SCAN_STATE,SCAN_STATE,SCAN_STATE = range(0,3)
    MAX_RETRIES = 5
    #MAX_SCAN_TIMEOUT = 15
    #MIN_SCAN_TIMEOUT = 5
    #MAX_ID_TIMEOUT = 30
    MAX_SCAN_TIMEOUT = 1
    MIN_SCAN_TIMEOUT = 1
    MAX_ID_TIMEOUT = 1
    
    def __init__(self,ip):
        threading.Thread.__init__(self)
        self.crit_sec = threading.Lock()
        self.ip = ip
        self.answer = None
        self.coap = None
        self.running = False
        self.state = WorkerThread.BRD_DESC_STATE
        self.pt_index = 0
        self.brd_desc = None
        self.retries = 0
        self.data = {}
        self.scan_time = WorkerThread.MAX_SCAN_TIMEOUT
        self.id_time = WorkerThread.MAX_ID_TIMEOUT
        dispatcher.connect(self.cancel,signal='QUIT',sender=dispatcher.Any)
        dispatcher.connect(self.cancel,signal='DEL-MOTE',sender=dispatcher.Any)
        dispatcher.connect(self.set_scan_time,signal='SCAN-TIME',sender=dispatcher.Any)
        self.create_coap()
        self.filewr = open(OUTFILE, 'w')
        self.Printtite = False
        
    def create_coap(self):
        if self.coap:
            self.coap.close()
            
        while True:
            try:
                self.coap = coap.coap(udpPort=self.get_random_port())
            except:
                time.sleep(1)
            else:
                break

    def set_scan_time(self,scan_time):
        with self.crit_sec:
            self.scan_time = scan_time
    
    def wait_startup(self):
        time.sleep(random.random()*WorkerThread.RANDOM_MAX_STARTUP_TIME)

    def get_random_port(self):
        return random.randint(49152,65535)
        
    def cancel(self):
        with self.crit_sec:
            print 'Thread cancel',self.ip
            if self.coap:
                self.coap.close()
            self.coap = None
            self.running = False

    def get_uri(self,uri):
        try:
            d=''
            print 'Thread',self.ip,uri
            dispatcher.send(signal='LOG-MSG-MOTE',ip=self.ip,value=uri)
            d = self.coap.GET(uri)
            d = ''.join([ chr(c) for c in d ])
            r = json.loads(d)
        except Exception, e:
            ans = {'ans':None,'error':True, 'error_msg': repr(e), 'data':d}
        else:
            ans = {'ans':r,'error':False}
        return ans
            
    def do_brd_desc(self):
        uri = 'coap://[{0}]/d'.format(self.ip)
        return self.get_uri(uri)

    def do_pt_desc(self,index):
        uri = 'coap://[{0}]/d/pt/{1}'.format(self.ip,index)
        #print 'Thread',self.ip,uri
        return self.get_uri(uri)
    
    def do_value(self,index=-1):
        if index >= 0:
            uri = 'coap://[{0}]/s/{1}'.format(self.ip,index)
        else:            
            uri = 'coap://[{0}]/s'.format(self.ip)
        return self.get_uri(uri)

    def do_write(self,index,value):
        uri = 'coap://[{0}]/s/{1}/{2}'.format(self.ip,index,value)
        self.coap.PUT(uri)

    def run(self):
        global contador
        global tipo

        self.wait_startup()
        self.running = True
        self.pt_index = 0
        self.brd_desc = None
        self.retries = 0
        self.state = WorkerThread.BRD_DESC_STATE
        #print 'Thread', self.ip, 'running'
        while self.running:
            if self.retries > WorkerThread.MAX_RETRIES:
                break
            
            t1 = time.time()

            tempo_inicio = time.time() # Estatisticas - captura o tempo inicial
            # execute current state
            if self.state == WorkerThread.BRD_DESC_STATE:
                ans = self.do_brd_desc()
            elif self.state == WorkerThread.PT_DESC_STATE:
                ans = self.do_pt_desc(self.pt_index)
            elif self.state == WorkerThread.SCAN_STATE:
                ans = self.do_value(self.pt_index)
            else:
                break
            

            # check errors
            if ans['error']:
                dispatcher.send(signal='MOTE-ERROR',ip=self.ip,error=copy.deepcopy(ans['error_msg']+', data:'+ans['data']))
                self.retries = self.retries + 1
                # try to create a new coap connection at each 2 errors
                if(self.retries % 2) == 0:
                    self.create_coap()
                continue

            # calculate next state
            self.retries = 0
            if self.state == WorkerThread.BRD_DESC_STATE:
                dispatcher.send(signal='NEW-MOTE-ID',ip=self.ip,mid=copy.deepcopy(ans['ans']))
                self.brd_desc = ans['ans']
                # wait a response with valid data
                if self.brd_desc:
                    if self.brd_desc['npts'] > 0:
                        self.pt_index = 0
                        self.data = {}
                        self.state = WorkerThread.PT_DESC_STATE
                    else:
                        break
            elif self.state == WorkerThread.PT_DESC_STATE:
                self.data[self.pt_index] = {}
                self.data[self.pt_index]['name'] = ans['ans'][u'n']
                self.data[self.pt_index]['value'] = None
                self.data[self.pt_index]['type'] = ans['ans'][u't']
                dispatcher.send(signal='NEW-MOTE-VALUE',ip=self.ip,value=copy.deepcopy(ans['ans']))
                self.pt_index += 1
                if self.pt_index >= self.brd_desc['npts']:
                    self.state = WorkerThread.SCAN_STATE
                    self.pt_index = 0
            elif self.state == WorkerThread.SCAN_STATE:
                self.data[self.pt_index]['value'] = ans['ans'][u'v']
                dispatcher.send(signal='NEW-MOTE-VALUE',ip=self.ip,value=copy.deepcopy(ans['ans']))
                self.pt_index += 1
                if self.pt_index >= self.brd_desc['npts']:
                    self.pt_index = 0
            else:
                break

            # control loop           
            try:
                lum = self.data[0]['value']
                led = self.data[1]['value']
            except:
                print 'not ready'
                pass
            else:
                keys = self.data.keys()
                keys.sort()

                # rff - imprime valor em arquivo  
                #self.filewr.write(str(keys) + '\n')
                if self.Printtite == False:
                  self.filewr.write('            var1, var2, var3\n')     #(PARAMLEITURA)
                  self.Printtite = True

                #timestamp = time.strftime("[%H:%M:%S]")
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                for k in keys:
                    print k, self.data[k]['name'], self.data[k]['value']
                    # rff - salva dado em arquivo 
                    #if k > 2 :       # (PARAMLEITURA)
                       #lin_nomes = '{0}, {1}, {2}, {3},{4}, {5} \n'.format(self.data[0]['name'], 
                       #                                                     self.data[1]['name'],
                       #                                                     self.data[2]['name'],
                       #                                                     self.data[3]['name'],
                       #                                                     self.data[4]['name'],
                       #                                                     self.data[5]['name'])
                    #lin_vals = '{0} - {1}, {2} \n'.format(timestamp, self.data[0]['value'],
                    #                                                        self.data[1]['value']);
                    #lin_vals = '{} - {}, {}, {}\n'.format(timestamp, self.data[0]['value'],
                    #                                                        self.data[1]['value'],
                    #                                                        self.data[2]['value']);
                    #self.filewr.write(lin_vals)

        
                      
            # sleep the remaining time
            t2 = time.time() - t1
            if self.state == WorkerThread.BRD_DESC_STATE:
                t2 = self.id_time - t2
            else:
                t2 = self.scan_time - t2

            #print 'Thread sleep',self.ip,t2
            if t2 > 0:
                time.sleep(t2)
            else:
                time.sleep(WorkerThread.MIN_SCAN_TIMEOUT)

            contador = contador + 1
            if contador > 6:
                contador = 4
                a = self.data[0]['value']
                b = self.data[1]['value']
                c = self.data[2]['value']

                query = "INSERT INTO medicao VALUES (DEFAULT, '{}', '{}', {}, {}, {});".format(tipo, timestamp, a, b, c)
                
                if GravaValores(query):
                    print "Gravado com sucesso."
                    # Em caso de timeout deve executar 'GravaTempo(0)'

        #print 'Thread end',self.ip
        dispatcher.send(signal='DEL-MOTE',ip=self.ip) 
        self.filewr.close()
        self.cancel()
        
class ThreadScan(object):
    def __init__(self):
        self.running = False
        self.crit_sec = threading.Lock()
        self.mote_list = {}
        self.stats = {}
        dispatcher.connect(self.add_mote,signal='ADD-MOTE',sender=dispatcher.Any)
        dispatcher.connect(self.del_mote,signal='DEL-MOTE',sender=dispatcher.Any)
        dispatcher.connect(self.mote_error,signal='MOTE-ERROR',sender=dispatcher.Any)
        dispatcher.connect(self.new_mote_id,signal='NEW-MOTE-ID',sender=dispatcher.Any)
        dispatcher.connect(self.new_mote_value,signal='NEW-MOTE-VALUE',sender=dispatcher.Any)

    def add_mote(self,ip):
        with self.crit_sec:
            if not self.mote_list.has_key(ip):
                self.mote_list[ip] = { 'task':None }
                self.mote_list[ip]['task'] = WorkerThread(ip)
                self.mote_list[ip]['task'].start()

    def del_mote(self,ip):
        with self.crit_sec:
            if self.mote_list.has_key(ip):
                del self.mote_list[ip]

    def mote_error(self,ip,error):
        with self.crit_sec:
            if self.stats.has_key(ip):
                self.stats[ip]['errors'] = self.stats[ip]['errors'] + 1
            
    def new_mote_id(self,ip,mid):
        with self.crit_sec:
            self.stats[ip] = { 'scans':0, 'errors':0 }

    def new_mote_value(self,ip,value):
        with self.crit_sec:
            self.stats[ip]['scans'] = self.stats[ip]['scans'] + 1

    def get_stats_sum(self):
        keys = self.stats.keys()
        r = { 'errors':0, 'scans':0 ,'alive':len(keys)}
        for ip in keys:
            v = self.stats[ip]
            r['scans'] = r['scans'] + v['scans']
            r['errors'] = r['errors'] + v['errors']
        #print r
        return r
    
class SensorScannerGUI(object):
    def __init__(self, master):
        self.master = master
        self.ipv6_addr = StringVar()
        self.ipv6_addr.set(IPDEFAULT)
        self.status = StringVar()
        self.mote = StringVar()
        self.scan_time = IntVar()
        self.status.set('')
        #self.start = False
        self.msgq = Queue()
        self.scan = ThreadScan()
        self.crit_sec = threading.Lock()
        self.create_gui()
        dispatcher.connect(self.remove_mote_from_list,signal='DEL-MOTE',sender=dispatcher.Any)
        dispatcher.connect(self.mote_error,signal='MOTE-ERROR',sender=dispatcher.Any)
        dispatcher.connect(self.new_mote_id,signal='NEW-MOTE-ID',sender=dispatcher.Any)
        dispatcher.connect(self.new_mote_value,signal='NEW-MOTE-VALUE',sender=dispatcher.Any)
        dispatcher.connect(self.log_msg_mote,signal='LOG-MSG-MOTE',sender=dispatcher.Any)        
        self.master.mainloop()

    def mote_error(self,ip,error):
        with self.crit_sec:
            self.msgq.put(('LOG','ERR {0} {1}'.format(ip,error)))
            self.master.event_generate('<<ProcessMessage>>', when='tail')
            
    def new_mote_id(self,ip,mid):
        with self.crit_sec:
            self.msgq.put(('LOG','ID  {0} {1}'.format(ip,mid)))
            self.master.event_generate('<<ProcessMessage>>', when='tail')

    def log_msg_mote(self,ip,value):
        with self.crit_sec:
            self.msgq.put(('LOG','MSG {0} {1}'.format(ip,value)))
            self.master.event_generate('<<ProcessMessage>>', when='tail')

    def new_mote_value(self,ip,value):
        with self.crit_sec:
            self.msgq.put(('LOG','VAL {0} {1}'.format(ip,value)))
            self.master.event_generate('<<ProcessMessage>>', when='tail')
        
    def process_message(self,event):
        t,m = self.msgq.get()
        if t == 'LOG':
            m = time.strftime("[%H:%M:%S] ") + m
            self.add_log(m)
        elif t == 'STATUS':
            self.status.set(m)
        self.update_status_bar()
        self.master.update_idletasks()

    def add_log(self,msg=''):
        self.log.insert(END,msg + '\n')
        self.log.see(END)
        
    def add_mote(self,event=None):
        if self.validate_ipv6():
            ip = self.ipv6_addr.get()
            ips = [ self.mote_list.get(idx) for idx in range(0,self.mote_list.size())]
            if ip not in ips:
                dispatcher.send(signal='ADD-MOTE',ip=ip)
                self.mote_list.insert(END,ip)

    def remove_mote_from_list(self,ip):
        for idx in range(0,self.mote_list.size()):
            if self.mote_list.get(idx) == ip:
                self.mote_list.delete(idx)
            
    def remove_mote(self,event=None):
        sel = self.mote_list.curselection()
        if sel:
            idx = int(sel[0])
            ip = self.mote_list.get(idx)
            dispatcher.send(signal='DEL-MOTE',ip=ip)

    def start_stop(self,event=None):
        keys = self.scan.stats.keys()
        keys.sort()
        for ip in keys:
            v = self.scan.stats[ip]
            self.add_log('Stats for ' + ip)
            self.add_log('    Scans : {0}'.format(v['scans']))
            self.add_log('    Errors: {0}'.format(v['errors']))
            
    def update_status_bar(self):
        r = self.scan.get_stats_sum()
        m = 'Scan frames {0}, Error frames {1}, Mote alive {2}'.format(r['scans'],r['errors'],r['alive'])
        self.status.set(m)
        
        #self.start = not self.start;
        #if self.start:
        #    self.start_stop_bt['text'] = 'Stop'
        #else:
        #    self.start_stop_bt['text'] = 'Start'
    
    def validate_ipv6(self):
        ipv6 = self.ipv6_addr.get().strip()
        self.ipv6_addr.set(ipv6)

        # http://stackoverflow.com/questions/53497/regular-expression-that-matches-valid-ipv6-addresses
        pattern = r"\b(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|" + \
            r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|" + \
            r"([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|" + \
            r"([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|" + \
            r":((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|" + \
            r"::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]).){3,3}(25[0-5]|" + \
            r"(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|" + \
            r"1{0,1}[0-9]){0,1}[0-9]).){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\b"

        if re.match(pattern, ipv6):
            return True
        else:
            tkMessageBox.showwarning("IPv6","Invalid IPv6 address")
            return False

        return True

    def set_scan_time(self,event=None):
        try:
            v = self.scan_time.get()
        except:
            tkMessageBox.showwarning("Scan Time","Invalid scan time")
        else:
            dispatcher.send(signal='SCAN-TIME',scan_time=v)
            
    def create_gui(self):
        self.master.wm_title("Sensor Data Scanner")

        f = Frame(self.master,padx=5,pady=5)
        Label(f,text="New Mote:").pack(side=LEFT,expand=NO)
        Entry(f,textvariable=self.ipv6_addr,width=20).pack(side=LEFT,expand=YES,fill=X)
        Button(f,text="Add",width=10,command=self.add_mote,default=ACTIVE).pack(side=LEFT,expand=NO)
        f.pack(side=TOP,fill=X)
        f = Frame(self.master,padx=5,pady=5)

        f1 = Frame(f,padx=5)
        Label(f1,text="Mote List:").pack(side=LEFT,expand=NO)
        #p = ['a','b','c']
        #OptionMenu(f, self.mote, *p).pack(side=LEFT,expand=YES,fill=X)
        self.list_ybar = Scrollbar(f1)
        self.list_ybar.pack(side=RIGHT, fill=Y)        
        self.mote_list = Listbox(f1,height=3,yscrollcommand=self.list_ybar.set)
        self.mote_list.pack(side=LEFT,expand=YES,fill=X)
        self.list_ybar.config(command=self.mote_list.yview)
        f1.pack(side=LEFT,expand=YES,fill=X)

        f2 = Frame(f)
        Button(f2,text="Remove",width=10,command=self.remove_mote,default=ACTIVE).pack(side=TOP,expand=NO)
        self.start_stop_bt = Button(f2,text="Stats",width=10,command=self.start_stop,default=ACTIVE)
        self.start_stop_bt.pack(side=TOP,expand=NO)
        f2.pack(side=TOP,fill=X)

        f.pack(side=TOP,fill=X)

        f = Frame(self.master,padx=5,pady=5)
        Label(f,text="Scan time:").pack(side=LEFT,expand=NO)
        Spinbox(f,values=range(1,121),width=5,textvariable=self.scan_time,command=self.set_scan_time).pack(side=LEFT,expand=NO,fill=X)
        f.pack(side=TOP,fill=X)
        
        f = Frame(self.master,padx=5,pady=5)
        self.log_ybar = Scrollbar(f)
        self.log_ybar.pack(side=RIGHT, fill=Y)
        ft=("courier new", 10, "normal")
        self.log = Text(f,width=60,height=15,font=ft,yscrollcommand=self.log_ybar.set)
        self.log.pack(side=TOP, expand=YES, fill=BOTH)
        self.log_ybar.config(command=self.log.yview)
        f.pack(side=TOP,expand=YES,fill=BOTH)

        f = Frame(self.master)
        Label(f,textvariable=self.status,anchor=W,relief=SUNKEN).pack(side=TOP,expand=YES,fill=X)
        f.pack(side=LEFT,expand=YES,fill=X)

        self.scan_time.set(30)
        self.master.bind("<Return>", self.add_mote)
        self.master.bind('<<ProcessMessage>>', self.process_message)

        self.master.protocol("WM_DELETE_WINDOW", self.close)
        
    def close(self):
        dispatcher.send(signal='QUIT')
        self.master.destroy()

SensorScannerGUI(Tk())
