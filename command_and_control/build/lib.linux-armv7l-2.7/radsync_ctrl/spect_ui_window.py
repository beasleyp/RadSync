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