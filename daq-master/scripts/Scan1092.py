# Scan1092.py
# 2011-06-17 Hans Harhoff Andersen
# Purpose: To do 1092 scan automatically.
ARGS = ['StartCav','EndCav','FinishCav','ScanPoints','ScanRepeat']
import Stabilization
import Stabilization
import time
import sys
import scipy as sp

def Scan1092(filename,dirname,StartCav,EndCav,FinishCav,ScanPoints,ScanRepeat):

# Import functions:
    reload(Stabilization)
    plot=gui_exports['plot']
    purgatory=gui_exports['purgatory']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    SetCav1092  = f_set['MonoLasers_1091']
    ReadCav1092  = f_read['MonoLasers_1091']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    ReadIonPMT = f_read['IonPhotonCounter_COUNT']
    Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
    const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
# Set up plotting:
    try:
#  purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.TWODPLOT)  
        purgatory(plot.set_labels, 'Cav1092[DAC2]', 'IonPhotonCounter_COUNTS','<empty>')
    except Exception,e:
        print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when setting up plot'
	print e
    mydb = data.database(filename, dirname, 1, 3, 'Cav1092, IonPhotonCounter_COUNT')
    print "Running Scan1092: StartCav=%.4f, EndCav=%.4f, FinishCav=%.4f"%(StartCav,EndCav,FinishCav)
    Cav1092s=sp.linspace(StartCav,EndCav,ScanPoints)


# Prepare for scan:
    Inttime=300

    try:
        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break
            print "Scan %d"%(i)
            j=0
            while j<len(Cav1092s):
                if __main__.STOP_FLAG: break

                Cav1092=Cav1092s[j]
                SetCav1092(Cav1092)
                isok=0
                while isok==0:
                    if __main__.STOP_FLAG: break
                    try:
                        time.sleep(2.*Inttime/1000)
                        counts=ReadIonPMT()
#                        shelved=ReadUnshelved()
                        if counts=='NA':
                            print "counts=",counts
                        elif counts=='':
                            print "counts=",counts
                        else:
                            isok=1
                    except Exception,e:
                        print time.strftime('%H:%M:%S'),__file__,"Exception occured in from IonPhotonCounter. Trying again!"
                        print e
                        time.sleep(1)
                mydb.add_data_point([Cav1092,counts,0.0])
                try:
                    purgatory(plot.add_point,Cav1092,counts,0.0)
                    purgatory(plot.repaint)
                except Exception,e:
                    print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when adding plot point'
                    print e
                j=j+1
    finally:
        SetCav1092(FinishCav)
    print "Done\n"

def RunScript(dirname,filename,StartCav,EndCav,FinishCav,ScanPoints,ScanRepeat):
    Scan1092(dirname,filename,StartCav,EndCav,FinishCav,ScanPoints,ScanRepeat)
