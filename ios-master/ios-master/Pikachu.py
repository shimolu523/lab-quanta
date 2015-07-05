import gtk
import time
import threading
import __main__
import helpers
import socket

RAMPSTEP = .01
RAMPSLEEP = .01

DEVICENAME="Pikachu"

class io_stream:
    def __init__(self, ui_target = None):
        self.ui_target = ui_target;
        return
    
    def register(self):
        self.device = {}
        self.device['lock'] = threading.Lock()
        self.dacstate = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        try:
            self.device['lock'].acquire()

            devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))
            assert devname, "Did not find %s in devmap"%(DEVICENAME)
            self.device['serverip'] = socket.gethostbyname(devname.split(':')[0])
            self.device['serverport'] = int(devname.split(':')[1])

            self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
            assert self.alias, "Did not find alias for %s"%(DEVICENAME)

        finally:
            self.device['lock'].release()

        if self.ui_target:
            self.speedchoice1 = gtk.combo_box_entry_new_text()
            for string in ['NORM','FAST', 'SLOW']:
                self.speedchoice1.append_text(string)
            iter = self.speedchoice1.get_model().get_iter_first()
            self.speedchoice1.set_active_iter(iter)
            self.speedchoice1.connect("changed", self.set_speed_clicked, 1)
            
            dmmspeed1 = gtk.Label("%s_ADC1"%(self.alias))

            self.speedchoice2 = gtk.combo_box_entry_new_text()
            for string in ['NORM','FAST', 'SLOW']:
                self.speedchoice2.append_text(string)
            iter = self.speedchoice2.get_model().get_iter_first()
            self.speedchoice2.set_active_iter(iter)
            self.speedchoice2.connect("changed", self.set_speed_clicked, 2)
            
            dmmspeed2 = gtk.Label("%s_ADC2"%(self.alias))

            hbox1 = gtk.HBox(False, 5)
            hbox1.pack_start(dmmspeed1, True, True, 5)
            hbox1.pack_start(self.speedchoice1, True, True, 5)

            hbox2 = gtk.HBox(False, 5)
            hbox2.pack_start(dmmspeed2, True, True, 5)
            hbox2.pack_start(self.speedchoice2, True, True, 5)

            self.topvbox = gtk.VBox(False, 5)
            self.topvbox.pack_start(hbox1, True, True, 5)
            self.topvbox.pack_start(hbox2, True, True, 5)

            self.ui_target.pack_start(self.topvbox, False, False, 5)
            self.ui_target.show_all()

        # sync up the ADCs to us
        self.set_speed(1, "NORM")
        self.set_speed(2, "NORM")
        
    def unregister(self):
        try:
            self.device['lock'].acquire()
            if self.ui_target:
                self.topvbox.destroy()
        finally:
            self.device['lock'].release()
        return

    def set_speed_clicked(self, widget, data = None):
        if data == 1:
            speed = self.speedchoice1.child.get_text()
        elif data == 2:
            speed = self.speedchoice2.child.get_text()
        else:
            return True
        self.set_speed(data, speed)
        return True
    
    def set_speed(self, chan, speed):
        if __main__.ABORT_FLAG: return
    
        try:
            self.device['lock'].acquire()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"

            if (speed == "FAST"): int_speed = 5
            if (speed == "NORM"): int_speed = 7
            if (speed == "SLOW"): int_speed = 9

            s.connect((self.device['serverip'], self.device['serverport']))
            s.sendall('ADC%d %d\n'%(chan, int_speed))
            rv = s.recv(1024)
            s.close()
        finally:
            self.device['lock'].release()
        return


    def hooks_provides(self):
        return ({'%s_DAC0'%(self.alias): self.setdac0, '%s_DAC1'%(self.alias): self.setdac1,
                 '%s_DAC2'%(self.alias): self.setdac2, '%s_DAC3'%(self.alias): self.setdac3,
                 '%s_DAC4'%(self.alias): self.setdac4, '%s_DAC5'%(self.alias): self.setdac5},
                {'%s_DAC0'%(self.alias): self.readdac0, '%s_DAC1'%(self.alias): self.readdac1,
                 '%s_DAC2'%(self.alias): self.readdac2, '%s_DAC3'%(self.alias): self.readdac3,
                 '%s_DAC4'%(self.alias): self.readdac4, '%s_DAC5'%(self.alias): self.readdac5,
		 '%s_ADC1'%(self.alias): self.readadc1, '%s_ADC2'%(self.alias) : self.readadc2})

    def readdac0(self):
        return self.readdac(0)

    def readdac1(self):
        return self.readdac(1)

    def readdac2(self):
        return self.readdac(2)

    def readdac3(self):
        return self.readdac(3)

    def readdac4(self):
        return self.readdac(4)

    def readdac5(self):
        return self.readdac(5)

    def setdac0(self, value):
        return self.rampdac(0, value)

    def setdac1(self, value):
        return self.rampdac(1, value)

    def setdac2(self, value):
        return self.rampdac(2, value)

    def setdac3(self, value):
        return self.rampdac(3, value)

    def setdac4(self, value):
        return self.rampdac(4, value)

    def setdac5(self, value):
        return self.rampdac(5, value)

    def rampdac(self, chan, value):
	self.readdac(chan) # make sure self.dacstate[chan] is up to date
	
        while (abs(value - self.dacstate[chan]) > RAMPSTEP and not __main__.ABORT_FLAG):
            if (value > self.dacstate[chan]):
                self.setdac(chan, self.dacstate[chan] + RAMPSTEP)
            else:
                self.setdac(chan, self.dacstate[chan] - RAMPSTEP)
            time.sleep(RAMPSLEEP)

        if not __main__.ABORT_FLAG:
            self.setdac(chan, value)
    
    def readdac(self, chan):
        if __main__.ABORT_FLAG: return
        if (chan < 0 or chan > 5):
            return

        try:
            self.device['lock'].acquire()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"
            s.connect((self.device['serverip'], self.device['serverport']))

            # generate the string
            s.sendall('DAC%d?\n' % chan)
            rv = s.recv(1024)
            s.close()

            self.dacstate[chan] = float(rv.strip())
        finally:
            self.device['lock'].release()

        return self.dacstate[chan]

    def setdac(self, chan, value):
        if __main__.ABORT_FLAG: return
        if (chan < 0 or chan > 5):
            return

        if (abs(value) > 11.0):
            print "Value set for DAC %d way off, ignoring"%(chan)
            return
        value = min(max(-10.0, value), 10.0)

        try:
            self.device['lock'].acquire()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"
            s.connect((self.device['serverip'], self.device['serverport']))

            # Determine which DAC range we will use
            if (abs(value) < 2.5):
                range = 12
                fullscale = 2.5
            elif (abs(value) < 5.0) :
                range = 10
                fullscale = 5.0
            else:
                range = 11
                fullscale = 10

            # Convert floats to integers
            int_value = int(2**16 * (value + fullscale)/(2*fullscale))

            # generate the string
            s.sendall('DAC%d DCV, %d, %d, 0, 10, 0\n'%(chan, range, int_value))
            rv = s.recv(1024)
            s.close()

            self.dacstate[chan] = value
        finally:
            self.device['lock'].release()

        return

    def readadc1(self):
        return self.readadc(1)

    def readadc2(self):
        return self.readadc(2)
    

    def readadc(self, chan):
        if __main__.ABORT_FLAG: return 0.0

        try:
            self.device['lock'].acquire()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"

            s.connect((self.device['serverip'], self.device['serverport']))
            s.sendall('ADC%d?\n'%(chan))
            rv = s.recv(1024)

            (adc, speed, strval) = rv.split(' ', 2)
            try:
                val = -(20.0*(int(strval)^2**23))/(2**24) + 10.0
            except:
                val = 0.0
            s.shutdown(2)
            s.close()
        finally:
            self.device['lock'].release()

        return val

        
