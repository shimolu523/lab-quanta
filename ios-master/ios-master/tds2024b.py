# tds2024b.py
# IO module for interfacing with Tektronix TDS2024B oscilloscope.
# Author: Zachary Fisher (zfisher@mit.edu)
# 
# Requires: Agilent libusb. Download here:
# http://www.home.agilent.com/upload/cmc_upload/All/usbtmc.html?&cc=US&lc=eng
#
# Lots of code borrowed from WaveMaster.py, tek2daq.py and:
# https://github.com/sbrinkmann/PyOscilloskop/blob/master/src/rigolScope.py
##################################################################
import gtk
import helpers
import math
import time
import threading
import string
import sys
import os
import __main__

# Define a global devicename
DEVICENAME="TDS2024"

class UsbTmcDriver:
   def __init__(self, device):
       self.device = device
       self.FILE = os.open('/dev/usbtmc%d'%device, os.O_RDWR)

       # TODO: Test that the file opened

   def write(self, command):
       os.write(self.FILE, command)

   def read(self, length = 4000):
       return os.read(self.FILE, length)

   def getName(self):
       self.write("*IDN?")
       return self.read(300)

   def sendReset(self):
       self.write("*RST")

   def close(self):
       os.close(self.FILE)

def getDevice(device_id_string):
	devicelist = open('/dev/usbtmc0', 'r')
	oscilloscopes = [d for d in devicelist if d.find(device_id_string) > -1] #ex: 002 \t Tektronix ....
	bus = int(oscilloscopes[0][0:3])
	assert (bus > 0 and bus <= 9), "invalid bus (things to check: is the device plugged in? is the agilent libusb installed?)"
	return bus

