import gtk
import time
import threading
import __main__
import helpers
import socket

DEVICENAME="AudioAlert"

class io_stream:
    def __init__(self, ui_target = None):
        self.ui_target = ui_target;
        return
    
    def register(self):
        self.device = {}
        self.device['lock'] = threading.Lock()
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
        return ({'%s_cavityunlocked'%(self.alias):self.set_cavityunlocked,
                '%s_cavityrelocked'%(self.alias):self.set_cavityrelocked,
                '%s_say'%(self.alias):self.set_say,
                '%s_scandone'%(self.alias):self.set_scandone},
                {})

    def set_cavityunlocked(self):
        cmd='CAVITYUNLOCKED\n'
        return self.set(cmd) 

    def set_scandone(self):
        cmd='SCANDONE\n'
        return self.set(cmd) 

    def set_say(self,text):
        cmd='SAY:%s\n'%(text)
        return self.set(cmd) 

    def set_cavityrelocked(self):
        cmd='CAVITYRELOCKED\n'
        return self.set(cmd) 

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


