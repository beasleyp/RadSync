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
import time
import sys

from tkinter import *

#Gui Rekated imports 
import matplotlib
matplotlib.use("TkAgg")

import csv
from enum import Enum

#import from RadSync src folder
from . import trigger_control
from . import lnr_clok_1500
from . import trimble_thunderbolt_e
from . import network_utils
from . import main_ui_window
from . import radsync_network_interface as raddic

os.system('sudo renice -18 `pgrep idle`')
os.system('clear') 
# GPSDO presence flag
GPSDO_Present = True

'''
handles for network interface 
'''

def handle_slave_trigger_request(unix_trigger_deadline, trigger_duration, trigger_id):
    '''
    function ran when a slave node recevies a trigger request from the master node
    '''
    # request trigger from trigger module
    Trigger.setup_slave_trigger(unix_trigger_deadline, trigger_duration, trigger_id)
    # send response to master node with gps validity
    message =  raddic.create_radsync_trig_ack_message(str(System_tracker.this_node), System_tracker.get_node_gps_state())
    Client.send_message(message)

def handle_slave_trigger_ack(node_number,gps_sync_state):
    '''
    function ran when master node received triger ack from slave 
    '''
    
    if int(node_number) == 1:
        #set node validity in system tracker 
        print(gps_sync_state)
        System_tracker.node_1_gps_quality = gps_sync_state
        #If node 2 is disconnected, or we have recieved its gps validity already, and arestor is connected send arestor trigger ack
        if ((System_tracker.node_2_connected == False) or (System_tracker.node_2_gps_quality != raddic.not_connected)) and (System_tracker.arestor_connected):
            send_arestor_trigger_ack(True)
           
    if int(node_number) == 2:
        System_tracker.node_2_gps_quality = gps_sync_state
        #If node 1 is disconnected, or we have recieved its gps validity already, and arestor is connected send arestor trigger ack
        if ((System_tracker.node_1_connected == False) or (System_tracker.node_1_gps_quality != raddic.not_connected)) and System_tracker.arestor_connected:
            send_arestor_trigger_ack(True)  
    
    
def send_arestor_trigger_ack(force_message):
    # check to see if any other RadSync Nodes are connected. If not, send ack message to Arestor.
    if int(System_tracker.this_node) == 0:
        if ((System_tracker.node_1_connected == False) or (System_tracker.node_1_gps_quality != raddic.not_connected)) and ((System_tracker.node_2_connected == False) or (System_tracker.node_2_gps_quality != raddic.not_connected)) and System_tracker.arestor_connected:
            message = raddic.create_arestor_trig_req_response(str(Trigger.unix_gps_trigger_deadline), System_tracker.get_node_gps_state(), System_tracker.node_1_gps_quality, System_tracker.node_2_gps_quality)
            Server.send_to_arestor(message)
    # regardless of what's connected send ack to arestor. Normally ran by 'handle_slave_trigger_ack' function.
    if force_message == True:      
        message = raddic.create_arestor_trig_req_response(str(Trigger.unix_gps_trigger_deadline), System_tracker.get_node_gps_state(), System_tracker.node_1_gps_quality, System_tracker.node_2_gps_quality)
        Server.send_to_arestor(message)
        
def handle_arestor_trigger_request(trigger_type,trigger_delay):
    '''
    function ran when master node received trigger req from Arestor 
    
    '''
    # set the trigger type to that requested by 
    Trigger.triggId = int(trigger_type)
    # update the trigger selection
    Trigger.set_trigger_type()
    # setup a trigger in the trigger subsystem
    Trigger.setTriggerPending(trigger_delay,1)

    


def handle_slave_trigger_validity(node_number,trigger_validity):
    if int(node_number) == 1: 
        System_tracker.node_1_trig_validity = trigger_validity
    if int(node_number) == 2:
        System_tracker.node_2_trig_validity = trigger_validity








#*************Exit Routine****************
def exit_routine(): # runs this routine upon exit
    global Server, System_tracker, Client
    MainUi.gpsdo_textbox.insert(END,"****Exiting Program****\n")
    MainUi.mGui.destroy() # close the window
    #Server.stopServer()
    GPSDO.pollGpsdoMetrics(False)
    GPSDO.GPSDO_SER.close()
    time.sleep(1)
    setup_file_to_save_gpsdo_metics(False)
    if System_tracker.this_node == 0:
        Server.stop_server()
    else:
        Client.stop_client()
    os._exit(1)
    

def _set_system_time():
  global system_time_set_flag, gpsdo_connected, GPSDO
  system_time_set_flag = False
  if (system_time_set_flag == False):
      
    if gpsdo_connected == GPSDOType.LNRCLOK1500 :
        try:
            GPSDO_Date = GPSDO.getGpsDate
            print('GPSDO_Date = ', GPSDO_Date)
            GPSDO_Time = GPSDO.getGpsTime()
            print('GPSDO_Time = ', GPSDO_Time)
            TimeLength = len(GPSDO_Time) - 2
            gpstime = GPSDO_Date[0:4] + GPSDO_Date[5:7] + GPSDO_Date[8:10] + " " + GPSDO_Time
            print('GPSDO_date_time = ', gpstime)
            os.system('sudo date -u --set="%s"'% gpstime)
            print("System Time set to GPS time")
            system_time_set_flag = True
        except Exception as  e:
            print(str(e))
    elif gpsdo_connected == GPSDOType.THUNDERBOLTE :
        try:
            
            #GPSDO.epochGpsDateTime
            gpstime = "@" + str(1644596668)
            print(str(gpstime))
            command = "sudo date -s " + gpstime 
            os.system(command)
            print("System Time set to GPS time")
            system_time_set_flag = True
        except Exception as  e:
            print(str(e))
        

