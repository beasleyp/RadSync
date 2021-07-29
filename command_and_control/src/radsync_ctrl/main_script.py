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
main_script.py contains the entry points for the scripts created by the 
installer (found in setup.py)
'''



#Master Node Script

from time import * # double check this
import os
import RPi.GPIO as GPIO
import time
import sys
#from Tkinter import *

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
from . import trigger_control
from . import grclok_1500
from . import network_utils
from . import main_ui_window

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
  print("Shutting down thread: " + str(self))
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
        print("System Time set to GPS time")
    except( Exception, e):
      print(str(e))

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

'''
functions to deal with saving gpsdo metrics to file
'''

def setup_file_to_save_gpsdo_metics(flag):
  global gpsdo_metrics_writer, gpsdo_metrics_file
  header = ['GPS Time','epoch Time','GPSDO Status','RB Status','Current Freq','Holdover Freq','Time Constant Mode','Time Constant Value','Latitude','N/S','Longitude','E/W','Validiity','Fine Phase Comparator','Effective Time Interval','PPSREF sigma']
  if flag:
    print("Open file for saving GPSDO metrics")
    now = datetime.datetime.now()
    file_name = "GPSDO_Log_Files/N0_GPSDO_Log " + now.strftime("%Y-%m-%d %H:%M:%S")+ ".txt"
    gpsdo_metrics_file = open(file_name,"a")
    gpsdo_metrics_writer = csv.writer(gpsdo_metrics_file)
    gpsdo_metrics_writer.writerow(header)
  elif not flag:
    try:
      f.close()
      print('Closing for saving GPSDO metrics')
    except( Exception,e):
      pass     
      
def save_gpsdo_metrics_to_file():
      global gpsdo_metrics_writer, gpsdo_metrics_file
      gpsdo_metrics_writer.writerow([GPSDO.GpsDateTime,GPSDO.epochGpsDateTime,GPSDO.Status,GPSDO.RbStatus,GPSDO.CurrentFreq,GPSDO.HoldoverFreq,GPSDO.ConstantMode,GPSDO.ConstantValue,GPSDO.Latitude,GPSDO.LatitudeLabel,GPSDO.Longitude,GPSDO.LongitudeLabel,GPSDO.Validity,GPSDO.FinePhaseComp,GPSDO.EffTimeInt,GPSDO.PPSRefSigma])
      

       
# *********************** Program Begin ********************************
def main():
    global Trigger, MainUi
    print("Entry point Success")
    
    #first check if a the GPSDO is reachable - if not break with error
    #GPSDO = grclok_1500.SpecGPSDO(True) # Create GPSDO instance
    
    #setup Gui
    Trigger = trigger_control.Trigger() # Create trigger instance
    MainUi = main_ui_window.RadSyncUi()
    
    
    

'''    
    
    # Setup the GUI
    mGui = Tk()
    mGui.geometry("1900x1000+220+140") # Window Geometry
    mGui.title("GPSDO Synchrnonisation System - Master Node Control Interface")
    #mGui.configure(bg="skyblue")
    LARGE_FONT= ("Verdana", 12)
    style.use("ggplot")
    # End of GUI setup 
  
  
  
  


Setup_CheckBox()
setSysTime() #set OS time to GPS Time
#clock() #Setup live clock on GUI
mGui.after(1000, updateGpsdoMetrics)
TCPServer = network_utils.RadSyncServer() #Create NetworkConnection Server
mGui.mainloop() #End of program

# *********************** Program End ********************************
'''