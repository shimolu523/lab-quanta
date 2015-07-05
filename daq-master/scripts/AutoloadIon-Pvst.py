# AutoloadIon.py
# Hans 2011-03-23
#
from __future__ import division
ARGS=['Freq422','IntTime','Threshold','OvenTime','WaitTime','OvenCurrent']
import time
import scipy as sp
import downhill
import Stabilization
import CavityStabilization
class AutoloadIonClassPvst:
	def __init__(self,filename,dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent):
		reload(Stabilization)
                try:
                    self.plot=gui_exports['plot']
                    self.purgatory=gui_exports['purgatory']
                    self.MMAmp=f_read['IonPhotonCounter_MMAMP']
                    self.Counts=f_read['IonPhotonCounter_COUNT']
                    self.TopmidRead=f_read['3631A_topmid_+6V']
                    self.CompRead=f_read['3631A_comp_+6V']
                    self.TopmidSet=f_set['3631A_topmid_+6V']
                    self.Unshut=f_set['PIShutter_unshut']
                    self.Shut=f_set['PIShutter_shut']
                    self.ScanDone = f_set['AudioAlert_scandone']
                    self.CompSet=f_set['3631A_comp_+6V']
                    self.Magic=f_set['IonPhotonCounter_MAGIC']
                    self.InttimeSet=f_set['IonPhotonCounter_INTTIME']
                    self.InttimeRead=f_read['IonPhotonCounter_INTTIME']
                    self.SetParameter=f_set['DDS_PARAM']
                    self.SetDDS_FREQ1=f_set['DDS_FREQ1']
                    self.SetDDS_AMP1=f_set['DDS_AMP1']
                    self.Say = f_set['AudioAlert_say']
                    self.SetDDS_FREQ0=f_set['DDS_FREQ0']
                    self.SetDDS_AMP0=f_set['DDS_AMP0']
                    self.SetDDS_FREQ2=f_set['DDS_FREQ2']
                    self.ReadParameter=f_read['DDS_PARAM']
                    self.OvenVoltage=f_read['PSUP_3633A_V']
                    self.OvenI=f_set['PSUP_3633A_I']
                    self.F422=f_read['WS7_F3']
                    self.F461=f_read['WS7_F1']
                    self.F674=f_read['WS7_F5']
                    self.inttime_i=self.InttimeRead()
                    self.OvenTime=OvenTime
                    self.inttime=int(IntTime)
                    self.InttimeSet(self.inttime)
                    self.MMAmp_i=self.MMAmp()
                    self.OvenThreshold=0.460
                    self.Threshold=Threshold
                    self.OvenCurrent=OvenCurrent                    
                    self.Freq422=Freq422
                    self.WaitTime=WaitTime
                    self.Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
                    self.const = self.Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
                    self.CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
                    self.const = self.CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
                except Exception as e:
                    print "Exception occured while instantiating AutoloadIonClass:",e
                    raise e
# Setting up database:
                #self.mydb = data.database(filename, dirname, 1, 3, 'Time,Oven Voltage,Counts' )
	def OvenOn(self):
		self.OvenI(self.OvenCurrent)
	def OvenOff(self):
		self.OvenI(0)
	def Autoload(self):
#print "Checking power levels of 422 and 1092 MonoLaser."
#                self.CavStab.MonoLaserLockCheck('421')
#                self.CavStab.MonoLaserLockCheck('1091')

                try:
                    # Set 422 laser frequency 
                    self.F422target=self.Freq422
                    if abs(self.F422()-self.F422target)>0.00001:
                            self.Stab.BlueLockFreq(freq=self.F422target)                    
                    # 461 Frequency:
                    print "461 laser frequency: %.6f"%(self.F461())
                    while abs(650.50386-self.F461())>0.00004:
                        text= "461 laser is off resonance!"
                        print text
#                        self.Say(text)
                        time.sleep(5)
                        if __main__.STOP_FLAG: break
#                        return deltatime,-1                    
                    print "674 laser frequency: %.6f"%(self.F674())
                    if abs(444.77904-self.F674())>0.00003:
                            print "674 laser is off resonance. Recalibrate Wavemeter!"
                            __main__.STOP_FLAG=True
                            return deltatime,-1
                except Exception,e:
                    print "Exception occured while checking/setting laser frequencies:",e
                    raise e
                Counts=self.Counts()
                self.backgroundCounts=self.Counts()
                self.IonThreshold=self.backgroundCounts+self.Threshold
                timestart=time.time()
                try:
                    print "Turning on oven",
                    sys.stdout.flush()
                    self.OvenOn()
                    OvenVoltageStart=self.OvenVoltage()
                    self.Unshut()
                    deltatime=time.time()-timestart
                except Exception,e:
                    print "Exception occured turning on oven and unshutting",e
                    raise e
                try:
                    self.SetDDS_FREQ1(self.ReadParameter('F_BlueHi'))
                    self.SetDDS_AMP1(self.ReadParameter('A_BlueHi'))
                    # Make sure 674 nm laser is off:
                    self.SetDDS_FREQ0(0)
                    self.SetDDS_AMP0(0)
                    # Make sure 422 Cavity Probe Beam is off:
                    self.SetDDS_FREQ2(0)
                except Exception,e:
                        print "Exception occured when setting DDS",e
                        raise e
                numberofions=-1
                try:
                    index=0
                    while True:
                        OvenVoltage=self.OvenVoltage()
                        if __main__.STOP_FLAG: return deltatime,-1, OvenVoltageStart, OvenVoltage
                        time.sleep(0.1)
                        if index<0:                        
                            print ".",
                            index=30
                            sys.stdout.flush()
                        index=index-1                        
                        Counts=self.Counts()
                        end_counts=Counts
                        deltatime=time.time()-timestart

                        if OvenVoltage>self.OvenThreshold:
                                print "\nOven voltage:",OvenVoltage," above OvenThreshold=",self.OvenThreshold
                                print "Too hot! Aborting."
                                return deltatime,-1,OvenVoltageStart, OvenVoltage
                        if deltatime>self.OvenTime:
                                break
                    print "turning off oven and shutting shutters."
                    self.Shut()
                    self.OvenOff()
                    # Determining number of ions:
                    print "Oven on for deltatime=%.f seconds; will wait %.f seconds"%(deltatime,self.WaitTime),
                    sys.stdout.flush()
                    timewaitstart=time.time()
                    while self.WaitTime>time.time()-timewaitstart:
                        time.sleep(1)
                        if __main__.STOP_FLAG: break
                    if self.Counts()>self.IonThreshold:
                        numberofions=1
                    else:
                        numberofions=0
                    print "and loaded %.f ion(s)"%numberofions
                    return deltatime,numberofions, OvenVoltageStart, OvenVoltage
                except Exception,e:
                    print "Exception occured in loading loop",e
                    raise e
		self.InttimeSet(self.inttime_i)
                

def RunScript(filename,dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent):
    AutoloadIon(filename,dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent)
def AutoloadIon(filename, dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent):
	# Instantiate the workhorse:
	Loaderinst=AutoloadIonClassPvst(filename,dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent)
	# Run workhorse
	try:
            deltatime, numberofions, OvenVoltageStart, OvenVoltage=Loaderinst.Autoload()
	except Exception,e:
		Loaderinst.OvenOff()
                __main__.STOP_FLAG=True
		raise e
	Loaderinst.OvenOff()
	Loaderinst.InttimeSet(Loaderinst.inttime_i)
        return deltatime,numberofions
