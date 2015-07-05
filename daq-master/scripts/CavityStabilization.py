import __main__
import re, pyextfigure
import time
import scipy
import scipy.optimize
import sys

class CavityStabilization:
    def __init__(self, f_set, f_read, gui_exports):
        self.plot = gui_exports['plot']
        self.purgatory = gui_exports['purgatory']
        self.f421set = f_set['MonoLasers_421']
        self.f421read = f_read['MonoLasers_421']
        self.f421quiet = f_set['MonoLasers_Quiet421']
        self.OpenDDS = f_set['DDS_SETPROG']
        self.RunDDS = f_set['DDS_RUNPROG']
        self.ReadUnshelved = f_read['DDS_NBRIGHT']
        self.ReadAvgBright = f_read['DDS_LASTAVG']
        self.Say=f_set['AudioAlert_say']
        self.CavityUnlocked=f_set['AudioAlert_cavityunlocked']
        self.CavityRelocked=f_set['AudioAlert_cavityrelocked']
        self.CavLockRead=f_read['TDS3000_CH2Vmean']
        self.ADCVAL421Check=f_read['MonoLasers_421_ADCVAL']
        self.ADCVAL1091Check=f_read['MonoLasers_1091_ADCVAL']
        self.ADCVAL674Check=f_read['MonoLasers_674_ADCVAL']
        self.ADCVAL1033Check=f_read['MonoLasers_1033_ADCVAL']

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
        self.RunDDSandReadTotal = RunDDSandReadTotal 
        self.SetParameter  = f_set['DDS_PARAM']
        self.ReadParameter  = f_read['DDS_PARAM']
        self.IonPosSet = f_set['3631A_topright_-25V']
        self.IonPosRead = f_read['3631A_topright_-25V']
        self.ReadIonPMT = f_read['IonPhotonCounter_COUNT']
        self.ReadCavPMT = f_read['CavityPhotonCounter_COUNT']
        self.DCFreqSet = f_set['DDS_FREQ1']
        self.DCAmpSet = f_set['DDS_AMP1']
        self.CavFreqSet = f_set['DDS_FREQ2']
        self.CavBeamRead = f_read['3631A_botleft_+25V']
        self.CavBeamSet = f_set['3631A_botleft_+25V']
        self.ProbePowerRead = f_read['3631A_leftmost_+25V']
        self.ProbePowerSet = f_set['3631A_leftmost_+25V']
        self.ProbePowerMeasure = f_read['DMM_bot_V']
        
        self.beam0 = 24.
        self.beam90 = 0.
        
        self.maxProbePower = 15.
        
        self.BlueCav = self.f421read()
        self.CavCenter = self.ReadParameter('F_CavityCenter')
        self.ProbePower = self.ProbePowerRead()
        self.ProbePower_SB = 9.8#self.ProbePowerRead()
        self.IonPos = self.IonPosRead()
        if self.IonPos > 0:
            self.IonPos = 0
        
        self.const = {}

        self.BlueCounter = 1
        self.CavCounter = 1
        self.ProbeCounter_SB = 1
        self.ProbeCounter = 1
        self.ScatterRateCounter = 1
        self.IonCounter = 1

    def LoadConstants(self, constsFile):
        cfile = open(constsFile)
        for line in cfile:
            m = re.match('(\w+)\s*=\s*([^#\n\r]*)', line)
            if m:
                key = m.group(1)
                val = m.group(2)
                self.const[key] = float(val)
            else:
                exec line
        cfile.close()
        return self.const
    
    def BlueLock(self, BlueLockOn, loop):
        try:
            if ((not((BlueLockOn > 0) & ((loop) | (self.BlueCounter == BlueLockOn)))) | (__main__.STOP_FLAG)):
                self.BlueCounter = self.BlueCounter + 1
                return -1, self.BlueCav
            self.BlueCounter = 1
            
            self.MonoLaserLockCheck('421')
            self.MonoLaserLockCheck('1091')
            try:
                self.DCFreqSet(self.ReadParameter('F_BlueOn'))
                self.DCAmpSet(self.ReadParameter('A_BlueOn'))
                self.CavFreqSet(0)
                deltaBlueCavMax=0.008
                bluerv = -1
                if (loop):
                    print "Locking Blue"
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode, pyextfigure.DUALTWODPLOT)
                    self.purgatory(self.plot.set_labels, 'Exp No', 'Scatter', 'Blue Cav')
                
                    self.BlueCav = self.f421read()

                    i = 0 # Stops the lock after 30 iterations
                    NotBrightCounter=0 # Makes sure that the scan finishes.
                    while (i < 40 and not __main__.STOP_FLAG):
                        i = i + 1
			# This is where the cavity falls out of lock! Changing bluecav too much at one time is bad! 
			# Will implement solution 1) from http://quanta.mit.edu/~ionsearch/MT-planartraps/archives/2011/02/fuchu_day_135_n_1.html
                        time.sleep(0.5)
                        try:
                            bluerv = self.ReadIonPMT()
                        except:
                            print __file__,"[Loop mode] Failed to do ReadIonPMT()"
                        deltaBlueCav=0
                        if bluerv > 0.1*self.const['BlueSet']:
                            deltaBlueCav=self.const['BlueGain'] * (self.const['BlueSet'] - bluerv) / self.const['BlueSet']
                        else:
                            print "Ion not bright enough!"
                            if NotBrightCounter<10:
                                i=i-1
                                NotBrightCounter=NotBrightCounter+1
                            
                        while (abs(deltaBlueCav)>deltaBlueCavMax):
	                   print "deltaBlueCav=",deltaBlueCav,", too large trying smaller value."
			   deltaBlueCav=deltaBlueCav/abs(deltaBlueCav)*deltaBlueCavMax
                           sys.stdout.flush()
                        
                        self.BlueCav = self.BlueCav - deltaBlueCav 
                        try:
			    self.f421set(self.BlueCav)
                        except:
                            print __file__,"Failed to do f421set"
                        print "blueRV = %d, BlueCav = %f, deltaBlueCav= %f"%(bluerv, self.BlueCav,deltaBlueCav)
                    print "Done locking blue. blueRV=",bluerv
                       
    #                        time.sleep(0.5)
    #			try: 
    #	                        bluerv = self.ReadIonPMT()
    #			except Exception,e:
    #				print __file__,"Failed to read IonPMT()"
    #                        self.purgatory(self.plot.add_point, i, bluerv, self.BlueCav)
    #                        self.purgatory(self.plot.repaint)
    #
    #                        if bluerv > 0.2*self.const['BlueSet']:
    #                            self.BlueCav = self.BlueCav - self.const['BlueGain'] * (self.const['BlueSet'] - bluerv) / self.const['BlueSet']
    #			try:
    #	                        self.f421set(self.BlueCav)
    #        		except:
    #				print __file__,"Failed to do f421 set!"
    #	                print "blueRV = %d, BlueCav = %f"%(bluerv, self.BlueCav)
                else:
		# This is where the cavity falls out of lock! Changing bluecav too much at one time is bad! 
		# Will implement solution 1) from http://quanta.mit.edu/~ionsearch/MT-planartraps/archives/2011/02/fuchu_day_135_n_1.html
		    isok=0
		    index=0
                    index2=0
		    while not isok:
                            if __main__.STOP_FLAG: break
                            time.sleep(1.0)
			    try:
	                    	    bluerv = self.ReadIonPMT()
			    except:
				    print __file__,"[Not in loop mode] Failed to do ReadIonPMT()"
			    # I am guessing this if-clause is meant to detect that the laser fell out of lock or something.
			    if bluerv > 0.1*self.const['BlueSet']:
				deltaBlueCav=self.const['BlueGain'] * (self.const['BlueSet'] - bluerv) / self.const['BlueSet']
				if abs(deltaBlueCav)>deltaBlueCavMax:
					if index==0:
