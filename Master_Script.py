#!/usr/bin/env python


#Master Node

from gps import *
from time import * # double check this
import os
import struct
import RPi.GPIO as GPIO
import time
import sys
import spidev
from Tkinter import *
import serial
import socket 
import threading
import thread
import datetime
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from collections import deque
import numpy as np
import csv


# ************************** Setup **************************************

# elevate python
#pythonPID = os.getpid()
#elevatePriority = "sudo renice -n -19 -p " + str(pythonPID)
#os.system(elevatePriority)
#elevate idle
os.system('sudo renice -18 `pgrep idle`')

# gpsd lifecycle managment
os.system('clear') # not sure if all this is neccessary yet
#os.system('sudo killall gpsd')
#os.system('sudo gpsd /dev/ttyS0 -F /var/run/gpsd.sock')
#os.system('sudo service ntp restart')
# end of commands to reset the service


# Setup the GUI
mGui = Tk()
mGui.geometry("1900x1000+220+140") # Window Geometry
mGui.title("GPSDO Synchrnonisation System - Master Node Control Interface")
#mGui.configure(bg="skyblue")
LARGE_FONT= ("Verdana", 12)
style.use("ggplot")
# End of GUI setup 

# GPSDO 
GPSDO_Present = True
High = GPIO.HIGH
Low = GPIO.LOW

#************************ Setup Complete ********************************

# ************************ Variables ************************************
#Tick boxs on mGui
Track_state = IntVar()
Sync_state = IntVar()
GPS_state = IntVar()
Beat_PPS_State = IntVar()
Save_PPS_State = IntVar()
Poll_GPSDO = IntVar() 
# PPS Error Variables
PPS_Error_Length = 10 #60 * 2 # length of PPS Error Arrays graph time axis (default 2 mins)
Fine_Phase_Comp = deque(maxlen = PPS_Error_Length)
Effective_Time_Int = deque(maxlen = PPS_Error_Length)
PPSREF_Sigma = deque(maxlen = PPS_Error_Length)
Polling_GPSDO = False
Save_PPS = False
Save_PPS_Flag = False
#mGUI general variables
TriggerTextLabel = StringVar()
trig_time = StringVar()
current_time = StringVar()
exitFlag = -1
Nil = 0b00000000 
user_query = StringVar()
#Variables for Oscillator Data Frame
Gpsdo_Status = IntVar()
Rb_Status = IntVar()
Current_Freq = IntVar()
Holdover_Freq = IntVar()
Constant_Mode = IntVar()
Constant_Value = IntVar()
#Variables for GPS Receiver Data Frame
GPSDO_Latitude = IntVar()
GPSDO_Longitude = IntVar()
GPSDO_Altitude = IntVar()
GPSDO_Satellites = IntVar()
GPSDO_Tracking = IntVar()
GPSDO_Validity = IntVar()
# GPS Popout Variables
Latitude = StringVar()
Longitude = StringVar()
TimeUTC = StringVar()
Altitude = StringVar()
EPS = StringVar()
EPX = StringVar()
EPV = StringVar()
EPT = StringVar()
Speed = StringVar()
Climb = StringVar()
Track = StringVar()
Mode = StringVar()
Sat = StringVar()
# Oscillator variables Window
FreqAdj = StringVar()
PeakVoltRB = StringVar()
DC_Photo = StringVar()
Varac = StringVar()
RBLamp = StringVar()
RBHeating = StringVar()
Alarm = StringVar()
Tracking = StringVar()
Tau = StringVar()
CompOff = StringVar()
RawAdj = StringVar()
FreqCorr = StringVar()
SyncPeriod = StringVar()
DisableTimeMonitor = False
Calibrated = False
GpsdoStatus = StringVar()


DisableTimeMonitor = False
GPS_Readings = False
SystemTimeSet = False


# *********************End of Variables *********************************

#*************Exit Routine****************
def exit_routine(): # runs this routine upon exit
    TCPServer.stopServer()
    GPSDO.pollGpsdoMetrics(False)
    time.sleep(1)
    exitFlag = 1
    time.sleep(1)
    DO_TextBox.insert(END,"****Exiting Program****\n")
    mGui.destroy() # close the window
    os._exit(1)
    f.close()
    mGui.protocol('WM_DELETE_WINDOW',exit_routine)

def stopThread(self):
  print "Shutting down thread: " + str(self)
  if self.process is not None:
    self.process.terminate()
    self.process = None

def return_hit(event): ####
  if (user_query.get() != ""):
    GPSDO_Send()
    user_query.set("") # clear the query box when enter is pressed
  if (trig_time.get() != ""):
    Trigger.setTriggerPending()
    #trig_time.set("") # clear the trigger query box
  mGui.bind('<Return>',return_hit)




#***************END***********************

# GPS polling definition
class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    try:
        print "Enabling the watch"
        gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    except Exception,e:
        print "GPSD: " + str(e)
        self.RestartSocketGPS()
        gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
        print "Done resetting sockets"
    self.current_value = None
    self.running = True #setting the thread running to true

  def run(self):
    while (self.running):
      try:
        gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer#
      except Exception,e:
        print "GPSD: " + str(e)
      print str(gpsd.fix.latitude)
      print str(gpsd.satellites)
      print "gpsd running"
      time.sleep(2)
      if(not GPSDO.streamGps):
        gpsd.close()
        print "gpsd closing"
        break
    

def RestartSocketGPS():
  global gpsd
  os.system('clear') # not sure if all this is neccessary yet
  os.system('sudo killall gpsd')
  os.system('sudo gpsd /dev/ttyS0 -F /var/run/gpsd.sock')
  os.system('sudo service ntp restart')
  gpsd = None # Global variable




