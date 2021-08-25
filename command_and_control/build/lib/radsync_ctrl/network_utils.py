# Copyright (C) University College London 2021

# Matt Ritchie <m.ritchie@ucl.ac.uk>
# Piers Beasley <piers.beasley.19@ucl.ac.uk>

# This file is part of RadSync.

# The RadSync program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


# static ip addresses of Raspberry Pis
NODE_0_IP_ADDRESS = "192.168.1.200"
NODE_1_IP_ADDRESS = "192.168.1.201"
NODE_2_IP_ADDRESS= "192.168.1.202"

EXIT_FLAG = "-1"
SERVER_PORT = 25001
BUFFER_SIZE = 1024

import socket
import threading 
import time
from tkinter import *

from . import radsync_network_interface
from . import main_script


'''
Code for Client to connect to RadSync Master node 
'''



class SlaveRadSyncClient():
    

    def start_client(self):
        '''
        create a new thread to run the server in called server_thread
        '''
        self.client_thread = threading.Thread(target=self._setup_client_thread)
        self.client_thread.start()
        
    def _setup_client_thread(self):
      '''
      '''
      self.client_thread = threading.currentThread()
      while True:
          print('running')
          with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.client_socket:    
              self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
              
              # try and connect to server in while loop that only breaks when
              # no error 1 Hz
              while True:   
                try:
                     self.client_socket.connect((NODE_0_IP_ADDRESS, SERVER_PORT)) #connect to server 
                     print('Connected to Node 0 \n')
                     main_script.MainUi.network_text_box.insert(END, 'Connected to Node 0 \n')
                     break
                except Exception as e:
                     print('Connection to Node 0 failed\n')
                     main_script.MainUi.network_text_box.insert(END, 'Connection to Node 0 failed \n')
                     time.sleep(1)
                     continue
            
              # when connected to server listen to port until server initiaites close 
              # or a disconnection flag is received.
              while True:
                    #receive message from server  
                    message = self.client_socket.recv(1024).decode() 
                    #is it a disconnect flag or has the server disocnnected
                    if message == EXIT_FLAG or not message:
                        print("client Shutdown initiated by server\n")
                        break
                    print('message received from server: ', message)
                    radsync_network_interface.radsync_decode_message(message)
                    time.sleep(1)
              self.client_socket.close()
              time.sleep(1)          
    
    def send_message(self,message):
        message = str.encode(message)
        self.client_socket.sendall(message)
    
    
    
    
'''
Code for RadSync Master Node Server
'''


ARESTOR_CONNECTED = False
N1_CONNECTED = False
N2_CONNECTED = False



class MasterRadSyncServer():

    def start_server(self):
        '''
        create a new thread to run the server in called server_thread
        '''
        self.server_thread = threading.Thread(target=self._setup_server_thread)
        self.server_thread.start()
        
    def stop_server(self):
        global ARESTOR_CONNECTED
        '''
        method to shutdown the ThreadedTCPServer 
        '''
        self.server_thread.do_run = False
        self.server.shutdown(socket.SHUT_RDWR)
        self.server.close
        
    def broadcast_to_slaves(self,message):
        global N1_CONNECTED, N2_CONNECTED
        if N1_CONNECTED:
            message = str.encode(message)
            self.radsync_node_1_con.sendall(message)
        if N2_CONNECTED:
            message = str.encode(message)
            self.radsync_node_2_con.sendall(message)
        
    def send_to_arestor(self,message):
        global ARESTOR_CONNECTED
        if ARESTOR_CONNECTED:
            message = str.encode(message)
            self.arestor_con.sendall(message)
        else:
            print('Arestor is not connected')
            
            
        
    def _setup_server_thread(self):
      global ARESTOR_CONNECTED,N1_CONNECTED,N2_CONNECTED
      '''
      Called in a new thread to hosts the ThreadedTCPServer. 
          each time a new client is connected, a new thread is started to deal 
          with the connection. The new connction's thread entry point is handle 
          method of the MyHandle class
      '''
      self.server_thread = threading.currentThread()
      with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as self.server:
          self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
          self.server.bind((NODE_0_IP_ADDRESS,SERVER_PORT))
          self.server.listen(3)
          print('Server Started: ', self.server)
          
          # while loop to listen for connections from slave   
          while (getattr(self.server_thread,"do_run",True)):
              # handle clients
              #listen for connections from slave
              try:
                 con, addr = self.server.accept()
                 
                 if (addr[0] == NODE_1_IP_ADDRESS):
                   self.radsync_node_1_con = con
                   print('RadSync Node 1 Connected')
                   main_script.MainUi.network_text_box.insert(END, 'RadSync Node 1 Connected \n')
                   name = 'RadSync Node 1'
                   self.node1_thread = threading.Thread(target=_handle_client, args=(self.radsync_node_1_con, addr, name))
                   N1_CONNECTED = True
                   self.node1_thread.start()
                  
                 elif (addr[0] == NODE_2_IP_ADDRESS):
                   self.radsync_node_2_con = con
                   print('RadSync Node 2 Connected')
                   main_script.MainUi.network_text_box.insert(END, 'RadSync Node 2 Connected \n')
                   name = 'RadSync Node 2'
                   self.node2_thread = threading.Thread(target=_handle_client, args=(self.radsync_node_2_con, addr, name))
                   N2_CONNECTED = True
                   self.node2_thread.start()
                   
                 else:
                   self.arestor_con = con
                   print('Arestor Command and Control Connected')
                   main_script.MainUi.network_text_box.insert(END, 'Arestor Command and Control Connected \n')
                   name = 'Arestor'
                   self.arestor_thread = threading.Thread(target=_handle_client, args=(self.arestor_con, addr, name))
                   ARESTOR_CONNECTED = True
                   self.arestor_thread.start()
                   

              except Exception as e:
                 print(str(e))
              time.sleep(1)  
          
def _handle_client(con, addr, name):
    global ARESTOR_CONNECTED,N1_CONNECTED,N2_CONNECTED
    '''
    Called in a server_thread to hosts each client connection. 
    a new thread is spawned for each client connection.
    '''
    while True:
        message = con.recv(BUFFER_SIZE)
        if (not message or message.decode() == EXIT_FLAG):
            print (name, ' Disconnected')
            
            main_script.MainUi.network_text_box.insert(END, str(name + ' Disconnected'))
            if name == 'arestor':
                ARESTOR_CONNECTED = False
            if name == 'RadSync Node 1':
                N1_CONNECTED = False
            if name == 'RadSync Node 2':
                N2_CONNECTED = False
            break
        message = message.decode()  
        print(message)
        radsync_network_interface.radsync_decode_message(message)
        print(message)
        time.sleep(1)            
              
     
    