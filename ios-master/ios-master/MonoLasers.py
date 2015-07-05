import gtk
import time
import threading
import __main__
import helpers
import socket

DEVICENAME="MonoLasers"
RAMPSTEP = .01
RAMPSLEEP = .1


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
        return ({'%s_421'%(self.alias): self.set_421,
                 '%s_Quiet421'%(self.alias): self.quiet_421,
                 '%s_674'%(self.alias): self.set_674,
                 '%s_844'%(self.alias): self.set_844,
                 '%s_Quiet674'%(self.alias): self.quiet_674,
                 '%s_Quiet844'%(self.alias): self.quiet_844,
                 '%s_1033'%(self.alias): self.set_1033,
                 '%s_1091'%(self.alias): self.set_1091},
                {'%s_421'%(self.alias): self.read_421,
                 '%s_674'%(self.alias): self.read_674,
                 '%s_844'%(self.alias): self.read_844,
                 '%s_1033'%(self.alias): self.read_1033,
                 '%s_1091'%(self.alias): self.read_1091,
                 '%s_421_ADCVAL'%(self.alias): self.read_421_adcval,
                 '%s_674_ADCVAL'%(self.alias): self.read_674_adcval,
                 '%s_844_ADCVAL'%(self.alias): self.read_844_adcval,
                 '%s_1033_ADCVAL'%(self.alias): self.read_1033_adcval,
                 '%s_1091_ADCVAL'%(self.alias): self.read_1091_adcval})
    
    
    def read_421(self):
	rv = self.read_cavity(self.device['serverip'], self.device['serverport'])
        return rv
    
    def read_674(self):
	rv = self.read_cavity(self.device['serverip'], self.device['serverport'] + 1)
        return rv
    
    def read_1033(self):
	rv = self.read_cavity(self.device['serverip'], self.device['serverport'] + 2)
        return rv
    
    def read_1091(self):
	rv = self.read_cavity(self.device['serverip'], self.device['serverport'] + 3)
        return rv

    def read_844(self):
	rv = self.read_cavity(self.device['serverip'], self.device['serverport'] + 5)
        return rv


    def read_421_adcval(self):
	rv = self.read_cavity_adcval(self.device['serverip'], self.device['serverport'])
        return rv

    def read_674_adcval(self):
	rv = self.read_cavity_adcval(self.device['serverip'], self.device['serverport'] + 1)
        return rv

    def read_1033_adcval(self):
	rv = self.read_cavity_adcval(self.device['serverip'], self.device['serverport'] + 2)
        return rv

    def read_1091_adcval(self):
	rv = self.read_cavity_adcval(self.device['serverip'], self.device['serverport'] + 3)
        return rv

    def read_844_adcval(self):
	rv = self.read_cavity_adcval(self.device['serverip'], self.device['serverport'] + 5)
        return rv


    def set_421(self, value):
        return self.ramp_cavity(self.device['serverport'], value)

    def quiet_421(self, value):
        if (value):
            self.send_receive('BeQuiet 1', self.device['serverip'], self.device['serverport'])
        else:
            self.send_receive('BeQuiet 0', self.device['serverip'], self.device['serverport'])

    def set_674(self, value):
        return self.ramp_cavity(self.device['serverport']+1, value)

    def quiet_674(self, value):
        if (value):
            self.send_receive('BeQuiet 1', self.device['serverip'], self.device['serverport'] + 1)
        else:
            self.send_receive('BeQuiet 0', self.device['serverip'], self.device['serverport'] + 1)

    def set_844(self, value):
        return self.ramp_cavity(self.device['serverport']+ 4, value)

    def quiet_844(self, value):
        if (value):
            self.send_receive('BeQuiet 1', self.device['serverip'], self.device['serverport'] + 5)
        else:
            self.send_receive('BeQuiet 0', self.device['serverip'], self.device['serverport'] + 5)


    def set_1033(self, value):
        return self.ramp_cavity(self.device['serverport']+2, value)

    def set_1091(self, value):
        return self.ramp_cavity(self.device['serverport']+3, value)

    def send_receive(self, str, server, port):
        try:
	    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((server, port))
            s.sendall(str)
            rv = s.recv(1024)
            s.shutdown(2)
            s.close()
        except:
	    print "Error in transmission!"
	    return None
	    
	return rv

    def read_cavity(self, ip, port):
        try:
            self.device['lock'].acquire()
	    rv = self.send_receive('CavityVolt?\n', ip, port)
	   
            try:
                (label, strval) = rv.split(' ', 2)
	        if (label == "CavityVolt:"): curval = float(strval)
                else: return 0.0
       	    except:
                print "Failed to get current cavity voltage"
                return
	finally:
            self.device['lock'].release()

	return curval

    def read_cavity_adcval(self, ip, port):
        try:
            self.device['lock'].acquire()
	    rv = self.send_receive('ADC VAL?\n', ip, port)
	   
            try:
                curval = float(rv)
       	    except:
                print "Failed to get current ADC value"
                return -1
	finally:
            self.device['lock'].release()

        return curval

    def ramp_cavity(self, port, target):
        if __main__.ABORT_FLAG: return

        norm_target = min(max(target, -10), 10)
        if (abs(norm_target - target) > 1):
            print "Cavity voltage %f is way off, ignoring"%(target)
            return
        target = norm_target

        try:
	    curval = self.read_cavity(self.device['serverip'], port)
            self.device['lock'].acquire()
	    if (curval == None):
	    	return

            while (abs(target - curval) > RAMPSTEP and not __main__.ABORT_FLAG):
                if (target > curval):
                    curval = curval + RAMPSTEP;
                else:
                    curval = curval - RAMPSTEP;
		str = 'CavityVolt %f'%(curval)
		time.sleep(RAMPSLEEP)
	        rv = self.send_receive(str, self.device['serverip'], port)
		if (rv != 'ACK\n'):
		    print "Bad response! - ", rv
            
	    if not __main__.ABORT_FLAG:
		str = 'CavityVolt %f'%(target)
	        self.send_receive(str, self.device['serverip'], port)

        finally:
            self.device['lock'].release()
