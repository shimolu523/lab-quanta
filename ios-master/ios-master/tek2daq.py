# This is the python dirver to read TDS3000 oscilloscope
# frame work is copied from /usr/local/data_acq/ios/DMM1.py in maxwell
# comments might be too extensive, since first time putting such a thing together, for future reference
# Molu Shi 2011.5.5

####### importing python library #######

import gtk
import helpers
import math
import time
import Gpib
import threading
import __main__
import struct

DEVICENAME="TDS3000"                                                     # defined in the corresponding devmap.acq file, collocated with daq

class io_stream:                                                         # "self" meaning all variables, function, etc. defined in this class
    def __init__(self, ui_target = None):                                # refering functions defined within this class
        self.ui_target = ui_target;                                      # once class renamed upon calling, "self" changes accordingly
        return

    def register(self):
        self.lock = threading.Lock()                                     # calling the "Lock" function under class "threading"."()" implies Lock is a func
        try:                                                             # the daq suite has multiple programs working in parallel, lock makes sure that
            self.lock.acquire()                                          # when one is changing the parameters, no others can change it simultaneously
            devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))            
            assert devname, "Did not find %s in devmap"%(DEVICENAME)
            self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
            assert self.alias, "Did not find alias for %s"%(DEVICENAME)
        finally:
            self.lock.release()
        if self.ui_target:
            pass

        self.tds = Gpib.Gpib(devname)                                    # self.tds is now the gpib buffer 
        self.tds.clear()                                                 # clear the gpib buffer
        time.sleep(.1)
        self.tds.range = .1


    def unregister(self):
        try:
            self.lock.acquire()
            if self.ui_target:
                pass
        finally:
            self.lock.release()
        return

    def hooks_provides(self):                                             # values displayed on the daq graphical interface    
        return ({},{'%s_CH1Vpp'%(self.alias): self.read_CH1Vpp,'%s_CH1Vmean'%(self.alias): self.read_CH1Vmean,'%s_CH2Vpp'%(self.alias): self.read_CH2Vpp,'%s_CH2Vmean'%(self.alias): self.read_CH2Vmean})
        
    def read_CH1Vpp(self):
        if __main__.ABORT_FLAG: return 0.0
        try:
            self.lock.acquire()
            rv = readCH1Vpp(self.tds)
        finally:
            self.lock.release()
        return rv

    def read_CH1Vmean(self):
        if __main__.ABORT_FLAG: return 0.0
        try:
            self.lock.acquire()
            rv = readCH1Vmean(self.tds)
        finally:
            self.lock.release()
        return rv

    def read_CH2Vpp(self):
        if __main__.ABORT_FLAG: return 0.0
        try:
            self.lock.acquire()
            rv = readCH2Vpp(self.tds)
        finally:
            self.lock.release()
        return rv

    def read_CH2Vmean(self):
        if __main__.ABORT_FLAG: return 0.0
        try:
            self.lock.acquire()
            rv = readCH2Vmean(self.tds)
        finally:
            self.lock.release()
        return rv


def readCH1Vpp(tds):
    tds.write('MEASUrement:IMMed:SOURCE1 CH1')                # telling oscilloscope to measure CH1, with port IMMed
    tds.write('MEASUrement:IMMed:TYPe PK2pk')                # specifying measurement type peak-to-peak voltage
    tds.write('MEASUrement:IMMed:VALue?')                    # now sending a query to oscilloscope, which will write to the gpib buffer
    Vpp1 = tds.read()                                         # python now reads from gpib (recall to add "()" to specify calling a function)              
    Vpp1 = float(Vpp1)
    return Vpp1

def readCH1Vmean(tds):
    tds.write('MEASUrement:IMMed:SOURCE1 CH1')                # telling oscilloscope to measure CH1, with port IMMed
    tds.write('MEASUrement:IMMed:TYPe MEAN')                 # specifying measurement type peak-to-peak voltage
    tds.write('MEASUrement:IMMed:VALue?')                    # now sending a query to oscilloscope, which will write to the gpib buffer
    Vmean1 = tds.read()                                       # python now reads from gpib (recall to add "()" to specify calling a function)
    Vmean1 = float(Vmean1)
    return Vmean1

def readCH2Vpp(tds):
    tds.write('MEASUrement:IMMed:SOURCE1 CH2')                # telling oscilloscope to measure CH2, with port IMMed
    tds.write('MEASUrement:IMMed:TYPe PK2pk')                # specifying measurement type peak-to-peak voltage
    tds.write('MEASUrement:IMMed:VALue?')                    # now sending a query to oscilloscope, which will write to the gpib buffer
    Vpp2 = tds.read()                                         # python now reads from gpib (recall to add "()" to specify calling a function)
    Vpp2 = float(Vpp2)
    return Vpp2

def readCH2Vmean(tds):
    tds.write('MEASUrement:IMMed:SOURCE1 CH2')                # telling oscilloscope to measure CH2, with port IMMed
    tds.write('MEASUrement:IMMed:TYPe MEAN')                 # specifying measurement type peak-to-peak voltage
    tds.write('MEASUrement:IMMed:VALue?')                    # now sending a query to oscilloscope, which will write to the gpib buffer
    Vmean2 = tds.read()                                       # python now reads from gpib (recall to add "()" to specify calling a function)
    Vmean2 = float(Vmean2)
    return Vmean2

