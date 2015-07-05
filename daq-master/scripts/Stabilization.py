import __main__
import time
import re, pyextfigure
import sys

class Stabilization:
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
        self.SetParameter  = f_set['DDS_PARAM']
        self.ReadParameter  = f_read['DDS_PARAM']
        self.F422=f_read['WS7_F3']
        self.CavOffset = self.ReadParameter('F_RedCenter')
        self.RedPiTime = self.ReadParameter('us_PiTime')
        self.Say = f_set['AudioAlert_say']

        self.ramD = 0.
        self.rabD = 0.
	self.freqgain=1000
        self.const = {}

        self.RABI = 2
        self.RAMSEY = 1

        self.RabiCounter = 0

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

    def BlueLockCounts(self,BlueSet):
        try:
            print "BlueLockCounts(%d): Locking Blue..."%(BlueSet)
            self.purgatory(self.plot.clear)
            self.purgatory(self.plot.set_mode, pyextfigure.DUALTWODPLOT)
            self.purgatory(self.plot.set_labels, 'Exp No', 'Scatter', 'Blue Cav')

            # save all parameters that are going to be changed for use in locking
            us_MeasTime = self.ReadParameter('us_MeasTime')
            saved_F_RedOn = self.ReadParameter('F_RedOn')
            saved_SCloops = self.ReadParameter('SCloops')
            saved_ms_ReadoutDly = self.ReadParameter('ms_ReadoutDly')
#            saved_ms_TrigDly = self.ReadParameter('ms_TrigDly')
            try:
                self.OpenDDS('prog/Shelving.pp')
                self.SetParameter('F_RedOn', 0)
                self.SetParameter('SCloops', 0)
                self.SetParameter('ms_ReadoutDly', 0)
#                self.SetParameter('ms_TrigDly', 0)
                self.BlueCav = self.f421read()

                i = 0
                bluerv = -1
                while (i < 30 and not __main__.STOP_FLAG):
                    i = i + 1
                    
                    self.RunDDS()
                    self.ReadUnshelved()
                    bluerv = self.ReadAvgBright()

                    self.purgatory(self.plot.add_point, i, bluerv, self.BlueCav)
                    self.purgatory(self.plot.repaint)
                    IonBrightness=us_MeasTime*1e-6*BlueSet
		    deltaBlueCav=self.const['BlueGain']/10 * (IonBrightness - bluerv)
                    deltaBlueCavMax=0.005
                    if abs(deltaBlueCav)<deltaBlueCavMax:
                        self.BlueCav = self.BlueCav - deltaBlueCav
                    else:
			print "deltaBlueCav is too large!"
                        self.BlueCav = self.BlueCav-deltaBlueCav/abs(deltaBlueCav)*deltaBlueCavMax
                    self.f421set(self.BlueCav)
#                    time.sleep(0.5)
                    print "blueRV = %.2f, BlueCav = %f, deltaBlueCav=%f, IonBright=%.2f"%(bluerv, self.BlueCav, deltaBlueCav, IonBrightness)
            finally:
                # clean up. restore changed parameters
                self.SetParameter('F_RedOn', saved_F_RedOn)
                self.SetParameter('SCloops', saved_SCloops)
                self.SetParameter('ms_ReadoutDly', saved_ms_ReadoutDly)
#                self.SetParameter('ms_TrigDly', saved_ms_TrigDly)
		print "Done locking blue"
            return bluerv, self.BlueCav
        
        except Exception, e:
            print "Exception occurred in BlueLockCounts:", e
	    return -1, self.BlueCav


    def BlueLock(self):
        try:
            print "Locking Blue..."
            self.purgatory(self.plot.clear)
            self.purgatory(self.plot.set_mode, pyextfigure.DUALTWODPLOT)
            self.purgatory(self.plot.set_labels, 'Exp No', 'Scatter', 'Blue Cav')

            # save all parameters that are going to be changed for use in locking
            saved_F_RedOn = self.ReadParameter('F_RedOn')
            saved_SCloops = self.ReadParameter('SCloops')
            saved_ms_ReadoutDly = self.ReadParameter('ms_ReadoutDly')
