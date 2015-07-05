# CavityStandingWaveScan3.py
# Edited by Hans, 2011-02-26: Trying to fix DDS time out errors when calling CavFreq(0). Also trying to figure out a way to make the cavity lock more stable.
ARGS = ['Width', 'ScanPoints', 'ScanRepeat', 'ProbePower', 'BlueLockOn', 'CavLockOn', 'IonLockOn', 'IonSet','SBcool']

import CavityStabilization
import time

def RunScript(filename, dirname, Width, ScanPoints, ScanRepeat, ProbePower, BlueLockOn, CavLockOn, IonLockOn, IonSet,SBcool):
    
    Width = abs(Width)
    if Width > 19:
        print "Width > 19 V is out of range."
        return

    # IonSet = 0 locks to the cavity standing wave antinode
    # IonSet = 1 locks halfway between the node and the antinode
    # IonSet = 2 locks to the node
    
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
        # This one is know to raise errors:
	isok = 0
	while not isok:
		try:
			CavFreqSet(0)
			isok = 1
		except Exception, e:
			print "[",__file__,time.asctime(),"] A time out error occured while calling CavFreqSet(0):",e
			sys.stdout.flush()
			time.sleep(0.5)
			print "Retrying..."
		

	if not(IonLockOn):
            IonPosSet(0)
            
        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        
        bluelockrv, BlueCav = CavStab.BlueLock(BlueLockOn, True)
        cavlockrv, CavCenter = CavStab.CavLock(CavLockOn, True)
        ionlockrv, IonPos = CavStab.IonLock(IonLockOn, IonSet, True)

        ##################################################
        # Set up plotting
        ##################################################
        if IonLockOn > 0:
            plotLabel = 'IonPos'
        elif CavLockOn > 0:
            plotLabel = 'CavCenter'
        else:
            plotLabel = 'BlueCav'
        
        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.DUALTWODPLOT)  
        purgatory(plot.set_labels, 'Ion position [V]', 'Scatter into cavity [photons]', plotLabel)
        mydb = data.database(filename, dirname, 1, 8, 'Ion position [V], Scatter into cavity [photons], bluelockrv, BlueCav, cavlockrv, CavCenter, ionlockrv, IonPos')

        ##################################################
        # Perform the experiment
        ##################################################
        print "Running CavityStandingWaveScan3: The experiment..."
        
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
                ionlockrv, IonPos = CavStab.IonLock(IonLockOn, IonSet, False)

                if __main__.STOP_FLAG:
                    break
                    
                ##################################################
                # Measurement step
                ##################################################
                IonPosition = IonPositionVals[j]
# The code below used to turn on the CAVPROBEDDS. Now we do this in the pp script! Hans, 2011-04-10
        	# This one is know to raise errors:
#		isok = 0
#		while not isok:
#			try:
#				CavFreqSet(ReadParameter('F_CavityCenter'))
#				isok = 1
#			except Exception, e:
#				print "[",__file__,time.asctime(),"] A time out error occured while calling CavFreqSet:",e
#				sys.stdout.flush()
#				time.sleep(0.5)
#				print "Retrying..."
		
                
                IonPosSet(IonPos + IonPosition)
                
                CavBeamSet(beam90)
                ProbePowerSet(ProbePower)
                f421quiet(1)
                time.sleep(0.2)
                
                if SBcool==1:
                    OpenDDS('prog/ReadCavityPMT_SBC.pp')
		else:
                    OpenDDS('prog/ReadCavityPMT.pp')
                CavityScatter = RunDDSandReadTotal()

                IonPosSet(IonPos)
# 
# The code below used to turn off the CAVPROBEDDS. Now we do this in the pp script! Hans, 2011-04-10
        	# This one is know to raise errors:
#		isok = 0
#		while not isok:
#			try:
#				CavFreqSet(0)
#				isok = 1
#			except Exception, e:
#				print "[",__file__,time.asctime(),"] A time out error occured while calling CavFreqSet(0):",e
#				sys.stdout.flush()
#				time.sleep(0.5)
#				print "Retrying..."
		
                f421quiet(0)

                mydb.add_data_point([IonPosition, CavityScatter, bluelockrv, BlueCav, cavlockrv, CavCenter, ionlockrv, IonPos], int(i*len(IonPositionVals) + j))
                purgatory(plot.add_point, IonPosition, CavityScatter, eval(plotLabel))
                purgatory(plot.repaint)

                print "IonPosition = %f V, CavityScatter = %f photons"%(IonPosition, CavityScatter)

    except Exception,e:
        print "[",__FILe__,time.asctime(),"]Exception occurred in RunScript:", e
        traceback.print_exc()
