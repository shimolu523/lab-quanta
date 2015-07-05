import gtk
import time
import Gpib
import threading
import helpers
import __main__

DEVICENAME="HPRFGEN"

class io_stream:
    def __init__(self, ui_target = None):
        self.ui_target = ui_target;
        return
    
    def register(self):
        if self.ui_target:
            self.topvbox = gtk.VBox(gtk.FALSE, 0)
            self.ui_target.pack_start(self.topvbox, gtk.FALSE, gtk.FALSE, 5)
            self.ui_target.show_all()

        self.lock = threading.Lock()
        try:
            self.lock.acquire()

            devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))
            assert devname, "Did not find %s in devmap"%(DEVICENAME)
            self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
            assert self.alias, "Did not find alias for %s"%(DEVICENAME)

            self.rfgen = Gpib.Gpib(devname)
            self.rfgen.clear()
            time.sleep(.1)
        finally:
            self.lock.release()


    def unregister(self):
        try:
            self.lock.acquire()
            #self.rfgen.write('*RST');
            if self.ui_target:
                self.topvbox.destroy()
        finally:
            self.lock.release()
            
        return
    
    def hooks_provides(self):
        return ({'%s_V'%(self.alias): self.rfgen_setV,
                 '%s_f'%(self.alias): self.rfgen_setf},
                {'%s_V'%(self.alias): self.rfgen_readV,
                 '%s_f'%(self.alias): self.rfgen_readf})

    def rfgen_setV(self, value):
	if __main__.ABORT_FLAG: return
    
        norm_value = min(max(value, 0), 10)
        if (abs(norm_value - value) > 1.):
            print "rfgen voltage %f is way off, ignoring"%(value)
            return
        value = norm_value
        try:
            self.lock.acquire()
            self.rfgen.write('AMP %fVOL'%(value))
        finally:
            self.lock.release()
        return

    def rfgen_setf(self, value):
	if __main__.ABORT_FLAG: return
    
        norm_value = min(max(value, 0), 20e6)
        if (abs(norm_value - value) > 1e6):
            print "rfgen voltage %f is way off, ignoring"%(value)
            return
        value = norm_value
        try:
            self.lock.acquire()
            self.rfgen.write('FRE %fHZ'%(value))
        finally:
            self.lock.release()
        return

    def rfgen_readV(self):
	if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            #self.rfgen.write('AMP?')
            #val = float
        finally:
            self.lock.release()
        return 0.

    def rfgen_readf(self):
	if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            #self.rfgen.write('AMP?')
            #val = float
        finally:
            self.lock.release()
        return 0.