def GPS_POLLER(threadName): ####
  global SystemTimeSet, gpsp, GPS_Readings
  global Latitude,Longitude,TimeUTC,Altitude,EPS,EPX,EPV,EPT,Speed,Climb,Track,Mode,Sat # bring the string vars into the scope
  GPS_Init = False
  try:
    while (exitFlag == -1):
      while (GPS_Readings == True):
        if (GPS_Init == False): # initialise GPS communications once
          gpsp = GpsPoller() # create the thread
          gpsp.start() # start it up
          print "Started up the GPS Polling thread"
          GPS_Init = True
        try:
          #os.system('clear')
          Latitude.set("Latitude: " + str(gpsd.fix.latitude))
          Longitude.set("Longitude: " + str(gpsd.fix.longitude))
          TimeUTC.set("Time UTC: " + str(str(gpsd.utc) + " + " + str(gpsd.fix.time)))
          Altitude.set("Altitude /m: " + str(gpsd.fix.altitude))
          EPS.set("EPS: " + str(gpsd.fix.eps))
          EPX.set("EPX: " + str(gpsd.fix.epx))
          EPV.set("EPV: " + str(gpsd.fix.epv))
          EPT.set("EPT: " + str(gpsd.fix.ept))
          Speed.set("Speed (m/s): " + str(gpsd.fix.speed))
          Climb.set("Climb: " + str(gpsd.fix.climb))
          Track.set("Track: " + str(gpsd.fix.track))
          Mode.set("Mode: " + str(gpsd.fix.mode))
          Sat.set("Satellites: " + str(gpsd.satellites))

          #Set the system time to the time received from the GPS
          if (gpsd.utc != None) & (gpsd.utc != "") & (gpsd.utc != " ") & (SystemTimeSet == False):
            print "Setting system time to GPS Time"
            gpstime = gpsd.utc[0:4] + gpsd.utc[5:7] + gpsd.utc[8:10] + ' ' + gpsd.utc[11:13] + gpsd.utc[13:19]
            #print str(gpstime)
            os.system('sudo date -u --set="%s"'% gpstime)
            print "Set system time successfully"
            SystemTimeSet = True
          time.sleep(2) #set to whateverprint
        except Exception,e:
          print str(e)
      time.sleep(0.001) # ensure this does not interrupt
  except Exception,e:
    print str(e)


class NetworkConnection:
 
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
          except Exception,e:
             print str(e)
        #listen for message from slave 
        try:
          message = self.con.recv(sys.getsizeof("N1 Trigger Valid"))
          if not message:
            self.slaveConnected = False
            NetworkTextBox.insert(END, "Slave Disconnected ... \n")
          print "message recieved",message
          message = str(message.decode()+ '\n\n')
          TextBox.insert(END, message)
          self.broadcastMessage('received')
        except Exception, e:
          print str(e)
        time.sleep(0.5)
      

      
