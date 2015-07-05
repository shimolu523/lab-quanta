# DopplerCoolRabi.py
# 2011-03-23 Hans Harhoff Andersen
# Copied from CavityCoolingRabi.pyi to do temperature measurements after DopplerCooling.
# Edited by Hans, 2011-02-25: Added exception handling for when DDS is to slow.
ARGS = ['StartT', 'EndT','ReadoutDF', 'ScanPoints', 'ScanRepeat', 'LockOption','StabCount']

import Stabilization
import CavityStabilization
# ReadoutDF is the readout detuning e.g. the red or blue sideband.
def RunScript(filename, dirname, StartT, EndT, ReadoutDF, ScanPoints, ScanRepeat, LockOption,StabCount):
    DopplerCoolRabi(filename, dirname, StartT, EndT, ReadoutDF, ScanPoints, ScanRepeat, LockOption,StabCount)

def DopplerCoolRabi(filename, dirname, StartT, EndT, ReadoutDF, ScanPoints, ScanRepeat, LockOption,StabCount):
    
    reload(CavityStabilization)
    reload(Stabilization)

    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    ReadUnshelved = f_read['DDS_NBRIGHT']
    ReadAvgBright = f_read['DDS_LASTAVG']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    LockOption = int(LockOption)
  #  CavFreqSet = f_set['DDS_FREQ2']
    f421quiet = f_set['MonoLasers_Quiet421']
    IonCount = 1
    try:
        saved_redtime = ReadParameter('us_RedTime')
                
        ##################################################
        # Set up locks
        ##################################################

        Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
        const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')

        bluelockrv, BlueCav = Stab.BlueLockCounts(StabCount)
        ramseylockrv, RedCenter = Stab.RamseyLock(LockOption, True)
        rabilockrv, RedPiTime = Stab.RabiLock(LockOption, True)
        
        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        
        ##################################################
        # Set up plotting
        ##################################################
        plotLabel = ['BlueCav', 'RedCenter', 'RedPiTime', 'RedCenter'][LockOption]

        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.DUALTWODPLOT)  
        purgatory(plot.set_labels, 'Rabi pulse length [us]', 'Shelving rate', plotLabel)
        mydb = data.database(filename, dirname, 1, 10, 'Rabi pulse length [us], P[0], P[1], P[2], bluelockrv, BlueCav, ramseylockrv, RedCenter, rabilockrv, RedPiTime')

        ##################################################
        # Perform the experiment
        ##################################################
        print "Running DopplerCoolRabi.py..."
        
        timestep = (1.0*EndT - StartT)/(ScanPoints - 1)
	# Looping over scans i.e. how many times should we measure the same thing.
        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break

            print "Scan %d"%(i)
            j=0
	# Looping over pulse lengths:
            while j <= int(ScanPoints):
                if __main__.STOP_FLAG: break
                
                ##################################################
                # Lock step
                ##################################################
                
                ramseylockrv, RedCenter = Stab.RamseyLock(LockOption, False)
                rabilockrv, RedPiTime = Stab.RabiLock(LockOption, False)
                CavLockCheckOn=0                
                if CavLockCheckOn==1:
                    CavStab.CavLockCheck()
                ##################################################
                # Measurement step
                ##################################################
                f421quiet(1)
                time.sleep(0.05) # FIXME: Did this break everything? was 0.2.
                
                timeval = StartT + j * timestep;
                OpenDDS('prog/DopplerCoolShelving.pp')
#                SetParameter('F_CavityOn', ReadParameter('F_CavityCenter') + CavityOnDF)
		# To measure temperature we should compare red and blue sideband i.e. do rabi floppings on both.
                SetParameter('F_RedOn', RedCenter + ReadoutDF)
                SetParameter('us_RedTime',timeval)
	# Run DopplerCoolShelving.pp and get a shelving rate:
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
 #### Weird code for the case that there is more than one ion. Should be safe to ignore?
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
                bluerv, BlueCav = Stab.BlueLockNoDDSRunCounts(StabCount)  

                if not len(sciencerv)<3:			 #CavLockRead() > CavLockThreshold:
                    ##################################################
                    # Plot and save step
                    ##################################################
		    datapoint=[timeval, sciencerv[0], sciencerv[1], sciencerv[2], bluelockrv, BlueCav, ramseylockrv, RedCenter, rabilockrv, RedPiTime]
		    datapoint_index=int(i*ScanPoints+j)
                    mydb.add_data_point(datapoint, datapoint_index)
                    purgatory(plot.add_point, timeval, plotrv, eval(plotLabel))
                    purgatory(plot.repaint)
                    j=j+1
                else:
			print "Something wrong with sciencerv:",sciencerv
        SetParameter('us_RedTime',saved_redtime)
	
    except Exception,e:
        print __file__,"Exception occurred in RunScript:", e
        traceback.print_exc()
