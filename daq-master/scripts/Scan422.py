# 422scan.py
# 2011-05-04 Hans Harhoff Andersen
# Purpose: To do 422 scan automatically.
ARGS = ['StartCav','EndCav','FinishCav','ScanPoints','ScanRepeat','DDSFREQ','DDSAMP']
import Stabilization
import CavityStabilization
import time
import sys
import scipy as sp

def Scan422(filename,dirname,StartCav,EndCav,FinishCav,ScanPoints,ScanRepeat,DDSFREQ,DDSAMP):

# Import functions:
    reload(Stabilization)
    plot=gui_exports['plot']
    purgatory=gui_exports['purgatory']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    ReadUnshelved = f_read['DDS_NBRIGHT']
    ReadAvgBright = f_read['DDS_LASTAVG']
    SetBlueCav  = f_set['MonoLasers_421']
    ReadBlueCav  = f_read['MonoLasers_421']
    SetDDS_FREQ1=f_set['DDS_FREQ1']
    SetDDS_FREQ2=f_set['DDS_FREQ2']
    SetDDS_AMP1=f_set['DDS_AMP1']
    SetDDS_FREQ0=f_set['DDS_FREQ0']
    SetDDS_AMP0=f_set['DDS_AMP0']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    ReadIonPMT = f_read['IonPhotonCounter_COUNT']
    Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
    const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
    CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
    const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
    #### Locking #######
#if BlueLockOn==1:
#       bluelockrv, BlueCav = Stab.BlueLock()
# Set up plotting:
    try:
#  purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.TWODPLOT)  
        purgatory(plot.set_labels, 'BlueCav[DAC2]', 'IonPhotonCounter_COUNTS','<empty>')
    except Exception,e:
        print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when setting up plot'
	print e
    mydb = data.database(filename, dirname, 1, 3, 'BlueCav, IonPhotonCounter_COUNT')
    print "Running 422scan: DDS_Freq=%d, DDS_AMP=%d, StartCav=%.4f, EndCav=%.4f, FinishCav=%.4f"%(DDSFREQ,DDSAMP,StartCav,EndCav,FinishCav)
    bluecavs=sp.linspace(StartCav,EndCav,ScanPoints)
#    OpenDDS('prog/Shelving.pp')

#    SetParameter('us_RedTime',us_RedTime)
#    SetParameter('SCloops',SCloops)
    print "Checking power levels of 422 and 1092 MonoLaser."
    CavStab.MonoLaserLockCheck('421')
    CavStab.MonoLaserLockCheck('1091')
#    CavStab.MonoLaserLockCheck('674') # This laser is not necessary here.

    SetDDS_FREQ1(DDSFREQ)
    SetDDS_AMP1(DDSAMP)
#   Turn of 674 and 422 (Cavity Probe):
    SetDDS_FREQ0(0)
    SetDDS_AMP0(0)
    SetDDS_FREQ2(0)
# Prepare for scan:
    Inttime=300
    lastcounts=0
    try:
        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break
            print "Scan %d"%(i)
            j=0
            while j<len(bluecavs):
                if __main__.STOP_FLAG: break

#          freq=freqs[j]
                bluecav=bluecavs[j]
# SET 422 freq!
                SetBlueCav(bluecav)
                isok=0
                while isok==0:
                    if __main__.STOP_FLAG: break
                    CavStab.MonoLaserLockCheck('421')
                    CavStab.MonoLaserLockCheck('1091')
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
                mydb.add_data_point([bluecav,counts,0.0])
                try:
                    purgatory(plot.add_point,bluecav,counts,0.0)
                    purgatory(plot.repaint)
                except Exception,e:
                    print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when adding plot point'
                    print e
                if counts<lastcounts*0.9 and lastcounts>40000: # Detect whether we crossed resonance and stop in that case to avoid heating the ion.
                    print "Scan crossed S-P resonance at j=%d; breaking!"%(j)
                    print "counts=%d, lastcounts=%d"%(counts,lastcounts)
                    break
                else:
                    lastcounts=counts
                j=j+1
    finally:
        SetBlueCav(FinishCav)
        SetDDS_FREQ1(ReadParameter('F_BlueHi'))
        SetDDS_AMP1(ReadParameter('A_BlueHi'))
    print "Done\n"

def RunScript(dirname,filename,StartCav,EndCav,FinishCav,ScanPoints,ScanRepeat,DDSFREQ,DDSAMP):
    Scan422(dirname,filename,StartCav,EndCav,FinishCav,ScanPoints,ScanRepeat,DDSFREQ,DDSAMP)