class SpecGPSDO:
    
    def __init__(self):
      self.gpsdoDetected = False
      self.streamGps = False
      self.setupSerialCon()
      self.firstQuery = True
      #Intialise Rb metrics
      self.FreqAdjRaw = -1
      self.Reserve1 = -1
      self.PeakVoltRBRaw = -1
      self.DC_PhotoRaw = -1
      self.VaracCtrlRaw = -1
      self.RBLampCurrentRaw = -1
      self.RBHeatingCurrentRaw = -1
      self.Reserve2 = -1
      self.FreqAdjNorm = ""
      self.PeakVoltRBNorm = ""
      self.DC_PhotoNorm = ""
      self.VaracCtrlNorm = ""
      self.RBLampCurrentNorm = ""
      self.RBHeatingCurrentNorm = ""    
      #Intialise tracking metrics     
      self.AlarmVal = ""
      self.TrackingVal = ""
      self.TauVal = ""
      self.CompOffVal = ""
      self.RawAdjVal = ""
      self.RawResponse = ""
      #Variables for Oscillator Data Frame
      self.Status =  ""
      self.RbStatus = ""
      self.CurrentFreq = ""
      self.HoldoverFreq = ""
      self.ConstantMode = ""
      self.ConstantValue = ""
      #Variables for GPS Receiver Data Frame
      self.Latitude =  ""
      self.LatitudeLabel = ""
      self.Longitude =  ""
      self.LongitudeLabel = ""
      self.Altitude =  ""
      self.Satellites = ""
      self.Tracking = ""
      self.Validity = ""
      #PPS Error Related Metrics 
      self.hasPolled = False
      self.PPSRefSigma = 0
      self.FinePhaseComp = 0
      self.EffTimeInt = 0
      #General GPSDO Metrics
      self.PPSPulseWidth = 0
      self.GpsDateTime = 0
      self.epochGpsDateTime = 0
      #Get PPSOUT Pulse Width
      self.getPPSPulseWidth()
      
            
    def setupSerialCon(self):
      if (GPSDO_Present == True):
          self.GPSDO_SER = serial.Serial(
              port = '/dev/ttyS0',
              baudrate = 9600,
              parity = serial.PARITY_NONE,
              stopbits = serial.STOPBITS_ONE,
              bytesize = serial.EIGHTBITS,
              timeout = 1)
          #print "GPSDO Setup Started"
          c = 3
          while (c > 0): #loop through 3 attempts to connect to GPSDO
            c -= 1
          if (self.getSerialNo() == ''):
            self.gpsdoDetected = False
            print "GPSDO not detected"
          else:
            time.sleep(0.1)
            self.setGpsCom(False)
            self.stopBeating()  #Ensure GPSDO isn't beating any messages
            time.sleep(0.1)
          try:
            gpsdoID = self.getID()
            #DO_TextBox.insert(END,"GPSDO Communications Initiated\n")
            #DO_TextBox.yview(END)
            #print "GPSDO Communications Initiated"
            print "GPSDO ID :", gpsdoID
            self.gpsdoDetected = True
          except Exception, e:
            print str(e)
            #Do_TextBox.insert(END,"GPSDO Communication Failed\n")
            print "GPSDO Communication Failed"
            self.gpsdoDetected = False
    
    def passCommand(self, command):     #pass command to GPSDO and display response in GPSDO response textbox
        command = command + "\r"
        self.GPSDO_SER.write(command)
        response = self.GPSDO_SER.readline()
        DO_TextBox.insert(END,response[:-2]+"\n")
        DO_TextBox.yview(END)

    def collectResponse(self, command): #pass command to GPSDO and return response to call
        command = command + "\r"
        self.GPSDO_SER.write(command)
        response = self.GPSDO_SER.readline()
        return response          
    
    def readLine(self):
        return self.GPSDO_SER.readline()
     
    def sendQuery(self, query):         # method for querying GPSDO 
        self.GPSDO_SER.write(query)
        time.sleep(0.1)
        response = self.GPSDO_SER.readline()
        return response
              
    def getID(self):
      return self.collectResponse("ID")
    
    def getSerialNo(self): 
      return self.collectResponse("SN") 
      
    def setGpsCom(self, flag):
        if flag == True:
            self.collectResponse('@@@@GPS')
            while(True):
              print self.GPSDO_SER.readline() + "\n"
            #print "GPS Mode Enabled"
        elif (flag == False):
            self.collectResponse('@@@@')
            #print "GPS Mode Disabled"
            
    def setTrack(self, flag):
        if flag == True:
            response = self.collectResponse('TR1')
            if (response[:-2] == "1"):
                print "Tracking to PPSREF set \n"
        elif (flag == False):
            response = self.collectResponse('TR0')
            if response[:-2] == "0":
                print "Tracking to PPSREF unset \n"

    def setSync(self, flag):
        if (flag == True):
            response = self.collectResponse('SY1')
            if response[:-2] == "1":
                print "PPSOUT synchronisation to PPSINT set \n"
        elif (flag == False):
            response = self.collectResponse('SY0')
            if (response[:-2] == "0"):
                print "PPSOUT synchronisation to PPSINT unset \n"
    
    def isTrackingSet(self):
        response = self.collectResponse('TR?')
        if response[:-2] == "1":
                print "Tracking to PPSREF is Set\n"
                return True
        if response[:-2] == "0":
                print "Tracking to PPSREF not set \n"
                return False

    def isSyncSet(self):
        response = self.collectResponse('SY?')
        if response[:-2] == "1":
            print "PPSOUT synchronisation to PPSINT set \n"
            return True
        if response[:-2] == "0":
            print "PPSOUT synchronisation to PPSINT not set \n"
            return False
     
    def getPPSPulseWidth(self):
         pulse_Length = self.collectResponse('PW?????????') 
         #print "Pulse Length in ns:" , pulse_Length
         self.PPSPulseWidth = 66*round(float(pulse_Length)/66) # find the actual pulse length, must be multiple of 66ns
         #print "Pulse length in ns:", pulse_Length 
         return self.PPSPulseWidth  
                                   
    def stopBeating(self):
        response = "0"
        while (response != ""):
          self.collectResponse("BT0")
          self.collectResponse("MAW0B00")
          self.collectResponse("MAW0C00")
          time.sleep(0.1)
          response = self.readLine()
          #response = self.readLine()
          if not response: break
        #print "Stopped Beating GPSDO Messages"
      
    def getGpsdoStatus(self):
         x= str(self.collectResponse('ST')[0:1])
         return decodeGPSDOStatus(x)
      
    def decodeGPSDOStatus(self,x):
      return {
        '0' : "Warming Up",
        '1' : "Tracking Set Up",
        '2' : "Tracking PPS REF",
        '3' : "Sync to PPS REF",
        '4' : "Free Run",
        '5' : "PPS REF Unstable",
        '6' : "No PPS REF",
        '7' : "Frozen",
        '8' : "Factory Diagnostic",
        '9' : "Searching RB Line...",
        }[x]
      
    def getGpsTime(self):
      return str(self.collectResponse('TD'))[0:8]
    
    def getGpsDate(self):
       return str(self.collectResponse('DT'))[0:10]
       
    def getRbMetrics(self):
      count = 5
      try:
        M = self.collectResponse('M')
      except Exception,e:
        print str(e)
        M = " "
      if (len(M) != 26):
        try:
          while (count > 0) & (len(M) != 26):
            print "Not Responding Trying again in 2 seconds"
            time.sleep(2)
            M = self.collectResponse('M')
            count -= 1
        except Exception,e:
          print str(e)
      self.FreqAdjRaw = int(M[0:2],16)
      self.Reserve1 = int(M[3:5],16)
      self.PeakVoltRBRaw = int(M[6:8],16)
      self.DC_PhotoRaw = int(M[9:11],16)
      self.VaracCtrlRaw = int(M[12:14],16)
      self.RBLampCurrentRaw = int(M[15:17],16)
      self.RBHeatingCurrentRaw = int(M[18:20],16)
      self.Reserve2 = int(M[21:23],16)
      self.FreqAdjNorm = str(round(float(self.FreqAdjRaw)/51,3)) + "V"
      self.PeakVoltRBNorm = str(round(float(self.PeakVoltRBRaw)/51,3)) + "V"
      self.DC_PhotoNorm = str(round(float(self.DC_PhotoRaw)/51,3)) + "V"
      self.VaracCtrlNorm = str(round(float(self.VaracCtrlRaw)/51,3)) + "V"
      self.RBLampCurrentNorm = str(round(float(self.RBLampCurrentRaw*100)/51,3))+"mA"
      self.RBHeatingCurrentNorm = str(round(float(self.RBHeatingCurrentRaw*100)/51,3))+"mA"       
       
    def getTrackingSettings(self):
      self.AlarmVal = (self.collectResponse('AW???'))[0:3]
      self.TrackingVal = (self.collectResponse('TW???'))[0:3]
      self.TauVal = (self.collectResponse('TC??????'))[0:6]
      self.CompOffVal = (self.collectResponse('CO????'))[0:4] 
      self.RawAdjVal = self.collectResponse('RA????')
      self.RawResponse = (self.collectResponse('FC??????'))

    def getGpsData(self,flag):
      if (flag):
        self.setGpsCom(True)
        self.streamGps = True
        self.gpsp = GpsPoller() # create the thread
        self.gpsp.start() # start it up
        print "Started up the GPS Polling thread"
      elif(not flag):
        self.streamGps = False
        self.setGpsCom(False)
     
    def pollGpsdoMetrics(self,flag):
      if flag:
          self.hasPolled = True
          self.collectResponse("BTA")
          self.collectResponse("MAW0BB0")
          self.collectResponse("MAW0C10")
          self.PPSMetrics = threading.Thread(target=self.PPSMetricsPoller)
          self.PPSMetrics.start()
      if not flag:
       if self.hasPolled:
         self.PPSMetrics.do_run = False
         time.sleep(0.1)
       self.stopBeating()
       self.firstQuery = True


    def PPSMetricsPoller(self):
      self.PPSMetrics = threading.currentThread()
      while (getattr(self.PPSMetrics, "do_run", True)):
        try:
          response = self.readLine() 
          if (response[0:6] == "$PTNTA"):
            self.decodePTNTA(response)
          elif (response[0:6] == "$PTNTS"):
            self.decodePTNTS(response)
          elif (response[0:6] == "$GPRMC"):
            self.decodeGPRMC(response)
        except Exception,e:
          pass
          #print str(e)
        time.sleep(0.1)
      #print "Stopping PPSMetricsPoller"
    
    def dateTimeToEpoch(self,dateTime):
         p = '%Y%m%d%H%M%S'
         epoch = datetime.datetime(1970, 1, 1)
         #print "epoch :", epoch
         epochTime = (datetime.datetime.strptime(dateTime,p) - epoch).total_seconds()
         #print "epoch_Time :", epochTime
         return epochTime
      
    
    def decodePTNTA(self, response):
       responseArray = response.split(",")
       #Date and time
       self.GpsDateTime = int(responseArray[1]);
       newEpochTime = self.dateTimeToEpoch(responseArray[1])
       if (((newEpochTime - self.epochGpsDateTime) != 1) and (self.firstQuery == False)):
          print "Error in date and time from GPSDO"
          print (newEpochTime - self.epochGpsDateTime)
       self.epochGpsDateTime = newEpochTime
       self.firstQuery = False
       #print "GPS Time : ", self.GpsDateTime
       #Oscilator Quality 
       if (responseArray[2]=="0"):
          self.RbStatus = "Warming Up"
       elif (responseArray[2]=="1"):
          self.RbStatus = "Freerun"
       elif (responseArray[2]=="2"):
          self.RbStatus = "Disciplined"
       #PPSREF-PPSInT Interval
       val = int(responseArray[4])
       if val < 499999999:
         self.EffTimeInt = int(responseArray[4])
       else:
         self.EffTimeInt = int(responseArray[4])-999999999
       #Fine Phase Comparator
       self.FinePhaseComp = int(responseArray[5])
       #GPSDO Status
       self.Status = self.decodeGPSDOStatus(str(responseArray[6]))
       #GPS Vaalidity 
       validity = responseArray[8].split("*")
       if (validity[0] == "0"):
          self.Validity = "Invalid"
       elif (validity[0] == "1"):
          self.Validity = "Manual"
       elif (validity[0] == "2"):
          self.Validity = "Older than 240 hrs"
       elif (validity[0] == "3"):
          self.Validity = "Fresh"
       
    def decodePTNTS(self,response):
      responseArray = response.split(",") 
      self.Status = self.decodeGPSDOStatus(str(responseArray[2]))
      self.CurrentFreq = float.fromhex(responseArray[3])
      self.HoldoverFreq = float.fromhex(responseArray[4])
      if (responseArray[8] == "0"):
         self.ConstantMode = "Fixed"
      elif (responseArray[8] == "1"):
         self.ConstantMode = "Auto"
      self.ConstantValue = responseArray[9] + " s"
      self.PPSRefSigma = float(responseArray[10])
      
    def decodeGPRMC(self,response):
       responseArray = response.split(",") 
       self.Latitude =  responseArray[3] 
       self.LatitudeLabel = responseArray[4]
       self.Longitude = responseArray[5]
       self.LongitudeLabel = responseArray[6]
       