#            saved_ms_TrigDly = self.ReadParameter('ms_TrigDly')
            try:
                self.OpenDDS('prog/Shelving.pp')
                self.SetParameter('F_RedOn', 0)
                self.SetParameter('SCloops', 0)
                self.SetParameter('ms_ReadoutDly', 0)
#                self.SetParameter('ms_TrigDly', 0)
                self.BlueCav = self.f421read()

                i = 0
                bluerv = -1
                while (i < 30 and not __main__.STOP_FLAG):
                    i = i + 1
                    
                    self.RunDDS()
                    self.ReadUnshelved()
                    bluerv = self.ReadAvgBright()

                    self.purgatory(self.plot.add_point, i, bluerv, self.BlueCav)
                    self.purgatory(self.plot.repaint)
                    deltaBlueCav=- self.const['BlueGain'] * (self.const['IonBrightness'] - bluerv)
                    deltaBlueCavMax=0.008
                    if abs(deltaBlueCav)>deltaBlueCavMax:
                        print "deltaBlueCav too big!",deltaBlueCav
                        deltaBlueCav=deltaBlueCav/abs(deltaBlueCav)*deltaBlueCavMax
                        sys.stdout.flush()
                    self.BlueCav = self.BlueCav + deltaBlueCav
                    self.f421set(self.BlueCav)
#                    time.sleep(0.5)
                    print "blueRV(From DDS) = %.2f, BlueCav = %f"%(bluerv, self.BlueCav)
            finally:
                # clean up. restore changed parameters
                self.SetParameter('F_RedOn', saved_F_RedOn)
                self.SetParameter('SCloops', saved_SCloops)
                self.SetParameter('ms_ReadoutDly', saved_ms_ReadoutDly)
#                self.SetParameter('ms_TrigDly', saved_ms_TrigDly)
		print "Done locking blue"
            return bluerv, self.BlueCav
        
        except Exception, e:
            print "Exception occurred in BlueLock:", e
            self.BlueCav=-1
            raise e
            return -1, self.BlueCav

    def BlueLockNoDDSRun(self):
        try:
            try:
                self.BlueCav = self.f421read()
            except Exception,e:
                print __file__,"Exception occurred in BlueLockNoDDSRun while doing f421read()"
                print e
            bluerv = self.ReadAvgBright()

            # only do this lock if enough ions were bright
            if (self.ReadUnshelved() >= 20):
                if (bluerv > self.const['IonBrightness']/2):
                    deltaBlueCav=- self.const['BlueGain'] * (self.const['IonBrightness'] - bluerv)
                    deltaBlueCavMax=0.002
                    if abs(deltaBlueCav)>deltaBlueCavMax:
                        print "[BlueLockNoDDSRun]: deltaBlueCav too big: %f"%deltaBlueCav
                        deltaBlueCav=deltaBlueCav/abs(deltaBlueCav)*deltaBlueCavMax
                        sys.stdout.flush()
                    self.BlueCav = self.BlueCav+deltaBlueCav 
                    self.f421set(self.BlueCav)
                    print "Ionbrightness=%.3f, bluerv=%.3f, deltaBlueCav=%.5f, BlueCav=%.5f"%(self.const['IonBrightness'],bluerv,deltaBlueCav,self.BlueCav)
                else:
                    print("bluerv<= self.const['IonBrightness']/2 so nothing is done.")
                    print("bluerv=%i, IonBrightness/2=%d"%(bluerv,self.const['IonBrightness']))
            else:
                text="Not enough ions are bright; skipping BlueLock"
                print text
            #  self.Say(text)
            return bluerv, self.BlueCav
        except Exception, e:
            print time.strftime('%H:%M:%S'),__file__,"Exception occurred in BlueLockNoDDSRun:", e
	    return -1, self.BlueCav


