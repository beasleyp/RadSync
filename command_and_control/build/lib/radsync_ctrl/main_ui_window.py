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
from . import grclok_1500_popout

from tkinter import *
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib import style
from collections import deque
import numpy as np
import time


class RadSyncUi():
    
    def __init__(self, node_number):
        global mGui 
        
        
        # Setup Ui Layout
        self.mGui = Tk()
        self.mGui.geometry("1900x1000+220+140") # Window Geometry
        style.use("ggplot")
        
        # Variables for Oscillator Data Frame
        self.gpsdo_status = StringVar()
        self.disciplining_status = StringVar()
        self.current_gpsdo_freq = StringVar()
        self.gpsdo_holdover_freq = StringVar()
        self.gpsdo_time_constant_mode = StringVar()
        self.gpsdo_time_constant_value = StringVar()
        self.gpsdo_holdover_duration = StringVar()
        
        # Variables for GPS Receiver Data Frame
        self.gpsdo_latitude = StringVar()
        self.gpsdo_longitude = StringVar()
        self.gpsdo_altitude = StringVar()
        self.gpsdo_satellites = StringVar()
        self.gpsdo_tracking_info = StringVar()
        self.gpsdo_gps_status = StringVar()
                
        # Variables for checkboxes
        self.gpsdo_track_checkbox_state = IntVar()
        self.gpsdo_sync_checkbox_state = IntVar()
        self.gpsdo_gps_comms_checkbox_state = IntVar()
        self.gpsdo_polling_checkbox_state = IntVar()
        self.save_gpsdo_metrics_checkbox_state = IntVar()
        
        # Variables to control polling
        self.is_polling_gpsdo = False
        self.save_gpsdo_metrics_flag = False

        # Variables for trigger box
        self.user_trigger_delay_input = StringVar()
        self.trigger_countdown_text = StringVar()
    
        # Variables for PPSOUT Error Variables
        self.pps_graphs_xaxis_length = 10 #60 * 2 # length of PPS Error Arrays graph time axis (default 2 mins)
        self.fine_phase_comparator_deque = deque(maxlen = self.pps_graphs_xaxis_length)
        self.effective_time_interval_deque = deque(maxlen = self.pps_graphs_xaxis_length)
        self.ppsref_sigma_deque = deque(maxlen = self.pps_graphs_xaxis_length)
        
        # General Variables
        self.current_time = StringVar()
        self.gpsdo_user_query = StringVar()
       
        # Varibles for trigger
        self.rfsoctriggState = IntVar()
        self.bladeradtriggState = IntVar()
        self.freqdivtriggState = IntVar()
        
        if node_number == 0:
            self.mGui.title("RadSync Node 0 - Master Node Control Interface")
            self._setup_master_ui_layout()
        if node_number == 1:
            self.mGui.title("RadSync Node 1 - Slave Node Control Interface")
            self._setup_slave_ui_layout()
        self.update_gpsdo_metrics()
    
    '''
    GPSDO related control functions 
        the GPSDO service is insitialied in the main_script module as a global object, 
        it is imopoted to this module as a global object.
        avaliable as 'main_script.GPSDO'
    '''        

    # was trackMode
    def set_track_mode(self):
        if self.gpsdo_track_checkbox_state.get() == 1:
            main_script.GPSDO.setTrack(True)
            self.gpsdo_textbox.insert(END,"Tracking to PPSREF Set \n")
            self.gpsdo_textbox.yview(END)
        elif self.gpsdo_track_checkbox_state.get() == 0:
            main_script.GPSDO.setTrack(False)
            self.gpsdo_textbox.insert(END,"Tracking to PPSREF Unset \n")
            self.gpsdo_textbox.yview(END)
            
    def set_sync_mode(self):
        if self.gpsdo_sync_checkbox_state.get() == 1:
            main_script.GPSDO.setSync(True)
            self.gpsdo_textbox.insert(END,"PPSOUT Synchronisation to PPSINT Set \n")
            self.gpsdo_textbox.yview(END)
        elif self.gpsdo_sync_checkbox_state.get() == 0:
            main_script.GPSDO.setSync(False)
            self.gpsdo_textbox.insert(END,"PPSOUT Synchronisation to PPSINT Unset \n")
            self.gpsdo_textbox.yview(END)

    def set_gpsdo_mode(self):
        if self.gpsdo_gps_comms_checkbox_state.get() == 1:
            main_script.GPSDO.setGpsCom(True)
            #self.gpsdo_textbox.insert(END,"GPS Mode Enabled")
            self.gpsdo_textbox.yview(END)
        elif self.gpsdo_gps_comms_checkbox_state.get() == 0:
            main_script.GPSDO.setGpsCom(False)
            #self.gpsdo_textbox.insert(END,"GPS Mode Disabled")
            self.gpsdo_textbox.yview(END)
    
    
    def gpsdo_send(self): 
        query = self.gpsdo_user_query.get()
        response = main_script.GPSDO.collectResponse(query)
        self.gpsdo_textbox.insert(END,response[:-2]+"\n")
        self.gpsdo_textbox.yview(END)
    
    def set_poll_gpsdo(self, flag):
        if (flag):
         self.gpsdo_polling_checkbox_state.set(1)
         self.save_gpsdo_metrics_checkbox_state.set(1)
         self.poll_gpsdo()
         self.save_gpsdo_metrics()
        elif (flag == False):
         self.gpsdo_polling_checkbox_state.set(0)
         self.poll_gpsdo()

         
    def poll_gpsdo(self):
       if (self.gpsdo_polling_checkbox_state.get() == 1):
         main_script.GPSDO.pollGpsdoMetrics(True)
         self.is_polling_gpsdo = True
         self.mCheck_Save.config(state=ACTIVE)
       elif (self.gpsdo_polling_checkbox_state.get() == 0):
         main_script.GPSDO.pollGpsdoMetrics(False)
         self.is_polling_gpsdo = False
         self.save_gpsdo_metrics_checkbox_state.set(0)
         self.save_gpsdo_metrics
         self.mCheck_Save.config(state=DISABLED)    
        
    def save_gpsdo_metrics(self): 
        if self.save_gpsdo_metrics_checkbox_state.get() == 1:
            main_script.setup_file_to_save_gpsdo_metics(True)
            self.save_gpsdo_metrics_flag =  True 
        elif self.save_gpsdo_metrics_checkbox_state.get() == 0:
            main_script.setup_file_to_save_gpsdo_metics(False)
            self.save_gpsdo_metrics_flag = False
    
    
    '''
    Trigger related functions 
    '''
    def _request_trigger(self):
        # muse be polling to use the current trigger archetecture
        if(self.is_polling_gpsdo == False):
            self.set_poll_gpsdo(True)
            time.sleep(1)
        self.trigger_time_entry_box.configure(state=DISABLED) # Disable the entry box
        trigger_delay = int(self.user_trigger_delay_input.get()) 
        
        if (trigger_delay < 10) or (trigger_delay == ""): #don't accept a trigger deadline less than 10s away.
          self.trigger_text_box.insert(END, "Minimum trigger delay is 10s;\nTrigger delay set to 10s; \n")
          self.trigger_text_box.yview(END)
          trigger_delay = 10
        # request a trigger from trigger routine with trigger_delay in s  
        main_script.Trigger.setTriggerPending(trigger_delay)
    
    '''
    Network related functions 
    '''
    def _connect_to_master(self):
        pass
    
    def _disconnect_from_master(self):
        pass
    
    '''
    UI related functions
    '''    
    def return_hit(self, event):
      if (self.gpsdo_user_query.get() != ""):
        self.gpsdo_send()
        self.gpsdo_user_query.set("") # clear the query box when enter is pressed
      if (self.gpsdo_user_query.get() != ""):
        main_script.Trigger.setTriggerPending()
      self.mGui.bind('<Return>',return_hit)
            
    def clock(self):
        '''
        Function to update the clock on the main UI window- updates 1 Hz
        '''
        self.trigger_text_box.set("Time: "+str(datetime.datetime.now().time())[0:8] ) # refresh the display
        self.mGui.after(1000, self.clock)       
              

    def update_gpsdo_metrics(self):
       '''
       Funtction to update the GPSDO metrics - upates at 1 Hz
       '''
       #Variables for Oscillator Data Frame
       self.gpsdo_status.set(main_script.GPSDO.Status)
       self.disciplining_status.set(main_script.GPSDO.DiscipliningStatus)
       self.current_gpsdo_freq.set(main_script.GPSDO.CurrentFreq)
       self.gpsdo_holdover_freq.set(main_script.GPSDO.HoldoverFreq)
       self.gpsdo_time_constant_mode.set(main_script.GPSDO.ConstantMode)
       self.gpsdo_time_constant_value.set(main_script.GPSDO.ConstantValue)
       self.gpsdo_holdover_duration.set(main_script.GPSDO.HoldoverDuration)
       #Variables for GPS Receiver Data Frame
       self.gpsdo_latitude.set(str((round(main_script.GPSDO.Latitude,8))) + " " + main_script.GPSDO.LatitudeLabel)
       self.gpsdo_longitude.set(str((round(main_script.GPSDO.Longitude,8))) + " " + main_script.GPSDO.LongitudeLabel)
       #self.gpsdo_altitude.set(GPSDO.Altitude)
       #self.gpsdo_satellites.set(GPSDO.SatellitesPPS Error Items)
       #self.gpsdo_tracking_info.set(GPSDO.Tracking)
       self.gpsdo_gps_status.set(main_script.GPSDO.GPSStatus)
       self.mGui.after(1000, self.update_gpsdo_metrics)
       if self.save_gpsdo_metrics_flag:
           main_script.save_gpsdo_metrics_to_file()
    
    def setup_checkboxes(self):
        #setup GPSDO control check boxes
        tracking = main_script.GPSDO.isTrackingSet()
        synced = main_script.GPSDO.isSyncSet()
        if (tracking == True):
            self.gpsdo_track_checkbox_state.set(1)
        elif (tracking == False):
            self.gpsdo_track_checkbox_state.set(0)
        if (synced == True):
             self.gpsdo_sync_checkbox_state.set(1)
        elif (synced == False):
             self.gpsdo_sync_checkbox_state.set(0)
        main_script.GPSDO.setGpsCom(False)
        self.save_gpsdo_metrics_checkbox_state.set(0)
        self.gpsdo_polling_checkbox_state.set(0)
        self.save_gpsdo_metrics_checkbox_state.set(0)

                 
    def animate(self,i):
        if self.is_polling_gpsdo:
            
           self.effective_time_interval_deque.append(main_script.GPSDO.EffTimeInt)
           self.fine_phase_comparator_deque.append(main_script.GPSDO.FinePhaseComp)
           self.ppsref_sigma_deque.append(main_script.GPSDO.PPSRefSigma)
           Effective_Time_Int_np = np.array(self.effective_time_interval_deque,dtype=int)
           Fine_Phase_Comp_np = np.array(self.fine_phase_comparator_deque,dtype=int)
           PPSREF_Sigma_np = np.array(self.ppsref_sigma_deque,dtype=float)
           time_axis = np.linspace(-len(self.fine_phase_comparator_deque),0,len(self.fine_phase_comparator_deque))
           
           self.fpco.clear()
           self.fpco.plot(time_axis,Fine_Phase_Comp_np)
           self.fpco.set_title ("Fine Phase Comparator - PPSREF vs PPSINT", fontsize=10)
           self.fpco.set_ylabel("Temporal Error (ns)", fontsize=10)
           self.fpco.set_xlabel("Time (s)", fontsize=10)
           
           self.etio.clear()
           self.etio.plot(time_axis,Effective_Time_Int_np)
           self.etio.set_title ("Effective Time Interval - PPSREF vs PPSINT", fontsize=10)
           self.etio.set_ylabel("Temporal Error (ns)", fontsize=10)
           self.etio.set_xlabel("Time (s)", fontsize=10)
    
           self.sigo.clear()
           self.sigo.plot(time_axis,PPSREF_Sigma_np)
           self.sigo.set_title ("PPSREF Sigma", fontsize=10)
           self.sigo.set_ylabel("Time Variance (ns)", fontsize=10)
           self.sigo.set_xlabel("Time (s)", fontsize=10)    
        
    def _setup_master_ui_layout(self):
        '''
        function to setup the main UI structure
        '''

        # Create left and right frames
        left_frame = Frame(self.mGui, width=600, height=700,bd=1)
        left_frame.grid(row=0, column=0, padx=10, pady=5,sticky=N)
        right_frame = Frame(self.mGui, width=1200, height=700,bd=1)
        right_frame.grid(row=0, column=1, padx=10, pady=5,sticky=N)
        
        #***** Populate Left Frame ********
        
        # GPSDO Control Frame
        gpsdo_control_frame = Frame(left_frame, width=575, height=200,highlightbackground="black", highlightthickness=2)
        gpsdo_control_frame.grid(row=0,column=0, pady=10, padx=10)
        mlabel = Label(gpsdo_control_frame,text="GPSDO Controls",font=("Arial", 11)).grid(row=0,column=0,columnspan=3, pady=5,padx=5)
        mlabel = Label(gpsdo_control_frame,text="Track: ").grid(row=2,column=0)
        mlabel = Label(gpsdo_control_frame,text="Sync: ").grid(row=2,column=1)
        mlabel = Label(gpsdo_control_frame,text="GPS: ").grid(row=2,column=2)
        self.mCheck_TR = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=self.gpsdo_track_checkbox_state,onvalue=1,offvalue=0,command=self.set_track_mode)
        self.mCheck_SY = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=self.gpsdo_sync_checkbox_state,onvalue=1,offvalue=0,command=self.set_sync_mode)
        self.mCheck_GPS = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=self.gpsdo_gps_comms_checkbox_state,onvalue=1,offvalue=0,command=self.set_gpsdo_mode)
        self.mCheck_TR.grid(row=3,column=0)
        self.mCheck_SY.grid(row=3,column=1)
        self.mCheck_GPS.grid(row=3,column=2)
        mlabel = Label(gpsdo_control_frame,text="Enter Query").grid(row=4,column=0,columnspan=3,sticky=W,padx=5)
        self.gpsdo_message_entry = Entry(gpsdo_control_frame,textvariable=self.gpsdo_user_query).grid(row=5,column=0,columnspan=2,sticky=W,padx=5)
        self.mbutton = Button(gpsdo_control_frame,text="Send",command=self.gpsdo_send).grid(row=5,column=2,padx=5)
        self.mlabel = Label(gpsdo_control_frame,text="GPSDO Response").grid(row=6,column=0,columnspan=3,sticky=W,padx=5)
        self.gpsdo_textbox = Text(gpsdo_control_frame,height=6,width=45)
        self.gpsdo_textbox.grid(row=7,column=0, columnspan = 3,pady=5,padx=5)
        self.gpsdo_textbox_scroll = Scrollbar(self.gpsdo_textbox,command=self.gpsdo_textbox.yview)
        self.gpsdo_textbox.configure(yscrollcommand=self.gpsdo_textbox_scroll.set)
        #end of GPSDO control frame
        
        
        # Trigger Control Frame 
        trigger_control_frame = Frame(left_frame, width=575, height=200,highlightbackground="black", highlightthickness=2)
        trigger_control_frame.grid(row=1,column=0,pady=10,padx=10)
        mlabel = Label(trigger_control_frame,text="Trigger Controls",font=("Arial", 11)).grid(row=0,column=0,columnspan=3,pady=5,padx=5)
        mlabel = Label(trigger_control_frame,text="RFSoC: ").grid(row=1,column=0)
        mlabel = Label(trigger_control_frame,text="bladeRAD: ").grid(row=1,column=1)
        mlabel = Label(trigger_control_frame,text="Freq Div: ").grid(row=1,column=2)
        mCheck_rfsocTrigg = Checkbutton(trigger_control_frame,state=ACTIVE,variable=self.rfsoctriggState,onvalue=1,offvalue=0,command=main_script.Trigger.triggerSelect)
        mCheck_bladeradTrigg = Checkbutton(trigger_control_frame,state=ACTIVE,variable=self.bladeradtriggState,onvalue=1,offvalue=0,command=main_script.Trigger.triggerSelect)
        mCheck_freqdiv_Trigg = Checkbutton(trigger_control_frame,state=ACTIVE,variable=self.freqdivtriggState,onvalue=1,offvalue=0,command=main_script.Trigger.triggerSelect)
        mCheck_rfsocTrigg.grid(row=2,column=0)
        mCheck_bladeradTrigg.grid(row=2,column=1)
        mCheck_freqdiv_Trigg.grid(row=2,column=2)
        mTrigLabel = Label(trigger_control_frame,text="Enter seconds in future to Trigger").grid(row=3,column=0, columnspan=3,sticky=W,padx=5)
        self.trigger_time_entry_box = Entry(trigger_control_frame,textvariable=self.user_trigger_delay_input)
        self.trigger_time_entry_box.grid(row=4,column=0,columnspan=2,sticky=W,padx=5)
        mTrigConfirm = Button(trigger_control_frame,text="Confirm",command=self._request_trigger).grid(row=4,column=2,padx=5)
        self.trigger_countdown_text.set("Seconds until Trigger: Nil")
        mTrigLabel = Label(trigger_control_frame,textvariable=self.trigger_countdown_text).grid(row=5,column=0,columnspan=3,sticky=W,padx=5)
        self.trigger_text_box = Text(trigger_control_frame, height=8, width=45)
        self.trigger_text_box.grid(row=6,column=0, columnspan=3,pady=5,padx=5)
        scroll = Scrollbar(self.trigger_text_box,command=self.trigger_text_box.yview)
        self.trigger_text_box.configure(yscrollcommand=scroll.set)
        # End of Trigger controls
        
        #Network management
        network_control_frame = Frame(left_frame, width=575, height=200,highlightbackground="black", highlightthickness=2)
        network_control_frame.grid(row=3,column=0,pady=10,padx=10)
        NetworkMainLabel = Label(network_control_frame,text="Network Information",font=("Arial",11)).grid(row=0,column=0,columnspan=2,pady=5,padx=5)
        self.network_text_box = Text(network_control_frame, height=8, width=45)
        self.network_text_box.grid(row=1,column=0,columnspan=2,pady=5,padx=5)
        self.network_text_box_scroll = Scrollbar(self.network_text_box,command=self.network_text_box.yview)
        self.network_text_box.configure(yscrollcommand=scroll.set)

        
        
        self.mTimeLabel = Label(left_frame,textvariable=self.trigger_text_box).grid(row=4,sticky=W,pady=10,padx=5)
        mExit = Button(left_frame,text="Exit",command=main_script.exit_routine).grid(row=5,sticky=W,padx=5)
        
        
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
        
        GPSDO_Terminal = Button(metrics_bar_frame,text="GPSDO Parameters",command=grclok_1500_popout.LaunchTerminal())
        GPSDO_Terminal.grid(row=0,column=0,columnspan=2, pady=5, padx=10)
        mlabel = Label(metrics_bar_frame,text="Poll GPSDO",width=labelw,justify=LEFT,anchor="w").grid(row=1,column=0, padx=xpad,pady=ypad)
        mCheck_Poll = Checkbutton(metrics_bar_frame,state=ACTIVE,variable=self.gpsdo_polling_checkbox_state,onvalue=1,offvalue=0,command=self.poll_gpsdo)
        mCheck_Poll.grid(row=1,column=1, padx=xpad,pady=ypad)
        #mlabel = Label(metrictracking_infos_bar_frame,text="Poll GPS Receiver",width=labelw,justify=LEFT,anchor="w").grid(row=2,column=0,padx=xpad,pady=ypad)
        #mCheck_Poll = Checkbutton(metrics_bar_frame,state=DISABLED,variable=Save_PPS,onvalue=1,offvalue=0,command=self.Save_PPS_Error)
        #mCheck_Poll.grid(row=2,column=1, pady=5, padx=10)
        mlabel = Label(metrics_bar_frame,text="Save Data",width=labelw,justify=LEFT,anchor="w").grid(row=3,column=0,padx=xpad,pady=ypad)
        self.mCheck_Save = Checkbutton(metrics_bar_frame,state=DISABLED,variable=self.save_gpsdo_metrics_checkbox_state,onvalue=1,offvalue=0,command=self.save_gpsdo_metrics)
        self.mCheck_Save.grid(row=3,column=1,padx=xpad,pady=ypad)
        #End of Toolbar Frame
        
        
        #Oscillator Frame
        oscillator_frame = Frame(right_frame,width=300,height=300,highlightbackground="black", highlightthickness=2)
        oscillator_frame.grid(row=1,column=1,pady=10,padx=10)
        #oscillator_frame.grid_propagate(0)
        mlabel = Label(oscillator_frame, text="Oscillator Information",font=("Arial",11)).grid(row=0,column=0,columnspan=2,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="GPSDO Status: ",width=labelw,justify=LEFT,anchor="w").grid(row=2,column=0,sticky=W,padx=xpad,pady=ypad)
        mStatus = Label(oscillator_frame,textvariable=self.gpsdo_status,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=2,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="Disciplining Status: ",width=labelw,justify=LEFT,anchor="w").grid(row=3,column=0,sticky=W,padx=xpad,pady=ypad)
        mDisapliningStatus = Label(oscillator_frame,textvariable=self.disciplining_status,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=3,column=1, sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="Current Freq:  ",width=labelw,justify=LEFT,anchor="w").grid(row=4,column=0, sticky=W,padx=xpad,pady=ypad)
        mCurFreq = Label(oscillator_frame,textvariable=self.current_gpsdo_freq,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=4,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="Holdover Freq:  ",width=labelw,justify=LEFT,anchor="w").grid(row=5,column=0,sticky=W,padx=xpad,pady=ypad)
        mHoldFreq = Label(oscillator_frame,textvariable=self.gpsdo_holdover_freq,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=5,column=1, sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="Time Constant Mode:  ",width=labelw,justify=LEFT,anchor="w").grid(row=6,column=0, sticky=W,padx=xpad,pady=ypad)
        mTimeConMode = Label(oscillator_frame,textvariable=self.gpsdo_time_constant_mode,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=6,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabelend = Label(oscillator_frame,text="Time Constant Value:  ",width=labelw,justify=LEFT,anchor="w").grid(row=7,column=0,sticky=W,padx=xpad,pady=ypad)
        mTimeConVal = Label(oscillator_frame,textvariable=self.gpsdo_time_constant_value,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=7,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="Holdover Duration (s):  ",width=labelw,justify=LEFT,anchor="w").grid(row=8,column=0,sticky=W,padx=xpad,pady=ypad)
        mHoldoverDur = Label(oscillator_frame,textvariable=self.gpsdo_holdover_duration,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=8,column=1,sticky=W,padx=xpad,pady=ypad)
        #End of Oscillator Frame
        
        
        #GPS Receiver Frame
        gpsReceiever_frame = Frame(right_frame,width=300,height=300,highlightbackground="black", highlightthickness=2)
        gpsReceiever_frame.grid(row=1,column=2,pady=10,padx=10)
        #oscillator_frame.grid_propagate(0)
        mlabel = Label(gpsReceiever_frame, text="GPS Recevier Data",font=("Arial",11)).grid(row=0,column=0,columnspan=2,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="Latitude: ",width=labelw,justify=LEFT,anchor="w").grid(row=2,column=0,sticky=W,padx=xpad,pady=ypad)
        mLatitude = Label(gpsReceiever_frame,textvariable=self.gpsdo_latitude,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=2,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="Longitude: ",width=labelw,justify=LEFT,anchor="w").grid(row=3,column=0,sticky=W,padx=xpad,pady=ypad)
        mLongitude = Label(gpsReceiever_frame,textvariable=self.gpsdo_longitude,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=3,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="Altitude (WGS84):  ",width=labelw,justify=LEFT,anchor="w").grid(row=4,column=0, sticky=W,padx=xpad,pady=ypad)
        mAltitude = Label(gpsReceiever_frame,textvariable=self.gpsdo_altitude,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=4,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="Satellites:  ",width=labelw,justify=LEFT,anchor="w").grid(row=5,column=0,sticky=W,padx=xpad,pady=ypad)
        mSatellites = Label(gpsReceiever_frame,textvariable=self.gpsdo_satellites,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=5,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="Tracking:  ",width=labelw,justify=LEFT,anchor="w").grid(row=6,column=0, sticky=W,padx=xpad,pady=ypad)
        mTracking = Label(gpsReceiever_frame,textvariable=self.gpsdo_tracking_info,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=6,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="GPS Status:  ",width=labelw,justify=LEFT,anchor="w").grid(row=7,column=0,sticky=W,padx=xpad,pady=ypad)
        mValididty = Label(gpsReceiever_frame,textvariable=self.gpsdo_gps_status,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=7,column=1,sticky=W,padx=xpad,pady=ypad)
        #End of GPS Receiever Frame
        
        #Setup Figures
        fpc_figure, (self.fpco,self.etio,self.sigo) = plt.subplots(nrows=3, ncols=1, figsize=(14,8), dpi=75, constrained_layout=True)
        graph_frame = Frame(right_frame,highlightbackground="black", highlightthickness=2,bg="white")
        graph_frame.grid(row=2,column=0,columnspan=3,pady=10,padx=10)
        fpc_canvas = FigureCanvasTkAgg(fpc_figure,graph_frame)
        fpc_canvas.get_tk_widget().grid(row=0,column=0,sticky=W,pady=10,padx=10)
        ani = animation.FuncAnimation(fpc_figure, self.animate, interval=1000)
        fpc_canvas.draw()
        # End of figures
        
        
        
    def _setup_slave_ui_layout(self):
        '''
        function to setup a slave UI structure
        '''

        # Create left and right frames
        left_frame = Frame(self.mGui, width=600, height=700,bd=1)
        left_frame.grid(row=0, column=0, padx=10, pady=5,sticky=N)
        right_frame = Frame(self.mGui, width=1200, height=700,bd=1)
        right_frame.grid(row=0, column=1, padx=10, pady=5,sticky=N)
        
        #***** Populate Left Frame ********
        
        # GPSDO Control Frame
        gpsdo_control_frame = Frame(left_frame, width=575, height=200,highlightbackground="black", highlightthickness=2)
        gpsdo_control_frame.grid(row=0,column=0, pady=10, padx=10)
        mlabel = Label(gpsdo_control_frame,text="GPSDO Controls",font=("Arial", 11)).grid(row=0,column=0,columnspan=3, pady=5,padx=5)
        mlabel = Label(gpsdo_control_frame,text="Track: ").grid(row=2,column=0)
        mlabel = Label(gpsdo_control_frame,text="Sync: ").grid(row=2,column=1)
        mlabel = Label(gpsdo_control_frame,text="GPS: ").grid(row=2,column=2)
        self.mCheck_TR = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=self.gpsdo_track_checkbox_state,onvalue=1,offvalue=0,command=self.set_track_mode)
        self.mCheck_SY = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=self.gpsdo_sync_checkbox_state,onvalue=1,offvalue=0,command=self.set_sync_mode)
        self.mCheck_GPS = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=self.gpsdo_gps_comms_checkbox_state,onvalue=1,offvalue=0,command=self.set_gpsdo_mode)
        self.mCheck_TR.grid(row=3,column=0)
        self.mCheck_SY.grid(row=3,column=1)
        self.mCheck_GPS.grid(row=3,column=2)
        mlabel = Label(gpsdo_control_frame,text="Enter Query").grid(row=4,column=0,columnspan=3,sticky=W,padx=5)
        self.gpsdo_message_entry = Entry(gpsdo_control_frame,textvariable=self.gpsdo_user_query).grid(row=5,column=0,columnspan=2,sticky=W,padx=5)
        self.mbutton = Button(gpsdo_control_frame,text="Send",command=self.gpsdo_send).grid(row=5,column=2,padx=5)
        self.mlabel = Label(gpsdo_control_frame,text="GPSDO Response").grid(row=6,column=0,columnspan=3,sticky=W,padx=5)
        self.gpsdo_textbox = Text(gpsdo_control_frame,height=6,width=45)
        self.gpsdo_textbox.grid(row=7,column=0, columnspan = 3,pady=5,padx=5)
        self.gpsdo_textbox_scroll = Scrollbar(self.gpsdo_textbox,command=self.gpsdo_textbox.yview)
        self.gpsdo_textbox.configure(yscrollcommand=self.gpsdo_textbox_scroll.set)
        #end of GPSDO control frame
        
        
        # Trigger Control Frame 
        trigger_control_frame = Frame(left_frame, width=575, height=200,highlightbackground="black", highlightthickness=2)
        trigger_control_frame.grid(row=1,column=0,pady=10,padx=10)
        mlabel = Label(trigger_control_frame,text="Trigger Controls",font=("Arial", 11)).grid(row=0,column=0,columnspan=3,pady=5,padx=5)
        self.trigger_countdown_text.set("Seconds until Trigger: Nil")
        mTrigLabel = Label(trigger_control_frame,textvariable=self.trigger_countdown_text).grid(row=5,column=0,columnspan=3,sticky=W,padx=5)
        self.trigger_text_box = Text(trigger_control_frame, height=8, width=45)
        self.trigger_text_box.grid(row=6,column=0, columnspan=3,pady=5,padx=5)
        scroll = Scrollbar(self.trigger_text_box,command=self.trigger_text_box.yview)
        self.trigger_text_box.configure(yscrollcommand=scroll.set)
        # End of Trigger controls
        
        #Network management
        network_control_frame = Frame(left_frame, width=575, height=200,highlightbackground="black", highlightthickness=2)
        network_control_frame.grid(row=3,column=0,pady=10,padx=10)
        NetworkMainLabel = Label(network_control_frame,text="Network Information",font=("Arial",11)).grid(row=0,column=0,columnspan=2,pady=5,padx=5)
        self.network_text_box = Text(network_control_frame, height=8, width=45)
        self.network_text_box.grid(row=1,column=0,columnspan=2,pady=5,padx=5)
        self.network_text_box_scroll = Scrollbar(self.network_text_box,command=self.network_text_box.yview)
        self.network_text_box.configure(yscrollcommand=scroll.set)
        mButtonListen = Button(network_control_frame,text="Connect",command=self._connect_to_master).grid(row=2,column=0,pady=5,padx=5)
        mButtonDisconnect = Button(network_control_frame,text="Disconnect",command=self._disconnect_from_master).grid(row=2,column=1,pady=5,padx=5)
        #End of Network management frame
        
        
        self.mTimeLabel = Label(left_frame,textvariable=self.trigger_text_box).grid(row=4,sticky=W,pady=10,padx=5)
        mExit = Button(left_frame,text="Exit",command=main_script.exit_routine).grid(row=5,sticky=W,padx=5)
        
        
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
        
        GPSDO_Terminal = Button(metrics_bar_frame,text="GPSDO Parameters",command=grclok_1500_popout.LaunchTerminal())
        GPSDO_Terminal.grid(row=0,column=0,columnspan=2, pady=5, padx=10)
        mlabel = Label(metrics_bar_frame,text="Poll GPSDO",width=labelw,justify=LEFT,anchor="w").grid(row=1,column=0, padx=xpad,pady=ypad)
        mCheck_Poll = Checkbutton(metrics_bar_frame,state=ACTIVE,variable=self.gpsdo_polling_checkbox_state,onvalue=1,offvalue=0,command=self.poll_gpsdo)
        mCheck_Poll.grid(row=1,column=1, padx=xpad,pady=ypad)
        #mlabel = Label(metrictracking_infos_bar_frame,text="Poll GPS Receiver",width=labelw,justify=LEFT,anchor="w").grid(row=2,column=0,padx=xpad,pady=ypad)
        #mCheck_Poll = Checkbutton(metrics_bar_frame,state=DISABLED,variable=Save_PPS,onvalue=1,offvalue=0,command=self.Save_PPS_Error)
        #mCheck_Poll.grid(row=2,column=1, pady=5, padx=10)
        mlabel = Label(metrics_bar_frame,text="Save Data",width=labelw,justify=LEFT,anchor="w").grid(row=3,column=0,padx=xpad,pady=ypad)
        self.mCheck_Save = Checkbutton(metrics_bar_frame,state=DISABLED,variable=self.save_gpsdo_metrics_checkbox_state,onvalue=1,offvalue=0,command=self.save_gpsdo_metrics)
        self.mCheck_Save.grid(row=3,column=1,padx=xpad,pady=ypad)
        #End of Toolbar Frame
        
        
        #Oscillator Frame
        oscillator_frame = Frame(right_frame,width=300,height=300,highlightbackground="black", highlightthickness=2)
        oscillator_frame.grid(row=1,column=1,pady=10,padx=10)
        #oscillator_frame.grid_propagate(0)
        mlabel = Label(oscillator_frame, text="Oscillator Information",font=("Arial",11)).grid(row=0,column=0,columnspan=2,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="GPSDO Status: ",width=labelw,justify=LEFT,anchor="w").grid(row=2,column=0,sticky=W,padx=xpad,pady=ypad)
        mStatus = Label(oscillator_frame,textvariable=self.gpsdo_status,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=2,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="Disciplining Status: ",width=labelw,justify=LEFT,anchor="w").grid(row=3,column=0,sticky=W,padx=xpad,pady=ypad)
        mDisapliningStatus = Label(oscillator_frame,textvariable=self.disciplining_status,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=3,column=1, sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="Current Freq:  ",width=labelw,justify=LEFT,anchor="w").grid(row=4,column=0, sticky=W,padx=xpad,pady=ypad)
        mCurFreq = Label(oscillator_frame,textvariable=self.current_gpsdo_freq,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=4,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="Holdover Freq:  ",width=labelw,justify=LEFT,anchor="w").grid(row=5,column=0,sticky=W,padx=xpad,pady=ypad)
        mHoldFreq = Label(oscillator_frame,textvariable=self.gpsdo_holdover_freq,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=5,column=1, sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="Time Constant Mode:  ",width=labelw,justify=LEFT,anchor="w").grid(row=6,column=0, sticky=W,padx=xpad,pady=ypad)
        mTimeConMode = Label(oscillator_frame,textvariable=self.gpsdo_time_constant_mode,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=6,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabelend = Label(oscillator_frame,text="Time Constant Value (s):  ",width=labelw,justify=LEFT,anchor="w").grid(row=7,column=0,sticky=W,padx=xpad,pady=ypad)
        mTimeConVal = Label(oscillator_frame,textvariable=self.gpsdo_time_constant_value,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=7,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(oscillator_frame,text="Holdover Duration (s):  ",width=labelw,justify=LEFT,anchor="w").grid(row=8,column=0,sticky=W,padx=xpad,pady=ypad)
        mHoldoverDur = Label(oscillator_frame,textvariable=self.gpsdo_holdover_duration,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=8,column=1,sticky=W,padx=xpad,pady=ypad)
        #End of Oscillator Frame
        
        
        #GPS Receiver Frame
        gpsReceiever_frame = Frame(right_frame,width=300,height=300,highlightbackground="black", highlightthickness=2)
        gpsReceiever_frame.grid(row=1,column=2,pady=10,padx=10)
        #oscillator_frame.grid_propagate(0)
        mlabel = Label(gpsReceiever_frame, text="GPS Recevier Data",font=("Arial",11)).grid(row=0,column=0,columnspan=2,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="Latitude: ",width=labelw,justify=LEFT,anchor="w").grid(row=2,column=0,sticky=W,padx=xpad,pady=ypad)
        mLatitude = Label(gpsReceiever_frame,textvariable=self.gpsdo_latitude,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=2,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="Longitude: ",width=labelw,justify=LEFT,anchor="w").grid(row=3,column=0,sticky=W,padx=xpad,pady=ypad)
        mLongitude = Label(gpsReceiever_frame,textvariable=self.gpsdo_longitude,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=3,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="Altitude (WGS84):  ",width=labelw,justify=LEFT,anchor="w").grid(row=4,column=0, sticky=W,padx=xpad,pady=ypad)
        mAltitude = Label(gpsReceiever_frame,textvariable=self.gpsdo_altitude,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=4,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="Satellites:  ",width=labelw,justify=LEFT,anchor="w").grid(row=5,column=0,sticky=W,padx=xpad,pady=ypad)
        mSatellites = Label(gpsReceiever_frame,textvariable=self.gpsdo_satellites,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=5,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="Tracking:  ",width=labelw,justify=LEFT,anchor="w").grid(row=6,column=0, sticky=W,padx=xpad,pady=ypad)
        mTracking = Label(gpsReceiever_frame,textvariable=self.gpsdo_tracking_info,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=6,column=1,sticky=W,padx=xpad,pady=ypad)
        mlabel = Label(gpsReceiever_frame,text="GPS Status:  ",width=labelw,justify=LEFT,anchor="w").grid(row=7,column=0,sticky=W,padx=xpad,pady=ypad)
        mValididty = Label(gpsReceiever_frame,textvariable=self.gpsdo_gps_status,width=valw,justify=LEFT,anchor="w",bg="white").grid(row=7,column=1,sticky=W,padx=xpad,pady=ypad)
        #End of GPS Receiever Frame
        
        #Setup Figures
        fpc_figure, (self.fpco,self.etio,self.sigo) = plt.subplots(nrows=3, ncols=1, figsize=(14,8), dpi=75, constrained_layout=True)
        graph_frame = Frame(right_frame,highlightbackground="black", highlightthickness=2,bg="white")
        graph_frame.grid(row=2,column=0,columnspan=3,pady=10,padx=10)
        fpc_canvas = FigureCanvasTkAgg(fpc_figure,graph_frame)
        fpc_canvas.get_tk_widget().grid(row=0,column=0,sticky=W,pady=10,padx=10)
        ani = animation.FuncAnimation(fpc_figure, self.animate, interval=1000)
        fpc_canvas.draw()
        # End of figures        