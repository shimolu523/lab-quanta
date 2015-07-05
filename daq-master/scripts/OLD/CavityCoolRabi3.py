# CavityCoolRabi3.py
# Edited by Hans, 2011-02-25: Added exception handling for when DDS is to slow.
ARGS = ['StartT', 'EndT', 'CavityOnDF', 'ReadoutDF', 'ScanPoints', 'ScanRepeat', 'LockOption', 'CavLockOn', 'ProbeLockOn', 'ProbeSet', 'IonLockOn', 'IonSet']

import Stabilization
import CavityStabilization

def RunScript(filename, dirname, StartT, EndT, CavityOnDF, ReadoutDF, ScanPoints, ScanRepeat, LockOption, CavLockOn, ProbeLockOn, ProbeSet, IonLockOn, IonSet):
    CavityCoolRabi2(filename, dirname, StartT, EndT, CavityOnDF, ReadoutDF, ScanPoints, ScanRepeat, LockOption, CavLockOn, ProbeLockOn, ProbeSet, IonLockOn, IonSet)

def CavityCoolRabi3(filename, dirname, StartT, EndT, CavityOnDF, ReadoutDF, ScanPoints, ScanRepeat, LockOption, CavLockOn, ProbeLockOn, ProbeSet, IonLockOn, IonSet):
    # IonSet = 0 locks to the cavity standing wave antinode
    # IonSet = 1 locks halfway between the node and the antinode
    # IonSet = 2 locks to the node

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
    LockOption = int(LockOption)
    CavFreqSet = f_set['DDS_FREQ2']
    f421quiet = f_set['MonoLasers_Quiet421']
    CavBeamSet = f_set['3631A_botleft_+25V']
    ProbePowerRead = f_read['3631A_leftmost_+25V']
    ProbePowerSet = f_set['3631A_leftmost_+25V']
    IonCount = 1
    CavLockRead = f_read['DMM_top_V']
    CavLockThreshold = 1.0
    
    beam0 = 24.
    beam90 = 0.
    maxProbePower = 15.

    try:
        saved_redtime = ReadParameter('us_RedTime')
                
        ##################################################
        # Set up locks
        ##################################################
        CavFreqSet(0)

        Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
        const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')

        bluelockrv, BlueCav = Stab.BlueLock()
        ramseylockrv, RedCenter = Stab.RamseyLock(LockOption, True)
        rabilockrv, RedPiTime = Stab.RabiLock(LockOption, True)
        
        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        
        cavlockrv, CavCenter = CavStab.CavLock(CavLockOn, True)
        probelockrv, ProbePower = CavStab.ProbeLock(ProbeLockOn, ProbeSet, True)
        ionlockrv, IonPos = CavStab.IonLock(IonLockOn, IonSet, True)
        
        ##################################################
        # Set up plotting
        ##################################################
        if IonLockOn > 0:
            plotLabel = 'IonPos'
        elif CavLockOn > 0:
            plotLabel = 'CavCenter'
        elif ProbeLockOn > 0:
            plotLabel = 'ProbePower'
        else:
            plotLabel = ['BlueCav', 'RedCenter', 'RedPiTime', 'RedCenter'][LockOption]

        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.DUALTWODPLOT)  
        purgatory(plot.set_labels, 'Rabi pulse length [us]', 'Shelving rate', plotLabel)
        mydb = data.database(filename, dirname, 1, 16, 'Rabi pulse length [us], P[0], P[1], P[2], bluelockrv, BlueCav, ramseylockrv, RedCenter, rabilockrv, RedPiTime, cavlockrv, CavCenter, probelockrv, ProbePower, ionlockrv, IonPos')

        ##################################################
        # Perform the experiment
        ##################################################
        print "Running..."
        
        timestep = (1.0*EndT - StartT)/(ScanPoints - 1)

        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break

            print "Scan %d"%(i)
            j=0
            while j <= int(ScanPoints):
                if __main__.STOP_FLAG: break
                
                #checking if cavity is locked before measurement: 
                #if locked continue with measurement, if not, wait for it 
                #to be relocked and then wait 5sec before proceeding with measurement
                CavLockOk = 0
                CavLockPast = 1
                while CavLockOk == 0:
                    if CavLockRead() > CavLockThreshold:
                        CavLockOk = 1
                        if CavLockPast == 0:
                            print "resuming measurement in 5 sec..."
                            time.sleep(1)
                            print "resuming measurement in 4 sec..."
                            time.sleep(1)
                            print "resuming measurement in 3 sec..."
                            time.sleep(1)
                            print "resuming measurement in 2 sec..."
                            time.sleep(1)
                            print "resuming measurement in 1 sec..."
                            time.sleep(1)
                            print "Cavity relocked"
                        else:
                            print "Cavity lock ok"
                    else:   
                        print "Cavity unlocked!"
                        CavLockPast=0
                        
                ##################################################
                # Lock step
                ##################################################
                
                ramseylockrv, RedCenter = Stab.RamseyLock(LockOption, False)
                rabilockrv, RedPiTime = Stab.RabiLock(LockOption, False)
                    
                cavlockrv, CavCenter = CavStab.CavLock(CavLockOn, False)
                probelockrv, ProbePower = CavStab.ProbeLock(ProbeLockOn, ProbeSet, False)
                ionlockrv, IonPos = CavStab.IonLock(IonLockOn, IonSet, False)

                ##################################################
                # Measurement step
                ##################################################
                CavBeamSet(beam90)
                ProbePowerSet(ProbePower)
                f421quiet(1)
                time.sleep(0.2)
                
                timeval = StartT + j * timestep;
                OpenDDS('prog/CavityCoolShelving.pp')
                SetParameter('F_CavityOn', ReadParameter('F_CavityCenter') + CavityOnDF)
                SetParameter('F_RedOn', RedCenter + ReadoutDF)
                SetParameter('us_RedTime',timeval)
                RunDDS()
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
                            
                f421quiet(0)
                
                ##################################################
                # Lock 422 step
                ##################################################
                bluerv, BlueCav = Stab.BlueLockNoDDSRun()  

                #checking if cavity is still locked. If so, plot and save. 
                #Otherwise, repeat point
                if CavLockRead() > CavLockThreshold:
                    ##################################################
                    # Plot and save step
                    ##################################################
                    mydb.add_data_point([timeval, sciencerv[0], sciencerv[1], sciencerv[2], bluelockrv, BlueCav, ramseylockrv, RedCenter, rabilockrv, RedPiTime, cavlockrv, CavCenter, probelockrv, ProbePower, ionlockrv, IonPos], int(i*ScanPoints + j))
                    purgatory(plot.add_point, timeval, plotrv, eval(plotLabel))
                    purgatory(plot.repaint)
                    j=j+1
                else:
                    print "cavity unlocked - discarding and repeating measurement"
        SetParameter('us_RedTime',saved_redtime)
	
    except Exception,e:
        print "Exception occurred in RunScript:", e
        traceback.print_exc()
