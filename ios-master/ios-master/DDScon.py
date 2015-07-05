import gtk
import time
import threading
import __main__
import helpers
import socket

DEVICENAME="DDScon"

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
        return ({'%s_AMP0'%(self.alias): self.set_amp0,
                 '%s_FREQ0'%(self.alias): self.set_freq0,
		 '%s_AMP1'%(self.alias): self.set_amp1,
                 '%s_FREQ1'%(self.alias): self.set_freq1,
		 '%s_AMP2'%(self.alias): self.set_amp2,
                 '%s_FREQ2'%(self.alias): self.set_freq2,
                 '%s_DIGOUT'%(self.alias): self.set_digout,
                 '%s_THRES0'%(self.alias): self.set_thres0,
                 '%s_PARAM'%(self.alias): self.set_param,
		 '%s_SETPROG'%(self.alias):self.set_setprog,
                 '%s_RUNPROG'%(self.alias): self.set_runprog},
                {'%s_LASTAVG'%(self.alias): self.read_lastavg,
                 '%s_THRES0'%(self.alias): self.read_thres0,
                 '%s_NBRIGHT'%(self.alias): self.read_nbright,
                 '%s_PARAM'%(self.alias): self.read_param,
                 '%s_RUNNBRIGHT'%(self.alias): self.read_runnbright,
                 '%s_RUNNTOTAL'%(self.alias): self.read_runntotal})

    def read_lastavg(self):
    	return self.read('LASTAVG?\n')[0]

    def read_thres0(self):
    	return self.read('THRES0?\n')[0]

    def read_nbright(self, hist=False):
    	if (hist): return self.read('NBRIGHT?\n')[1:]
	else: return self.read('NBRIGHT?\n')[0]

    def read_runnbright(self):
        self.set('RUNIT\n')
    	return self.read('NBRIGHT?\n')[0]

    def read_runntotal(self):
        self.set('RUNIT\n')
    	return self.read('NTOTAL?\n')[0]

    def read_param(self, name = 'F_RedOn'):
    	return self.read('PARAMETER? %s\n'%(name))[0]

    def read(self, query):
        if __main__.ABORT_FLAG: return
        try:
            self.device['lock'].acquire()
            try:
	    	rv = 'NA'
                while (1):
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    if not s:
                        raise "Error opening socket"
                    s.settimeout(.5)
                    s.connect((self.device['serverip'], self.device['serverport']))
                    s.sendall(query)
                
                    rv = s.recv(1024)
                    s.shutdown(2)
                    s.close()
                    if not (rv == 'Wait\n'):
                        break
                    time.sleep(.02)

            	(label, value) = map(lambda x: x.strip(), rv.split(' ', 1))
		if (label == "RESULT:"): val = map(float, value.split(' '))
		else: val = [0.0]
            except Exception, inst:
	    	print "Exception occured in reading from DDS\nException: ", inst
		print "Last rv value: ", rv
                val = [0.0]
        finally:
            self.device['lock'].release()
        
        return val

    def set_setprog(self, name):
    	cmd = 'SETPROG %s'%(name)
        return self.set(cmd)

    def set_runprog(self, value = None):
        return self.set('RUNIT')

    def set_param(self, arg0, arg1 = None):
        if (arg1 == None):
            name = 'F_RedOn'
            value = float(arg0)
        else:
            name = arg0
            value = float(arg1)

        return self.set('PARAMETER %s'%(name), value)

    def set_amp0(self, value):
        return self.set('AMP0', value)

    def set_freq0(self, value):
        return self.set('FREQ0', value)

    def set_amp1(self, value):
        return self.set('AMP1', value)

    def set_freq1(self, value):
        return self.set('FREQ1', value)
    
    def set_amp2(self, value):
        return self.set('AMP2', value)

    def set_freq2(self, value):
        return self.set('FREQ2', value)

    def set_digout(self, value):
        return self.set('DIGOUT', value)

    def set_thres0(self, value):
        return self.set('THRES0', value)
	
    def set(self, item, value = None):
        if __main__.ABORT_FLAG: return

        try:
            self.device['lock'].acquire()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if not s:
                raise "Error opening socket"

            #s.settimeout(1.0)
            s.settimeout(2.0)
            s.connect((self.device['serverip'], self.device['serverport']))
            if (value != None):
                cmd='%s %f\n'%(item, value)
            else:
                cmd='%s\n'%(item)
            s.sendall(cmd)
            try:
                rv = s.recv(1024)
            except Exception, inst:
                print "Timed out waiting for socket\n Exception: ", inst
                print "Command was:",cmd
                rv = ''

            if (rv != 'ACK\n'):
                print time.strftime("%H:%M",time.localtime()),__file__,": Function set() didn't get ACK from driver! Got %s instead"%(rv)
                print "Was trying to send this command -->",cmd,"<--"
            s.shutdown(2)
            s.close()
        finally:
            self.device['lock'].release()

        return