#						print __file__,time.strftime('%H:%M:%S'),"deltaBlueCav=%.5f too large"%(deltaBlueCav)
#						print "Setting DDSAMP1 again."
						self.DCAmpSet(self.ReadParameter('A_BlueOn'))
					else:
						print "bluerv=%d, deltaBlueCav=%.3f still too large retrying."%(bluerv,deltaBlueCav)
						deltaBlueCav=deltaBlueCav/abs(deltaBlueCav)*deltaBlueCavMax
					index=index+1
					isok =0
					
					sys.stdout.flush()
        	   		else:
			   		self.BlueCav = self.BlueCav - deltaBlueCav 
                    			isok =1
                            else:
                                if index2==0:
                                    text=time.strftime("%H:%M:%S")+"Did we loose the ion? bluerv=%d"%bluerv
                                    print text
                                    self.Say(text)
                                    index2=index2+1
                                else:
                                    print ".",
                                    time.sleep(1)
                                    index2=index2+1
                            if index2>5:
                                text="Ion was lost! Aborting."
                                print text
                                self.Say(text)
                                __main__.STOP_FLAG=True
                                break

                                time.sleep(1)
			    if index>1 and isok==0:
			    	deltaBlueCav=deltaBlueCav/abs(deltaBlueCav)*deltaBlueCavMax
				print "deltaBlueCav is too large doing smaller step=%.4f"%(deltaBlueCav)
				self.BlueCav=self.BlueCav-deltaBlueCav	
			        self.f421set(self.BlueCav)
				isok=0
		    try:
			    self.f421set(self.BlueCav)
                            time.sleep(1.0)
                            bluerv2=self.ReadIonPMT()
		    except:
			    print __file__,"Failed to do f421set, or ReadIonPMT()"
                    print "blueRV = %d, blueRV2=%d, BlueCav = %f, deltaBlueCav= %f"%(bluerv,bluerv2, self.BlueCav,deltaBlueCav)

            finally:
                self.DCFreqSet(self.ReadParameter('F_BlueHi'))
                self.DCAmpSet(self.ReadParameter('A_BlueHi'))
            
            return bluerv, self.BlueCav
        
        except Exception, e:
            print __file__,"Exception occurred in BlueLock:", e
	    return -1, self.BlueCav
            
    def MonoLaserLockCheck(self,MonoLaser):
#        print "Welcome to MonoLaserLockCheck!"
#        if self.ADCVAL421Check()<0.02:
#            return False
#        else:
        try:
            functionstring='self.ADCVAL%sCheck'%MonoLaser