'''
functions to deal with saving gpsdo metrics to file
'''

def setup_file_to_save_gpsdo_metics(flag):
  global gpsdo_metrics_writer, gpsdo_metrics_file
  header = ['GPS Time','epoch Time','GPSDO Status','RB Status','Current Freq','Holdover Freq','Time Constant Mode','Time Constant Value','Latitude','N/S','Longitude','E/W','Altitude (WGS84)','GPS Status','Fine Phase Comparator','Effective Time Interval','PPSREF sigma']
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
      print(str(e))
         
      
def save_gpsdo_metrics_to_file():
      global gpsdo_metrics_writer, gpsdo_metrics_file
      gpsdo_metrics_writer.writerow([GPSDO.GpsDateTime,GPSDO.epochGpsDateTime,GPSDO.Status,GPSDO.DiscipliningStatus,GPSDO.CurrentFreq,GPSDO.HoldoverFreq,GPSDO.ConstantMode,GPSDO.ConstantValue,GPSDO.Latitude,GPSDO.LatitudeLabel,GPSDO.Longitude,GPSDO.LongitudeLabel,GPSDO.Altitude,GPSDO.GPSStatus,GPSDO.FinePhaseComp,GPSDO.EffTimeInt,GPSDO.PPSRefSigma])
      

class sync_system_state():
    '''
    class and methods used to track the state of the synchrnisation system
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
            elif pps_error < 30:
                 self.this_node_gps_quality = raddic.nominal_gps_sync
            else:
                 self.this_node_gps_quality = raddic.poor_gps_sync
        else:
            self.this_node_gps_quality = GPSDO.Status
        return self.this_node_gps_quality 
    
    def reset_states(self):
            self.this_node_gps_quality = raddic.not_connected
            self.node_1_gps_quality = raddic.not_connected
            self.node_2_gps_quality = raddic.not_connected
            self.this_node_trig_validity = raddic.not_connected
            self.node_1_trig_validity = raddic.not_connected
            self.node_2_trig_validity = raddic.not_connected
    
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

class GPSDOType(Enum):
        NOTCONNECTED = 1
        LNRCLOK1500 = 2
        THUNDERBOLTE = 3

def _connect_to_gpsdo():
    global gpsdo_connected
    '''
    attempt to connect to a GPSDO - LNRCLOK-1500 first, then Trimble.
    '''
    '''
    GPSDO = lnr_clok_1500.SpecGPSDO(True) # Create GPSDO instance
    gpsdo_connected = GPSDOType.LNRCLOK1500
    print("Connected to Spectratime LNRCLOK-1500 GPSDO")
    return GPSDO
    '''
    try:
        GPSDO = lnr_clok_1500.SpecGPSDO(True) # Create GPSDO instance
        gpsdo_connected = GPSDOType.LNRCLOK1500
        print("Connected to Spectratime LNRCLOK-1500 GPSDO")
        return GPSDO
    except Exception as e:
        print(str(e))
        try:
            if GPSDO.gpsdoDetected == True:
                gpsdo_connected = GPSDOType.LNRCLOK1500
        except Exception as e:
            gpsdo_connected = GPSDOType.NOTCONNECTED

    
    if gpsdo_connected == GPSDOType.NOTCONNECTED:
        try:
            GPSDO = trimble_thunderbolt_e.ThunderboltGPSDO(True) # Create GPSDO instance           
            gpsdo_connected = GPSDOType.THUNDERBOLTE
            print("Connected to Trimble Thunderbolt E GPSDO")
            return GPSDO
        except Exception as e:
            print(str(e))
            print("Unable to connect to a GPSDO")
    


# *********************** Program Begin ********************************
def main():
    '''
    Entry point for RadSync Control Script.
    '''
    global Trigger, MainUi, GPSDO, System_tracker, Server, Client

    args = parse_cmdline_args()
    
    # Connect to a GPSDO
    GPSDO = _connect_to_gpsdo()
    
    if args.node == 0:
        #Initialise Trigger
        Trigger = trigger_control.Trigger(args.node) # Create trigger instance
        MainUi = main_ui_window.RadSyncUi(args.node)
        time.sleep(5)
        
        #Start server to serve connections to RadSyn Slaves and Arestor clients 
        Server = network_utils.MasterRadSyncServer()
        Server.start_server()
    
    if args.node == 1:
        #Initialise Trigger
        Trigger = trigger_control.Trigger(args.node) # Create trigger instance
        MainUi = main_ui_window.RadSyncUi(args.node)
        time.sleep(5)
        Client = network_utils.SlaveRadSyncClient()
        Client.start_client()

    # Start UI main thread
    MainUi.setup_checkboxes() 
    MainUi.mGui.protocol('WM_DELETE_WINDOW',exit_routine)
    
    MainUi.set_poll_gpsdo(True)

    System_tracker = sync_system_state(args.node)
  
    #set RPI time to gps time - to delete when NTP server running
    #_set_system_time() 

    
    MainUi.mGui.mainloop()   