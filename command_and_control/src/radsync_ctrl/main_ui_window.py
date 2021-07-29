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

from tkinter import *
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib import style
from collections import deque
import numpy as np


from main_script imp


'''
Initialise Global Variables used in the Gui
'''
Track_state = 0
Sync_state = 0
GPS_state = 0
Beat_PPS_State = 0
Save_PPS_State = 0
Poll_GPSDO = 0 
# PPS Error Variables
PPS_Error_Length = 10 #60 * 2 # length of PPS Error Arrays graph time axis (default 2 mins)
Fine_Phase_Comp = deque(maxlen = PPS_Error_Length)
Effective_Time_Int = deque(maxlen = PPS_Error_Length)
PPSREF_Sigma = deque(maxlen = PPS_Error_Length)
Polling_GPSDO = False
Save_PPS = False
Save_PPS_Flag = False
#mGUI general variables
TriggerTextLabel = ""
trig_time = ""
current_time = ""
exitFlag = -1
Nil = 0b00000000 
user_query = ""
#Variables for Oscillator Data Frame
Gpsdo_Status = 0
Rb_Status = 0
Current_Freq = 0
Holdover_Freq = 0
Constant_Mode = 0
Constant_Value = 0
#Variables for GPS Receiver Data Frame
GPSDO_Latitude = 0
GPSDO_Longitude = 0
GPSDO_Altitude = 0
GPSDO_Satellites = 0
GPSDO_Tracking = 0
GPSDO_Validity = 0
# GPS Popout Variables
Latitude = ""
Longitude = ""
TimeUTC = ""
Altitude = ""
EPS = ""
EPX = ""
EPV = ""
EPT = ""
Speed = ""
Climb = ""
Track = ""
Mode = ""
Sat = ""
# Oscillator variables Window
FreqAdj = ""
PeakVoltRB = ""
DC_Photo = ""
Varac = ""
RBLamp = ""
RBHeating = ""
Alarm = ""
Tracking = ""
Tau = ""
CompOff = ""
RawAdj = ""
FreqCorr = ""
SyncPeriod = ""
DisableTimeMonitor = False
Calibrated = False
GpsdoStatus = ""







class RadSyncUi():
    
    def __init__(self):
        global mGui 
        mGui = Tk()
        mGui.geometry("1900x1000+220+140") # Window Geometry
        mGui.title("GPSDO Synchrnonisation System - Master Node Control Interface")
        #mGui.configure(bg="skyblue")
        LARGE_FONT= ("Verdana", 12)
        style.use("ggplot")
        self.setupUiLayout()

    def trackMode(self):
        global DO_TextBox
        if Track_state.get() == 1:
            GPSDO.setTrack(True)
            DO_TextBox.insert(END,"Tracking to PPSREF Set \n")
            DO_TextBox.yview(END)
        elif Track_state.get() == 0:
            GPSDO.setTrack(False)
            DO_TextBox.insert(END,"Tracking to PPSREF Unset \n")
            DO_TextBox.yview(END)
            
    def syncMode(self):
        global DO_TextBox
        if Sync_state.get() == 1:
            GPSDO.setSync(True)
            DO_TextBox.insert(END,"PPSOUT Synchronisation to PPSINT Set \n")
            DO_TextBox.yview(END)
        elif Sync_state.get() == 0:
            GPSDO.setSync(False)
            DO_TextBox.insert(END,"PPSOUT Synchronisation to PPSINT Unset \n")
            DO_TextBox.yview(END)

    def gpsMode(self):
        global DO_TextBox
        if GPS_state.get() == 1:
            GPSDO.setGpsCom(True)
            #DO_TextBox.insert(END,"GPS Mode Enabled")
            DO_TextBox.yview(END)
        elif GPS_state.get() == 0:
            GPSDO.setGpsCom(False)
            #DO_TextBox.insert(END,"GPS Mode Disabled")
            DO_TextBox.yview(END)
        
          
    def GPSDO_Send(self): 
        global DO_TextBox
        query = user_query.get()+"\r"
        response = GPSDO.sendQuery(query)
        DO_TextBox.insert(END,response[:-2]+"\n")
        DO_TextBox.yview(END)
    
    def pollGPSDO(self):
       global DO_TextBox   
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
        
    
    def setupUiLayout(self):
        global mGui
        global DO_TextBox, NetworkTextBox, mTimeLabel
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
        mCheck_TR = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=Track_state,onvalue=1,offvalue=0,command=self.trackMode)
        mCheck_SY = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=Sync_state,onvalue=1,offvalue=0,command=self.syncMode)
        mCheck_GPS = Checkbutton(gpsdo_control_frame,state=ACTIVE,variable=GPS_state,onvalue=1,offvalue=0,command=self.gpsMode)
        mCheck_TR.grid(row=3,column=0)
        mCheck_SY.grid(row=3,column=1)
        mCheck_GPS.grid(row=3,column=2)
        mlabel = Label(gpsdo_control_frame,text="Enter Query").grid(row=4,column=0,columnspan=3,sticky=W,padx=5)
        mEntry = Entry(gpsdo_control_frame,textvariable=user_query).grid(row=5,column=0,columnspan=2,sticky=W,padx=5)
        mbutton = Button(gpsdo_control_frame,text="Send",command=self.GPSDO_Send).grid(row=5,column=2,padx=5)
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
        mCheck_Poll = Checkbutton(metrics_bar_frame,state=ACTIVE,variable=Poll_GPSDO,onvalue=1,offvalue=0,command=self.pollGPSDO)
        mCheck_Poll.grid(row=1,column=1, padx=xpad,pady=ypad)
        mlabel = Label(metrics_bar_frame,text="Poll GPS Receiver",width=labelw,justify=LEFT,anchor="w").grid(row=2,column=0,padx=xpad,pady=ypad)
        mCheck_Poll = Checkbutton(metrics_bar_frame,state=DISABLED,variable=Save_PPS,onvalue=1,offvalue=0,command=self.Save_PPS_Error)
        mCheck_Poll.grid(row=2,column=1, pady=5, padx=10)
        mlabel = Label(metrics_bar_frame,text="Save Data",width=labelw,justify=LEFT,anchor="w").grid(row=3,column=0,padx=xpad,pady=ypad)
        mCheck_Save = Checkbutton(metrics_bar_frame,state=DISABLED,variable=Save_PPS_State,onvalue=1,offvalue=0,command=self.Save_PPS_Error)
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