class Trigger:
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
      self.bladeradtriggState = IntVar()
      self.rfsoctriggState = IntVar()
      self.freqdivtriggState = IntVar()
      self.rfsocTrigg = True
      self.bladeradTrigg = True 
      self.freqdivTrigg = True
      self.triggId = 0;
      #Setup Trigger IO Control 
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




# *************** End of networking threads ******************

#*********** END of All Thread Related definitions ********************

# ******************** Flag set definitions ***************************
def listenForSlaves():
  TCPServer.startServer()

def disconnectSlaves():
  TCPServer.stopServer()
# ******************** End of Flag set definitions *************************


def GPSDO_Send(): 
    query = user_query.get()+"\r"
    response = GPSDO.sendQuery(query)
    DO_TextBox.insert(END,response[:-2]+"\n")
    DO_TextBox.yview(END)

def pollGPSDO():
   global Polling_GPSDO
   if (Poll_GPSDO.get() == 1):
     GPSDO.pollGpsdoMetrics(True)
     Polling_GPSDO = True
     mCheck_Save.config(state=ACTIVE)
   elif (Poll_GPSDO.get() == 0):
     GPSDO.pollGpsdoMetrics(False)
     Polling_GPSDO = False
     Save_PPS_State.set(0)
     Save_PPS_Error()
     mCheck_Save.config(state=DISABLED)
                  
def Save_PPS_Error(): 
  if Save_PPS_State.get() == 1:
        saveToFile(True)
  elif Save_PPS_State.get() == 0:
        saveToFile(False)
        
    
def saveToFile(flag):
  global Save_PPS, Save_PPS_Flag, writer,f
  header = ['GPS Time','epoch Time','GPSDO Status','RB Status','Current Freq','Holdover Freq','Time Constant Mode','Time Constant Value','Latitude','N/S','Longitude','E/W','Validiity','Fine Phase Comparator','Effective Time Interval','PPSREF sigma']
  if flag:
    print "Open file for saving GPSDO metrics"
    now = datetime.datetime.now()
    file_name = "GPSDO_Log_Files/N0_GPSDO_Log " + now.strftime("%Y-%m-%d %H:%M:%S")+ ".txt"
    f = open(file_name,"a")
    writer = csv.writer(f)
    writer.writerow(header)
    Save_PPS = True
  elif not flag:
    Save_PPS = False
    try:
      f.close()
      print 'Closing for saving GPSDO metrics'
    except Exception,e:
      pass
      
    
    
    
def trackMode():
    if Track_state.get() == 1:
        GPSDO.setTrack(True)
        DO_TextBox.insert(END,"Tracking to PPSREF Set \n")
        DO_TextBox.yview(END)
    elif Track_state.get() == 0:
        GPSDO.setTrack(False)
        DO_TextBox.insert(END,"Tracking to PPSREF Unset \n")
        DO_TextBox.yview(END)

def syncMode():
    if Sync_state.get() == 1:
        GPSDO.setSync(True)
        DO_TextBox.insert(END,"PPSOUT Synchronisation to PPSINT Set \n")
        DO_TextBox.yview(END)
    elif Sync_state.get() == 0:
        GPSDO.setSync(False)
        DO_TextBox.insert(END,"PPSOUT Synchronisation to PPSINT Unset \n")
        DO_TextBox.yview(END)

def gpsMode():
    if GPS_state.get() == 1:
        GPSDO.setGpsCom(True)
        #DO_TextBox.insert(END,"GPS Mode Enabled")
        DO_TextBox.yview(END)
    elif GPS_state.get() == 0:
        GPSDO.setGpsCom(False)
        #DO_TextBox.insert(END,"GPS Mode Disabled")
        DO_TextBox.yview(END)
          
def Setup_CheckBox():
#setup GPSDO control check boxes
    tracking = GPSDO.isTrackingSet()
    synced = GPSDO.isSyncSet()
    if (tracking == True):
        Track_state.set(1)
    elif (tracking == False):
        Track_state.set(0)
    if (synced == True):
        Sync_state.set(1)
    elif (synced == False):
        Sync_state.set(0)
    GPSDO.setGpsCom(False)
    GPS_state.set(0)
    Save_PPS_State.set(0)
    Poll_GPSDO.set(0)