#            print functionstring
#            sys.stdout.flush()
            ADCVALCheck=eval(functionstring)
        except Exception as e:
            print "Exception occured while trying to assign ADCVALCheck to %s"%functionstring
            print e
            raise e
        MonoLaserLockThreshold = self.const['MonoLaserLockThreshold_%s'%(MonoLaser)]
        try:
            if ADCVALCheck() > MonoLaserLockThreshold or __main__.STOP_FLAG:
                return True
            elif ADCVALCheck()==-1:
                return  True # FIXME: This is not actually correct...
            else:
                print time.strftime('%H:%M:%S'),
                text= "Monolaser %s Fell out of lock!"%(MonoLaser)
                self.Say(text)
                print(text)
                isok=0
                print "Waiting for MonoLaser %s to be locked again"%MonoLaser,
                while isok==0:
                    if __main__.STOP_FLAG: break
                    if ADCVALCheck()>MonoLaserLockThreshold:
                        isok=1
                    print ".",
                    time.sleep(1) # Sleep for one second while waiting for MonoLaser to be relocked.
                    sys.stdout.flush()
                    if isok==1:
                        print "\nMonoLaser Locked! Restarting in 10 seconds"
                        sys.stdout.flush()
                        for i in range(10,0,-1):
                            print i
                            sys.stdout.flush()
                            time.sleep(1)
                            # Make sure that MonoLaser is consistently locked for 10 seconds!
                            if ADCVALCheck()<MonoLaserLockThreshold:
                                isok=0
                                print "Not locked!"
                print time.strftime('%H:%M:%S'),"Resuming measurements"
                # Return false since the MonoLaser was unlocked which means our last data point is not right!
                return False
        except Exception,e:
            print '\n',time.strftime('%H:%M:%S'),__file__,"Exception occurred in MonoLaserLockCheck():",e
            return -1
            return True

    def CavLockCheck(self,AutoLock=False):
#	self.CavLockThreshold = 0.1

        self.MonoLaserLockCheck('421')
        self.CavLockThreshold = self.const['CavLockThreshold']
        index=0
        try:
           # print "Cavity locked?",
            if self.CavLockRead() > self.CavLockThreshold or __main__.STOP_FLAG:
            #    print "OK"
                return True
            else:
                print time.strftime('%H:%M:%S'),"Cavity Fell out of lock!"
                self.CavityUnlocked()
                isok=0
                print "Waiting for cavity to be locked again",
                while isok==0:
                    index=index+1
                    if __main__.STOP_FLAG: break
                    self.MonoLaserLockCheck('421')
                    if self.CavLockRead()>self.CavLockThreshold:
                        isok=1
                    print ".",
                    if index%120==0:
                        self.CavityUnlocked()
                    time.sleep(1) # Sleep for one second while waiting for cavity to be relocked.
                    sys.stdout.flush()
                    if isok==1:
                        print "\nCavity Locked! Restarting in 10 seconds"
                        sys.stdout.flush()
                        for i in range(10,0,-1):
                            print i
                            sys.stdout.flush()
                            time.sleep(1)
                            # Make sure that Cavity is consistently locked for 10 seconds!
                            if self.CavLockRead()<self.CavLockThreshold:
                                isok=0
                                print "Not locked!"
                print time.strftime('%H:%M:%S'),"Resuming measurements"
#        self.CavityRelocked()
                # Return false since the cavity is unlocked which means our last data point is not right!
                return False
        except Exception,e:
            print '\n',time.strftime('%H:%M:%S'),__file__,"Exception occurred in CavLockCheck():",e
            return False
            


    def CavLock(self, CavLockOn, loop):
        try:
# I think CavLockOn determines how often the CavLock should be run!
            if ((not((CavLockOn > 0) & ((loop) | (self.CavCounter == CavLockOn)))) | (__main__.STOP_FLAG)):
                self.CavCounter = self.CavCounter + 1
                return -1, self.CavCenter
            self.CavCounter = 1
            
            saved_CavBeam = self.CavBeamRead()
            if saved_CavBeam < 12.:
                saved_CavBeam = 0.
            else:
                saved_CavBeam = 24.
            saved_ProbePower = self.ProbePowerRead()
            
            try:
                self.CavBeamSet(self.beam0)
                self.ProbePowerSet(self.maxProbePower)
                self.f421quiet(1)
                time.sleep(2.0)
                
                cavrv = -1
                if (loop):
                    print "Locking Cavity Center"
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode, pyextfigure.DUALTWODPLOT)
                    self.purgatory(self.plot.set_labels, 'Exp No', 'Signal', 'Cav Center')

                    self.CavCenter = self.ReadParameter('F_CavityCenter')

                    i = 0
                    while (i < 20 and not __main__.STOP_FLAG):
                        self.CavLockCheck()
                        i = i + 1
                        
                        self.CavFreqSet(self.CavCenter - self.const['CavFWHM']/2)
                        time.sleep(0.5)
                        cavrv1 = self.ReadCavPMT()

                        self.CavFreqSet(self.CavCenter + self.const['CavFWHM']/2)
                        time.sleep(0.5)
                        cavrv2 = self.ReadCavPMT()
                        
                        cavrv = 2.*(cavrv2 - cavrv1)/(cavrv1 + cavrv2)

                        self.purgatory(self.plot.add_point, i, cavrv, self.CavCenter)
                        self.purgatory(self.plot.repaint)
                        deltaCav=self.const['CavGain'] * cavrv
                        deltaCavMax=0.005
                        if abs(deltaCav)<deltaCavMax:
                            self.CavCenter = self.CavCenter + deltaCav
                        else:
                            self.CavCenter = self.CavCenter + deltaCav/abs(deltaCav)*deltaCavMax
                        self.SetParameter('F_CavityCenter', self.CavCenter)
                        print "cavRV = %f, CavCenter = %f, cavrv1=%d,cavrv2=%d"%(cavrv, self.CavCenter,cavrv1,cavrv2)
                        if (cavrv1<50e3) or (cavrv2<50e3):
                            text='Warning, Cavity return value is below 50000.'
