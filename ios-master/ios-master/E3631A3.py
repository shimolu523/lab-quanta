import gtk
import helpers
import math
import time
import Gpib
import threading
import __main__

DEVICENAME="E3631A3"

class io_stream:
    def __init__(self, ui_target = None):
        self.ui_target = ui_target;
        return
    
    def register(self):
        self.lock = threading.Lock()

        self.lock.acquire()
        devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))
        assert devname, "Did not find %s in devmap"%(DEVICENAME)
        self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
        assert self.alias, "Did not find alias for %s"%(DEVICENAME)

        self.psup = Gpib.Gpib(devname)
        self.psup.clear()
        time.sleep(.1)
        #self.psup.write('*RST')
        #self.psup.write('OUTP:ON')
        self.lock.release()


    def unregister(self):
        self.lock.acquire()
        #self.psup.write('*RST')
        self.lock.release()
        return
    
    def hooks_provides(self):
        return ({'%s_+25V'%(self.alias): self.set_p25V, 
                 '%s_-25V'%(self.alias): self.set_n25V,
                 '%s_+6V'%(self.alias): self.set_p6V,
                 '%s_+25I'%(self.alias): self.set_p25I, 
                 '%s_-25I'%(self.alias): self.set_n25I,
                 '%s_+6I'%(self.alias): self.set_p6I},
                {'%s_+25V'%(self.alias): self.read_p25V, 
                 '%s_-25V'%(self.alias): self.read_n25V,
                 '%s_+6V'%(self.alias): self.read_p6V,
                 '%s_+25I'%(self.alias): self.read_p25I, 
                 '%s_-25I'%(self.alias): self.read_n25I,
                 '%s_+6I'%(self.alias): self.read_p6I})

    def read_p25V(self):
        return self.read_Vchan('P25V')

    def read_n25V(self):
        return self.read_Vchan('N25V')

    def read_p6V(self):
        return self.read_Vchan('P6V')

    def read_p25I(self):
        return self.read_Ichan('P25V')

    def read_n25I(self):
        return self.read_Ichan('N25V')

    def read_p6I(self):
        return self.read_Ichan('P6V')

    def set_p25V(self, value):
        return self.set_Vchan(value, 'P25V') 

    def set_n25V(self, value):
        return self.set_Vchan(value, 'N25V') 

    def set_p6V(self, value):
        return self.set_Vchan(value, 'P6V') 

    def set_p25I(self, value):
        return self.set_Ichan(value, 'P25V') 

    def set_n25I(self, value):
        return self.set_Ichan(value, 'N25V') 

    def set_p6I(self, value):
        return self.set_Ichan(value, 'P6V') 

    def read_Vchan(self, chan):
        if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            self.psup.write('MEAS:VOLT? %s'%(chan))
            rv = float(self.psup.read())
        finally:
            self.lock.release()
        return rv

    def set_Vchan(self, value, chan):
        if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            self.psup.write('APPL %s,%f, MAX'%(chan, value))
        finally:
            self.lock.release()
        return

    def read_Ichan(self, chan):
        if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            self.psup.write('MEAS:CURR? %s'%(chan))
            rv = float(self.psup.read())
        finally:
            self.lock.release()
        return rv

    def set_Ichan(self, value, chan):
        if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            self.psup.write('APPL %s,MAX,%f'%(chan, value))
        finally:
            self.lock.release()
        return