#setup trigger check boxes
    Trigger.rfsoctriggState.set(0) 
    Trigger.bladeradtriggState.set(0) 
    Trigger.freqdivtriggState.set(0)
    
    
def setSysTime():
  SysTimeSet = False
  if (SysTimeSet == False):
    try:
        GPSDO_Date = GPSDO.getGpsDate()
        GPSDO_Time = GPSDO.getGpsTime()
        TimeLength = len(GPSDO_Time) - 2
        gpstime = GPSDO_Date[0:4] + GPSDO_Date[5:7] + GPSDO_Date[8:10] + " " + GPSDO_Time
        os.system('sudo date -u --set="%s"'% gpstime)
        print "System Time set to GPS time"
    except Exception,e:
      print str(e)

def clock():
  current_time.set("Time: "+str(datetime.datetime.now().time())[0:8] ) # refresh the display
  mGui.after(1000, clock)

def updateRbMetrics():
  global top
  global FreqAdj, PeakVoltRB, DC_Photo, Varac, RBLamp, RBHeating
  GPSDO.getRbMetrics()
  FreqAdj.set("Frequency Adjust Voltage: " + GPSDO.FreqAdjNorm)
  PeakVoltRB.set("Peak RB Voltage: " + GPSDO.PeakVoltRBNorm)
  DC_Photo.set("DC Photocell Voltage: " + GPSDO.DC_PhotoNorm)
  Varac.set("Varactor Control Voltage: " + GPSDO.VaracCtrlNorm)
  RBLamp.set("RB Lamp Current: " + GPSDO.RBLampCurrentNorm)
  RBHeating.set("RB Heating Current: " + GPSDO.RBHeatingCurrentNorm)

def updateTrackingSettings():
  global top
  global Alarm, Tracking, Tau, CompOff, RawAdj, FreqCorr
  GPSDO.getTrackingSettings()
  Alarm.set("Alarm Window: " + str(GPSDO.AlarmVal) +" us")
  Tracking.set("Tracking Window: " + str(GPSDO.TrackingVal) + " us")
  Tau.set("Time Constant: " + str(GPSDO.TauVal) +" s")
  CompOff.set("Comparator Offset: " + str(GPSDO.CompOffVal) + " ns")
  RawAdj.set("Raw Phase Adjust: " + str(GPSDO.RawAdjVal))
  FreqCorrRaw = str(GPSDO.RawResponse)
  FreqSign = str(GPSDO.RawResponse[0])
  FreqNorm = round(float(FreqCorrRaw)*(0.00512),5)
  if (FreqSign == "+"):
    FreqCorr.set("Frequency in use: " + "+" + str(FreqNorm) + " mHz")
  elif (FreqSign == "-"):
    FreqCorr.set("Frequency in use: " + "-" + str(FreqNorm) + " mHz")

def LaunchTerminal(): 
  global top
  global FreqAdj, PeakVoltRB, DC_Photo, Varac, RBLamp, RBHeating
  global Alarm, Tracking, Tau, CompOff, RawAdj, FreqCorr
  global DisableTimeMonitor
  global GpsdoStatus
  DisableTimeMonitor = True
  top = Toplevel()
  top.geometry("600x300+200+200")
  top.title("GPSDO Parameters")
  mLabel = Label(top,text="Probe Values:").place(x=10,y=10)
  mProbeHeart = Button(top,text="Refresh Values",command=refreshValues).place(x=100,y=10)

  #Obtain ID's and display
  mID= Label(top,text="ID: ").place(x=340,y=10)
  ID = str(GPSDO.getID())
  mIDRes = Label(top,text=ID).place(x=360,y=10)
  mStatus = Label(top,textvariable=GpsdoStatus).place(x=10,y=200)

  # create the master command labels
  mFreqAdjLabel = Label(top,textvariable=FreqAdj).place(x=10,y=50)
  mPeakVoltRBLabel = Label(top,textvariable=PeakVoltRB).place(x=10,y=70)
  mDC_PhotoLabel = Label(top,textvariable=DC_Photo).place(x=10,y=90)
  mVaracLabel = Label(top,textvariable=Varac).place(x=10,y=110)
  mRBLampLabel = Label(top,textvariable=RBLamp).place(x=10,y=130)
  mRBHeatingLabel = Label(top,textvariable=RBHeating).place(x=10,y=150)


  #create the tracking commmand labels
  mAlarmLabel = Label(top,textvariable=Alarm).place(x=340,y=50)
  mTrackingLabel = Label(top,textvariable=Tracking).place(x=340,y=70)
  mTauLabel = Label(top,textvariable=Tau).place(x=340,y=90)
  mCompOffLabel = Label(top,textvariable=CompOff).place(x=340,y=110)
  mRawAdjLabel = Label(top,textvariable=RawAdj).place(x=340,y=130)
  mFreqCorrLabel = Label(top,textvariable=FreqCorr).place(x=340,y=150)

  #Launch GPS Mode
  mGPSButton = Button(top,text="View GPS Signals",command=ViewGPS).place(x=400,y=240)

  Exit = Button(top, text="Exit",command=TopExit).place(x=530,y=240)

  refreshValues()

def refreshValues(): 
  global GpsdoStatus
  GpsdoStatus.set("Status: " + GPSDO.getGpsdoStatus() )
  updateTrackingSettings()
  updateRbMetrics()


def TopExit(): ####
    global DisableTimeMonitor
    top.destroy()
    DisableTimeMonitor = False

# ******************** GPS related defintions********************

def ExitGPS():####
    global gps_top, GPS_Readings
    GPSDO.getGpsData(False)
    #print "GPS Mode Disabled"
    #GPS_Readings = False
    time.sleep(0.1)
    #collectResponse('@@@@') # Disable GPS mode
    gps_top.destroy()

