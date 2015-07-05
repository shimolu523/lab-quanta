# WaveMaster.py
#
# This io module defines interaction with the wavemaster
##################################################################
import gtk
import helpers
import math
import time
import threading
import os
import __main__

# Define a global devicename
DEVICENAME="Picon"

#################################################################
# class io_stream
#
# Required. This class is a wrapper for the whole instrument. It
# must have an init method accepting optional argument, register method, 
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
        devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))
        assert devname, "Did not find %s in devmap"%(DEVICENAME)
        self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
        assert self.alias, "Did not find alias for %s"%(DEVICENAME)

        # Create a lock to serialize all communication
        self.lock.acquire()
        try:
            # Open the device
            self.fd = os.open(devname, os.O_NONBLOCK|os.O_RDONLY)

            if (self.fd < 0):
                 raise "Error opening %s!" % devname
            # Pause
            time.sleep(.1)
        finally:
            # release the lock
            self.lock.release()
	# We cache last value
	
	self.lastvalue = {'TIME': 0, 'TOTAL': 0, 'MAX': 0, 'MIN': 0, 'CENTERX': 0, 'CENTERY': 0}

    ##################################################################
    # unregister
    #
    # Called bu gui when the io is disabled from menu.
    # Should clean up, remove all created buttons, close
    # communication channels, files etc.
    ##################################################################
    def unregister(self):
        self.lock.acquire()
        os.close(self.fd)
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
        return ({},{"%s_TIME"%(self.alias) : self.read_time,
                    "%s_TOTAL"%(self.alias) : self.read_total,
                    "%s_MAX"%(self.alias) : self.read_max,
                    "%s_MIN"%(self.alias) : self.read_min,
                    "%s_CENTERX"%(self.alias) : self.read_centerx,
                    "%s_CENTERY"%(self.alias) : self.read_centery})

    ##################################################################
    # read_*
    #
    # Implementation of a read_function. Note that every function
    # should read the __main__.ABORT_FLAG, and if it is set it should
    # not touch the hardware and return asap!
    ##################################################################
    def read_time(self):
        if __main__.ABORT_FLAG: return 0.0

        self.update()
        return self.lastvalue['TIME']

    def read_total(self):
        if __main__.ABORT_FLAG: return 0.0

        self.update()
        return self.lastvalue['TOTAL']

    def read_max(self):
        if __main__.ABORT_FLAG: return 0.0

        self.update()
        return self.lastvalue['MAX']

    def read_min(self):
        if __main__.ABORT_FLAG: return 0.0

        self.update()
        return self.lastvalue['MIN']

    def read_centerx(self):
        if __main__.ABORT_FLAG: return 0.0

        self.update()
        return self.lastvalue['CENTERX']

    def read_centery(self):
        if __main__.ABORT_FLAG: return 0.0

        self.update()
        return self.lastvalue['CENTERY']

    def update(self):
        try:
            self.lock.acquire()
            str = ''
            
            tmpstr = os.read(self.fd, 1000)
            while(tmpstr):
                str = tmpstr
                tmpstr = os.read(self.fd, 1000)

            if str:
	    	try:
                    message = str.rstrip().split('\n')[-1]
                    values = message.split(';')
                    self.lastvalue['TIME'] = int(values[0][6:])
                    self.lastvalue['TOTAL'] = int(values[1][7:])
                    self.lastvalue['MAX'] = int(values[2][5:])
                    self.lastvalue['MIN'] = int(values[3][5:])
                    self.lastvalue['CENTERX'] = float(values[4][10:])
                    self.lastvalue['CENTERY'] = float(values[5][10:])
		except:
		    print "Picon: Couldn't parse string ", message
            
        finally:
            self.lock.release()
        return self.lastvalue