# Syntax error?
    def BlueLockNoDDSRunCounts(self,BlueSet):
        try:
#            print "BlueLockNoDDSRunCounts() is running"
            self.BlueCav = self.f421read()
            bluerv = self.ReadAvgBright()
            us_MeasTime = self.ReadParameter('us_MeasTime')
            IonBrightness=us_MeasTime*1e-6*BlueSet
            deltaBlueCav=self.const['BlueGain'] * (IonBrightness - bluerv)
            deltaBlueCavMax=0.1
            # only do this lock if enough ions were bright
            if (self.ReadUnshelved() >= 20):
                if (bluerv > IonBrightness/2):
                    if abs(deltaBlueCav)<deltaBlueCavMax:
                        self.BlueCav = self.BlueCav - deltaBlueCav
                    else:
                        print "deltaBlueCav is to large!"
                        self.BlueCav = self.BlueCav-deltaBlueCav/abs(deltaBlueCav)*deltaBlueCavMax
#                       self.BlueCav = self.BlueCav - self.const['BlueGain'] * (self.const['IonBrightness'] - bluerv)
                    self.f421set(self.BlueCav)
                    print "blueRV = %d, BlueCav = %f, deltaBlueCav=%f, IonBright=%.2f"%(bluerv, self.BlueCav, deltaBlueCav, IonBrightness)
            return bluerv, self.BlueCav


        except Exception, e:
            print "Exception occurred in BlueLockNoDDSRunCounts:", e
	    return -1, self.BlueCav

    def BlueLockFreq(self,freq=710.96305):
        try:
            print "Locking Blue Frequency..."
            self.purgatory(self.plot.clear)
            self.purgatory(self.plot.set_mode, pyextfigure.DUALTWODPLOT)
            self.purgatory(self.plot.set_labels, 'Exp No', 'Frequency-Target frequency [MHz]', 'Blue Cav')
            self.BlueCav_i=self.f421read()
            # save all parameters that are going to be changed for use in locking
#            saved_F_RedOn = self.ReadParameter('F_RedOn')
#            saved_SCloops = self.ReadParameter('SCloops')
#            saved_ms_ReadoutDly = self.ReadParameter('ms_ReadoutDly')
#            saved_ms_TrigDly = self.ReadParameter('ms_TrigDly')
            try:
 #               self.OpenDDS('prog/Shelving.pp')
 #               self.SetParameter('F_RedOn', 0)
 #               self.SetParameter('SCloops', 0)
 #               self.SetParameter('ms_ReadoutDly', 0)
#                self.SetParameter('ms_TrigDly', 0)
                self.BlueCav = self.f421read()
		
                i = 0
                bluerv = -1
                while (i < 30 and not __main__.STOP_FLAG):
                    i = i + 1
                    
#                    self.RunDDS()
#                    self.ReadUnshelved()
#                    bluerv = self.ReadAvgBright()
                    freqrv=self.F422()
                    self.purgatory(self.plot.add_point, i, (freqrv-freq)*1e6, self.BlueCav)
                    self.purgatory(self.plot.repaint)
                    deltaCav=self.freqgain*(freq - freqrv)
		    deltaCavThreshold=0.03
                    if abs(deltaCav)<deltaCavThreshold:
                        self.BlueCav = self.BlueCav - deltaCav 
                    elif abs(deltaCav)/10<deltaCavThreshold:
			print "deltaCav larger than", deltaCavThreshold,", decreasing!"
                        deltaCav=0.02*deltaCav/abs(deltaCav)
                        self.BlueCav=self.BlueCav - deltaCav
                    else:
			print "422 laser is too far off resonant for my taste! FIX IT!"
                        print "deltaCav=%f, freqrv=%f"%(deltaCav,freqrv)
                        if freqrv==-4:
                            print "Channel overexposed!"
                        return -1      		
                    self.f421set(self.BlueCav)
                    time.sleep(0.5)
                    print "freqRV = %f, BlueCav = %f"%(freqrv, self.BlueCav)
            finally:
                # clean up. restore changed parameters