# self.Say(text)
                            print text
                else:
                    self.CavLockCheck()
                    self.CavFreqSet(self.CavCenter - self.const['CavFWHM']/2)
                    time.sleep(0.5)
                    cavrv1 = self.ReadCavPMT()

                    self.CavFreqSet(self.CavCenter + self.const['CavFWHM']/2)
                    time.sleep(0.5)
                    cavrv2 = self.ReadCavPMT()
                        
                    cavrv = 2.*(cavrv2 - cavrv1)/(cavrv1 + cavrv2)
                    
                    #self.CavCenter = self.CavCenter + self.const['CavGain'] * cavrv
                    deltaCav=self.const['CavGain'] * cavrv
                    deltaCavMax=0.005
                    if abs(deltaCav)<deltaCavMax:
                        self.CavCenter = self.CavCenter + deltaCav
                    else:
                        self.CavCenter = self.CavCenter + deltaCav/abs(deltaCav)*deltaCavMax
                    self.SetParameter('F_CavityCenter', self.CavCenter)
                    print "cavRV = %f, CavCenter = %f, cavrv1=%d,cavrv2=%d"%(cavrv, self.CavCenter,cavrv1,cavrv2)
                    if (cavrv1+cavrv2<100e3):
                        text='Warning, Cavity return value is below 50000.'
#                        self.Say(text)
                        print text
                    #print "cavRV = %f, CavCenter = %f"%(cavrv, self.CavCenter)                    
            finally:
                self.CavBeamSet(saved_CavBeam)
                self.ProbePowerSet(saved_ProbePower)
                self.CavFreqSet(0)
                self.f421quiet(0)
                time.sleep(0.2)
            
            return cavrv, self.CavCenter
        
        except Exception, e:
            print "Exception occurred in CavLock:", e
	    return -1, self.CavCenter

# ProbeLock_0deg is the analogue of ProbeLock but for the 0 deg beam. Please note that it does not Stabilize the power when probing the CavityResonance, but rather the power in the Probe beam when it is used for Cavity Cooling.
    def ProbeLock_0deg(self, ProbeLockOn, ProbeSet, loop):
        try:
            if ((not((ProbeLockOn > 0) & ((loop) | (self.ProbeCounter == ProbeLockOn)))) | (__main__.STOP_FLAG)):
                self.ProbeCounter = self.ProbeCounter + 1
                return -1, self.ProbePower
            self.ProbeCounter = 1
            
            saved_CavBeam = self.CavBeamRead()
            if saved_CavBeam < 12.:
                saved_CavBeam = 0.
            else:
                saved_CavBeam = 24.
            saved_ProbePower = self.ProbePowerRead()
            
            try:
                self.CavBeamSet(self.beam90)
# It is actually not necessary to measure the power of 0deg beam since it should be proportional to the beam90 power assuming the same coupling, that 422 is in quiet mode and  that 0deg beam is resonant with cavity.
#self.CavBeamSet(self.beam0) # FIXME: Test that power levels and gain match.
                self.CavFreqSet(self.CavCenter)
                self.ProbePowerSet(self.ProbePower)
                
                proberv = -1
                if (loop):
                    print "Locking Probe Power(Cavity Cooling 90degree power)"
                    print "Current values: ProbePower=%.3f, saved_ProbePower=%.3f"%(self.ProbePower,saved_ProbePower)
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode, pyextfigure.DUALTWODPLOT)
                    self.purgatory(self.plot.set_labels, 'Exp No', 'Signal', 'Probe Power')

                    i = 0
                    warningindex=0
                    while (i < 20 and not __main__.STOP_FLAG):
                        i = i + 1
                        
                        time.sleep(0.2)
                        proberv = self.ProbePowerMeasure()

                        self.purgatory(self.plot.add_point, i, proberv, self.ProbePower)
                        self.purgatory(self.plot.repaint)
                        if proberv > 0.001*ProbeSet:
                            self.ProbePower = self.ProbePower + self.const['ProbeGain'] * (ProbeSet - proberv) / ProbeSet # FIXME: Use another gain value?
                            if self.ProbePower < 0:
                                self.ProbePower = 0
                            if self.ProbePower > 15:
                                self.ProbePower = 15
                                text='Warning. Probe power is out of range:',
                                if  warningindex<4:
                                    self.Say(text)
                                    warningindex=warningindex+1
                                print text
                        else:
                            print "ProbeLock_0deg: I have done nothing!"
                        self.ProbePowerSet(self.ProbePower)
                        print "probeRV = %.3f, ProbeSet=%.3f, ProbePower = %.3f"%(proberv, ProbeSet, self.ProbePower)
                else:
                    time.sleep(0.2)
                    proberv = self.ProbePowerMeasure()
                    deltaProbePower=0
                    if proberv > 0.2*ProbeSet:
                        deltaProbePower=self.const['ProbeGain'] * (ProbeSet - proberv) / ProbeSet
                        self.ProbePower = self.ProbePower + deltaProbePower 
                        if self.ProbePower < 0:
                            self.ProbePower = 0
                        if self.ProbePower > 15:
                            self.ProbePower = 15
                            if self.ProbePower > 15:
                                self.ProbePower = 15
                                text='Warning. Probe power is out of range:',
                                self.Say(text)
                                print text
                    self.ProbePowerSet(self.ProbePower)
                    print "probeRV = %.3f, ProbeSet=%.3f, ProbePower = %.3f, deltaProbePower=%.3f"%(proberv, ProbeSet, self.ProbePower,deltaProbePower)
