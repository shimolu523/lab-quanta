import gtk
import helpers
import math
import time
import Gpib
import threading
import __main__

DEVICENAME="DMM2"

class io_stream:
    def __init__(self, ui_target = None):
        self.ui_target = ui_target;
        return
    
    def register(self):
        self.lock = threading.Lock()

        devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))
        assert devname, "Did not find %s in devmap"%(DEVICENAME)
        self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
        assert self.alias, "Did not find alias for %s"%(DEVICENAME)

        self.dmm = Gpib.Gpib(devname)
        self.dmm.clear()
        time.sleep(.1)
        self.dmm.range = .1
        self.set_speed(self.dmm, 'NORM')

        if self.ui_target:
            self.speedchoice = gtk.combo_box_entry_new_text()
            for string in ['NORM','FAST', 'SLOW']:
                self.speedchoice.append_text(string)
            iter = self.speedchoice.get_model().get_iter_first()
            self.speedchoice.set_active_iter(iter)
            self.speedchoice.connect("changed", self.set_speed_clicked)
            
            dmmspeed = gtk.Label("%s"%(self.alias))
            self.tophbox = gtk.HBox(False, 5)
            self.tophbox.pack_start(dmmspeed, True, True, 5)
            self.tophbox.pack_start(self.speedchoice, True, True, 5)

            self.ui_target.pack_start(self.tophbox, False, False, 5)
            self.ui_target.show_all()
    
    def set_speed_clicked(self, widget, data = None):
        speed = self.speedchoice.child.get_text()
        self.set_speed(self.dmm, speed)
        return True
    
    def set_speed(self, dmm, speed):
        if __main__.ABORT_FLAG: return
    
        try:
            self.lock.acquire()
            dmm.write('*RST')
            if (speed == 'FAST'):
                dmm.write('DISP OFF')
                dmm.write('ZERO:AUTO ONCE')
                dmm.write('VOLT:DC:NPLC .2')
            if (speed == 'NORM'):
                dmm.write('DISP ON')
                dmm.write('ZERO:AUTO ONCE')
                dmm.write('VOLT:DC:NPLC 1')
            if (speed == 'SLOW'):
                dmm.write('DISP ON')
                dmm.write('ZERO:AUTO ONCE')
                dmm.write('VOLT:DC:NPLC 10')
        finally:
            self.lock.release()
        return

    def unregister(self):
        self.lock.acquire()
        self.dmm.write('*RST')
        self.lock.release()
        if self.ui_target:
            self.tophbox.destroy()
        return
    
    def hooks_provides(self):
        return ({},{'%s_V'%(self.alias): self.read_dmm})

    def read_dmm(self):
        if __main__.ABORT_FLAG: return 0.0
    
        try:
            self.lock.acquire()
            rv = readdmm(self.dmm)
        finally:
            self.lock.release()
        return rv

def readdmm(dmm):
    dmm.write('READ?')
    rv = float(dmm.read())

    if ((abs(rv) > 1.1 * dmm.range) and (dmm.range < 1000)):
        dmm.range = 10*dmm.range
        dmm.write('VOLT:DC:RANG %.E'%(dmm.range))
        return readdmm(dmm)
    elif ((abs(rv) < .1 * dmm.range) and (dmm.range > .1)):
        dmm.range = .1 * dmm.range
        dmm.write('VOLT:DC:RANG %.E'%(dmm.range))
        return readdmm(dmm)
    else:
        return rv