#                self.SetParameter('F_RedOn', saved_F_RedOn)
#                self.SetParameter('SCloops', saved_SCloops)
#                self.SetParameter('ms_ReadoutDly', saved_ms_ReadoutDly)
#                self.SetParameter('ms_TrigDly', saved_ms_TrigDly)
		print "Done locking blue frequency!"
            return freqrv, self.BlueCav
        
        except Exception, e:
            print "Exception occurred in BlueLock:", e
	    return -1, self.BlueCav


    def RamseyLock(self, LockOption, loop):
        try:
            if (not (LockOption & self.RAMSEY)):
                return -1, self.ReadParameter('F_RedCenter')
            
            saved_SCloops = self.ReadParameter('SCloops')
            saved_us_RamseyDly = self.ReadParameter('us_RamseyDly')
            saved_ms_ReadoutDly = self.ReadParameter('ms_ReadoutDly')
            saved_Ph_Ramsey = self.ReadParameter('Ph_Ramsey')

            try:
                self.OpenDDS('prog/Ramsey.pp')
                self.SetParameter('SCloops', self.const['LockSCLoops']) 
                self.SetParameter('us_RamseyDly', self.const['LockRamTime'])
                self.SetParameter('ms_ReadoutDly', 0)
                self.CavOffset = self.ReadParameter('F_RedCenter')

                if (loop): # loop if this is the first time locking
                    print "Locking Red Frequency(RamseyLock)"
		# Set up plotting:
                    self.purgatory(self.plot.set_labels, 'Exp No', 'Signal', 'Cav Offset')
                    locked = 0
		# Clear plot
                    self.purgatory(self.plot.clear)
                    i = 0
                    lockrv = -1
		# Run while not told to stop. Stop if locked for more than 20 iterations!
                    while (not __main__.STOP_FLAG and not (locked > 20)):
                        self.SetParameter('F_RedOn', self.CavOffset)
                        self.SetParameter('Ph_Ramsey', 45.)
		# Run Ramsey.pp
                        self.RunDDS()  
			isok = 0
		# Try to read. If not ok try again!
			while not isok:
			    try:
				lockrv1 = self.ReadUnshelved(hist=True)
				if not len(lockrv1)<2:
				    isok = 1
				else:
				    print "[",__file__,time.asctime(),"] Empty value in lockrv1? = ",lockrv1
				    print "[",__file__,"] Retrying"
				    sys.stdout.flush()
				    time.sleep(0.5)
			    except Exception, inst:
				print "[",__file__, time.asctime(),"] Error in ReadUnshelved Exception: ", inst
				sys.stdout.flush()
				time.sleep(0.5)

                        self.SetParameter('Ph_Ramsey', -45.)
		# Run once more but with Ph_Ramsey shifted from +45 to -45:
                        self.RunDDS()
			isok = 0
			while not isok:
			    try:
				lockrv2 = self.ReadUnshelved(hist=True)
				if not len(lockrv2)<2:
				    isok = 1
				else:
				    print "[",__file__,time.asctime(),"] Empty value in lockrv2? = ",lockrv2
				    print "[",__file__,"] Retrying"
				    sys.stdout.flush()
				    time.sleep(0.5)
			    except Exception, inst:
				print "[",__file__, time.asctime(),"] Error in ReadUnshelved Exception: ", inst
				sys.stdout.flush()
				time.sleep(0.5)
		# Compare lockrv1 and Lockrv2. The only difference is Ph_Ramsey being +45 and -45 respectively.
		# The only change is to the second pulse which gets its phase shifted.
                        if (lockrv1[2] + lockrv2[2] > 20):
                            lockrv = (lockrv2[2] - lockrv1[2])/2.
                        else:
                            lockrv = (lockrv2[1] - lockrv1[1])/2.
                            
                        P = lockrv
                        self.ramD = .99 * self.ramD + .1 * P
                        print "RV = %d, P = %f, ramD = %f, Off = %f"%(lockrv, P, self.ramD, self.CavOffset)
                        self.CavOffset = self.CavOffset + self.const['RamseyGain'] * (P + self.ramD)
                            
                        self.purgatory(self.plot.add_point, i, lockrv, self.CavOffset)
                        self.purgatory(self.plot.repaint)
                        i = i + 1

                        if (abs(self.ramD) < 5.):
                            locked = locked + 1
                        else:
                            locked = 0
                else:   # don't loop during scan
                    self.SetParameter('F_RedOn', self.CavOffset)
                    self.SetParameter('Ph_Ramsey', 45.)
                    self.RunDDS()
		    isok=0
		    while not isok:
			try:
	                	lockrv1 = self.ReadUnshelved(hist=True)
				if not len(lockrv1)<2:
				    isok=1
				else:
				    print "[",__file__,time.asctime(),"] Empty value in lockrv1? =",lockrv1
				    print "Retrying..."
				    sys.stdout.flush()
				    time.sleep(0.5)
		        except Exception,e:
			    print "[",__file__,time.asctime(),"] Error in ReadUnshelved Exception: ",e
			    sys.stdout.flush()
			    time.sleep(0.5)
                    self.SetParameter('Ph_Ramsey', -45.)
                    self.RunDDS()
		    isok=0
		    while not isok:
			try:
				lockrv2 = self.ReadUnshelved(hist=True)
				if not len(lockrv2)<2:
				    isok=1
				else:
				    print "[",__file__,time.asctime(),"] Empty value in lockrv2? =",lockrv2
				    print "Retrying..."
				    sys.stdout.flush()
				    time.sleep(0.5)
		        except Exception,e:
			    print "[",__file__,time.asctime(),"] Error in ReadUnshelved Exception: ",e
			    sys.stdout.flush()
			    time.sleep(0.5)

                    if (lockrv1[2] + lockrv2[2] > 20):
                        lockrv = (lockrv2[2] - lockrv1[2])/2
                    else:
                        lockrv = (lockrv2[1] - lockrv1[1])/2.

                    P = lockrv
                    self.ramD = .99 * self.ramD + .1 * P
                    deltaCavOffsetMax=0.002 # MHz
                    deltaCavOffset=self.const['RamseyGain'] * (P + self.ramD)
                    if abs(deltaCavOffset)>deltaCavOffsetMax:
                        print "deltaCavOffset out of bounds in ramseylock (Stabilization.py)"
                        deltaCavOffset=deltaCavOffset/abs(deltaCavOffset)*deltaCavOffsetMax
                    DoIt=True
                    if DoIt:
                       self.CavOffset = self.CavOffset + deltaCavOffset
                    print "RV = %d, P = %f, ramD = %f, Off = %f, deltaCavOffset=%f"%(lockrv, P, self.ramD, self.CavOffset,deltaCavOffset)
            finally:
                self.SetParameter('F_RedCenter', self.CavOffset)
                self.SetParameter('SCloops', saved_SCloops)
                self.SetParameter('us_RamseyDly', saved_us_RamseyDly)
                self.SetParameter('ms_ReadoutDly', saved_ms_ReadoutDly)
                self.SetParameter('Ph_Ramsey', saved_Ph_Ramsey)

                
            return lockrv, self.CavOffset

        except Exception, e:
            print __file__,time.strftime('%H:%M:%S'),"Exception occurred in RamseyLock:", e
	    return -1, self.CavOffset

