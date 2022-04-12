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
'''
Notes on trigger validity 

'''


from . import main_script
from . import grclok_1500_popout

import RPi.GPIO as GPIO
import time
from tkinter import *
import datetime

from . import radsync_network_interface as raddic





class Trigger():
    #inialise class level static variables 
    Trigger_Pass = 31   # Trigger Pass Pulse Output Pin for Primary Trigger (RFSoC and BladeRF Trigger)
    Trigger_2_Pass = 33 # Trigger Pass Pulse Output Pin for Secondary Trigger (bladeRad)
    Trigger_or_Pass = 37 # Trigger Pass for holding up OR gate for bladeRAD trigger
    Sync_Pass = 29      # Trigger Pass Pulse Output Pin for Clock Divider Sync
    PPS_OUT = 15        # PPS_OUT from the GPSDO
    
  
    def __init__(self,node):
      #initalise object level variables
      self.Trigger_Pending = False
      self.Epoch_Trigger_Deadline = -1 #set trigger deadline to -1; default before set
      self.Epoch_Time = -1 #set epoch time to -1; default before set
      self.Pulse_Pre_Delay = 0 # set pulse pre delay to 0; default before set
      self.Window_Length = 1 #Trigger window length; default
      self.Delay_Trigger_Sec  = -1   
      self.trigger_duration = -1
      self.unix_gps_trigger_deadline = -1
      # Trigger Variables 
      self.bladeradtriggState = 0
      self.rfsoctriggState = 0
      self.freqdivtriggState = 0
      self.rfsocTrigg = True
      self.bladeradTrigg = True 
      self.freqdivTrigg = True
      self.triggId = 0;
      self.trigg_valadity = False
      self.node = int(node);
     
     
      #Setup Trigger IO Control 
      Low = GPIO.LOW
      GPIO.setwarnings(False)
      GPIO.cleanup()
      GPIO.setmode(GPIO.BOARD)
      GPIO.setup(Trigger.Trigger_Pass, GPIO.OUT)
      GPIO.setup(Trigger.Trigger_2_Pass, GPIO.OUT)
      GPIO.setup(Trigger.Trigger_or_Pass, GPIO.OUT)
      GPIO.setup(Trigger.Sync_Pass, GPIO.OUT)
      GPIO.output(Trigger.Trigger_Pass,Low) # Initial state of Trigger
      GPIO.output(Trigger.Trigger_2_Pass,Low) # Initial state of Trigger 2
      GPIO.setup(Trigger.Trigger_or_Pass, Low) #Intitial State of OR gate input
      GPIO.output(Trigger.Sync_Pass,Low) # Initial state of Sync
      GPIO.setup(Trigger.PPS_OUT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
      #start thread to detect PPS signal and send interupt
      GPIO.add_event_detect(Trigger.PPS_OUT, GPIO.RISING, callback= self.ppsDetected)
    
    def ppsDetected(self, channel):
      #print "PPS Detected" 
      time.sleep(0.3)
      if self.Trigger_Pending == True:
        self.calculateTriggerTime()
        self.Trigger_Pending = False
      self.realTimeCounter() # always query RTC
      
    def setTriggerPending(self,trigger_delay,trigger_duration):
        '''
        public method that can receive a trigger request from UI or Arestor
        '''
        self.Delay_Trigger_Sec = trigger_delay # number of seconds in future to trigger
        self.trigger_duration = trigger_duration #
        self.calculatePulseDelay()
        self.Trigger_Pending = True
      
        
    def setup_slave_trigger(self, unix_trigger_deadline, trigger_duration, trig_id):
      '''
      function to accept trigger from master RadSync node
      entry point to trigger subsystem from network
      '''
      self.unix_gps_trigger_deadline  = float(unix_trigger_deadline)
      self.trigger_duration = int(trigger_duration)
      self.triggId = int(trig_id)
      #print( "Unix Trigger Deadline", self.unix_gps_trigger_deadline) 
      self.set_trigger_type()
      self.calculatePulseDelay()
      
        
    def calculateTriggerTime(self):
      if (main_script.MainUi.is_polling_gpsdo == True):
         self.unix_gps_trigger_deadline = main_script.GPSDO.epochGpsDateTime + self.Delay_Trigger_Sec
         #print( "GPS Trigger Deadline : ", self.unix_gps_trigger_deadline )
         main_script.send_arestor_trigger_ack(False)
         self.broadcastTrigger()
         
      if (main_script.MainUi.is_polling_gpsdo == False):
         date = str(datetime.datetime.now())
         date = date[0:11]
         try:
           gps_Time = main_script.GPSDO.getGpsTime()
         except Exception as e :
           print(str(e))
         #print( "gps_time :", gps_Time)
         date_Time = date + gps_Time 
         #print("date_time :", date_Time)
         p = '%Y-%m-%d %H:%M:%S'
         epoch = datetime.datetime(1970, 1, 1)
         #print("epoch :", epoch)
         self.Epoch_Time = (datetime.datetime.strptime(date_Time,p) - epoch).total_seconds()
         #print("epoch_Time =", self.Epoch_Time)
         self.Epoch_Trigger_Deadline = self.Epoch_Time + self.Delay_Trigger_Sec #set trigger epoch time 
        # print("Epoch Trigger Deadline", self.Epoch_Trigger_Deadline)
         #self.realTimeCounter()
         self.broadcastTrigger()
      
    def broadcastTrigger(self):
        '''
        function to initiate broadcast of trigger request to slave nodes and 
        send ack to Arestor if connected
        '''
        if self.node == 0:
            #print('broadcast trigger')
            message = raddic.create_radsync_trig_req_message(self.unix_gps_trigger_deadline, self.trigger_duration, self.triggId)
            main_script.Server.broadcast_to_slaves(message)

      
    def triggerSelect(self):      
      #Query UI trigger check boxes
      if main_script.MainUi.rfsoctriggState.get() == 1:
        self.rfsocTrigg = True
      else:
        self.rfsocTrigg = False
      if main_script.MainUi.bladeradtriggState.get() == 1:
        self.bladeradTrigg = True
      else:
        self.bladeradTrigg = False
      if main_script.MainUi.freqdivtriggState.get() == 1:
        self.freqdivTrigg = True
      else:
        self.freqdivTrigg = False
      
      #Set Trigger Id
      if (self.freqdivTrigg == False and self.bladeradTrigg == False and self.rfsocTrigg == True) :
        self.triggId = 1
      elif (self.freqdivTrigg == False and self.bladeradTrigg == True and self.rfsocTrigg == False) :
        self.triggId = 2
      elif (self.freqdivTrigg == False and self.bladeradTrigg == True and self.rfsocTrigg == True) :
        self.triggId = 3
      elif (self.freqdivTrigg == True and self.bladeradTrigg == False and self.rfsocTrigg == False) :
        self.triggId = 4
      elif (self.freqdivTrigg == True and self.bladeradTrigg == False and self.rfsocTrigg == True) :
        self.triggId = 5
      elif (self.freqdivTrigg == True and self.bladeradTrigg == True and self.rfsocTrigg == False) :
        self.triggId = 6
      elif (self.freqdivTrigg == True and self.bladeradTrigg == True and self.rfsocTrigg == True) :
        self.triggId = 7
    
    def set_trigger_type(self):   
      if self.triggId  == 1:
        self.freqdivTrigg = False 
        self.bladeradTrigg = False 
        self.rfsocTrigg = True
      elif self.triggId == 2:
        self.freqdivTrigg = False 
        self.bladeradTrigg = True
        self.rfsocTrigg = False
      elif self.triggId  == 3:
        self.freqdivTrigg = False
        self.bladeradTrigg = True 
        self.rfsocTrigg = True
      elif self.triggId  == 4:
        self.freqdivTrigg = True 
        self.bladeradTrigg = False 
        self.rfsocTrigg = False 
      elif self.triggId  == 5:
        self.freqdivTrigg = True 
        self.bladeradTrigg = False 
        self.rfsocTrigg = True
      elif self.triggId  == 6:
        self.freqdivTrigg = True
        self.bladeradTrigg = True 
        self.rfsocTrigg = False
      elif self.triggId == 7:
        self.freqdivTrigg = True
        self.bladeradTrigg = True 
        self.rfsocTrigg = True
    
    def calculatePulseDelay(self):
      self.Pulse_Pre_Delay = 1 + 0.5*main_script.GPSDO.PPSPulseWidth*0.000000001 - 0.5*self.Window_Length
      #print("Pulse Pre_delay", str(self.Pulse_Pre_Delay))

      
    def realTimeCounter(self):
      print("Trigger Deadline: ", self.unix_gps_trigger_deadline)
      print("Current time", main_script.GPSDO.epochGpsDateTime)
      if self.unix_gps_trigger_deadline != -1: #only clock RTC if there is a trigger time set.
         delta = self.unix_gps_trigger_deadline - main_script.GPSDO.epochGpsDateTime
         main_script.MainUi.trigger_countdown_text.set("Time until Trigger: " + str(delta))
         if (delta == 1) or (delta < -1):
            GPIO.remove_event_detect(Trigger.PPS_OUT)
            self.sendTrigger() 
            self.unix_gps_trigger_deadline = -1 # reset the epoch trigger deadline
            GPIO.add_event_detect(Trigger.PPS_OUT, GPIO.RISING, callback= self.ppsDetected)
      if self.Epoch_Trigger_Deadline != -1: #only clock RTC if there is a trigger time set.
        self.Epoch_Time += 1 # increment epoch time each time the RTC is clocked.
        delta = self.Epoch_Trigger_Deadline - self.Epoch_Time
        main_script.MainUi.trigger_countdown_text.set("Time until Trigger: " + str(delta))
        print("old trigger")
        if delta == 1:
          self.sendTrigger()
          self.Epoch_Trigger_Deadline = -1 # reset the epoch trigger deadline
      
        
        
        
        
    def sendTrigger(self):
      High = GPIO.HIGH
      Low = GPIO.LOW  
      time.sleep(self.Pulse_Pre_Delay-0.3) # allow the current pulse to pass
      try:
          if self.rfsocTrigg == True:
            GPIO.output(Trigger.Trigger_Pass, High)
            print("RFSoC Trigger Pass")
            
          if self.bladeradTrigg == True:
            GPIO.output(Trigger.Trigger_2_Pass, High)
            print("bladeRAD Trigger Pass")
            
          if self.freqdivTrigg == True:
            GPIO.output(Trigger.Sync_Pass, High)
            print("Frequency Divider Trigger Pass")
          
          time.sleep(self.Window_Length*0.5) # open the window for an appropriate time
         
          # if bladeRAD trigger - asssert or gate high halfway AND gate HIGH duration   
          if self.bladeradTrigg == True:
              GPIO.output(Trigger.Trigger_or_Pass, High) 
          

          # pause for half AND gate HIGH duration   
          time.sleep(self.Window_Length*0.5) # open the window for an appropriate time
          GPIO.output(Trigger.Trigger_Pass, Low) # ensure the pass pulse has gone low
          GPIO.output(Trigger.Trigger_Pass, Low)
          GPIO.output(Trigger.Trigger_Pass, Low)
          GPIO.output(Trigger.Trigger_2_Pass, Low) # ensure the pass pulse has gone low
          GPIO.output(Trigger.Trigger_2_Pass, Low)
          GPIO.output(Trigger.Trigger_2_Pass, Low)
          GPIO.output(Trigger.Sync_Pass, Low) # ensure the pass pulse has gone low
          GPIO.output(Trigger.Sync_Pass, Low)
          GPIO.output(Trigger.Sync_Pass, Low)
          
          
          #check trigger valadity
          if ((main_script.GPSDO.epochGpsDateTime - self.unix_gps_trigger_deadline ) == 0):
              self.trigg_valadity = True
              main_script.MainUi.trigger_text_box.insert(END, 'Trigger Valid\n')
          else:
            main_script.MainUi.trigger_text_box.insert(END, 'Trigger Error of ' + str(int(main_script.GPSDO.epochGpsDateTime - self.unix_gps_trigger_deadline )) + ' s \n')     
            self.trigg_valadity = False

         
          # pause for trigger duration if bladeRad trigger requested
          if self.bladeradTrigg == True:
              time.sleep(self.trigger_duration-0.5)
              print("trigger duration ",self.trigger_duration)
          GPIO.output(Trigger.Trigger_or_Pass, Low)
          GPIO.output(Trigger.Trigger_or_Pass, Low)
          GPIO.output(Trigger.Trigger_or_Pass, Low)
          
          # broadcast trigger valadity to other radar or master node
          self._broadcast_trigger_validity(self.trigg_valadity)
          
          main_script.MainUi.trigger_countdown_text.set("Time until Trigger: Nil") # reset the trigger label
          if self.node == 0:
            main_script.MainUi.trigger_time_entry_box.configure(state=NORMAL)
      except Exception as e:
          print(str(e))
          os._exit(1)
          
          
          
          
    def _broadcast_trigger_validity(self,this_node_validity):
        if self.node == 0:
            #pause to ensute all other nodes reponses are received
            time.sleep(2)
            #send validity message to the Arestor System
            message = raddic.create_arestor_trig_validity_message(this_node_validity,main_script.System_tracker.node_1_trig_validity,main_script.System_tracker.node_2_trig_validity)
            main_script.Server.send_to_arestor(message)
            main_script.Server.disconnect_from_arestor()
            #reset trigger states
            main_script.System_tracker.reset_states()
            
        else:
            #send validity message to master node
            message = raddic.create_radsync_trig_validity_message(self.node, this_node_validity)
            main_script.Client.send_message(message)