def ViewGPS(): # inititates the GPS top level interface
  global gps_top, status, GPS_Readings
  global Latitude,Longitude,TimeUTC,Altitude,EPS,EPX,EPV,EPT,Speed,Climb,Track,Mode,Sat

  gps_top = Toplevel()
  gps_top.geometry("500x200+150+150")
  gps_top.title("GPS Mode")
  GPSDO.getGpsData(True)
  #DisableTimeMonitor = True
  #collectResponse('@@@@GPS') # Enable gps mode
  #print "GPS mode enabled"
  time.sleep(1)
  #print "Setting GPS readings to true"
  #GPS_Readings = True

  #Initiate the labels
  mLat = Label(gps_top,textvariable=Latitude).place(x=10,y=10)
  mLong = Label(gps_top,textvariable=Longitude).place(x=10,y=30)
  mTimeUTC = Label(gps_top,textvariable=TimeUTC).place(x=10,y=50)
  mAlt = Label(gps_top,textvariable=Altitude).place(x=10,y=70)
  mEPS = Label(gps_top,textvariable=EPS).place(x=10,y=90)
  mEPX = Label(gps_top,textvariable=EPX).place(x=10,y=110)
  mEPV = Label(gps_top,textvariable=EPV).place(x=10,y=130)
  mEPT = Label(gps_top,textvariable=EPT).place(x=250,y=10)
  mSpeed = Label(gps_top,textvariable=Speed).place(x=250,y=30)
  mClimb = Label(gps_top,textvariable=Climb).place(x=250,y=110)
  mTrack = Label(gps_top,textvariable=Track).place(x=250,y=70)
  mMode = Label(gps_top,textvariable=Mode).place(x=250,y=90)
  mSat = Label(gps_top,textvariable=Sat).place(x=10,y=150)

  gpsExit = Button(gps_top,text="Exit",command=ExitGPS).place(x=450,y=160)


def launchPollWindow():
  print "Launching Poll Window"
  try:
    pollObj = MetricsWindow()
  except Exception, e:
    print str(e)
    

# ******************** PPS Error related defintions********************

def updateGpsdoMetrics():
   global writer
   #Variables for Oscillator Data Frame
   Gpsdo_Status.set(GPSDO.Status)
   Rb_Status.set(GPSDO.RbStatus)
   Current_Freq.set(GPSDO.CurrentFreq)
   Holdover_Freq.set(GPSDO.HoldoverFreq)
   Constant_Mode.set(GPSDO.ConstantMode)
   Constant_Value.set(GPSDO.ConstantValue)
   #Variables for GPS Receiver Data Frame
   GPSDO_Latitude.set(GPSDO.Latitude + " " + GPSDO.LatitudeLabel)
   GPSDO_Longitude.set(GPSDO.Longitude + " " + GPSDO.LongitudeLabel)
   #GPSDO_Altitude.set(GPSDO.Altitude)
   #GPSDO_Satellites.set(GPSDO.Satellites)
   #GPSDO_Tracking.set(GPSDO.Tracking)
   GPSDO_Validity.set(GPSDO.Validity)
   mGui.after(1000, updateGpsdoMetrics)
   if Save_PPS:
     writer.writerow([GPSDO.GpsDateTime,GPSDO.epochGpsDateTime,GPSDO.Status,GPSDO.RbStatus,GPSDO.CurrentFreq,GPSDO.HoldoverFreq,GPSDO.ConstantMode,GPSDO.ConstantValue,GPSDO.Latitude,GPSDO.LatitudeLabel,GPSDO.Longitude,GPSDO.LongitudeLabel,GPSDO.Validity,GPSDO.FinePhaseComp,GPSDO.EffTimeInt,GPSDO.PPSRefSigma])


def animate(i):
    global Polling_GPSDO
    if Polling_GPSDO == True:
       Effective_Time_Int.append(GPSDO.EffTimeInt)
       Fine_Phase_Comp.append(GPSDO.FinePhaseComp)
       PPSREF_Sigma.append(GPSDO.PPSRefSigma)
       Effective_Time_Int_np = np.array(Effective_Time_Int,dtype=int)
       Fine_Phase_Comp_np = np.array(Fine_Phase_Comp,dtype=int)
       PPSREF_Sigma_np = np.array(PPSREF_Sigma,dtype=float)
       time_axis = np.linspace(-len(Fine_Phase_Comp),0,len(Fine_Phase_Comp))
       
       fpco.clear()
       fpco.plot(time_axis,Fine_Phase_Comp_np)
       fpco.set_title ("Fine Phase Comparator - PPSREF vs PPSINT", fontsize=10)
       fpco.set_ylabel("Temporal Error (ns)", fontsize=10)
       fpco.set_xlabel("Time (s)", fontsize=10)
       
       etio.clear()
       etio.plot(time_axis,Effective_Time_Int_np)
       etio.set_title ("Effective Time Interval - PPSREF vs PPSINT", fontsize=10)
       etio.set_ylabel("Temporal Error (ns)", fontsize=10)
       etio.set_xlabel("Time (s)", fontsize=10)

       sigo.clear()
       sigo.plot(time_axis,PPSREF_Sigma_np)
       sigo.set_title ("PPSREF Sigma", fontsize=10)
       sigo.set_ylabel("Time Variance (ns)", fontsize=10)
       sigo.set_xlabel("Time (s)", fontsize=10)
# *********************** Program Begin ********************************

#Initialise all required objects 
Trigger = Trigger() # Create trigger instance
GPSDO = SpecGPSDO() # Create GPSDO instance

# *********************** Setup the GUI ********************************

# Create left and right frames
left_frame = Frame(mGui, width=600, height=700,bd=1)
left_frame.grid(row=0, column=0, padx=10, pady=5,sticky=N)

right_frame = Frame(mGui, width=1200, height=700,bd=1)
right_frame.grid(row=0, column=1, padx=10, pady=5,sticky=N)

#***** Populate Left Frame ********

# GPSDO Control Frame
gpsdo_control_frame = Frame(left_frame, width=575, height=200,highlightbackground="black", highlightthickness=2)
gpsdo_control_frame.grid(row=0,column=0, pady=10, padx=10)
mlabel = Label(gpsdo_control_frame,text="GPSDO Controls",font=("Arial", 11)).grid(row=0,column=0,columnspan=3, pady=5,padx=5)
mlabel = Label(gpsdo_control_frame,text="Track: ").grid(row=2,column=0)
mlabel = Label(gpsdo_control_frame,text="Sync: ").grid(row=2,column=1)
mlabel = Label(gpsdo_control_frame,text="GPS: ").grid(row=2,column=2)
mCheck_TR = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=Track_state,onvalue=1,offvalue=0,command=trackMode)
mCheck_SY = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=Sync_state,onvalue=1,offvalue=0,command=syncMode)
mCheck_GPS = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=GPS_state,onvalue=1,offvalue=0,command=gpsMode)
mCheck_TR.grid(row=3,column=0)
mCheck_SY.grid(row=3,column=1)
mCheck_GPS.grid(row=3,column=2)
mlabel = Label(gpsdo_control_frame,text="Enter Query").grid(row=4,column=0,columnspan=3,sticky=W,padx=5)
mEntry = Entry(gpsdo_control_frame,textvariable=user_query).grid(row=5,column=0,columnspan=2,sticky=W,padx=5)
mbutton = Button(gpsdo_control_frame,text="Send",command=GPSDO_Send).grid(row=5,column=2,padx=5)
mlabel = Label(gpsdo_control_frame,text="GPSDO Response").grid(row=6,column=0,columnspan=3,sticky=W,padx=5)
DO_TextBox = Text(gpsdo_control_frame,height=6,width=45)
DO_TextBox.grid(row=7,column=0, columnspan = 3,pady=5,padx=5)
DO_Scroll = Scrollbar(DO_TextBox,command=DO_TextBox.yview)
DO_TextBox.configure(yscrollcommand=DO_Scroll.set)
#end of GPSDO control frame


