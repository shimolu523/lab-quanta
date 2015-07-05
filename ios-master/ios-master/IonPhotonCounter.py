import gtk
import time
import threading
import __main__
import helpers
import socket

DEVICENAME="IonPhotonCounter"

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
        return ({'%s_INTTIME'%(self.alias):self.set_inttime,
                 '%s_MAGIC'%(self.alias):self.set_magic},
                {'%s_COUNT'%(self.alias): self.read_count,
                '%s_INTTIME'%(self.alias): self.read_inttime,
                '%s_MMAMP'%(self.alias): self.read_mmamp,
                '%s_MMPHS'%(self.alias): self.read_mmphs})

    def set_inttime(self,inttime):
        cmd='INTTIME: '+str(inttime)+'\n'
        return self.set(cmd)
    def set_magic(self,magic):
        if (magic==1):
            cmd='MAGIC\n'
        else:
            cmd='NOMAGIC\n'
        return self.set(cmd) 

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

    def read_inttime(self):
        rv=self.read('INTTIME?\n')
        try:
            (label,inttime)=rv.split(' ',2)
            if (label=='INTTIME:'): val=(int(inttime))
            else: val=0
        except Exception,e:
            val=0
            print "Error in",__file__,":",e
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


