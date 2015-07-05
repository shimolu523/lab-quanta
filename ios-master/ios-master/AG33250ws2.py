import gtk
import time
import Gpib
import threading
import helpers
import __main__

DEVICENAME="33250WS2"

class io_stream:
    def __init__(self, ui_target = None):
        self.ui_target = ui_target;
        return
    
    def register(self):
        self.lock = threading.Lock()
        try:
            self.lock.acquire()

            devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))
            assert devname, "Did not find %s in devmap"%(DEVICENAME)
            self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
            assert self.alias, "Did not find alias for %s"%(DEVICENAME)

            self.Agilent = Gpib.Gpib(devname)
            self.Agilent.clear()
            time.sleep(.1)
            # Annoying line that resets the signal generator so you loose the
            # ion:
           # self.Agilent.write('*RST');
          #  self.Agilent.write('APPL:DC DEF,DEF,0');
          #  self.Agilent.write('OUTP:LOAD INF');
            self.Agilent.state = {'mode' : 'DC', 'Vh' : 0., 'Vl' : 0., 'PW' : 1e-4, 'f' : 1000.0}
          #  self.Agilent.write('OUTP ON');
        finally:
            self.lock.release()

        if self.ui_target:
            self.modechoice = gtk.combo_box_entry_new_text()
            for string in ['DC','PULSE', 'SIN', 'SQUARE']:
                self.modechoice.append_text(string)
            iter = self.modechoice.get_model().get_iter_first()
            self.modechoice.set_active_iter(iter)
            self.modechoice.connect("changed", self.set_modechoice_clicked)
            
            wsmode = gtk.Label("%s"%(self.alias))
            self.tophbox = gtk.HBox(False, 5)
            self.tophbox.pack_start(wsmode, True, True, 5)
            self.tophbox.pack_start(self.modechoice, True, True, 5)

            self.ui_target.pack_start(self.tophbox, False, False, 5)
            self.ui_target.show_all()


    def unregister(self):
        try:
            self.lock.acquire()
            #self.Agilent.write('*RST');
            if self.ui_target:
                self.tophbox.destroy()
        finally:
            self.lock.release()
        
        return
    
    def set_modechoice_clicked(self, widget, data = None):
        try:
            self.lock.acquire()
            newmode = self.modechoice.child.get_text()
            if (newmode == 'PULSE'):
                self.Agilent.write('APPL:PULS 13017, 0.002, 0.001')
                self.Agilent.state.update({'mode' : 'PULSE', 'Vh' : .001, 'Vl' : -.001, 'f' : 13017})
            elif (newmode == 'DC'):
                self.Agilent.write('APPL:DC DEF, DEF, 0.0');
                self.Agilent.state.update({'mode' : 'DC', 'Vh' : .0, 'Vl' : -.0, 'f' : 0})
            elif (newmode == 'SIN'):
                self.Agilent.write('APPL:SIN 13017, 0.002, 0.0');
                self.Agilent.state.update({'mode' : 'SIN', 'Vh' : .001, 'Vl' : -.001, 'f' : 13017})
            elif (newmode == 'SQUARE'):
                self.Agilent.write('APPL:SQU 13017, 0.002, 0.0');
                self.Agilent.state.update({'mode' : 'SQUARE', 'Vh' : .001, 'Vl' : -.001, 'f' : 13017})
            else:
                raise "Bad mode!"
        finally:
            self.lock.release()
    
        return True

    def hooks_provides(self):
        return ({'%s_Freq'%(self.alias): self.set_Frq_locked,
                 '%s_Vamp'%(self.alias): self.set_Vamp_locked,
                 '%s_Vhigh'%(self.alias): self.set_Vh_locked,
                 '%s_Vlow'%(self.alias): self.set_Vl_locked,
                 '%s_Voff'%(self.alias): self.set_Voff_locked,
                 '%s_PulseWdth'%(self.alias): self.set_PulseWdth_locked,
                 '%s_OutPut'%(self.alias): self.set_OutPut},
                {})

    def set_Frq_locked(self, value):
    	if __main__.ABORT_FLAG: return

        try:
	    self.lock.acquire()
            self.set_Frq(value)
	finally:
            self.lock.release()
    def set_OutPut(self, value):
        if __main__.ABORT_FLAG: return

        try:
            self.lock.acquire()
            if value==0:
                self.Agilent.write('OUTP OFF');
            else:
                self.Agilent.write('OUTP ON');
        finally:
            self.lock.release()

    def set_Vamp_locked(self, value):
    	if __main__.ABORT_FLAG: return
        try:
	    self.lock.acquire()
            self.set_Vamp(value)
	finally:
            self.lock.release()

    def set_Vh_locked(self, value):
    	if __main__.ABORT_FLAG: return
        try:
	    self.lock.acquire()
            self.set_Vh(value)
	finally:
            self.lock.release()

    def set_Vl_locked(self, value):
    	if __main__.ABORT_FLAG: return
        try:
	    self.lock.acquire()
            self.set_Vl(value)
	finally:
            self.lock.release()

    def set_Voff_locked(self, value):
    	if __main__.ABORT_FLAG: return
        try:
	    self.lock.acquire()
            self.set_Voff(value)
	finally:
            self.lock.release()

    def set_PulseWdth_locked(self, value):
    	if __main__.ABORT_FLAG: return
        try:
	    self.lock.acquire()
            self.set_PulseWdth(value)
	finally:
            self.lock.release()


    def set_Vamp(self, value):
        if (self.Agilent.state['mode'] == 'DC'):
            return self.set_Voff(value)

        value = min(max(value, -0.0), 20.0)
            
        off = self.Agilent.state['Vl'] + self.Agilent.state['Vh']

        if (value > 20. - abs(off)):
            off = off/abs(off) * (10.0 - value/2.)
            self.set_Voff(off)

        self.Agilent.write("VOLT %g"%(value))
        self.Agilent.state['Vh'] = value/2. + off
        self.Agilent.state['Vl'] = -value/2. + off
        
        return

    def set_Voff(self, value):
        value = min(max(value, -9.999), 9.999)

        amp = self.Agilent.state['Vh'] - self.Agilent.state['Vl']

        if (value + amp/2 > 10.0):
            amp = 20. - 2*value
            self.set_Vamp(amp)
            
        self.Agilent.write("VOLT:OFFS %g"%(value))
        self.Agilent.state['Vh'] = value + amp/2.
        self.Agilent.state['Vl'] = value - amp/2.

        return
    
    def set_Vh(self, value):
        if (self.Agilent.state['mode'] == 'DC'):
            return self.set_Voff(value)
            
        value = min(max(value, -9.998), 10.0)
        
        if (value < self.Agilent.state['Vl'] + 2e-3):
            Vl = value - 2e-3
            self.set_Vl(Vl)
            self.Agilent.state['Vl'] = Vl
            
        self.Agilent.write("VOLT:HIGH %g"%(value))
        self.Agilent.state['Vh'] = value
        
        return

    def set_Vl(self, value):
        if (self.Agilent.state['mode'] == 'DC'):
            return self.set_Voff(value)
        
        value = min(max(value, -10.), 9.998)
        if (value > self.Agilent.state['Vh'] - 2e-3):
            Vh = value + 2e-3
            self.set_Vh(Vh)
            self.Agilent.state['Vh'] = Vh
            
        self.Agilent.write("VOLT:LOW %g"%(value))
        self.Agilent.state['Vl'] = value
        
        return

    def set_Frq(self, value):
        value = min(max(value, 1.0), 25.0e6)
        if ((self.Agilent.state['mode'] == 'PULSE') and (value > .99/self.Agilent.state['PW'])):
            return self.set_PulseWdth(.99/value)
        
        self.Agilent.write("FREQ %g"%(value))
        self.Agilent.state['f'] = value
        return

    def set_PulseWdth(self, value):
        if (self.Agilent.state['mode'] != 'PULSE'):
            return
        
        value = max(value, 10.0e-9)
        value = min(value, .99)
        if (value > .99/self.Agilent.state['f']):
            return self.set_Frq(.99/value)

        self.Agilent.write("PULS:WIDT %g"%(value))
        self.Agilent.state['PW'] = value
            
        return
    