# Trigger Control Frame 
trigger_control_frame = Frame(left_frame, width=575, height=200,highlightbackground="black", highlightthickness=2)
trigger_control_frame.grid(row=1,column=0,pady=10,padx=10)
mlabel = Label(trigger_control_frame,text="Trigger Controls",font=("Arial", 11)).grid(row=0,column=0,columnspan=3,pady=5,padx=5)
mlabel = Label(trigger_control_frame,text="RFSoC: ").grid(row=1,column=0)
mlabel = Label(trigger_control_frame,text="bladeRAD: ").grid(row=1,column=1)
mlabel = Label(trigger_control_frame,text="Freq Div: ").grid(row=1,column=2)
mCheck_rfsocTrigg = Checkbutton(trigger_control_frame,state=ACTIVE,variable=Trigger.rfsoctriggState,onvalue=1,offvalue=0,command=Trigger.triggerSelect)
mCheck_bladeradTrigg = Checkbutton(trigger_control_frame,state=ACTIVE,variable=Trigger.bladeradtriggState,onvalue=1,offvalue=0,command=Trigger.triggerSelect)
mCheck_freqdiv_Trigg = Checkbutton(trigger_control_frame,state=ACTIVE,variable=Trigger.freqdivtriggState,onvalue=1,offvalue=0,command=Trigger.triggerSelect)
mCheck_rfsocTrigg.grid(row=2,column=0)
mCheck_bladeradTrigg.grid(row=2,column=1)
mCheck_freqdiv_Trigg.grid(row=2,column=2)
mTrigLabel = Label(trigger_control_frame,text="Enter seconds in future to Trigger").grid(row=3,column=0, columnspan=3,sticky=W,padx=5)
mTriggerTimeEntry = Entry(trigger_control_frame,textvariable=trig_time)
mTriggerTimeEntry.grid(row=4,column=0,columnspan=2,sticky=W,padx=5)
mTrigConfirm = Button(trigger_control_frame,text="Confirm",command=Trigger.setTriggerPending).grid(row=4,column=2,padx=5)
TriggerTextLabel.set("Seconds until Trigger: Nil")
mTrigLabel = Label(trigger_control_frame,textvariable=TriggerTextLabel).grid(row=5,column=0,columnspan=3,sticky=W,padx=5)
TextBox = Text(trigger_control_frame, height=8, width=45)
TextBox.grid(row=6,column=0, columnspan=3,pady=5,padx=5)
scroll = Scrollbar(TextBox,command=TextBox.yview)
TextBox.configure(yscrollcommand=scroll.set)
# End of Trigger controls

#Network management
network_control_frame = Frame(left_frame, width=575, height=200,highlightbackground="black", highlightthickness=2)
network_control_frame.grid(row=3,column=0,pady=10,padx=10)
NetworkMainLabel = Label(network_control_frame,text="Network Information",font=("Arial",11)).grid(row=0,column=0,columnspan=2,pady=5,padx=5)
NetworkTextBox = Text(network_control_frame, height=8, width=45)
NetworkTextBox.grid(row=1,column=0,columnspan=2,pady=5,padx=5)
NetworkScroll = Scrollbar(TextBox,command=TextBox.yview)
NetworkTextBox.configure(yscrollcommand=scroll.set)
#mButtonListen = Button(network_control_frame,text="Listen",command=listenForSlaves).grid(row=2,column=0,pady=5,padx=5)
#mButtonDisconnect = Button(network_control_frame,text="Disconnect",command=disconnectSlaves).grid(row=2,column=1,pady=5,padx=5)
#End of Network management frame


mTimeLabel = Label(left_frame,textvariable=current_time).grid(row=4,sticky=W,pady=10,padx=5)
mExit = Button(left_frame,text="Exit",command=exit_routine).grid(row=5,sticky=W,padx=5)


#***** Finish Populate Left Frame ********

#***** Populate Right Frame ********
#values to format size of data frames
ypad=5
xpad=15
labelw=20
valw=15

#Toolbar Frame
metrics_bar_frame = Frame(right_frame,highlightbackground="black", highlightthickness=2)
metrics_bar_frame.grid(row=1,column=0,pady=10,padx=10,sticky=N)

GPSDO_Terminal = Button(metrics_bar_frame,text="GPSDO Parameters",command=LaunchTerminal)
GPSDO_Terminal.grid(row=0,column=0,columnspan=2, pady=5, padx=10)
mlabel = Label(metrics_bar_frame,text="Poll GPSDO",width=labelw,justify=LEFT,anchor="w").grid(row=1,column=0, padx=xpad,pady=ypad)
mCheck_Poll = Checkbutton(metrics_bar_frame,state=ACTIVE,variable=Poll_GPSDO,onvalue=1,offvalue=0,command=pollGPSDO)
mCheck_Poll.grid(row=1,column=1, padx=xpad,pady=ypad)
mlabel = Label(metrics_bar_frame,text="Poll GPS Receiver",width=labelw,justify=LEFT,anchor="w").grid(row=2,column=0,padx=xpad,pady=ypad)
mCheck_Poll = Checkbutton(metrics_bar_frame,state=DISABLED,variable=Save_PPS,onvalue=1,offvalue=0,command=Save_PPS_Error)
mCheck_Poll.grid(row=2,column=1, pady=5, padx=10)
mlabel = Label(metrics_bar_frame,text="Save Data",width=labelw,justify=LEFT,anchor="w").grid(row=3,column=0,padx=xpad,pady=ypad)
mCheck_Save = Checkbutton(metrics_bar_frame,state=DISABLED,variable=Save_PPS_State,onvalue=1,offvalue=0,command=Save_PPS_Error)
mCheck_Save.grid(row=3,column=1,padx=xpad,pady=ypad)
#End of Toolbar Frame


