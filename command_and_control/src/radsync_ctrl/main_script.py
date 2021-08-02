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

os.system('sudo renice -18 `pgrep idle`')
os.system('clear') 
# GPSDO presence flag
GPSDO_Present = True


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

def setSysTime():
  global system_time_set_flag
  system_time_set_flag = False
  if (system_time_set_flag == False):
    try:
        GPSDO_Date = GPSDO.getGpsDate()
        GPSDO_Time = GPSDO.getGpsTime()
        TimeLength = len(GPSDO_Time) - 2
        gpstime = GPSDO_Date[0:4] + GPSDO_Date[5:7] + GPSDO_Date[8:10] + " " + GPSDO_Time
        os.system('sudo date -u --set="%s"'% gpstime)
        print("System Time set to GPS time")
        system_time_set_flag = True
    except(Exception, e):
      print(str(e))
  

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
    except(Exception,e):
      pass     
      
def save_gpsdo_metrics_to_file():
      global gpsdo_metrics_writer, gpsdo_metrics_file
      gpsdo_metrics_writer.writerow([GPSDO.GpsDateTime,GPSDO.epochGpsDateTime,GPSDO.Status,GPSDO.RbStatus,GPSDO.CurrentFreq,GPSDO.HoldoverFreq,GPSDO.ConstantMode,GPSDO.ConstantValue,GPSDO.Latitude,GPSDO.LatitudeLabel,GPSDO.Longitude,GPSDO.LongitudeLabel,GPSDO.Validity,GPSDO.FinePhaseComp,GPSDO.EffTimeInt,GPSDO.PPSRefSigma])
      

       
# *********************** Program Begin ********************************
def main():
    global Trigger, MainUi, GPSDO
    print("Entry point Success")
    
    
    #Initialise Trigger
    Trigger = trigger_control.Trigger() # Create trigger instance
    
    # Start GPSDO service
    GPSDO = grclok_1500.SpecGPSDO(True) # Create GPSDO instance
    
    #Initialsie Main UI window 
    MainUi = main_ui_window.RadSyncUi()
    
    # Start UI main thread
    MainUi.setup_checkboxes() 
    MainUi.mGui.mainloop()    
    
