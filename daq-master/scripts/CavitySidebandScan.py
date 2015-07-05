ARGS = ['StarkSecFRQ1', 'StarkSecFRQ2', 'StarkSecFRQ3', 'Width', 'ScanPoints', 'ScanRepeat', 'ProbePower', 'BlueLockOn', 'CavLockOn', 'IonLockOn', 'IonSet']

import CavityStabilization

def RunScript(filename, dirname, StarkSecFRQ1, StarkSecFRQ2, StarkSecFRQ3, Width, ScanPoints, ScanRepeat, ProbePower, BlueLockOn, CavLockOn, IonLockOn, IonSet):

    # IonSet = 0 locks to the cavity standing wave antinode
    # IonSet = 1 locks halfway between the node and the antinode
    # IonSet = 2 locks to the node
    
    reload(CavityStabilization)
    
    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDSandReadTotal = f_read['DDS_RUNNTOTAL']
    def RunDDSandReadTotal():
	    isok = 0
	    while not isok:
	        try:
        	    rv=f_read['DDS_RUNNTOTAL']() 
	            isok=1
        	except Exception,e:
	            print "[",__file__,time.asctime(),"] Timeout/Error when calling DDS_RUNNTOTAL:",
        	    time.sleep(0.5)
	            print "Retrying..."
        	    sys.stdout.flush()
	    return rv
#    self.RunDDSandReadTotal=RunDDSandReadTotal
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    CavFreqSet = f_set['DDS_FREQ2']
    f421quiet = f_set['MonoLasers_Quiet421']
    CavBeamSet = f_set['3631A_botleft_+25V']
    ProbePowerRead = f_read['3631A_leftmost_+25V']
    ProbePowerSet = f_set['3631A_leftmost_+25V']
    
    beam0 = 24.
    beam90 = 0.
    maxProbePower = 15.

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
		
        
        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        
        bluelockrv, BlueCav = CavStab.BlueLock(BlueLockOn, True)
        cavlockrv, CavCenter = CavStab.CavLock(CavLockOn, True)
        ionlockrv, IonPos = CavStab.IonLock(IonLockOn, IonSet, True)
        print "Result from IonLock: ionlockrv=%f and IonPos=%f"%(ionlockrv,IonPos)
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
        purgatory(plot.set_labels, 'Frequency offset [MHz]', 'Scatter into cavity [photons]', plotLabel)
        mydb = data.database(filename, dirname, 1, 8, 'Frequency offset [MHz], Scatter into cavity [photons], bluelockrv, BlueCav, cavlockrv, CavCenter, ionlockrv, IonPos')

        ##################################################
        # Perform the experiment
        ##################################################
        print "Running ..."
        
        df = (scipy.array(range(int(ScanPoints))) - (ScanPoints - 1.)/2.)/(ScanPoints - 1)*Width
        FreqOffsetVals = scipy.unique(scipy.concatenate([df - StarkSecFRQ3, df - StarkSecFRQ2, df - StarkSecFRQ1, df, df + StarkSecFRQ1, df + StarkSecFRQ2, df + StarkSecFRQ3]))
        
        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break

            print "Scan %d"%(i)
            for j in range(len(FreqOffsetVals)):
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
                FreqOffset = FreqOffsetVals[j]
                
                
        	# This one is known to raise errors:
		isok = 0
		while not isok:
			try:
                            #CavFreqSet(ReadParameter('F_CavityCenter') + FreqOffset)
                            SetParameter('F_CavityOn',ReadParameter('F_CavityCenter')+FreqOffset)    
			    isok = 1
			except Exception, e:
			    print "[",__file__,time.asctime(),"] A time out error occured while calling SetParameter :",e
			    sys.stdout.flush()
			    time.sleep(0.5)
			    print "Retrying..."
		
                CavBeamSet(beam90)
                ProbePowerSet(ProbePower)
                f421quiet(1)
                time.sleep(0.2)
                
                OpenDDS('prog/ReadCavityPMT.pp')
                CavityScatter = RunDDSandReadTotal()

                CavFreqSet(0)
                f421quiet(0)
                if CavStab.CavLockCheck():
                    mydb.add_data_point([FreqOffset, CavityScatter, bluelockrv, BlueCav, cavlockrv, CavCenter, ionlockrv, IonPos], int(i*len(FreqOffsetVals) + j))
                    purgatory(plot.add_point, FreqOffset, CavityScatter, eval(plotLabel))
                    purgatory(plot.repaint)
                    print "FreqOffset = %f MHz, CavityScatter = %f photons"%(FreqOffset, CavityScatter)
                else:
                    print "Discarding and repeating measurement."
    except Exception,e:
        print time.strftime('%H:%M%S'),__file__,"Exception occurred in RunScript:"
        print e
        traceback.print_exc()
