# IRlockin.py
# sxwang
# Nov 2, 2010
#

import threading
import socket
import numarray, numpy
import Stabilization

ARGS = ['Ntrials', 'ms_shutter']

def RunScript(filename, dirname, Ntrials, ms_shutter):
    
    reload(Stabilization)

    # Functions
    ######################

#    PMTread = f_read['PhotoCounter_COUNT']

    f422read = f_read['MonoLasers_421']
    f422set = f_set['MonoLasers_421']

    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    ReadUnshelved = f_read['DDS_NBRIGHT']
    ReadAvgBright = f_read['DDS_LASTAVG']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    LockOption = 0
    IonCount = 1

    # Take data
    ######################

#    saved_countloop = ReadParameter('countloop')

    SetParameter('countloop', int(ms_shutter))
    
    bin = range(100)
    counts = numarray.zeros(100, 'Int64')
    
    trial = 0
    while trial < Ntrials:

        # Science step
        
        OpenDDS('prog/IRlockin.pp')
        RunDDS()
        readDDSmemory()
        
        # take data

        time.sleep(0.5)
        
        counts = counts + readDDSmemory()[bin]
            
        print 'trial = %i' % (trial)

        x = range(0,100,2)
        y = range(1,101,2)
        ioncounts = numpy.average(counts[x])
        bkgcounts = numpy.average(counts[y])
	delta = ioncounts-bkgcounts

	ionstd = numpy.std(counts[x])
	bkgstd = numpy.std(counts[y])

#        print 'total mean signal = %i counts/%ims, bkgnd = %i counts/%ims' % ( numarray.sum(counts[x])/(trial+1), ShutterPeriod*50, numarray.sum(counts[y])/(trial+1), ShutterPeriod*50)
	print 'ms_shutter: %ims' % ms_shutter
        print 'ir on :  mu = %ic (%icps), std = %ic (%icps)' % ( ioncounts, ioncounts/(ms_shutter*1e-3), ionstd, ionstd/(ms_shutter*1e-3))
        print 'ir off:  mu = %ic (%icps), std = %ic (%icps)' % ( bkgcounts, bkgcounts/(ms_shutter*1e-3), bkgstd, bkgstd/(ms_shutter*1e-3))
        print 'ion   :  mu = %ic (%icps)' %  (delta, delta/(ms_shutter*1e-3))
	plotIT(bin, counts/(trial+1))    
#        plotIT(bin, counts/(trial+1)/(ms_shutter*1e-3))
        trial = trial + 1

        # Abort?
        if __main__.STOP_FLAG: break
    
    # Store results
    ######################
    
    mydb = data.database(filename, dirname, 1, 2, 'trials = %i, counts' % (trial))
    for i in bin:
        mydb.add_data_point([bin[i], counts[i]], i)

#    SetParameter('countloop', saved_countloop)

    return



def readDDSmemory():
    
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
            if list[0] == "RESULT:":
                val = numarray.zeros(100, 'Int64')
                for i in range(len(list) - 1):
                    val[i] = int(list[i + 1])
            else: val = 0.0
        except Exception, inst:
            print "Exception occured in reading from DDS\n Exception: ", inst
            print "Last rv value: ", rv
            val = 0.0
    finally:
        LOCK.release()
    
    return val



def plotIT(x, y):
    
    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    
    purgatory(plot.clear)
    purgatory(plot.set_labels, 'Bin', 'Counts', '')
    purgatory(plot.set_mode, pyextfigure.TWODPLOT)
    
    for i in range(len(x)):
        purgatory(plot.add_point, x[i], y[i], 0.0)
    
    purgatory(plot.repaint)
    
    return