#################################################################
# class io_stream
#
# Required. This class is a wrapper for the whole instrument. It
#  must have an init method accepting optional argument, register method,
# unregister method, and hooks_provides method
#################################################################
class io_stream:
   #############################################################
   # __init__
   #
   # Called by gui when the io is enabled from menu. ui_target is a pointer
   # to a gtk.VBox, where this module is allowed to add buttons, etc.
   #############################################################
   def __init__(self, ui_target = None):
       self.ui_target = ui_target;
       self.device = getDevice('TDS2024B')
       return
   ##############################################################
   # register
   #
   # Called by gui after creating an instance of io_stream
   # It should open communication to the device, set any state
   # variables necessary, create whatever buttons, dialogs are
   # desired
   ##############################################################
   def register(self):
       self.lock = threading.Lock()

       # helpers.devmap_remap takes a string and returns a
       # corresponding value from devmap.data_acq file. Used
       # to configure gpib/serial addresses, and alias for the
       # device. See the file in ~ionsearch/data_acq.
       #devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))
       #assert devname, "Did not find %s in devmap"%(DEVICENAME)
       devname = 'TDS2000'
       #self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
       #assert self.alias, "Did not find alias for %s"%(DEVICENAME)
       self.alias = 'TDS2000'

       # Create a lock to serialize all communication
       self.lock.acquire()
       try:
           # Open the device

           # vid = 0x1268 # vendor: tektronix
           # pid = 0x0204 # product: oscilloscope processor (?)

           self.tds = UsbTmcDriver(self.device)

           time.sleep(.1)
       finally:
           # release the lock
           self.lock.release()


   ##################################################################
   # unregister
   #
   # Called bu gui when the io is disabled from menu.
   # Should clean up, remove all created buttons, close
   # communication channels, files etc.
   ##################################################################
   def unregister(self):
       self.lock.acquire()
       self.tds.close()
       self.lock.release()
       return

   ##################################################################
   # hooks_provides
   #
   # A tuple of dictionaries, one for set functions (here empty), and
   # one for read functions, both in {'functionname' : funcion, ...} format.
   # The functions listed here will be available for use to other
   # parts of the program.
   #
   # All read functions are expected to return a single float, all
   # set funcitons are expected to take a single float argument
   ##################################################################
   def hooks_provides(self):
       return ({'%s_horizScale'%(self.alias):self.set_horiz_scale,
                               '%s_horizPos'%(self.alias):self.set_horiz_pos,
                               '%s_CH1Vperdiv'%(self.alias):lambda x:self.set_channel_scale(1,x),
                               '%s_CH1posdiv'%(self.alias):lambda x:self.set_channel_pos(1,x),
                               '%s_CH2Vperdiv'%(self.alias):lambda x:self.set_channel_scale(2,x),
                               '%s_CH2posdiv'%(self.alias):lambda x:self.set_channel_pos(2,x),
                               '%s_CH3Vperdiv'%(self.alias):lambda x:self.set_channel_scale(3,x),
                               '%s_CH3posdiv'%(self.alias):lambda x:self.set_channel_pos(3,x),
                               '%s_CH4Vperdiv'%(self.alias):lambda x:self.set_channel_scale(4,x),
                               '%s_CH4posdiv'%(self.alias):lambda x:self.set_channel_pos(4,x)},
								{'%s_CH1Vpp'%(self.alias):lambda:self.read_channel(1, 'PK2pk'),
								'%s_CH1Vmean'%(self.alias):lambda:self.read_channel(1, 'MEAN'),
								'%s_CH1freq'%(self.alias):lambda:self.read_channel(1, 'FREQ'),
								'%s_CH2Vpp'%(self.alias):lambda:self.read_channel(2, 'PK2pk'),
								'%s_CH2Vmean'%(self.alias):lambda:self.read_channel(2, 'MEAN'),
								'%s_CH2freq'%(self.alias):lambda:self.read_channel(2, 'FREQ'),
								'%s_CH3Vpp'%(self.alias):lambda:self.read_channel(3, 'PK2pk'),
								'%s_CH3Vmean'%(self.alias):lambda:self.read_channel(3, 'MEAN'),
								'%s_CH3freq'%(self.alias):lambda:self.read_channel(3, 'FREQ'),
								'%s_CH4Vpp'%(self.alias):lambda:self.read_channel(4, 'PK2pk'),
								'%s_CH4Vmean'%(self.alias):lambda:self.read_channel(4, 'MEAN'),
								'%s_CH4freq'%(self.alias):lambda:self.read_channel(4, 'FREQ')})


   ##################################################################
   # read_channel
   #
   # A helper method that writes a measurement to the usb buffer.
   # channel is an integer (1-4); type is a string ('PK2pk' or 'MEAN' or 'FREQ')
   ##################################################################
   def read_channel(self, channel, mtype):
       if __main__.ABORT_FLAG: return 0.0
       try:
           self.lock.acquire()
           self.tds.write('MEASUrement:IMMed:SOUrce1 CH%d'%channel)      # sets channel number
           self.tds.write('MEASUrement:IMMed:TYPe %s'%mtype)             # pk2pk? mean? freq?
           self.tds.write('MEASUrement:IMMed:VALue?')                    # ask for value (IMMediately)
           rv = float(self.tds.read())
       finally:
           self.lock.release()
       return rv

   def set_horiz_scale(self, value):
       if __main__.ABORT_FLAG: return 0.0
       try:
           self.lock.acquire()
           self.tds.write('HORizontal:SCAle %f'%float(value))       # set horizontal scale to value in seconds
       finally:
           self.lock.release()

   def set_horiz_pos(self, value):
       if __main__.ABORT_FLAG: return 0.0
       try:
           self.lock.acquire()
           self.tds.write('HORizontal:POSition %f'%float(value))       # set horizontal position to value in seconds
       finally:
           self.lock.release()

   def set_channel_scale(self, channel, value):
       if __main__.ABORT_FLAG: return 0.0
       try:
           self.lock.acquire()
           self.tds.write('CH%d:SCAle %f'%(channel,float(value)))       # set channel scale to value in volts/div
       finally:
           self.lock.release()

   def set_channel_pos(self, channel, value):
           if __main__.ABORT_FLAG: return 0.0
           try:
               self.lock.acquire()
               self.tds.write('CH%d:POSition %f'%(channel,float(value)))  # set channel position to value in divisions (not volts!)
           finally:
               self.lock.release()


