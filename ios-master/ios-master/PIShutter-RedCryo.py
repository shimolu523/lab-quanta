import gtk
import time
import threading
import __main__
import helpers
import socket

DEVICENAME="PIShutter-RedCryo"

class io_stream:
    def __init__(self, ui_target = None):
        self.ui_target = ui_target;
        return
    
    def register(self):
        self.device = {}
        self.device['lock'] = threading.Lock()
        try:
            self.device['lock'].acquire()
            
            self.freqs = [405, 422, 461]

            devname = helpers.devmap_remap("%s:dev"%(DEVICENAME))
            assert devname, "Did not find %s in devmap"%(DEVICENAME)
            self.device['serverip'] = socket.gethostbyname(devname.split(':')[0])
            self.device['serverport'] = int(devname.split(':')[1])

            self.alias = helpers.devmap_remap("%s:alias"%(DEVICENAME))
            assert self.alias, "Did not find alias for %s"%(DEVICENAME)

        finally:
            self.device['lock'].release()

        if self.ui_target:
	    pass
        
    def unregister(self):
        try:
            self.device['lock'].acquire()
            if self.ui_target:
	        pass
        finally:
            self.device['lock'].release()
        return

    def hooks_provides(self):
        getters = dict(('%s_%d_is_open'%(self.alias, f), lambda:self.get_shutter(f)) for f in self.freqs)
        setters = dict(('%s_%d_set_open'%(self.alias, f), lambda set_to_open:self.set_shutter(f, set_to_open)) for f in self.freqs)
        return (setters, getters)

    def set_shutter(self, freq, set_to_open):
        if set_to_open:
            cmd='UNSHUT %d\n'%freq
        else:
            cmd='SHUT %d\n'%freq
        return self.set(cmd) 
        
    def get_shutter(self, freq):
        response = self.read('GET %d'%freq)
        if '(1)' in response:
            return 1 # shutter open
        elif '(0)' in response:
            return 0 # shutter closed
        else:
            return -1 # unknown

    def read(self, cmd):
        if __main__.ABORT_FLAG: return 0.0

        try:
            self.device['lock'].acquire()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"

            s.settimeout(0.5)
            s.connect((self.device['serverip'], self.device['serverport']))
            s.sendall(cmd)
            rv = s.recv(1024)

            s.shutdown(2)
            s.close()
        finally:
            self.device['lock'].release()

        return rv

    def set(self, cmd):
        if __main__.ABORT_FLAG: return 0.0

        try:
            self.device['lock'].acquire()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"

            s.settimeout(0.5)
            s.connect((self.device['serverip'], self.device['serverport']))
            s.sendall(cmd)
            rv = s.recv(1024)

            s.shutdown(2)
            s.close()
        finally:
            self.device['lock'].release()

        return 


