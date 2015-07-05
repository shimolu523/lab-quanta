import gtk
import time
import threading
import __main__
import helpers
import socket

DEVICENAME="CavityPhotonCounter"

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
        return ({},
                {'%s_COUNT'%(self.alias): self.read_count,
                '%s_MMAMP'%(self.alias): self.read_mmamp,
                '%s_MMPHS'%(self.alias): self.read_mmphs})

    def read_count(self):
        rv = self.read('COUNT?\n')
        try:
            (label, count) = rv.split(' ', 2)
            if (label == "COUNT:"): val = int(count)
            else: val = 0
        except:
            val = 0.0
	return val
            
    def read_mmamp(self):
        rv = self.read('MMOTION?\n')
        try:
            (label, amp, phs) = rv.split(' ', 2)
            if (label == "MMOTION:"): val = float(amp)
            else: val = 0
        except:
            val = 0.0
	return val

    def read_mmphs(self):
        rv = self.read('MMOTION?\n')
        try:
            (label, amp, phs) = rv.split(' ', 2)
            if (label == "MMOTION:"): val = float(phs)
            else: val = 0
        except:
            val = 0.0
	return val

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


