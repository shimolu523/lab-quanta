import gtk
import time
import Gpib
import threading
import helpers
import __main__

RAMPSTEP = .5
RAMPSLEEP = .01

DEVICENAME="Keithley1"

class io_stream:
    def __init__(self, ui_target = None):
        self.ui_target = ui_target;
        return
    
    def register(self):
        if self.ui_target:
            self.topvbox = gtk.VBox(False, 0)
            self.ui_target.pack_start(self.topvbox, False, False, 5)
            self.ui_target.show_all()

        self.lock = threading.Lock()
        try:
            self.lock.acquire()

            devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))
            assert devname, "Did not find %s in devmap"%(DEVICENAME)
            self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
            assert self.alias, "Did not find alias for %s"%(DEVICENAME)

            self.Keithley = Gpib.Gpib(devname)
            self.Keithley.clear()
        
            self.Keithley.write('*RST');
            self.Keithley.write(':SOUR:FUNC VOLT');
            self.Keithley.write(':SOUR:VOLT:RANG 20');
            self.Keithley.write(':SENS:FUNC "CURR"');
            self.Keithley.write(':SENS:CURR:PROT 15e-3');
            self.Keithley.write(':SENS:CURR:RANG 100e-3');
            self.Keithley.write(':SENS:CURR:NPLC 0.1');
            self.Keithley.write('OUTP ON');
        finally:
            self.lock.release()

        self.Keithley.state = self.K_read_V()

    def unregister(self):
        try:
            self.lock.acquire()
            self.Keithley.write('*RST');
            if self.ui_target:
                self.topvbox.destroy()
        finally:
            self.lock.release()
            
        return
    
    def hooks_provides(self):
        return ({'%s_V'%(self.alias): self.K_ramp_V},
                {'%s_I'%(self.alias): self.K_read_I,
                 '%s_V'%(self.alias): self.K_read_V})

    def K_ramp_V(self, value):
        norm_value = min(max(value, -210), 210)
        if (abs(norm_value - value) > 1):
            print "Keithley voltage %f is way off, ignoring"%(value)
            return
        value = norm_value

        while (abs(value - self.Keithley.state) > RAMPSTEP and not __main__.ABORT_FLAG):
            if (value > self.Keithley.state):
                self.K_set_V(self.Keithley.state + RAMPSTEP)
            else:
                self.K_set_V(self.Keithley.state - RAMPSTEP)
            time.sleep(RAMPSLEEP)

        if not __main__.ABORT_FLAG:
            self.K_set_V(value)

    def K_set_V(self, value):
        try:
            self.lock.acquire()
            self.Keithley.write(':SOUR:VOLT:LEV %f'%(value))
            self.Keithley.state = value
        finally:
            self.lock.release()
        return

    def K_read_V(self):
        if __main__.ABORT_FLAG: return 0.0
        
        try:
            self.lock.acquire()
            self.Keithley.write('READ?')
            rv = self.Keithley.read()
            values = map(float, rv.split(','))
        finally:
            self.lock.release()

        return values[0]

    def K_read_I(self):
        if __main__.ABORT_FLAG: return 0.0
        
        try:
            self.lock.acquire()
            self.Keithley.write('READ?')
            rv = self.Keithley.read()
            values = map(float, rv.split(','))
        finally:
            self.lock.release()

        return values[1]