# RabiResonanceLock
# Purpose: To lock F_RedCenter to the resonance of the S to D transition of the ion. Essentially the same purpose as RamseyLock but hopefully without the problem of locking to the wrong Ramsey fringe.
# Outline: Do a Rabi flop ie. 0 to 12 us_redtime. Fit the curve and determine amplitude. If amplitude >95% then proceed with RamseyLock. If ampltiude<95% start varying F_RedCenter until above 95%.
# Problem: The error signal does not tell me which side to go to. This means that the lock will be slow.
# Hans, 2011-06-14
    def RabiResonanceLock(self,LockOption,loop):
        print "FIXME: RabiResonanceLock: Not yet implemented!"
        return 0

# Rabi lock adjusts the pi-time in DDScon by doing rabi flops around the peak.
    def RabiLock(self, LockOption, loop):
        try:
            if (not (LockOption & self.RABI)):
                return -1, self.ReadParameter('us_PiTime')

            saved_SCloops = self.ReadParameter('SCloops')
            saved_F_RedOn = self.ReadParameter('F_RedOn')
            saved_us_RedTime = self.ReadParameter('us_RedTime')

            try:
                self.OpenDDS('prog/Shelving.pp')
                self.SetParameter('SCloops', self.const['LockSCLoops'])
                self.SetParameter('F_RedOn', self.CavOffset)
                self.RedPiTime = self.ReadParameter('us_PiTime')
                lockrv = -1
                
                if (loop):
                    print "Locking Red PiTime"
                    self.purgatory(self.plot.set_labels, 'Exp No', 'Signal', 'Red Pi Time')
                    locked = 0

                    self.purgatory(self.plot.clear)
                    i = 0
                    while (not __main__.STOP_FLAG and not (locked > 10) ):
                        self.SetParameter('us_RedTime', self.const['LockRabiFlops'] * self.RedPiTime)
                        self.RunDDS()

			isok = 0
			while not isok:
			    try:
				rv = self.ReadUnshelved(hist=True)
				if not len(rv)<2:
				    isok = 1
				else:
				    print "[",__file__,time.asctime(),"] Empty value in rv? = ",rv
				    print "[",__file__,"] Retrying"
				    sys.stdout.flush()
				    time.sleep(0.5)
			    except Exception, inst:
				print "[",__file__, time.asctime(),"] Error in ReadUnshelved Exception: ", inst
				sys.stdout.flush()
				time.sleep(0.5)
                        if (rv[2] > 10):
                            lockrv = rv[2]
                        else:
                            lockrv = rv[1]

                        P = lockrv - self.const['SamplesPerPoint']/2.
                        self.rabD = .99 * self.rabD + .1 * P
                        print "RV = %d, P = %f, rabD = %f, PiTime = %f"%(lockrv, P, self.rabD, self.RedPiTime)
                        self.RedPiTime = self.RedPiTime + self.const['RabiGain'] * (P + self.rabD)

                        self.purgatory(self.plot.add_point, i, lockrv, self.RedPiTime)
                        self.purgatory(self.plot.repaint)
                        i = i + 1

                        if (abs(self.rabD) < 5.):
                            locked = locked + 1
                        else:
                            locked = 0

                        self.SetParameter('us_PiTime', self.RedPiTime)

                else:
                    if (self.RabiCounter == self.const['RabiEveryCycle']):
                        self.RabiCounter = 0

                        self.SetParameter('us_RedTime', self.const['LockRabiFlops'] * self.RedPiTime)
                        self.RunDDS()  

                        rv = self.ReadUnshelved(hist=True)
                        if (rv[2] > 10):
                            lockrv = rv[2]
                        else:
                            lockrv = rv[1]

                        P = lockrv - self.const['SamplesPerPoint']/2.
                        self.rabD = .99 * self.rabD + .1 * P
                        self.RedPiTime = self.RedPiTime + self.const['RabiGain'] * (P + self.rabD)
                        self.SetParameter('us_PiTime', self.RedPiTime)
                    else:
                        self.RabiCounter = self.RabiCounter + 1
            finally:
                self.SetParameter('SCloops', saved_SCloops)
                self.SetParameter('F_RedOn', saved_F_RedOn)
		self.SetParameter('us_RedTime', saved_us_RedTime)

            return lockrv, self.RedPiTime

        except Exception, e:
            print "Exception occurred in RabiLock:", e
	    return -1, self.RedPiTime
