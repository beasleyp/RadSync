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

from . import main_script


import serial
import threading
import time
from tkinter import *
import datetime


def _decodeGPSDOStatus(x):
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

def _dateTimeToEpoch(dateTime):
        p = '%Y%m%d%H%M%S'
        epoch = datetime.datetime(1970, 1, 1)
        #print "epoch :", epoch
        epochTime = (datetime.datetime.strptime(dateTime,p) - epoch).total_seconds()
        #print "epoch_Time :", epochTime
        return epochTime

class SpecGPSDO():
    '''
    class for controling Spectratime LNR-Clok 1500 Rubidium GPS Disaplined Oscillator
    Connecting to GPSDO using serial connection on Raspberry Pi GPIO 
    '''
    
    def __init__(self, presence_flag):
      self.gpsdoPresent = presence_flag
      self.gpsdoDetected = False
      self.streamGps = False
      self._setupSerialCon()
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
      self.DiscipliningStatus = ""
      self.CurrentFreq = ""
      self.HoldoverFreq = ""
      self.ConstantMode = ""
      self.ConstantValue = ""
      self.HoldoverDuration = ""
      #Variables for GPS Receiver Data Frame
      self.Latitude =  ""
      self.LatitudeLabel = ""
      self.Longitude =  ""
      self.LongitudeLabel = ""
      self.Altitude =  ""  # currently unused in lnr_clok_1500
      self.Satellites = "" # currently unused in lnr_clok_1500
      self.GPSStatus = ""
      self.GPSReceiverMode = "" # Trimble Related
      self.SelfSurveyProgress = "" # Trimble Related 
      #PPS Error Related Metrics 
      self.hasPolled = False
      self.PPSRefSigma = 0
      self.FinePhaseComp = 0
      self.EffTimeInt = 0
      self.clockOffsetPPB = 0 # New 
      #General GPSDO Metrics
      self.PPSPulseWidth = 0
      self.GpsDateTime = 0
      self.epochGpsDateTime = 0
      #Get PPSOUT Pulse Width
      self.getPPSPulseWidth()
      
            
    def _setupSerialCon(self):
      if (self.gpsdoPresent == True):
         
             self.GPSDO_SER = serial.Serial(
                 port = '/dev/ttyS0',
                 baudrate = 9600,
                 parity = serial.PARITY_NONE,
                 stopbits = serial.STOPBITS_ONE,
                 bytesize = serial.EIGHTBITS,
                 timeout = 1)
             #print "GPSDO Setup Started"
              
             c = 3
             while c > 0: #loop through 3 attempts to connect to GPSDO
                 c -= 1
                 self.setGpsCom(False)
                 self.stopBeating()  #Ensure GPSDO isn't beating any messages
                 if (self.getSerialNo() == ''):
                   self.gpsdoDetected = False
                   print("GPSDO not detected")
                 else:
                   time.sleep(0.1)
              
             try:
                gpsdoID = self.getID()
                #main_script.MainUi.gpsdo_textbox.insert(END,"GPSDO Communications Initiated\n")
                #main_script.MainUi.gpsdo_textbox.yview(END)
                #print "GPSDO Communications Initiated"
                print("GPSDO ID :", gpsdoID)
                self.gpsdoDetected = True
             except Exception as e:
                print(str(e))
                #main_script.MainUi.gpsdo_textbox.insert(END,"GPSDO Communication Failed\n")
                print("GPSDO Communication Failed")
                self.gpsdoDetected = False
    
    
    def _passCommand(self, command):     #pass command to GPSDO and display response in GPSDO response textbox
        com = str(command + "\r")
        self.GPSDO_SER.write(str.encode(com))
        response = str(self.GPSDO_SER.readline().decode("utf-8"))
        main_script.MainUi.gpsdo_textbox.insert(END,response[:-2]+"\n")
        main_script.MainUi.gpsdo_textbox.yview(END)

    def collectResponse(self, command): #pass command to GPSDO and return response to call
        com = str(command + "\r")
        self.GPSDO_SER.write(str.encode(com))
        response = str(self.GPSDO_SER.readline().decode("utf-8"))
        return response          
    
    def _readLine(self):
        return str(self.GPSDO_SER.readline().decode("utf-8"))
     
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
              print(self.GPSDO_SER.readline() + "\n")
            #print "GPS Mode Enabled"
        elif (flag == False):
            self.collectResponse('@@@@')
            #print "GPS Mode Disabled"
            
    def setTrack(self, flag):
        if flag == True:
            response = self.collectResponse('TR1')
            if (response[:-2] == "1"):
                print("Tracking to PPSREF set \n")
        elif (flag == False):
            response = self.collectResponse('TR0')
            if response[:-2] == "0":
                print("Tracking to PPSREF unset \n")

    def setSync(self, flag):
        if (flag == True):
            response = self.collectResponse('SY1')
            if response[:-2] == "1":
                print("PPSOUT synchronisation to PPSINT set \n")
        elif (flag == False):
            response = self.collectResponse('SY0')
            if (response[:-2] == "0"):
                print("PPSOUT synchronisation to PPSINT unset \n")
    
    def isTrackingSet(self):
        response = self.collectResponse('TR?')
        if response[:-2] == "1":
                print("Tracking to PPSREF is Set\n")
                return True
        if response[:-2] == "0":
                print("Tracking to PPSREF not set \n")
                return False
        return False

    def isSyncSet(self):
        response = self.collectResponse('SY?')
        if response[:-2] == "1":
            print("PPSOUT synchronisation to PPSINT set \n")
            return True
        if response[:-2] == "0":
            print("PPSOUT synchronisation to PPSINT not set \n")
            return False
        return False
     
    def getPPSPulseWidth(self):
         pulse_Length = self.collectResponse('PW?????????') 
         #print( "Pulse Length in ns:" , pulse_Length)
         self.PPSPulseWidth = 66*round(float(pulse_Length)/66) # find the actual pulse length, must be multiple of 66ns
         #print( "Pulse length in ns:", pulse_Length)
         return self.PPSPulseWidth  
                                   
    def stopBeating(self):
        response = "0"
        while (response != ""):
          self.collectResponse("BT0")
          self.collectResponse("MAW0B00")
          self.collectResponse("MAW0C00")
          time.sleep(0.2)
          response = self._readLine()
          if not response: break
        #print "Stopped Beating GPSDO Messages"
      
    def getGpsdoStatus(self):
         x= str(self.collectResponse('ST')[0:1])
         return _decodeGPSDOStatus(x)
     
    def getGpsTime(self):
      return str(self.collectResponse('TD'))[0:8]
    
    def getGpsDate(self):
       return str(self.collectResponse('DT'))[0:10]
       
    def getRbMetrics(self):
      count = 5
      try:
        M = self.collectResponse('M')
      except Exception as e:
        print(str(e))
        M = " "
      if (len(M) != 26):
        try:
          while (count > 0) & (len(M) != 26):
            print("Not Responding Trying again in 2 seconds")
            time.sleep(2)
            M = self.collectResponse('M')
            count -= 1
        except Exception as e:
          print(str(e))
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

    '''
    def getGpsData(self,flag):
      if (flag):
        self.setGpsCom(True)
        self.streamGps = True
        self.gpsp = GpsPoller() # create the thread
        self.gpsp.start() # start it up
        print("Started up the GPS Polling thread")
      elif(not flag):
        self.streamGps = False
        self.setGpsCom(False)
    '''
    
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
          response = self._readLine() 
          #print(response)
          if (response[0:6] == "$PTNTA"):
            self.decodePTNTA(response)
          elif (response[0:6] == "$PTNTS"):
            self.decodePTNTS(response)
          elif (response[0:6] == "$GPRMC"):
            self.decodeGPRMC(response)
        except Exception as e:
          pass
          #print str(e)
        time.sleep(0.2)
      #print "Stopping PPSMetricsPoller"


    def decodePTNTA(self, response):
       responseArray = response.split(",")
       
       #Date and time
       self.GpsDateTime = int(responseArray[1]);
       newEpochTime = _dateTimeToEpoch(responseArray[1])
       if (((newEpochTime - self.epochGpsDateTime) != 1) and (self.firstQuery == False)):
          print("Error in date and time from GPSDO")
          print(newEpochTime - self.epochGpsDateTime)
       self.epochGpsDateTime = newEpochTime
       self.firstQuery = False
       #print( "GPS Time : ", self.GpsDateTime)
       
       #Oscilator Quality 
       if (responseArray[2]=="0"):
          self.DisapliningStatus = "Warming Up"
       elif (responseArray[2]=="1"):
          self.DisapliningStatus = "Freerun"
       elif (responseArray[2]=="2"):
          self.DisapliningStatus = "Disciplined"
       
        #PPSREF-PPSInT Interval
       val = int(responseArray[4])
       if val < 499999999:
         self.EffTimeInt = int(responseArray[4])
       else:
         self.EffTimeInt = int(responseArray[4])-999999999
       
        #Fine Phase Comparator
       self.FinePhaseComp = int(responseArray[5])
       
       #GPSDO Status
       self.Status = _decodeGPSDOStatus(str(responseArray[6]))
       
       #GPS Vaalidity 
       GPSStatus = responseArray[8].split("*")
       if (GPSStatus[0] == "0"):
          self.GPSStatus = "Invalid"
       elif (GPSStatus[0] == "1"):
          self.GPSStatus = "Manual"
       elif (GPSStatus[0] == "2"):
          self.GPSStatus = "Older than 240 hrs"
       elif (GPSStatus[0] == "3"):
          self.GPSStatus = "Fresh"
       
    def decodePTNTS(self,response):
      responseArray = response.split(",") 
      self.Status = _decodeGPSDOStatus(str(responseArray[2]))
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
       