#print "probeRV = %f, ProbePower = %f"%(proberv, self.ProbePower)
            finally:
                self.CavBeamSet(saved_CavBeam)
                self.CavFreqSet(0)
                self.ProbePowerSet(saved_ProbePower)
                time.sleep(0.2)
            
            return proberv, self.ProbePower
        
        except Exception, e:
            print "Exception occurred in ProbeLock:", e
	    return -1, self.ProbePower
####################################################################
# ProbeLock_0deg_SB is the analogue of ProbeLock but for the 0 deg beam. Please note that it does not Stabilize the power when probing the CavityResonance, but rather the power in the Probe beam when it is used for Cavity Cooling. This version is for locking the Sideband (SB) power level of the cavity. It is separate to not be mixed with the "regular" carrier Probepower and ProbeSet values.
    def ProbeLock_0deg_SB(self, ProbeLockOn, ProbeSet, loop):
        try:
            if ((not((ProbeLockOn > 0) & ((loop) | (self.ProbeCounter_SB == ProbeLockOn)))) | (__main__.STOP_FLAG)):
                self.ProbeCounter_SB = self.ProbeCounter_SB + 1
                return -1, self.ProbePower_SB
            self.ProbeCounter_SB = 1
            
            saved_CavBeam = self.CavBeamRead()
            if saved_CavBeam < 12.:
                saved_CavBeam = 0.
            else:
                saved_CavBeam = 24.
            saved_ProbePower = self.ProbePowerRead()
            
            try:
                self.CavBeamSet(self.beam90)
# It is actually not necessary to measure the power of 0deg beam since it should be proportional to the beam90 power assuming the same coupling, that 422 is in quiet mode and  that 0deg beam is resonant with cavity.
#self.CavBeamSet(self.beam0) # FIXME: Test that power levels and gain match.
                self.CavFreqSet(self.CavCenter)
                self.ProbePowerSet(self.ProbePower_SB)
                
                proberv = -1
                if (loop):
                    print "Locking Probe Power(Cavity Cooling 90degree power) for Cavity Sideband"
                    print "Current values: ProbePower=%.3f, saved_ProbePower=%.3f"%(self.ProbePower_SB,saved_ProbePower)
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode, pyextfigure.DUALTWODPLOT)
                    self.purgatory(self.plot.set_labels, 'Exp No', 'Signal', 'Probe Power')

                    i = 0
                    warningindex=0
                    while (i < 20 and not __main__.STOP_FLAG):
                        i = i + 1
                        
                        time.sleep(0.2)
                        proberv = self.ProbePowerMeasure()

                        self.purgatory(self.plot.add_point, i, proberv, self.ProbePower_SB)
                        self.purgatory(self.plot.repaint)
                        if proberv > 0.001*ProbeSet:
                            # Note that gain is multiplied with 20 here to compensate for the lower sensitivity around typical sideband power!
                            self.ProbePower_SB = self.ProbePower_SB + 50*self.const['ProbeGain'] * (ProbeSet - proberv) / ProbeSet # FIXME: Use another gain value?
                            if self.ProbePower_SB < 0:
                                self.ProbePower_SB = 0
                            if self.ProbePower_SB > 15:
                                self.ProbePower_SB = 15
                                text='Warning. Probe power for Side band is out of range:',
                                if  warningindex<4:
                                    self.Say(text)
                                    warningindex=warningindex+1
                                print text
                        else:
                            print "ProbeLock_0deg_SB: I have done nothing!"
                        self.ProbePowerSet(self.ProbePower_SB)
                        print "probeRV = %.3f, ProbeSet=%.3f, ProbePower_SB = %.3f (Cavity Sideband)"%(proberv, ProbeSet, self.ProbePower_SB)
                else:
                    time.sleep(0.2)
                    proberv = self.ProbePowerMeasure()
                    deltaProbePower=0
                    if proberv > 0.2*ProbeSet:
# ProbeGain is multiplied by 20 here to compensate for lower sensitivity in sideband power range.
                        deltaProbePower=50*self.const['ProbeGain'] * (ProbeSet - proberv) / ProbeSet
                        self.ProbePower_SB = self.ProbePower_SB + deltaProbePower 
                        if self.ProbePower_SB < 0:
                            self.ProbePower_SB = 0
                        if self.ProbePower_SB > 15:
                            self.ProbePower_SB = 15
                            text='Warning. Probe power for side band is out of range:',
                            self.Say(text)
                            print text
                    self.ProbePowerSet(self.ProbePower_SB)
                    print "probeRV = %.3f, ProbeSet=%.3f, ProbePower = %.3f, deltaProbePower=%.4f (Side band)"%(proberv, ProbeSet, self.ProbePower_SB,deltaProbePower)
#print "probeRV = %f, ProbePower = %f"%(proberv, self.ProbePower)
            finally:
                self.CavBeamSet(saved_CavBeam)
                self.CavFreqSet(0)
                self.ProbePowerSet(saved_ProbePower)
                time.sleep(0.2)
            
            return proberv, self.ProbePower_SB
        
        except Exception, e:
            print "Exception occurred in ProbeLock_0deg_SB:", e
	    return -1, self.ProbePower_SB

# Scatter rate lock. This lock tries to lock the scatter rate from eg. 90 degree beam into cavity assuming that BlueLaser 
    def ScatterRateLock(self,ScatterRateLockOn,ScatterSet,loop):
        try:
            # Turn on the right beams
            print("Locking Scatter rate from 90 degree beam to %d counts"%ScatterSet)
            if ((not((ScatterRateLockOn > 0) & ((loop) | (self.ScatterRateCounter == ScatterRateLockOn)))) | (__main__.STOP_FLAG)):
                self.ScatterRateCounter = self.ScatterRateCounter + 1
                return -1, self.ProbePower
            
            if loop:
                pass
                "Calibrating ScatterRate vs. ProbePower"
                
            else:
                pass

        except Exception as e:
            print("Exception occured in ScatterRateLock: %s"%e)
            raise e
        finally:
            pass
            #   Return to saved values!
        return scatterrate, ProbePower, ProbeSet
