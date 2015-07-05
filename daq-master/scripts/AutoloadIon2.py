# AutoloadIon.py
# Hans 2011-03-23
#
from __future__ import division
ARGS=['Freq422','IntTime','Threshold','OvenTime','WaitTime','OvenCurrent','LoadingTime','NumberOfLoads','DoScan422']
import time
import scipy as sp
import Stabilization
import CavityStabilization
import sys
import traceback
# Adding directory to path where fitting scripts are stored:
sys.path.append('/home/cavityexp/analysis/')
# Importing hansfit which is used to fit most of the taken dat:
import hansfit
reload(hansfit)
class AutoloadIonClassPvst:
	def __init__(self,filename,dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent,LoadingTime,NumberOfLoads,DoScan422):
		reload(Stabilization)
                try:
                    self.plot=gui_exports['plot']
                    self.purgatory=gui_exports['purgatory']
                    self.dirname=dirname
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
                    self.ReadBlueCav=f_read['MonoLasers_421']
                    self.DoScan422=DoScan422
                    self.inttime_i=self.InttimeRead()
                    self.OvenTime=OvenTime
                    self.LoadingTime=LoadingTime
                    self.inttime=int(IntTime)
                    self.InttimeSet(self.inttime)
                    self.MMAmp_i=self.MMAmp()
                    self.OvenThreshold=0.460
                    self.RFOutput=f_set['AGfungen1_OutPut'] 
                    self.Threshold=Threshold
                    self.OvenCurrent=OvenCurrent                    
                    self.Freq422=Freq422
                    self.WaitTime=WaitTime
                    self.NumberOfLoads=NumberOfLoads
                    self.Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
                    self.const = self.Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
                    self.CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
                    self.const = self.CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
                    label='OvenCurrent=%f, WaitTime=%f, Threshold=%f, Freq422=%f, IntTime=%.f, NumberOfLoads=%f, LoadingTime=%f, OvenTime=%f'%(OvenCurrent,WaitTime, Threshold,Freq422,IntTime,NumberOfLoads,LoadingTime, OvenTime)
                    label=label+'\n#LoadingTime,Probability of ion loading, Oven voltage Start, Oven voltage End'
                    self.mydb = data.database(filename, dirname, 1, 2, label )
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode,pyextfigure.TWODPLOT)
                    self.purgatory(self.plot.set_labels,'Exp no','Ion loaded?','<empty>')
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
                    # Dump ions:
                    self.SetDDS_FREQ1(self.ReadParameter('F_BlueHi'))
                    self.SetDDS_AMP1(self.ReadParameter('A_BlueHi'))
                    self.Shut()
                    self.RFOutput(0)
                    self.RFOutput(1)         
                except Exception,e:
                    print "Exception occured while dumping ion and setting DDScon:",e
                    traceback.print_exc(file=sys.stdout)
                    raise e
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
                self.purgatory(self.plot.clear)
                self.purgatory(self.plot.set_mode,pyextfigure.TWODPLOT)
                self.purgatory(self.plot.set_labels,'Exp no','Ion loaded?','<empty>')
                time.sleep(2)                
                Counts=self.Counts()
                self.backgroundCounts=self.Counts()
                self.IonThreshold=self.backgroundCounts+self.Threshold
                timestart=time.time()
                try:
                    print "Turning on oven",
                    sys.stdout.flush()
                    self.OvenOn()
                    OvenVoltageStart=self.OvenVoltage()
                    deltatime=time.time()-timestart
                except Exception,e:
                    print "Exception occured turning on oven.",e
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
                    print "Oven on for deltatime=%.f seconds; will load for %.f seconds"%(deltatime,self.LoadingTime)
                    # Here goes the loading loop:
                    ionload=sp.zeros(self.NumberOfLoads)
                    for i in range(self.NumberOfLoads):
                        print "Opening shutters."
                        self.Unshut()
                        timewaitstart=time.time()
                        while self.LoadingTime>time.time()-timewaitstart:
                            time.sleep(0.05)
                            if __main__.STOP_FLAG: break 
                        self.Shut()
                        timewaitstart=time.time()
                        OvenVoltage=self.OvenVoltage()                        
                        while self.WaitTime>time.time()-timewaitstart:
                            time.sleep(0.05)
                            if __main__.STOP_FLAG: break 
                        Counts=self.Counts()
                        print "Counts: %.f, threshold+background=%.f"%(Counts,self.IonThreshold)
                        if Counts>self.IonThreshold:
                            ionload[i]=1
                            # DoScan422: To estimate one or two ions.
                            if self.DoScan422==1 and __main__.STOP_FLAG==False:
                                self.InttimeSet(self.inttime_i)                                
                                timestamp=time.strftime('%H%M')
                                Scan422_filename='Scan422-'+timestamp
                                __main__.app.wTree.plotframe.set_label(Scan422_filename)
                                self.SetDDS_FREQ1(self.ReadParameter('F_BlueHi'))
                                self.SetDDS_AMP1(self.ReadParameter('A_BlueHi'))
                                self.Stab.BlueLockFreq() 
                                self.plot.clear()
                                BlueCav=self.ReadBlueCav()
                                ScanPoints=80
                                ScanRepeat=1
                                # Do a Scan422 at Hi settings to test number of peakscounts.
                                DDSFREQ=[self.ReadParameter('F_BlueHi')]
                                DDSAMP=[self.ReadParameter('A_BlueHi')]
                                # approximate calibration of 20 MHz. (to do both 251 and 231 scans)
                                delta=0.134 
                                Width=0.70 # To get rigth width of scan
                                offset=-0.10#0.08 # To get right start of scan
                                for i in range(len(DDSFREQ)):
                                    if __main__.STOP_FLAG: break
                                    StartCav=BlueCav+offset+i*delta
                                    EndCav=BlueCav+offset-Width+i*delta
                                    FinishCav=BlueCav+offset+i*delta
                                    Scan422(Scan422_filename,self.dirname,StartCav,EndCav,FinishCav,ScanPoints,ScanRepeat,DDSFREQ[i],DDSAMP[i])
                                    time.sleep(1)
                                self.InttimeSet(self.inttime)
                                try:
                                    #p1=hansfit.fitScan422(self.dirname,Scan422_filename)
                                    #print p1
                                    #peakcounts=p1[0]
                                    peakcounts=hansfit.Max_Counts(self.dirname,Scan422_filename)
                                    print "peakcounts from fit:",peakcounts
                                    if peakcounts>180000: # Fixme: Should look at 
                                        ionload[i]=2
                                        self.RFOutput(0)
                                        self.RFOutput(1)
                                    else:
                                        ionload[i]=1
                                        break
                                except Exception,e:
                                    print "Exception occured while doing hansfit.fitScan422:",e
                                    traceback.print_exc(file=sys.stdout)
                                    print "Continuing anyways"
                                    break
                            else: break
                        else:
                            ionload[i]=0
                            self.RFOutput(0)
                            self.RFOutput(1)
                            time.sleep(self.inttime/1000)
                            self.backgroundCounts=self.Counts()
                            self.IonThreshold=self.backgroundCounts+self.Threshold
                        print "and loaded %.f ion(s)"%ionload[i]
                        self.mydb.add_data_point([i,ionload[i]])
                        self.purgatory(self.plot.add_point,i,ionload[i],0)
                        self.purgatory(self.plot.repaint)
                        OvenVoltage=self.OvenVoltage()
                    self.OvenOff()
                    ProbIon=sum(ionload)/self.NumberOfLoads

                    print "Probability of loading ion (for loadingtime=%f) is: %f"%(self.LoadingTime,ProbIon)
                    self.InttimeSet(self.inttime_i)

                    return self.LoadingTime,ProbIon, OvenVoltageStart, OvenVoltage
                except Exception,e:
                    print "Exception occured in loading loop",e
                    self.InttimeSet(self.inttime_i)
                    raise e
		
                

def RunScript(filename,dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent,LoadingTime,NumberOfLoads,DoScan422):
    AutoloadIon2(filename,dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent,LoadingTime,NumberOfLoads,DoScan422)
def AutoloadIon2(filename, dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent,LoadingTime,NumberOfLoads,DoScan422):
	# Instantiate the workhorse:
	Loaderinst=AutoloadIonClassPvst(filename,dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent,LoadingTime,NumberOfLoads,DoScan422)
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
