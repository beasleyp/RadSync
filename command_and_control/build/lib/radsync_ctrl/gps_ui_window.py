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


# ****************** End of GPS related defintions********************