# SidebandScan.py
# Edited by Hans, 2011-02-25: Added exception handling for when DDS is to slow.
ARGS = ['StarkSecFRQ1', 'StarkSecFRQ2', 'StarkSecFRQ3', 'Width', 'ReadoutDLY', 'ScanPoints', 'ScanRepeat', 'LockOption','SCloops']

import Stabilization
import time
import sys
# Adding directory to path where fitting scripts are stored:
sys.path.append('/home/cavityexp/analysis/')
# Importing hansfit which is used to fit most of the taken data:
import hansfit
reload(hansfit)
def RunScript(filename, dirname, StarkSecFRQ1, StarkSecFRQ2, StarkSecFRQ3, Width, ReadoutDLY, ScanPoints, ScanRepeat, LockOption,SCloops):
    SidebandScan(filename, dirname, StarkSecFRQ1, StarkSecFRQ2, StarkSecFRQ3, Width, ReadoutDLY, ScanPoints, ScanRepeat, LockOption,SCloops)
def SidebandScan(filename, dirname, StarkSecFRQ1, StarkSecFRQ2, StarkSecFRQ3, Width, ReadoutDLY, ScanPoints, ScanRepeat, LockOption,SCloops):

    reload(Stabilization)

    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    f421quiet = f_set['MonoLasers_Quiet421']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    ReadUnshelved = f_read['DDS_NBRIGHT']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    ScanDone = f_set['AudioAlert_scandone']
    LockOption = int(LockOption)
    IonCount = 1

    try:
        Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
        const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
        plotLabels = ['BlueCav', 'CavOffset', 'RedPiTime', 'RedPiTime']
        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        # Locking step
        bluerv, BlueCav = Stab.BlueLock()
        ramseylockrv, CavOffset = Stab.RamseyLock(LockOption, True)
        rabilockrv, RedPiTime = Stab.RabiLock(LockOption, True)

        # set up plotting	
        print "Running..."
        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.DUALTWODPLOT)  
        purgatory(plot.set_labels, 'AOM', 'Shelving Rate', plotLabels[LockOption])
        mydb = data.database(filename, dirname, 1, 10, 'AOMFrq, P[0], P[1], P[2], Scatter, RamseyShelv, RabiShelv, BlueCav, CavOffset, RedPiTime')

        # Perform the experiment
        df = (scipy.array(range(int(ScanPoints))) - (ScanPoints - 1.)/2.)/(ScanPoints - 1)*Width
        aomvals = scipy.unique(scipy.concatenate([df - StarkSecFRQ3, df - StarkSecFRQ2, df - StarkSecFRQ1, df, df + StarkSecFRQ1, df + StarkSecFRQ2, df + StarkSecFRQ3]))
        SetParameter('F_StarkSec1',StarkSecFRQ1)
        SetParameter('F_StarkSec2',StarkSecFRQ2)
        SetParameter('F_StarkSec3',StarkSecFRQ3)
        SetParameter('SCloops',SCloops)
        SetParameter('ms_ReadoutDly', ReadoutDLY)
        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break

            print "Scan %d"%(i)
            for j in range(len(aomvals)):
                if __main__.STOP_FLAG: break
                CavStab.MonoLaserLockCheck('421')
                CavStab.MonoLaserLockCheck('1091')
                CavStab.MonoLaserLockCheck('674')
                CavStab.MonoLaserLockCheck('1033')
                ramseylockrv, CavOffset = Stab.RamseyLock(LockOption, False)
                rabilockrv, RedPiTime = Stab.RabiLock(LockOption, False)

                # Measurement step
#                f421quiet(1)
#                time.sleep(0.1)
                
                aomval = aomvals[j]
                OpenDDS('prog/Shelving.pp')
                
                isok = 0
                while not isok:
                    try:
                        SetParameter('F_RedOn', CavOffset + aomval)
                        isok = 1
                    except Exception, inst:
                        print "[",__file__,"] Error in DDS SetParameter Exception: ", inst
                        sys.stdout.flush()
                        time.sleep(0.5)
                    
                RunDDS()
                # The sleep line here is probably to give the laser time to go into quiet mode.
#                f421quiet(0)
               	# time.sleep(0.1)
                isok = 0
                while not isok:
                    try:
                        sciencerv = ReadUnshelved(hist=True)
                        if not len(sciencerv)<2:
                            isok = 1
                        else:
                            print "[",__file__,time.asctime(),"] Empty value in sciencerv? = ",sciencerv
                            print "[",__file__,"] Retrying"
                            sys.stdout.flush()
                            time.sleep(0.5)
                    except Exception, inst:
                        print "[",__file__, time.asctime(),"] Error in ReadUnshelved Exception: ", inst
                        sys.stdout.flush()
                        time.sleep(0.5)

                if ((IonCount == 1) and (sciencerv[2] > 10)):
                    IonCount = 2
                    
                if (IonCount == 2):
                    plotrv = sciencerv[1]
                else:
                    plotrv = sciencerv[0]
                    
                bluerv, BlueCav = Stab.BlueLockNoDDSRun()                

                mydb.add_data_point([aomval, sciencerv[0], sciencerv[1], sciencerv[2], bluerv, ramseylockrv, rabilockrv, BlueCav, CavOffset, RedPiTime], int(i*len(aomvals) + j))
                purgatory(plot.add_point, aomval, plotrv, eval(plotLabels[LockOption]) )
                purgatory(plot.repaint)

        SetParameter('ms_ReadoutDly', 0)
        secularfrequencies=hansfit.fitSidebandScan(dirname,filename)
        print secularfrequencies
        ScanDone()
    except Exception,e:
        print "[",__file__,time.asctime(),"] Exception occurred in RunScript:", e
        traceback.print_exc()
