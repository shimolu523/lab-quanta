import __main__
import re, pyextfigure
import time
import scipy
import scipy.optimize

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
        self.RunDDSandReadTotal = f_read['DDS_RUNNTOTAL']
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
       # self.CavityLockLevelRead = f_read['DMM_top_V']
        
        self.beam0 = 24.
        self.beam90 = 0.
        
        self.maxProbePower = 15.
        
        self.BlueCav = self.f421read()
        self.CavCenter = self.ReadParameter('F_CavityCenter')
        self.ProbePower = self.ProbePowerRead()
        self.IonPos = self.IonPosRead()
       # self.CavityLockLevel = self.CavityLockLevelRead()
        if self.IonPos > 0:
            self.IonPos = 0
        
        self.const = {}

        self.BlueCounter = 1
        self.CavCounter = 1
        self.ProbeCounter = 1
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
    
   # def CavityLockCheck(self):
        

    def BlueLock(self, BlueLockOn, loop):
        try:
            if ((not((BlueLockOn > 0) & ((loop) | (self.BlueCounter == BlueLockOn)))) | (__main__.STOP_FLAG)):
                self.BlueCounter = self.BlueCounter + 1
                return -1, self.BlueCav
            self.BlueCounter = 1
            
            try:
                self.DCFreqSet(self.ReadParameter('F_BlueOn'))
                self.DCAmpSet(self.ReadParameter('A_BlueOn'))
                self.CavFreqSet(0)

                bluerv = -1
                if (loop):
                    print "Locking Blue"
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode, pyextfigure.DUALTWODPLOT)
                    self.purgatory(self.plot.set_labels, 'Exp No', 'Scatter', 'Blue Cav')
                
                    self.BlueCav = self.f421read()

                    i = 0
                    while (i < 20 and not __main__.STOP_FLAG):
                        i = i + 1
                    
                        time.sleep(0.5)
                        bluerv = self.ReadIonPMT()

                        self.purgatory(self.plot.add_point, i, bluerv, self.BlueCav)
                        self.purgatory(self.plot.repaint)

                        if bluerv > 0.2*self.const['BlueSet']:
                            self.BlueCav = self.BlueCav - self.const['BlueGain'] * (self.const['BlueSet'] - bluerv) / self.const['BlueSet']
                        self.f421set(self.BlueCav)
                        print "blueRV = %d, BlueCav = %f"%(bluerv, self.BlueCav)
                else:
                    time.sleep(0.5)
                    bluerv = self.ReadIonPMT()
		# This is where the cavity falls out of lock! Changing bluecav too much at one time is bad! 
                    if bluerv > 0.2*self.const['BlueSet']:
                        self.BlueCav = self.BlueCav - self.const['BlueGain'] * (self.const['BlueSet'] - bluerv) / self.const['BlueSet']
                    self.f421set(self.BlueCav)
                    print "blueRV = %d, BlueCav = %f"%(bluerv, self.BlueCav)

            finally:
                self.DCFreqSet(self.ReadParameter('F_BlueHi'))
                self.DCAmpSet(self.ReadParameter('A_BlueHi'))
            
            return bluerv, self.BlueCav
        
        except Exception, e:
            print "Exception occurred in BlueLock:", e
	    return -1, self.BlueCav

    def CavLock(self, CavLockOn, loop):
        try:
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
                time.sleep(0.2)
                
                cavrv = -1
                if (loop):
                    print "Locking Cavity Center"
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode, pyextfigure.DUALTWODPLOT)
                    self.purgatory(self.plot.set_labels, 'Exp No', 'Signal', 'Cav Center')

                    self.CavCenter = self.ReadParameter('F_CavityCenter')

                    i = 0
                    while (i < 20 and not __main__.STOP_FLAG):
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

                        self.CavCenter = self.CavCenter + self.const['CavGain'] * cavrv
                        self.SetParameter('F_CavityCenter', self.CavCenter)
                        print "cavRV = %f, CavCenter = %f"%(cavrv, self.CavCenter)
                else:
                    self.CavFreqSet(self.CavCenter - self.const['CavFWHM']/2)
                    time.sleep(0.5)
                    cavrv1 = self.ReadCavPMT()

                    self.CavFreqSet(self.CavCenter + self.const['CavFWHM']/2)
                    time.sleep(0.5)
                    cavrv2 = self.ReadCavPMT()
                        
                    cavrv = 2.*(cavrv2 - cavrv1)/(cavrv1 + cavrv2)
                    
                    self.CavCenter = self.CavCenter + self.const['CavGain'] * cavrv
                    self.SetParameter('F_CavityCenter', self.CavCenter)
                    print "cavRV = %f, CavCenter = %f"%(cavrv, self.CavCenter)                    
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
                    print "Locking Probe Power"
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

                        if proberv < 0.2*ProbeSet:
                            self.ProbePower = self.ProbePower + self.const['ProbeGain'] * (ProbeSet - proberv) / ProbeSet
                            if self.ProbePower < 0:
                                self.ProbePower = 0
                            if self.ProbePower > 15:
                                self.ProbePower = 15
                        self.ProbePowerSet(self.ProbePower)
                        print "probeRV = %f, ProbePower = %f"%(proberv, self.ProbePower)
                else:
                    time.sleep(0.2)
                    proberv = self.ProbePowerMeasure()

                    if proberv < 0.2*ProbeSet:
                        self.ProbePower = self.ProbePower + self.const['ProbeGain'] * (ProbeSet - proberv) / ProbeSet
                        if self.ProbePower < 0:
                            self.ProbePower = 0
                        if self.ProbePower > 15:
                            self.ProbePower = 15
                    self.ProbePowerSet(self.ProbePower)
                    print "probeRV = %f, ProbePower = %f"%(proberv, self.ProbePower)
            finally:
                self.CavBeamSet(saved_CavBeam)
                self.CavFreqSet(0)
                self.ProbePowerSet(saved_ProbePower)
                time.sleep(0.2)
            
            return proberv, self.ProbePower
        
        except Exception, e:
            print "Exception occurred in ProbeLock:", e
	    return -1, self.ProbePower

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
                self.CavFreqSet(self.CavCenter)
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
                self.CavFreqSet(0)
                self.ProbePowerSet(saved_ProbePower)
                self.f421quiet(0)
                time.sleep(2.0)
            
            return ionrv, self.IonPos
        
        except Exception, e:
            print "Exception occurred in IonLock:", e
	    return -1, self.IonPos
