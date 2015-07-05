import time
import threading
import socket
import numpy as numarray

def ReadDDSmemory():
    
    LOCK = threading.Lock()
    SERVERIP = "dehmelt"
    SERVERPORT = 11120
    
    try:
	LOCK.acquire()
	try:
	    rv = 'NA'
	    while(1):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if not s:
		    raise "Error opening socket"
		s.settimeout(0.5)
		s.connect((SERVERIP, SERVERPORT))
		s.sendall('MEMORY?\n')
		
		rv = s.recv(1024)
		s.shutdown(2)
		s.close()
		if not (rv == 'Wait\n'):
		    break
		time.sleep(0.1)
	    
	    list = rv.split(' ')
	    if list[0] == 'RESULT:':
		val = numarray.zeros(len(list) - 1)
		for i in range(len(list) - 1):
		    val[i] = int(list[i + 1])
	    else: val = 0
	except Exception, inst:
	    print "Exception occured in reading from DDS\n Exception: ", inst
	    print "Last rv value: ", rv
	    val = 0
    finally:
	LOCK.release()
    
    return val