#Oscillator Frame
oscillator_frame = Frame(right_frame,width=300,height=300,highlightbackground="black", highlightthickness=2)
oscillator_frame.grid(row=1,column=1,pady=10,padx=10)
#oscillator_frame.grid_propagate(0)
mlabel = Label(oscillator_frame, text="Oscillator Information",font=("Arial",11)).grid(row=0,column=0,columnspan=2,padx=xpad,pady=ypad)
mlabel = Label(oscillator_frame,text="GPSDO Status: ",width=labelw,justify=LEFT,anchor="w").grid(row=2,column=0,sticky=W,padx=xpad,pady=ypad)
mStatus = Label(oscillator_frame,textvariable=Gpsdo_Status,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=2,column=1,sticky=W,padx=xpad,pady=ypad)
mlabel = Label(oscillator_frame,text="Rb Status: ",width=labelw,justify=LEFT,anchor="w").grid(row=3,column=0,sticky=W,padx=xpad,pady=ypad)
mRbStatus = Label(oscillator_frame,textvariable=Rb_Status,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=3,column=1, sticky=W,padx=xpad,pady=ypad)
mlabel = Label(oscillator_frame,text="Current Freq:  ",width=labelw,justify=LEFT,anchor="w").grid(row=4,column=0, sticky=W,padx=xpad,pady=ypad)
mCurFreq = Label(oscillator_frame,textvariable=Current_Freq,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=4,column=1,sticky=W,padx=xpad,pady=ypad)
mlabel = Label(oscillator_frame,text="Holdover Freq:  ",width=labelw,justify=LEFT,anchor="w").grid(row=5,column=0,sticky=W,padx=xpad,pady=ypad)
mHoldFreq = Label(oscillator_frame,textvariable=Holdover_Freq,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=5,column=1, sticky=W,padx=xpad,pady=ypad)
mlabel = Label(oscillator_frame,text="Time Constant Mode:  ",width=labelw,justify=LEFT,anchor="w").grid(row=6,column=0, sticky=W,padx=xpad,pady=ypad)
mTimeConMode = Label(oscillator_frame,textvariable=Constant_Mode,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=6,column=1,sticky=W,padx=xpad,pady=ypad)
mlabelend = Label(oscillator_frame,text="Time Constant Value:  ",width=labelw,justify=LEFT,anchor="w").grid(row=7,column=0,sticky=W,padx=xpad,pady=ypad)
mTimeConVal = Label(oscillator_frame,textvariable=Constant_Value,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=7,column=1,sticky=W,padx=xpad,pady=ypad)
#End of Oscillator Frame


#GPS Receiver Frame
gpsReceiever_frame = Frame(right_frame,width=300,height=300,highlightbackground="black", highlightthickness=2)
gpsReceiever_frame.grid(row=1,column=2,pady=10,padx=10)
#oscillator_frame.grid_propagate(0)
mlabel = Label(gpsReceiever_frame, text="GPS Recevier Data",font=("Arial",11)).grid(row=0,column=0,columnspan=2,padx=xpad,pady=ypad)
mlabel = Label(gpsReceiever_frame,text="Latitude: ",width=labelw,justify=LEFT,anchor="w").grid(row=2,column=0,sticky=W,padx=xpad,pady=ypad)
mLatitude = Label(gpsReceiever_frame,textvariable=GPSDO_Latitude,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=2,column=1,sticky=W,padx=xpad,pady=ypad)
mlabel = Label(gpsReceiever_frame,text="Longitude: ",width=labelw,justify=LEFT,anchor="w").grid(row=3,column=0,sticky=W,padx=xpad,pady=ypad)
mLongitude = Label(gpsReceiever_frame,textvariable=GPSDO_Longitude,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=3,column=1,sticky=W,padx=xpad,pady=ypad)
mlabel = Label(gpsReceiever_frame,text="Altitude:  ",width=labelw,justify=LEFT,anchor="w").grid(row=4,column=0, sticky=W,padx=xpad,pady=ypad)
mAltitude = Label(gpsReceiever_frame,textvariable=GPSDO_Altitude,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=4,column=1,sticky=W,padx=xpad,pady=ypad)
mlabel = Label(gpsReceiever_frame,text="Satellites:  ",width=labelw,justify=LEFT,anchor="w").grid(row=5,column=0,sticky=W,padx=xpad,pady=ypad)
mSatellites = Label(gpsReceiever_frame,textvariable=GPSDO_Satellites,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=5,column=1,sticky=W,padx=xpad,pady=ypad)
mlabel = Label(gpsReceiever_frame,text="Tracking:  ",width=labelw,justify=LEFT,anchor="w").grid(row=6,column=0, sticky=W,padx=xpad,pady=ypad)
mTracking = Label(gpsReceiever_frame,textvariable=GPSDO_Tracking,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=6,column=1,sticky=W,padx=xpad,pady=ypad)
mlabel = Label(gpsReceiever_frame,text="GPS Validitiy:  ",width=labelw,justify=LEFT,anchor="w").grid(row=7,column=0,sticky=W,padx=xpad,pady=ypad)
mValididty = Label(gpsReceiever_frame,textvariable=GPSDO_Validity,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=7,column=1,sticky=W,padx=xpad,pady=ypad)
#End of GPS Receiever Frame

#Setup Figures

fpc_figure, (fpco,etio,sigo) = plt.subplots(nrows=3, ncols=1, figsize=(14,8), dpi=75, constrained_layout=True)
graph_frame = Frame(right_frame,highlightbackground="black", highlightthickness=2,bg="white")
graph_frame.grid(row=2,column=0,columnspan=3,pady=10,padx=10)
fpc_canvas = FigureCanvasTkAgg(fpc_figure,graph_frame)
fpc_canvas.get_tk_widget().grid(row=0,column=0,sticky=W,pady=10,padx=10)
ani = animation.FuncAnimation(fpc_figure, animate, interval=1000)
fpc_canvas.draw()
# End of PPS Error Items



# ****************** Finished Setting Up GUI *************************

Setup_CheckBox()
setSysTime() #set OS time to GPS Time
#clock() #Setup live clock on GUI
mGui.after(1000, updateGpsdoMetrics)
TCPServer = NetworkConnection() #Create NetworkConnection Server
mGui.mainloop() #End of program

# *********************** Program End ********************************
