# CavityStandingWaveScan_0deg.py
# Forked by Hans on 2011-06-22 to do Cavity Standing Wave Scans with 0 degree beam.
# Edited by Hans on 2011-06-23 to detect using the IonPMT.
ARGS = ['StartV', 'EndV', 'ScanPoints', 'ScanRepeat','ProbeLockOn', 'ProbeSet', 'BlueLockOn', 'CavLockOn', 'IonLockOn', 'IonSet','SBcool']

import CavityStabilization
import time

def RunScript(filename, dirname,StartV, EndV, ScanPoints, ScanRepeat,ProbeLockOn,ProbeSet, BlueLockOn, CavLockOn, IonLockOn, IonSet,SBcool):
    CavityStandingWaveScan_0deg(filename, dirname,StartV, EndV, ScanPoints, ScanRepeat,ProbeLockOn,ProbeSet, BlueLockOn, CavLockOn, IonLockOn, IonSet,SBcool)
def CavityStandingWaveScan_0deg(filename, dirname,StartV, EndV, ScanPoints, ScanRepeat,ProbeLockOn,ProbeSet, BlueLockOn, CavLockOn, IonLockOn, IonSet,SBcool):
    StartV=abs(StartV)
    EndV=abs(EndV)
    if StartV>19:
	print "V>19 is out of range"    
        return
    if EndV>19:
        print "V>19 is out of range"
        return
    #Width = abs(Width)
    #if Width > 19:
     #   print "Width > 19 V is out of range."
      #  return
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
    ScanDone = f_set['AudioAlert_scandone']
    
    beam0 = 24.
    beam90 = 0.
#   maxProbePower = 10. # This doesn't do anything?

    try:
        ##################################################
        # Set up locks
        ##################################################
        # This one is known to raise errors:
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
        CavStab.CavLockCheck()
        cavlockrv, CavCenter = CavStab.CavLock(CavLockOn, True)
        probelockrv,ProbePower = CavStab.ProbeLock_0deg(ProbeLockOn,ProbeSet,True)
        ionlockrv, IonPos = CavStab.IonLock_0deg(IonLockOn, IonSet, True)
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
        purgatory(plot.set_labels, 'Ion position [V]', 'Scatter into IonPMT [photons]', plotLabel)
        mydb = data.database(filename, dirname, 1, 8, 'Ion position [V], Scatter into IonPMT [photons], bluelockrv, BlueCav, cavlockrv, CavCenter, ionlockrv, IonPos')

        ##################################################
        # Perform the experiment
        ##################################################
        print "Running CavityStandingWaveScan_0deg: The experiment..."
        
#        IonPositionVals = (scipy.array(range(int(ScanPoints))) - (ScanPoints - 1.))/(ScanPoints - 1.)*Width
        IonPositionVals = -(scipy.linspace(StartV,EndV,int(ScanPoints)))        

        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break

            print "Scan %d"%(i)
            j=0
            #for j in range(len(IonPositionVals)):
            while j<len(IonPositionVals):
                if __main__.STOP_FLAG: break
                timeinital=time.time()
                ##################################################
                # Lock step
                ##################################################
                # This line does not change the Blue DDS frequency it only reads the IonPMT level:
                bluelockrv, BlueCav = CavStab.BlueLock(BlueLockOn, False)
                cavlockrv, CavCenter = CavStab.CavLock(CavLockOn, False)
                ionlockrv, IonPos = CavStab.IonLock_0deg(IonLockOn, IonSet, False)
                probelockrv,ProbePower = CavStab.ProbeLock_0deg(ProbeLockOn,ProbeSet,False)
                CavStab.CavLockCheck()
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
#
# 	
            #   We need to add a line that sets F_CavityOn to F_CavityCenter
                SetParameter('F_CavityOn',ReadParameter('F_CavityCenter'))
                IonPosSet(IonPos + IonPosition)
                
#                CavBeamSet(beam90)
                CavBeamSet(beam0)
                ProbePowerSet(ProbePower)
                
                
                f421quiet(1)
                time.sleep(0.2)
                OpenDDS('prog/ReadIonPMT.pp')
#
#                if SBcool==1:
#                    OpenDDS('prog/ReadCavityPMT_SBC.pp')
#		else:
#                    OpenDDS('prog/ReadCavityPMT.pp')
                try:
                    IonScatter = RunDDSandReadTotal() # This is NOT counts per second! It's counts per (US_COUNTTIME*100*N_LOOPS) from the .pp script.
                except Exception,e:
                    time.strftime('%H:%M:%S'),__file__,'Exception occured while trying to read Ion scatter. Trying again.'
                    IonScatter = RunDDSandReadTotal()
                f421quiet(0)
                IonPosSet(IonPos)
                if CavStab.CavLockCheck():
                    mydb.add_data_point([IonPosition, IonScatter, bluelockrv, BlueCav, cavlockrv, CavCenter, ionlockrv, IonPos], int(i*len(IonPositionVals) + j))
                    purgatory(plot.add_point, IonPosition, IonScatter, eval(plotLabel))
                    purgatory(plot.repaint)
                    j=j+1
                    timefinal=time.time()
                    deltatime=timefinal-timeinital
                    print "IonPosition = %f V, IonScatter = %f photons, time to take datapoint = %f"%(IonPosition, IonScatter,deltatime)
                else:
                    print "Discarding and repeating measurement."
        ScanDone()
    except Exception,e:
        print __file__,time.strftime('%H:%M:%S'),"Exception occurred in RunScript:", e
        traceback.print_exc()
