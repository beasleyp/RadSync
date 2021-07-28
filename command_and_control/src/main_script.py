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


#Master Node Script

from gps import *
from time import * # double check this
import os
import RPi.GPIO as GPIO
import time
import sys
from Tkinter import *

import threading
import datetime

#Gui Rekated imports 
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib import style
from collections import deque
import numpy as np
import csv

#import from RadSync src folder
import trigger_control
import grclok_1500
import network_utils


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




# GPSDO presence flag
GPSDO_Present = True


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

#***************END***********************


  
# ************* General Program Related Definitions **********************

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

def return_hit(event): ####
  if (user_query.get() != ""):
    GPSDO_Send()
    user_query.set("") # clear the query box when enter is pressed
  if (trig_time.get() != ""):
    Trigger.setTriggerPending()
    #trig_time.set("") # clear the trigger query box
  mGui.bind('<Return>',return_hit)
  
# ************** End of General System Setup Related Definitions **************
          

# ******************** Network Related Definitions ***************************

def listenForSlaves():
  TCPServer.startServer()

def disconnectSlaves():
  TCPServer.stopServer()
  
# **************** End of Network Related Definitions *************************

# ******************** Save PPS Related Definitions ***************************


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
      
      
# ****************** End of PPS Save Related Definitions *********************




# ******************** GPS related defintions********************


    
  
# ************** Main window GPSDO metrics related defintions*****************

# **************** GUI Function Definitions ************************     
    

      
def GPSDO_Send(): 
    query = user_query.get()+"\r"
    response = GPSDO.sendQuery(query)
    DO_TextBox.insert(END,response[:-2]+"\n")
    DO_TextBox.yview(END)

def pollGPSDO():
   global Polling_GPSDO# Copyright (C) University College London 2021
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

def clock():
  current_time.set("Time: "+str(datetime.datetime.now().time())[0:8] ) # refresh the display
  mGui.after(1000, clock)       
       
# **************** End of GUI Function Definitions ************************     
  
# **************** End of function definitions ****************************************************************   
       
       
       
       
       
# *********************** Program Begin ********************************
if __name__ == "__main__":
    
    #first initalise communication to GPSDO 
    
    
    # Setup the GUI
    mGui = Tk()
    mGui.geometry("1900x1000+220+140") # Window Geometry
    mGui.title("GPSDO Synchrnonisation System - Master Node Control Interface")
    #mGui.configure(bg="skyblue")
    LARGE_FONT= ("Verdana", 12)
    style.use("ggplot")
    # End of GUI setup 
  
  
  
  

#Initialise all required objects 
Trigger = trigger_control.Trigger() # Create trigger instance
GPSDO = grclok_1500.SpecGPSDO(GPSDO_Present) # Create GPSDO instance

Setup_CheckBox()
setSysTime() #set OS time to GPS Time
#clock() #Setup live clock on GUI
mGui.after(1000, updateGpsdoMetrics)
TCPServer = network_utils.RadSyncServer() #Create NetworkConnection Server
mGui.mainloop() #End of program

# *********************** Program End ********************************
