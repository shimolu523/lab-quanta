import gtk
import time
import threading
import __main__
import helpers
import socket

DEVICENAME="WS7"

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
	    
	    self.server_ip = devname.split(':')[0]
	    self.server_port = int(devname.split(':')[1])
	finally:
	    self.lock.release()
        
    def unregister(self):
        try:
            self.lock.acquire()
            if self.ui_target:
                self.topvbox.destroy()
        finally:
            self.lock.release()
        return

    def hooks_provides(self):
        return ({}, {'%s_T'%(self.alias): self.readT,
                     '%s_F1'%(self.alias): self.readF1,
                     '%s_F2'%(self.alias): self.readF2,
                     '%s_F3'%(self.alias): self.readF3,
                     '%s_F4'%(self.alias): self.readF4,
                     '%s_F5'%(self.alias): self.readF5,
                     '%s_F6'%(self.alias): self.readF6,
                     '%s_F7'%(self.alias): self.readF7,
                     '%s_F8'%(self.alias): self.readF8})

    def readT(self):
        try:
            self.lock.acquire()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"
            s.connect((self.server_ip, self.server_port))

            s.sendall('T?\n')
            rv = s.recv(1024)
	    T = float(rv)
	    
            s.close()
        finally:
            self.lock.release()

	return T

    def readF1(self):
        return self.readF(1)

    def readF2(self):
        return self.readF(2)

    def readF3(self):
        return self.readF(3)

    def readF4(self):
        return self.readF(4)

    def readF5(self):
        return self.readF(5)

    def readF6(self):
        return self.readF(6)

    def readF7(self):
        return self.readF(7)

    def readF8(self):
        return self.readF(8)

    def readF(self, channel):
        try:
            self.lock.acquire()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"
            s.connect((self.server_ip, self.server_port))

            s.sendall('F%i?\n' % channel)
            rv = s.recv(1024)
	    F = float(rv)
	    
            s.close()
        finally:
            self.lock.release()

	return F
