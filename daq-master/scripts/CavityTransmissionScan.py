ARGS = ['Width', 'ScanPoints', 'ScanRepeat', 'ProbePower', 'WithSC', 'LockOption', 'BlueLockOn', 'CavLockOn', 'IonLockOn', 'IonSet']

import scipy
import Stabilization
import CavityStabilization
import ReadDDSmemory

def RunScript(filename, dirname, Width, ScanPoints, ScanRepeat, ProbePower, WithSC, LockOption, BlueLockOn, CavLockOn, IonLockOn, IonSet):

    # IonSet = 0 locks to the cavity standing wave antinode
    # IonSet = 1 locks halfway between the node and the antinode
    # IonSet = 2 locks to the node
    
    reload(Stabilization)
    reload(CavityStabilization)
    reload(ReadDDSmemory)
    
    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    ReadParameter  = f_read['DDS_PARAM']
    SetParameter  = f_set['DDS_PARAM']
    CavFreqSet = f_set['DDS_FREQ2']
    ReadCavPMT = f_read['CavityPhotonCounter_COUNT']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    RunDDSandReadTotal = f_read['DDS_RUNNTOTAL']
    f421quiet = f_set['MonoLasers_Quiet421']
    CavBeamRead = f_read['3631A_botleft_+25V']
    CavBeamSet = f_set['3631A_botleft_+25V']
    ProbePowerRead = f_read['3631A_leftmost_+25V']
    ProbePowerSet = f_set['3631A_leftmost_+25V']
    beam0 = 24.
    beam90 = 0.

    try:
        ##################################################
        # Set up locks
        ##################################################
        CavFreqSet(0)
        
        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        
        bluelockrv, BlueCav = CavStab.BlueLock(BlueLockOn, True)
        cavlockrv, CavCenter = CavStab.CavLock(CavLockOn, True)
        ionlockrv, IonPos = CavStab.IonLock(IonLockOn, IonSet, True)
        
        if WithSC:
            LockOption = int(LockOption)
            Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
            const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
            ramseylockrv, RedCenter = Stab.RamseyLock(LockOption, True)

        ##################################################
        # Set up plotting
        ##################################################
        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.DUALTWODPLOT)  
        purgatory(plot.set_labels, 'Frequency offset [MHz]', 'Average cavity transmission [counts/s]', 'Differential cavity transmission [counts/s]')
        mydb = data.database(filename, dirname, 1, 10, 'Frequency offset [MHz], Cavity transmission due to lock [counts/s], Cavity transmission at IonPos1 [counts/s], Cavity transmission at IonPos2 [counts/s], bluelockrv, BlueCav, cavlockrv, CavCenter, ionlockrv, IonPos')

        ##################################################
        # Perform the experiment
        ##################################################
        print "Running ..."
        
        FreqOffsetVals = (scipy.array(range(int(ScanPoints))) - (ScanPoints - 1.)/2.)/(ScanPoints - 1)*Width
        
        k = 0.
        DiffCavTransMean = 0.
        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break

            print "Scan %d"%(i)
            for j in range(len(FreqOffsetVals)):
                if __main__.STOP_FLAG: break
                
                k = k + 1.

                ##################################################
                # Lock step
                ##################################################
                bluelockrv, BlueCav = CavStab.BlueLock(BlueLockOn, False)
                cavlockrv, CavCenter = CavStab.CavLock(CavLockOn, False)
                ionlockrv, IonPos = CavStab.IonLock(IonLockOn, IonSet, False)
                
                if WithSC:
                    ramseylockrv, RedCenter = Stab.RamseyLock(LockOption, False)

                if __main__.STOP_FLAG:
                    break
                    
                ##################################################
                # Measurement step
                ##################################################
                CavBeamSet(beam0)
                ProbePowerSet(ProbePower)
                f421quiet(1)
                time.sleep(0.2)
                
                FreqOffset = FreqOffsetVals[j]
                SetParameter('F_CavityOn', ReadParameter('F_CavityCenter') + FreqOffset)
                
                if WithSC:
                    OpenDDS('prog/CavityTransmissionScan_withSC.pp')
                else:
                    OpenDDS('prog/CavityTransmissionScan.pp')
                RunDDS()
                DDSmemory = ReadDDSmemory.ReadDDSmemory()
                CavityTransmission0 = DDSmemory[0]
                CavityTransmission1 = DDSmemory[1]
                CavityTransmission2 = DDSmemory[2]

                CavFreqSet(0)
                f421quiet(0)
                time.sleep(0.2)
                
                mydb.add_data_point([FreqOffset, CavityTransmission0, CavityTransmission1, CavityTransmission2, bluelockrv, BlueCav, cavlockrv, CavCenter, ionlockrv, IonPos], int(i*len(FreqOffsetVals) + j))
                purgatory(plot.add_point, FreqOffset, 0.5*(CavityTransmission1 + CavityTransmission2) - CavityTransmission0, CavityTransmission2 - CavityTransmission1)
                purgatory(plot.repaint)
                
                DiffCavTransMean = DiffCavTransMean*(k - 1.)/k + (CavityTransmission2 - CavityTransmission1)/k
                print "mean(Differential cavity transmission) = %f counts/s"%(DiffCavTransMean)

    except Exception,e:
        print "Exception occurred in RunScript:", e
        traceback.print_exc()