###################################################################


# The Purpose of ProbeLock is NOT to lock the probe power, but rather to lock the Cavity Cooling 90degrees beam power. I guess we're stuck with the unfortunate name...
    def ProbeLock(self, ProbeLockOn, ProbeSet, loop):
        try:
            if ((not((ProbeLockOn > 0) & ((loop) | (self.ProbeCounter == ProbeLockOn)))) | (__main__.STOP_FLAG)):
                self.ProbeCounter = self.ProbeCounter + 1
                return -1, self.ProbePower
            self.ProbeCounter = 1
            
            saved_CavBeam = self.CavBeamRead()
            if saved_CavBeam < 12.:
                saved_CavBeam = 0.
            else:
                saved_CavBeam = 24.
            saved_ProbePower = self.ProbePowerRead()
            
            try:
                self.CavBeamSet(self.beam90)
                self.CavFreqSet(self.CavCenter)
                self.ProbePowerSet(self.ProbePower)
                
                proberv = -1
                if (loop):
                    print "Locking Probe Power(Cavity Cooling 90degree power)"
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode, pyextfigure.DUALTWODPLOT)
                    self.purgatory(self.plot.set_labels, 'Exp No', 'Signal', 'Probe Power')

                    i = 0
                    while (i < 20 and not __main__.STOP_FLAG):
                        i = i + 1
                        
                        time.sleep(0.2)
                        proberv = self.ProbePowerMeasure()

                        self.purgatory(self.plot.add_point, i, proberv, self.ProbePower)
                        self.purgatory(self.plot.repaint)
                        if proberv > 0.2*ProbeSet:
                            self.ProbePower = self.ProbePower + self.const['ProbeGain'] * (ProbeSet - proberv) / ProbeSet
                            if self.ProbePower < 0:
                                self.ProbePower = 0
                            if self.ProbePower > 15:
                                self.ProbePower = 15
                        self.ProbePowerSet(self.ProbePower)
                        print "probeRV = %f, ProbeSet=%f, ProbePower = %f"%(proberv, ProbeSet, self.ProbePower)
                else:
                    time.sleep(0.2)
                    proberv = self.ProbePowerMeasure()
                    deltaProbePower=0
                    if proberv > 0.2*ProbeSet:
                        deltaProbePower=self.const['ProbeGain'] * (ProbeSet - proberv) / ProbeSet
                        self.ProbePower = self.ProbePower + deltaProbePower 
                        if self.ProbePower < 0:
                            self.ProbePower = 0
                        if self.ProbePower > 15:
                            self.ProbePower = 15
                    self.ProbePowerSet(self.ProbePower)
                    print "probeRV = %f, ProbeSet=%f, ProbePower = %f, deltaProbePower=%f"%(proberv, ProbeSet, self.ProbePower,deltaProbePower)
#print "probeRV = %f, ProbePower = %f"%(proberv, self.ProbePower)
            finally:
                self.CavBeamSet(saved_CavBeam)
                self.CavFreqSet(0)
                self.ProbePowerSet(saved_ProbePower)
                time.sleep(0.2)
            
            return proberv, self.ProbePower
        
        except Exception, e:
            print "Exception occurred in ProbeLock:", e
	    return -1, self.ProbePower


    def IonLock_0deg(self, IonLockOn, IonSet, loop):
        try:
            if ((not((IonLockOn > 0) & ((loop) | (self.IonCounter == IonLockOn)))) | (__main__.STOP_FLAG)):
                self.IonCounter = self.IonCounter + 1
                return -1, self.IonPos
            self.IonCounter = 1
            
            saved_CavBeam = self.CavBeamRead()
            if saved_CavBeam < 12.:
                saved_CavBeam = 0.
            else:
                saved_CavBeam = 24.
            saved_ProbePower = self.ProbePowerRead()
            
            try:
                #self.CavBeamSet(self.beam90)
                self.CavBeamSet(self.beam0)
# Dangerous? Note that the following line is superfluous after we changed ReadCavityPMT.pp to always use the F_CavityOn value.
               #self.CavFreqSet(self.CavCenter)
# Replaced the line with this:
                self.SetParameter('F_CavityOn',self.CavCenter)
