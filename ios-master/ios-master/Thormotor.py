import socket
import gtk
import helpers
import math
import time
import Gpib
import threading
import __main__

TABLE_SIZE = 11

DEVICENAME="Thormotor"

class io_stream:
    def __init__(self, ui_target = None):
        self.ui_target = ui_target;
        return
    
    def register(self):
        self.lock = threading.Lock()
        self.controlwin = None
        self.origin = [0., 0.] 

        try:
            self.lock.acquire()
            devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))
            assert devname, "Did not find %s in devmap"%(DEVICENAME)
            self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
            assert self.alias, "Did not find alias for %s"%(DEVICENAME)

            self.server_ip = devname.split(':')[0]
	    self.server_port = int(devname.split(':')[1])
	    
            if self.ui_target:
	    	self.hbox = gtk.HBox(False, 5)
                pb = gtk.ToggleButton('Show Pos Control')
                pb.connect('toggled', self.pb_toggled, None)
		self.hbox.pack_start(pb, True, True, 5)
                self.ui_target.pack_start(self.hbox, False, False, 5)
                self.ui_target.show_all()

        finally:
            self.lock.release()

        return True

    def unregister(self):
        try:
            self.lock.acquire()
            #self.esp.write('*RST')
        finally:
            self.lock.release()
        if self.ui_target:
            self.hbox.destroy()

        return

    def pb_toggled(self, button, args = None):
        if button.get_active():
            self.controlwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.controlwin.set_title('Thormotor Control Window')
            self.controlwin.connect('delete_event', self.controlwin_delete, None)
            table = gtk.Table(TABLE_SIZE, TABLE_SIZE, True)
            
            self.center = gtk.RadioButton(None, None, None)
            for i in range(TABLE_SIZE):
                for j in range(TABLE_SIZE):
                    if ((i==j) and (i == (TABLE_SIZE - 1)/2)):
                        rad = self.center
                    else:
                        rad = gtk.RadioButton(self.center, None, None)
                    rad.connect("toggled", self.rad_toggled, (i,j))
                    table.attach(rad, i, i+1, j, j+1)
            # Buttons etc.
            self.origin = [self.readLX(), self.readLY()]
            self.origin_lab = gtk.Label('X: %.3f, Y: %.3f'%(self.origin[0], self.origin[1]))
            borigin = gtk.Button('Set Origin')
            borigin.connect("clicked", self.origin_clicked, None)

            tstep_lab = gtk.Label('Step [um]')
            self.tstep = gtk.SpinButton(None, .2, 0)
            self.tstep.set_range(0, 100)
            self.tstep.set_increments(5, 5)
            self.tstep.set_value(50)

            reset = gtk.Button('Reset Colors')
            reset.connect("clicked", self.reset_clicked, None)
            # put the stuff in the window
            hbox1 = gtk.HBox()
            hbox1.pack_start(borigin, False, False, 5)
            hbox1.pack_start(self.origin_lab, False, False, 5)
            hbox1.pack_start(tstep_lab, False, False, 5)
            hbox1.pack_start(self.tstep, False, False, 5)
            vbox = gtk.VBox()
            vbox.pack_start(table, False, False, 0)
            vbox.pack_start(hbox1, False, False, 5)
            vbox.pack_start(reset, False, False, 5)
            self.controlwin.add(vbox)
            self.controlwin.show_all()
        else:
            if self.controlwin:
                self.controlwin.destroy()

        return True

    def rad_toggled(self, button, params = None):
        if not button.get_active():
            button.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(65535, 0, 0))
        else:
            tstep = self.tstep.get_value()/1000.
            x = self.origin[0] + (params[0] - (TABLE_SIZE - 1)/2) * tstep 
            y = self.origin[1] + (params[1] - (TABLE_SIZE - 1)/2) * tstep
            self.setLX(x)
            self.setLY(y)
            
        return True

    def origin_clicked(self, widget, data = None):
        self.origin = [self.readLX(), self.readLY()]
        self.origin_lab.set_text('X: %.3f, Y: %.3f'%(self.origin[0], self.origin[1]))

        self.center.set_active(True)
        return True

    def reset_clicked(self, widget, data = None):
        center = self.center
        group = center.get_group()
        for rad in group:
            rad.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0))
            
        return True

    def controlwin_delete(self, controlwin, event, args = None):
        return True
    
    def hooks_provides(self):
        return ({'%s_LX'%(self.alias): self.setLX,
                 '%s_LY'%(self.alias): self.setLY,
                 '%s_PX'%(self.alias): self.setPX,
                 '%s_PY'%(self.alias): self.setPY,
                 '%s_PC'%(self.alias): self.setPC},
		{'%s_LX'%(self.alias): self.readLX,
                 '%s_LY'%(self.alias): self.readLY,
                 '%s_PX'%(self.alias): self.readPX,
                 '%s_PY'%(self.alias): self.readPY,
                 '%s_PC'%(self.alias): self.readPC})

    def setLX(self, pos):
        return self.set('0', pos)

    def setLY(self, pos):
        return self.set('1', pos)
    
    def setPX(self, pos):
        return self.set('2', pos)

    def setPY(self, pos):
        return self.set('3', pos)
    
    def setPC(self, pos):
        return self.set('4', pos)

    def set(self, axis, pos):
        if (pos < 0 or pos > 24):
            print "Value set for Thormotor %s out of range, ignoring"%(axis)
            return

        try:
            self.lock.acquire()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"
            s.connect((self.server_ip, self.server_port))

            s.sendall('move %s %f\n'%(axis, pos))
            rv = s.recv(1024)
            s.close()
        finally:
            self.lock.release()

        return

    def readLX(self):
        return self.read('0')

    def readLY(self):
        return self.read('1')

    def readPX(self):
        return self.read('2')

    def readPY(self):
        return self.read('3')

    def readPC(self):
        return self.read('4')
    
    def read(self, axis):
        try:
            self.lock.acquire()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"
            s.connect((self.server_ip, self.server_port))

            s.sendall('report %s\n'%axis)
            rv = s.recv(1024)
	    pos = float(rv[14:22])
	    
            s.close()
        finally:
            self.lock.release()

	return pos
