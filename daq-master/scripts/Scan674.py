# CavityResonanceScan.py
# 2011-04-20 Hans Harhoff Andersen
# Purpose: To see Cavity spectrum. Replaces manual OneDScan.
ARGS = ['StartF','EndF','ScanPoints','ScanRepeat','us_RedTime','SCloops','BlueLockOn']
import Stabilization
import CavityStabilization
import time
import sys
import scipy as sp

def RunScript(filename,dirname,StartF,EndF,ScanPoints,ScanRepeat,us_RedTime,SCloops,BlueLockOn):
    Scan674(filename,dirname,StartF,EndF,ScanPoints,ScanRepeat,us_RedTime,SCloops,BlueLockOn)

def Scan674(filename,dirname,StartF,EndF,ScanPoints,ScanRepeat,us_RedTime,SCloops,BlueLockOn):
# Import functions:
    reload(Stabilization)
    reload(CavityStabilization)
    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    ReadUnshelved = f_read['DDS_NBRIGHT']
    ReadAvgBright = f_read['DDS_LASTAVG']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    ScanDone = f_set['AudioAlert_scandone']
    Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
    const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
    CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
    const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
    print "Checking power levels of 422 and 1092 MonoLaser."
    CavStab.MonoLaserLockCheck('421')
    CavStab.MonoLaserLockCheck('1091')
    CavStab.MonoLaserLockCheck('674')
    #### Locking #######
    if BlueLockOn==1:
        bluelockrv, BlueCav = Stab.BlueLock()
# Set up plotting:
    try:
        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.TWODPLOT)  
        purgatory(plot.set_labels, 'DDS0 FREQ [MHz]', 'Shelving rate','<empty>')
    except Exception,e:
        print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when setting up plot'
	print e
    mydb = data.database(filename, dirname, 1, 3, 'DDS FREQ0, Absorption')
    print "Running 674scan:"
    freqs=sp.linspace(StartF,EndF,ScanPoints)
    OpenDDS('prog/Shelving.pp')

    SetParameter('us_RedTime',us_RedTime)
    SetParameter('SCloops',SCloops)

    for i in range(int(ScanRepeat)):
        if __main__.STOP_FLAG: break
        print "Scan %d"%(i)
        j=0
        while j<len(freqs):
            if __main__.STOP_FLAG: break

            freq=freqs[j]
            SetParameter('F_RedOn', freq)
            isok=0
            while isok==0:
                if __main__.STOP_FLAG: break
                try:
                    time.sleep(0.1)
                    RunDDS()
                    time.sleep(0.1)
                    shelved=ReadUnshelved()
                    if shelved=='NA':
                        print "Shelved=",shelved
                    elif shelved=='':
                        print "Shelved=",shelved
                    else:
                        isok=1
                except Exception,e:
                    print time.strftime('%H:%M:%S'),__file__,"Exception occured in ReadUnshelved(). Trying again!"
                    print e
                    time.sleep(1)
            bluelockrv, BlueCav = Stab.BlueLockNoDDSRun()
            mydb.add_data_point([freq,shelved,BlueCav])
            try:
                purgatory(plot.add_point,freq,shelved,BlueCav)
                purgatory(plot.repaint)
            except Exception,e:
                print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when adding plot point'
                print e
            j=j+1
    print "Done\n"
    ScanDone()