#               
#                self.ProbePowerSet(self.maxProbePower)
                self.ProbePowerSet(self.ProbePower)
                self.f421quiet(1)
                time.sleep(0.2)
                
                ionrv = -1
                if (loop):
                    print "Locking Ion Position (Probepower=%f)"%self.ProbePower
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode, pyextfigure.TWODPLOT)
                    self.purgatory(self.plot.set_labels, 'Ion Pos', 'Signal', '')

                    N = 5
                    IonPosArray = self.const['IonPos1'] + scipy.array(range(N))/(N - 1.)*(self.const['IonPos2'] - self.const['IonPos1'])
                    CavScatterArray = scipy.zeros(N)
                    i = 0
                    while (i < N and not __main__.STOP_FLAG):
                        self.CavLockCheck()
                        self.IonPosSet(IonPosArray[i])
                        time.sleep(0.01)
                        self.OpenDDS('prog/ReadIonPMT.pp')
                        CavScatterArray[i] = self.RunDDSandReadTotal()
                        
                        self.purgatory(self.plot.add_point, IonPosArray[i], CavScatterArray[i], 0)
                        self.purgatory(self.plot.repaint)
                        
                        print "IonPos = %f, CavScatter = %d"%(IonPosArray[i], CavScatterArray[i])
                        
                        i = i + 1
                    
                    p0 = [scipy.sqrt(200), 200]
                    fitfun = lambda p, POS0, POS: p[0]**2*scipy.cos(scipy.pi/(self.const['IonPos2'] - self.const['IonPos1'])*(POS - POS0))**2 + p[1]
                    errfun = lambda p, POS0, POS, CAVscatter: fitfun(p, POS0, POS) - CAVscatter
                    
                    N = 100
                    chiSQ = scipy.Inf
                    for IonPos0 in self.const['IonPos1'] + scipy.array(range(N))/(N - 1.)*(self.const['IonPos2'] - self.const['IonPos1']):
                        p1, success = scipy.optimize.leastsq(errfun, p0, args = (IonPos0, IonPosArray, CavScatterArray))
                        chiSQ0 = sum(errfun(p1, IonPos0, IonPosArray, CavScatterArray)**2)/scipy.size(IonPosArray)
                    
                        if chiSQ0 < chiSQ:
                            self.IonPos = IonPos0
                            chiSQ = chiSQ0
                    
                    if IonSet == 1:
                        self.IonPos = self.const['IonPos1'] + scipy.mod(self.IonPos - (self.const['IonPos2'] - self.const['IonPos1'])/4., self.const['IonPos2'] - self.const['IonPos1'])
                    elif IonSet == 2:
                        self.IonPos = self.const['IonPos1'] + scipy.mod(self.IonPos - (self.const['IonPos2'] - self.const['IonPos1'])/2., self.const['IonPos2'] - self.const['IonPos1'])
                    
                    self.IonPosSet(self.IonPos)
                    
                else:
                    if IonSet == 0:
                        IonPos1 = self.IonPos - (self.const['IonPos2'] - self.const['IonPos1'])/4.
                        IonPos1 = self.const['IonPos1'] + scipy.mod(IonPos1 - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                        IonPos2 = self.IonPos + (self.const['IonPos2'] - self.const['IonPos1'])/4.
                        IonPos2 = self.const['IonPos1'] + scipy.mod(IonPos2 - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                    elif IonSet == 1:
                        IonPos1 = self.IonPos
                        IonPos2 = self.IonPos + (self.const['IonPos2'] - self.const['IonPos1'])/2.
                        IonPos2 = self.const['IonPos1'] + scipy.mod(IonPos2 - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                    elif IonSet == 2:
                        IonPos1 = self.IonPos + (self.const['IonPos2'] - self.const['IonPos1'])/4.
                        IonPos1 = self.const['IonPos1'] + scipy.mod(IonPos1 - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                        IonPos2 = self.IonPos + 3.*(self.const['IonPos2'] - self.const['IonPos1'])/4.
                        IonPos2 = self.const['IonPos1'] + scipy.mod(IonPos2 - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                        
                    self.IonPosSet(IonPos1)
                    time.sleep(0.01)
                    self.OpenDDS('prog/ReadIonPMT.pp')
                    ionrv1 = self.RunDDSandReadTotal()
                    print "IonPos = %f, CavScatter = %d"%(IonPos1, ionrv1)
                        
                    self.IonPosSet(IonPos2)
                    time.sleep(0.01)
                    self.OpenDDS('prog/ReadIonPMT.pp')
                    ionrv2 = self.RunDDSandReadTotal()
                    print "IonPos = %f, CavScatter = %d"%(IonPos2, ionrv2)
                        
                    ionrv = 2.*(ionrv2 - ionrv1)/(ionrv1 + ionrv2)

                    self.IonPos = self.IonPos + self.const['IonGain'] * ionrv
                    self.IonPos = self.const['IonPos1'] + scipy.mod(self.IonPos - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                    print "ionRV = %f, IonPos = %f"%(ionrv, self.IonPos)                    
                        
                    self.IonPosSet(self.IonPos) # This is where IonLock sets the correct IonPosition (ie. voltage) for the setting chosen by IonSet.
            finally:
                self.CavBeamSet(saved_CavBeam)
# Superfluous line. The beam should already be off from the pp script!
                self.CavFreqSet(0)
                self.ProbePowerSet(saved_ProbePower)
                self.f421quiet(0)
                time.sleep(2.0)
            
            return ionrv, self.IonPos
        
        except Exception, e:
            print "Exception occurred in IonLock_0deg:", e
	    return -1, self.IonPos

    def IonLock(self, IonLockOn, IonSet, loop):
        try:
            if ((not((IonLockOn > 0) & ((loop) | (self.IonCounter == IonLockOn)))) | (__main__.STOP_FLAG)):
                self.IonCounter = self.IonCounter + 1
                return -1, self.IonPos
            self.IonCounter = 1
            
            saved_CavBeam = self.CavBeamRead()
            if saved_CavBeam < 12.:
                saved_CavBeam = 0.
            else:
                saved_CavBeam = 24.
            saved_ProbePower = self.ProbePowerRead()
            
            try:
                self.CavBeamSet(self.beam90)
           #self.CavBeamSet(self.beam0)
# Dangerous? Note that the following line is superfluous after we changed ReadCavityPMT.pp to always use the F_CavityOn value.
               #self.CavFreqSet(self.CavCenter)
# Replaced the line with this:
                self.SetParameter('F_CavityOn',self.CavCenter)
                self.ProbePowerSet(self.maxProbePower)
                self.f421quiet(1)
                time.sleep(0.2)
                
                ionrv = -1
                if (loop):
                    print "Locking Ion Position"
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode, pyextfigure.TWODPLOT)
                    self.purgatory(self.plot.set_labels, 'Ion Pos', 'Signal', '')

                    N = 5
                    IonPosArray = self.const['IonPos1'] + scipy.array(range(N))/(N - 1.)*(self.const['IonPos2'] - self.const['IonPos1'])
                    CavScatterArray = scipy.zeros(N)
                    i = 0
                    while (i < N and not __main__.STOP_FLAG):
                        self.IonPosSet(IonPosArray[i])
                        time.sleep(0.01)
                        self.OpenDDS('prog/ReadCavityPMT.pp')
                        CavScatterArray[i] = self.RunDDSandReadTotal()
                        
                        self.purgatory(self.plot.add_point, IonPosArray[i], CavScatterArray[i], 0)
                        self.purgatory(self.plot.repaint)
                        
                        print "IonPos = %f, CavScatter = %d"%(IonPosArray[i], CavScatterArray[i])
                        
                        i = i + 1
                    
                    p0 = [scipy.sqrt(200), 200]
                    fitfun = lambda p, POS0, POS: p[0]**2*scipy.cos(scipy.pi/(self.const['IonPos2'] - self.const['IonPos1'])*(POS - POS0))**2 + p[1]
                    errfun = lambda p, POS0, POS, CAVscatter: fitfun(p, POS0, POS) - CAVscatter
                    
                    N = 100
                    chiSQ = scipy.Inf
                    for IonPos0 in self.const['IonPos1'] + scipy.array(range(N))/(N - 1.)*(self.const['IonPos2'] - self.const['IonPos1']):
                        p1, success = scipy.optimize.leastsq(errfun, p0, args = (IonPos0, IonPosArray, CavScatterArray))
                        chiSQ0 = sum(errfun(p1, IonPos0, IonPosArray, CavScatterArray)**2)/scipy.size(IonPosArray)
                    
                        if chiSQ0 < chiSQ:
                            self.IonPos = IonPos0
                            chiSQ = chiSQ0
                    
                    if IonSet == 1:
                        self.IonPos = self.const['IonPos1'] + scipy.mod(self.IonPos - (self.const['IonPos2'] - self.const['IonPos1'])/4., self.const['IonPos2'] - self.const['IonPos1'])
                    elif IonSet == 2:
                        self.IonPos = self.const['IonPos1'] + scipy.mod(self.IonPos - (self.const['IonPos2'] - self.const['IonPos1'])/2., self.const['IonPos2'] - self.const['IonPos1'])
                    
                    self.IonPosSet(self.IonPos)
                    
                else:
                    if IonSet == 0:
                        IonPos1 = self.IonPos - (self.const['IonPos2'] - self.const['IonPos1'])/4.
                        IonPos1 = self.const['IonPos1'] + scipy.mod(IonPos1 - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                        IonPos2 = self.IonPos + (self.const['IonPos2'] - self.const['IonPos1'])/4.
                        IonPos2 = self.const['IonPos1'] + scipy.mod(IonPos2 - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                    elif IonSet == 1:
                        IonPos1 = self.IonPos
                        IonPos2 = self.IonPos + (self.const['IonPos2'] - self.const['IonPos1'])/2.
                        IonPos2 = self.const['IonPos1'] + scipy.mod(IonPos2 - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                    elif IonSet == 2:
                        IonPos1 = self.IonPos + (self.const['IonPos2'] - self.const['IonPos1'])/4.
                        IonPos1 = self.const['IonPos1'] + scipy.mod(IonPos1 - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                        IonPos2 = self.IonPos + 3.*(self.const['IonPos2'] - self.const['IonPos1'])/4.
                        IonPos2 = self.const['IonPos1'] + scipy.mod(IonPos2 - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                        
                    self.IonPosSet(IonPos1)
                    time.sleep(0.01)
                    self.OpenDDS('prog/ReadCavityPMT.pp')
                    ionrv1 = self.RunDDSandReadTotal()
                    print "IonPos = %f, CavScatter = %d"%(IonPos1, ionrv1)
                        
                    self.IonPosSet(IonPos2)
                    time.sleep(0.01)
                    self.OpenDDS('prog/ReadCavityPMT.pp')
                    ionrv2 = self.RunDDSandReadTotal()
                    print "IonPos = %f, CavScatter = %d"%(IonPos2, ionrv2)
                        
                    ionrv = 2.*(ionrv2 - ionrv1)/(ionrv1 + ionrv2)

                    self.IonPos = self.IonPos + self.const['IonGain'] * ionrv
                    self.IonPos = self.const['IonPos1'] + scipy.mod(self.IonPos - self.const['IonPos1'], self.const['IonPos2'] - self.const['IonPos1'])
                    print "ionRV = %f, IonPos = %f"%(ionrv, self.IonPos)                    
                        
                    self.IonPosSet(self.IonPos)
            finally:
                self.CavBeamSet(saved_CavBeam)
# Superfluous line. The beam should already be off from the pp script!
                self.CavFreqSet(0)
                self.ProbePowerSet(saved_ProbePower)
                self.f421quiet(0)
                time.sleep(2.0)
            
            return ionrv, self.IonPos
        
        except Exception, e:
            print "Exception occurred in IonLock:", e
	    return -1, self.IonPos
