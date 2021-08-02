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

import socket 


class RadSyncServer():
 
   def __init__(self):
      self.slaveConnected = False
      #Setup the network parameters
      self.LocalAddr = "192.168.1.200"
      self.RaspN1Addr = "192.168.1.201"
      self.RaspN2Addr = "192.168.1.202"
      self.Port = 25001
      self.Buffer_Size = 1024
      #create socket
      self.serverLive = False
      self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.tcpSocket.bind((self.LocalAddr, self.Port))
      self.startServer()   
               
   def startServer(self):
      NetworkTextBox.insert(END, "Listening for Slaves ... \n")
      self.tcpSocket.listen(1)
      self.connectionListener = threading.Thread(target=self.ConnectionListener)
      self.connectionListener.start()
      self.serverLive = True
         
   def stopServer(self):
    if self.serverLive == True:
      self.connectionListener.do_run = False
      self.tcpSocket.close()
      self.serverLive = False
      self.slaveConnected = False
      NetworkTextBox.insert(END, "Disconnected from slaves ... \n")
      
   
   def broadcastMessage(self,message):
      self.slave_connection.send(message.encode());
        
   def ConnectionListener(self):
      self.connectionListener = threading.currentThread()
      while (getattr(self.connectionListener, "do_run", True)):
        #listen for connections from slave
        if self.slaveConnected == False:
          try:
             self.con,self.addr = self.tcpSocket.accept()
             if (self.addr[0] == self.RaspN1Addr):
               self.slave_connection = self.con
               NetworkTextBox.insert(END, "Node 1 Connected \n")
               self.slaveConnected = True
             elif (self.addr[0] == self.RaspN2Addr):
               self.slave_connection = self.con
               NetworkTextBox.insert(END, "Node 2 Connected \n")
               self.slaveConnected = True
             else:
               NetworkTextBox.insert(END, "Device connected on IP:" + str(addr[0]) +"\n")
          except(Exception,e):
             print(str(e))
        #listen for message from slave 
        try:
          message = self.con.recv(sys.getsizeof("N1 Trigger Valid"))
          if(not message):
            self.slaveConnected = False
            NetworkTextBox.insert(END, "Slave Disconnected ... \n")
          print("message recieved",message)
          message = str(message.decode()+ '\n\n')
          TextBox.insert(END, message)
          self.broadcastMessage('received')
        except(Exception, e):
          print(str(e))
        time.sleep(0.5)
      


          
          