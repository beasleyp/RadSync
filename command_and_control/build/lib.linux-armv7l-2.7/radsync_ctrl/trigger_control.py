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






import RPi.GPIO as GPIO
import time



class Trigger():
    #inialise class level static variables 
    Trigger_Pass = 31   # Trigger Pass Pulse Output Pin for Primary Trigger (RFSoC and BladeRF Trigger)
    Trigger_2_Pass = 33 # Trigger Pass Pulse Output Pin for Secondary Trigger (bladeRad)
    Sync_Pass = 29      # Trigger Pass Pulse Output Pin for Clock Divider Sync
    PPS_OUT = 15        # PPS_OUT from the GPSDO
  
    def __init__(self):
      #initalise object level variables
      self.Trigger_Pending = False
      self.Epoch_Trigger_Deadline = -1 #set trigger deadline to -1; default before set
      self.Epoch_Time = -1 #set epoch time to -1; default before set
      self.Pulse_Pre_Delay = 0 # set pulse pre delay to 0; default before set
      self.Window_Length = 1 #Trigger window length; default
      self.Delay_Trigger_Sec  = -1   
      self.epochGpsTriggerTime = -1
      # Trigger Variables 
      self.bladeradtriggState = 0
      self.rfsoctriggState = 0
      self.freqdivtriggState = 0
      self.rfsocTrigg = True
      self.bladeradTrigg = True 
      self.freqdivTrigg = True
      self.triggId = 0;
      #Setup Trigger IO Control 
      High = GPIO.HIGH
      Low = GPIO.LOW
      GPIO.setwarnings(False)
      GPIO.cleanup()
      GPIO.setmode(GPIO.BOARD)
      GPIO.setup(Trigger.Trigger_Pass, GPIO.OUT)
      GPIO.setup(Trigger.Trigger_2_Pass, GPIO.OUT)
      GPIO.setup(Trigger.Sync_Pass, GPIO.OUT)
      GPIO.output(Trigger.Trigger_Pass,Low) # Initial state of Trigger
      GPIO.output(Trigger.Trigger_2_Pass,Low) # Initial state of Trigger 2
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
      
    def setTriggerPending(self):
      #print "set Trigger Pending"
      mTriggerTimeEntry.configure(state=DISABLED) # Disable the entry box
      try: 
        self.Delay_Trigger_Sec = int(trig_time.get()) # number of seconds in future to trigger
      except Exception, e:
        pass
      if (self.Delay_Trigger_Sec < 10) or (self.Delay_Trigger_Sec == ""): #don't accept a trigger deadline less than 10s away.
          TextBox.insert(END, "Minimum trigger delay is 10s;\nTrigger delay set to 10s; \n")
          TextBox.yview(END)
          self.Delay_Trigger_Sec = 10
      self.calculatePulseDelay()
      self.Trigger_Pending = True
      
        
    def calculateTriggerTime(self):
      if (Polling_GPSDO == True):
         self.epochGpsTriggerTime = GPSDO.epochGpsDateTime + self.Delay_Trigger_Sec
         print "GPS Trigger Deadline : ", self.epochGpsTriggerTime
         self.broadcastTrigger()
         
      if (Polling_GPSDO == False):
         date = str(datetime.datetime.now())
         date = date[0:11]
         try:
           gps_Time = GPSDO.getGpsTime()
         except Exception,e:
           print str(e)
         print "gps_time :", gps_Time
         date_Time = date + gps_Time 
         print "date_time :", date_Time
         p = '%Y-%m-%d %H:%M:%S'
         epoch = datetime.datetime(1970, 1, 1)
         print "epoch :", epoch
         self.Epoch_Time = (datetime.datetime.strptime(date_Time,p) - epoch).total_seconds()
         print "epoch_Time =", self.Epoch_Time
         self.Epoch_Trigger_Deadline = self.Epoch_Time + self.Delay_Trigger_Sec #set trigger epoch time 
         print "Epoch Trigger Deadline", self.Epoch_Trigger_Deadline
         self.realTimeCounter()
         self.broadcastTrigger()
      
    def broadcastTrigger(self):
      if TCPServer.slaveConnected == True:
        Message = "TR_" + str(self.epochGpsTriggerTime) + "_" + str(self.triggId)
        TCPServer.broadcastMessage(Message)
        NetworkTextBox.insert(END, "Trigger Time Broadcast \n")
      else: 
        NetworkTextBox.insert(END, "Trigger Time not Broadcast \n")

      
      
    def triggerSelect(self):      
      #Query UI trigger check boxes
      if self.rfsoctriggState.get() == 1:
        self.rfsocTrigg = True
      else:
        self.rfsocTrigg = False
      if self.bladeradtriggState.get() == 1:
        self.bladeradTrigg = True
      else:
        self.bladeradTrigg = False
      if self.freqdivtriggState.get() == 1:
        freqdivTrigg = True
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
      
    def calculatePulseDelay(self):
      #print "calc pre pulse"
      self.Pulse_Pre_Delay = 1 + 0.5*GPSDO.PPSPulseWidth*0.000000001 - 0.5*self.Window_Length
      print "Pulse Pre_delay", str(self.Pulse_Pre_Delay)
      #print "completed calc"
      
    def realTimeCounter(self):
      if self.epochGpsTriggerTime != -1: #only clock RTC if there is a trigger time set.
         delta = self.epochGpsTriggerTime - GPSDO.epochGpsDateTime
         TriggerTextLabel.set("Time until Trigger: " + str(delta))
         if (delta == 1):
            GPIO.remove_event_detect(Trigger.PPS_OUT)
            self.sendTrigger() 
            self.epochGpsTriggerTime = -1 # reset the epoch trigger deadline
            GPIO.add_event_detect(Trigger.PPS_OUT, GPIO.RISING, callback= self.ppsDetected)
      if self.Epoch_Trigger_Deadline != -1: #only clock RTC if there is a trigger time set.
        self.Epoch_Time += 1 # increment epoch time each time the RTC is clocked.
        delta = self.Epoch_Trigger_Deadline - self.Epoch_Time
        TriggerTextLabel.set("Time until Trigger: " + str(delta))
        print "old trigger"
        if delta == 1:
          self.sendTrigger()
          self.Epoch_Trigger_Deadline = -1 # reset the epoch trigger deadline
      
    def sendTrigger(self):
      time.sleep(self.Pulse_Pre_Delay-0.3) # allow the current pulse to pass
      try:
          if self.rfsocTrigg == True:
            GPIO.output(Trigger.Trigger_Pass, High)
            print "RFSoC Trigger Pass"
          if self.bladeradTrigg == True:
            GPIO.output(Trigger.Trigger_2_Pass, High)
            print "bladeRAD Trigger Pass"
          if self.freqdivTrigg == True:
            GPIO.output(Trigger.Sync_Pass, High)
            print "Frequency Divider Trigger Pass"
          time.sleep(self.Window_Length) # open the window for an appropriate time
          GPIO.output(Trigger.Trigger_Pass, Low) # ensure the pass pulse has gone low
          GPIO.output(Trigger.Trigger_Pass, Low)
          GPIO.output(Trigger.Trigger_Pass, Low)
          GPIO.output(Trigger.Trigger_2_Pass, Low) # ensure the pass pulse has gone low
          GPIO.output(Trigger.Trigger_2_Pass, Low)
          GPIO.output(Trigger.Trigger_2_Pass, Low)
          GPIO.output(Trigger.Sync_Pass, Low) # ensure the pass pulse has gone low
          GPIO.output(Trigger.Sync_Pass, Low)
          GPIO.output(Trigger.Sync_Pass, Low)
          if ((GPSDO.epochGpsDateTime - self.epochGpsTriggerTime) == 0):
            TextBox.insert(END, 'N0 Trigger Valid \n')
            print "time: ", GPSDO.epochGpsDateTime, 
            print "trigg time: " ,self.epochGpsTriggerTime
          else:
            TextBox.insert(END, 'Trigger Error of ' + str(int(GPSDO.epochGpsDateTime - self.epochGpsTriggerTime)) + ' s \n')     
          TriggerTextLabel.set("Time until Trigger: Nil") # reset the trigger label
          mTriggerTimeEntry.configure(state=NORMAL)
      except Exception,e:
          print str(e)
          os._exit(1)
