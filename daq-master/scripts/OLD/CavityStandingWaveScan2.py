ARGS = ['Width', 'ScanPoints', 'ScanRepeat', 'ProbeLockOn', 'ProbeSet', 'BlueLockOn', 'CavLockOn', 'IonLockOn', 'IonSet']

import Stabilization
import CavityStabilization

def RunScript(filename, dirname, Width, ScanPoints, ScanRepeat, ProbeLockOn, ProbeSet, BlueLockOn, CavLockOn, IonLockOn, IonSet):
    
    Width = abs(Width)
    if Width > 19:
        print "Width > 19 V is out of range."
        return

    # IonSet = 0 locks to the cavity standing wave antinode
    # IonSet = 1 locks halfway between the node and the antinode
    # IonSet = 2 locks to the node
    
    reload(Stabilization)
    reload(CavityStabilization)
    
    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDSandReadTotal = f_read['DDS_RUNNTOTAL']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    CavFreqSet = f_set['DDS_FREQ2']
    f421quiet = f_set['MonoLasers_Quiet421']
    CavBeamSet = f_set['3631A_botleft_+25V']
    ProbePowerRead = f_read['3631A_leftmost_+25V']
    ProbePowerSet = f_set['3631A_leftmost_+25V']
    IonPosSet = f_set['3631A_topright_-25V']
    
    beam0 = 24.
    beam90 = 0.
    maxProbePower = 15.

    try:
        ##################################################
        # Set up locks
        ##################################################
        CavFreqSet(0)
        if not(IonLockOn):
            IonPosSet(0)
            
        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        
        bluelockrv, BlueCav = CavStab.BlueLock(BlueLockOn, True)
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
            plotLabel = 'BlueCav'
        
        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.DUALTWODPLOT)  
        purgatory(plot.set_labels, 'Ion position [V]', 'Scatter into cavity [photons]', plotLabel)
        mydb = data.database(filename, dirname, 1, 8, 'Ion position [V], Scatter into cavity [photons], bluelockrv, BlueCav, cavlockrv, CavCenter, ionlockrv, IonPos')

        ##################################################
        # Perform the experiment
        ##################################################
        print "Running ..."
        
        IonPositionVals = (scipy.array(range(int(ScanPoints))) - (ScanPoints - 1.))/(ScanPoints - 1.)*Width
        
        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break

            print "Scan %d"%(i)
            for j in range(len(IonPositionVals)):
                if __main__.STOP_FLAG: break

                ##################################################
                # Lock step
                ##################################################
                bluelockrv, BlueCav = CavStab.BlueLock(BlueLockOn, False)
                cavlockrv, CavCenter = CavStab.CavLock(CavLockOn, False)
                probelockrv, ProbePower = CavStab.ProbeLock(ProbeLockOn, ProbeSet, False)
                ionlockrv, IonPos = CavStab.IonLock(IonLockOn, IonSet, False)

                if __main__.STOP_FLAG:
                    break
                    
                ##################################################
                # Measurement step
                ##################################################
                IonPosition = IonPositionVals[j]
                CavFreqSet(ReadParameter('F_CavityCenter'))
                IonPosSet(IonPos + IonPosition)
                
                CavBeamSet(beam90)
                ProbePowerSet(ProbePower)
                f421quiet(1)
                time.sleep(0.2)
                
                OpenDDS('prog/ReadCavityPMT.pp')
                CavityScatter = RunDDSandReadTotal()

                IonPosSet(IonPos)
                CavFreqSet(0)
                f421quiet(0)

                mydb.add_data_point([IonPosition, CavityScatter, bluelockrv, BlueCav, cavlockrv, CavCenter, probelockrv, ProbePower, ionlockrv, IonPos], int(i*len(IonPositionVals) + j))
                purgatory(plot.add_point, IonPosition, CavityScatter, eval(plotLabel))
                purgatory(plot.repaint)

                print "IonPosition = %f V, CavityScatter = %f photons"%(IonPosition, CavityScatter)

    except Exception,e:
        print "Exception occurred in RunScript:", e
        traceback.print_exc()
