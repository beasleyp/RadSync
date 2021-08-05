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


import argparse
import datetime
from time import * # double check this
import os
import RPi.GPIO as GPIO
import time
import sys

from tkinter import *

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
from . import radsync_network_interface as raddic

os.system('sudo renice -18 `pgrep idle`')
os.system('clear') 
# GPSDO presence flag
GPSDO_Present = True



def handle_slave_trigger_request(unix_trigger_deadline,trigger_id):
    # senf request to trigger module
    Trigger.setup_slave_trigger(unix_trigger_deadline,trigger_id)
    # send response to master node with gps validity
    message =  raddic.create_radsync_trig_ack_message(System_tracker.this_node, System_tracker.get_node_gps_state())
    Client.send_message(message)

def handle_slave_trigger_ack(node_number,gps_sync_state):
    
    if int(node_number) == 1:
        #set node validity in system tracker 
        System_tracker.node_1_gps_quality = gps_sync_state
        # node 2 is disconnected or we have recieved its gps validity already and arestor is connected. message arestor trigger ack
        
        if ((System_tracker.node_2_connected == False) or (System_tracker.node_2_gps_quality != raddic.not_connected)) and (System_tracker.arestor_connected):
            send_arestor_trigger_ack()
            
    if int(node_number) == 2:
        System_tracker.node_2_gps_quality = gps_sync_state
        if ((System_tracker.node_1_connected == False) or (System_tracker.node_1_gps_quality != raddic.not_connected)) and System_tracker.arestor_connected:
            send_arestor_trigger_ack()
    
    
def send_arestor_trigger_ack():
    message = raddic.create_arestor_trig_req_response(str(Trigger.unix_gps_trigger_deadline), System_tracker.this_node_gps_quality, System_tracker.node_1_gps_quality, System_tracker.node_2_gps_quality)
    Server.send_to_arestor(message)
        
def handle_arestor_trigger_request(trigger_type,trigger_delay):
    pass


#*************Exit Routine****************
def exit_routine(): # runs this routine upon exit
    MainUi.gpsdo_textbox.insert(END,"****Exiting Program****\n")
    MainUi.mGui.destroy() # close the window
    #TCPServer.stopServer()
    GPSDO.pollGpsdoMetrics(False)
    GPSDO.GPSDO_SER.close()
    setup_file_to_save_gpsdo_metics(False)
    os._exit(1)


def _set_system_time():
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
    file_name = "/home/pi/Desktop/GPSDO_Log_Files/N0_GPSDO_Log " + now.strftime("%Y-%m-%d %H:%M:%S")+ ".txt"
    gpsdo_metrics_file = open(file_name,"a")
    gpsdo_metrics_writer = csv.writer(gpsdo_metrics_file)
    gpsdo_metrics_writer.writerow(header)
  elif not flag:
    try:
      gpsdo_metrics_file.close()
      print('Closing file for saving GPSDO metrics')
    except Exception as e:
      pass     
      epoch_date
def save_gpsdo_metrics_to_file():
      global gpsdo_metrics_writer, gpsdo_metrics_file
      gpsdo_metrics_writer.writerow([GPSDO.GpsDateTime,GPSDO.epochGpsDateTime,GPSDO.Status,GPSDO.RbStatus,GPSDO.CurrentFreq,GPSDO.HoldoverFreq,GPSDO.ConstantMode,GPSDO.ConstantValue,GPSDO.Latitude,GPSDO.LatitudeLabel,GPSDO.Longitude,GPSDO.LongitudeLabel,GPSDO.Validity,GPSDO.FinePhaseComp,GPSDO.EffTimeInt,GPSDO.PPSRefSigma])
      

class sync_system_state():
    '''
    class and methods used to track the stateself.this_node_gps_quality  of the synchrnoisation system
        used by master and slave nodes
    '''    
    def __init__(self, node):
        self.this_node = node
        if self.this_node == 0:
            self.arestor_connected = False
            self.node_1_connected = False
            self.node_2_connected = False
            self.this_node_gps_quality = raddic.not_connected
            self.node_1_gps_quality = raddic.not_connected
            self.node_2_gps_quality = raddic.not_connected
            self.this_node_trig_validity = raddic.not_connected
            self.node_1_trig_validity = raddic.not_connected
            self.node_2_trig_validity = raddic.not_connected
        else:
            self.this_node_gps_quality = raddic.not_connected
            self.this_node_trig_validity = raddic.not_connected
    
    def get_node_gps_state(self):
        if GPSDO.Status == "Sync to PPS REF":
            pps_error = int(GPSDO.FinePhaseComp)
            if pps_error < 10:
                self.this_node_gps_quality = raddic.good_gps_sync
            elif pps_error < 20:
                 self.this_node_gps_quality = raddic.nominal_gps_sync
            else:
                 self.this_node_gps_quality = raddic.poor_gps_sync
        else:
            self.this_node_gps_quality = GPSDO.Status
        return self.this_node_gps_quality 
    
def parse_cmdline_args():
    '''
    passes the command line arguments to the scripts 
    '''
    parser = argparse.ArgumentParser(description='Program to control the UCL Radar Synchronisation System RadSync')
    
    parser.add_argument('node', action = 'store',
                        help = 'Select enter the number of RadSync node: '
                        '0 = master, 1,2 = slave', type = int)
    
    args = parser.parse_args()
    
    if args.node >2 or args.node<0:
        parser.error("Please enter a valid node number either 0,1,2")
    return args
    

# *********************** Program Begin ********************************
def main():
    '''
    Entry point for RadSync Control Script.
    '''
    global Trigger, MainUi, GPSDO, System_tracker, Server, Client

    args = parse_cmdline_args()
    
    # Start GPSDO service
    GPSDO = grclok_1500.SpecGPSDO(True) # Create GPSDO instance
    
    if args.node == 0:
        #Initialise Trigger
        Trigger = trigger_control.Trigger(args.node) # Create trigger instance
        MainUi = main_ui_window.RadSyncUi(args.node)
        
        # Start server to serve connections to RadSyn Slaves and Arestor clients 
        Server = network_utils.MasterRadSyncServer()
        Server.start_server()
    
    if args.node == 1:
        #Initialise Trigger
        Trigger = trigger_control.Trigger(args.node) # Create trigger instance
        MainUi = main_ui_window.RadSyncUi(args.node)
        
        Client = network_utils.SlaveRadSyncClient()
        Client.start_client()

    # Start UI main thread
    MainUi.setup_checkboxes() 
    MainUi.mGui.protocol('WM_DELETE_WINDOW',exit_routine)
    
    #set RPI time to gps time - to delete when NTP server running
    _set_system_time()
    MainUi.set_poll_gpsdo(True)
    
    System_tracker = sync_system_state(args.node)
    
     

    
    MainUi.mGui.mainloop()   