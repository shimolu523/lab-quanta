import gtk
import helpers
import math
import time
import Gpib
import threading
import __main__

DEVICENAME="E3633A"

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
        return ({'%s_V'%(self.alias): self.set_V, 
                 '%s_I'%(self.alias): self.set_I}, 
		{'%s_V'%(self.alias): self.read_V, 
                 '%s_I'%(self.alias): self.read_I})

    def read_V(self):
        if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            self.psup.write('MEAS:VOLT?')
            rv = float(self.psup.read())
        finally:
            self.lock.release()
        return rv

    def set_V(self, value):
        if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            self.psup.write('VOLT %f'%(value))
        finally:
            self.lock.release()
        return

    def read_I(self):
        if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            self.psup.write('MEAS:CURR?')
            rv = float(self.psup.read())
        finally:
            self.lock.release()
        return rv

    def set_I(self, value):
        if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            self.psup.write('CURR %f'%(value))
        finally:
            self.lock.release()
        return
