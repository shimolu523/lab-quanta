# AutoloadIon.py
# Hans 2011-03-23
# 
ARGS=['Freq422','IntTime','Threshold']
import time
import scipy as sp
import downhill
import Stabilization
class AutoloadIonClass:
	def __init__(self,filename,dirname,Freq422,IntTime,Threshold):
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
#		self.RFSet=f_set['AGfungen1_Freq']
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
            # saving initial values in case something goes wrong:
#		self.Topmid_i=self.TopmidRead()
#		self.Comp_i=self.CompRead()
                    self.inttime_i=self.InttimeRead()
                    self.inttime=int(IntTime)
                    self.InttimeSet(self.inttime)
#		self.Magic(1)
#		self.RF_i=14.32e6
#		self.RF_high=14.32e6
#		self.RF_low=14.26e6
                    self.MMAmp_i=self.MMAmp()
#		Set DDS freq/amp for 422!
                    self.OvenThreshold=1#0.437 
                    self.Threshold=Threshold
                    self.Freq422=Freq422
                    self.Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
                    self.const = self.Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
                    self.CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
                    self.const = self.CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
                except Exception as e:
                    print "Exception occured while instantiating AutoloadIonClass:",e
                    raise e
# Setting up database:
                self.mydb = data.database(filename, dirname, 1, 2, 'Oven Voltage,Counts' )
	# No such thing yet:
#		self.RFRead=f_read['?']
	def OvenOn(self):
		self.OvenI(3.2)
	def OvenOff(self):
		self.OvenI(0)
	def Autoload(self):
                success=0
                IonLoaded=False
                print "Checking power levels of 422 and 1092 MonoLaser."
                self.CavStab.MonoLaserLockCheck('421')
                self.CavStab.MonoLaserLockCheck('1091')
                try:
        		self.OvenOn()
	        	self.Unshut()
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
                        print "Exception occurd when setting DDS",e
                        raise e
                try:
                    print "674 laser frequency: %.6f"%(self.F674())
                    if abs(444.77904-self.F674())>0.00003:
                            print "674 laser is off resonance. Recalibrate Wavemeter!"
                            __main__.STOP_FLAG=True
                            return -1
                    # Set 422 laser frequency 
                    self.F422target=self.Freq422
                    self.Stab.BlueLockFreq(freq=self.F422target)
                    if abs(self.F422()-self.F422target)>0.00002:
                            self.Stab.BlueLockFreq(freq=self.F422target)

                    # 461 Frequency:
                    print "461 laser frequency: %.6f"%(self.F461())
                    if abs(650.50386-self.F461())>0.00004:
                        text= "461 laser is off resonance!"
                        print text
                        self.Say(text)
                        __main__.STOP_FLAG=True
                        return -1
                except Exception,e:
                    print "Exception occured while checking/setting laser frequencies:",e
                    raise e
		print "Turning on oven"
                try:
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode,pyextfigure.TWODPLOT)
                    self.purgatory(self.plot.set_labels,'OvenVoltage','Counts','<empty>')
                except Exception,e:
                    print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory while setting up plot:'
                    print e
		Counts=self.Counts()
		time.sleep(2)
		self.backgroundCounts=self.Counts()	
		self.IonThreshold=self.backgroundCounts+self.Threshold
                index=0
                try:
                    print time.strftime('%H:%M:%S'),"Loading ion. Background counts(with 422):",self.backgroundCounts
                    while Counts<self.IonThreshold:
                            if __main__.STOP_FLAG: break
                            time.sleep(1)
                            OvenVoltage=self.OvenVoltage()
                            Counts=self.Counts()
                            index=index+1
                            print "OvenVoltage,Counts:",OvenVoltage,Counts
                            try:
                                self.purgatory(self.plot.add_point,OvenVoltage,Counts,0)
                                self.purgatory(self.plot.repaint)
                            except Exception,e:
                                print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when adding plot point'
                                print e
                            self.mydb.add_data_point([OvenVoltage,Counts])
                            if OvenVoltage>self.OvenThreshold:
                                    print "Oven voltage:",OvenVoltage," above OvenThreshold=",self.OvenThreshold
                                    print "Too hot! Aborting."
                                    success=0        
#                                __main__.STOP_FLAG=True
                                    break
                            maxindex=80
                            if index>maxindex:
                                    print "Loops iterations:",index," above max iterations=",index
                                    print "Running for too long: Abort!"
                                    success=0        
#                                __main__.STOP_FLAG=True
                                    break

                            success=1
                    self.Shut()
                    self.OvenOff()
                    print "Loading for %d iterations of loading loop"%index
                except Exception,e:
                    print "Exception occured in loading loop",e
                    raise e
                print("Checking whether ion was loaded...")
                checktime=self.inttime*3
                self.InttimeSet(checktime)
                time.sleep(checktime/1000.*2)
                Counts=self.Counts()
                if Counts>self.IonThreshold:
                    IonLoaded=True
                else:
                    IonLoaded=False
		self.InttimeSet(self.inttime_i)
                # Test if an ion was actually loaded:
                
                if IonLoaded==True:
                    print "Succesfully loaded an ion (probably), counts:",Counts
                    return success
                else:
                    __main__.STOP_FLAG==True
                    print "Probably no ion here, stopping...counts were:",Counts
                    success=0
                    return success

def RunScript(filename,dirname,Freq422,IntTime,Threshold):
    AutoloadIon(filename,dirname,Freq422,IntTime,Threshold)
def AutoloadIon(filename, dirname,Freq422,IntTime,Threshold):
	# Instantiate the workhorse:
	Loaderinst=AutoloadIonClass(filename,dirname,Freq422,IntTime,Threshold)
	# Run workhorse
	try:
	    success=Loaderinst.Autoload()
	except Exception,e:
                success=0
                print "[",__file__,time.asctime(),"] An exception occured in Loaderinst.Autoload():",e
		Loaderinst.InttimeSet(Loaderinst.inttime_i)
		Loaderinst.OvenOff()
                __main__.STOP_FLAG=True
		raise e
	Loaderinst.OvenOff()
	Loaderinst.InttimeSet(Loaderinst.inttime_i)
        Loaderinst.ScanDone()
        return success
# Test running:
#RunScript('MMMtesting','/home/data/MMMtesting')
