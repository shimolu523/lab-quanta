# MicromotionMinimization.py
# Hans 2011-03-03
# Edited 2011-03-20 To add automatic setting of Magic and integration time.
# Edited 2011-07-06 To add Backquarter
ARGS=['IntTime','acc','delta','Beam (degree)']
import time
import scipy as sp
import downhill
import CavityStabilization
class MMMinimize:
	def __init__(self,filename,dirname,IntTime=5000,acc=1e-4,delta=0,Beam=45):
                self.Beam=Beam
                self.ScanDone = f_set['AudioAlert_scandone']
		self.plot=gui_exports['plot']
		self.purgatory=gui_exports['purgatory']
		self.MMAmp=f_read['IonPhotonCounter_MMAMP']
		self.TopmidRead=f_read['3631A_topmid_+6V']
		self.CompRead=f_read['3631A_comp_+6V']
		self.BackquarterRead=f_read['3631A_topright_+25V']
		self.TopmidSet=f_set['3631A_topmid_+6V']
		self.BackquarterSet=f_set['3631A_topright_+25V']
		self.CompSet=f_set['3631A_comp_+6V']
#		self.RFSet=f_set['AGfungen1_Freq']
		self.Magic=f_set['IonPhotonCounter_MAGIC']
		self.InttimeSet=f_set['IonPhotonCounter_INTTIME']
		self.InttimeRead=f_read['IonPhotonCounter_INTTIME']
                self.ReadIonPMTALL=f_read['IonPhotonCounter_ALL']
                self.SetDDS_FREQ1=f_set['DDS_FREQ1']
                self.SetDDS_FREQ2=f_set['DDS_FREQ2']
                self.SetDDS_AMP1=f_set['DDS_AMP1']
                self.SetDDS_FREQ0=f_set['DDS_FREQ0']
                self.SetDDS_AMP0=f_set['DDS_AMP0']
                self.SetParameter  = f_set['DDS_PARAM']
                self.ReadParameter  = f_read['DDS_PARAM']
                self.CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
                self.const = self.CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')

	# saving initial values in case something goes wrong:
		self.Topmid_i=self.TopmidRead()
		self.Comp_i=self.CompRead()
		self.Backquarter_i=self.BackquarterRead()
		self.inttime_i=self.InttimeRead()
		self.inttime=int(IntTime)
		self.acc=acc
		if delta==0:
			self.delta=self.acc*30
		else:
			self.delta=delta
		self.InttimeSet(self.inttime)
		self.Magic(1)
                time.sleep(self.inttime/1000.)

                try:
                    self.purgatory(self.plot.clear)
                    self.purgatory(self.plot.set_mode, pyextfigure.THREEDPLOT)  
                    spotsize=0.0003
                    self.purgatory(self.plot.set_spot_shape,spotsize,spotsize)
                    self.purgatory(self.plot.set_labels,'Topmid', 'Comp','MMamp')
                except Exception,e:
                    print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when setting up plot'
                    print e
                self.mydb = data.database(filename, dirname, 1, 4, 'Topmid, Comp,Backquarter, MMamp')
                                    # Turn on the right beams:
            #   Turn of 674
                self.SetDDS_FREQ0(0)
                self.SetDDS_AMP0(0)
            #   Choose beam:
                if self.Beam==0:
                    self.CavStab.CavLockCheck()
                    self.SetDDS_FREQ1(0)
                    self.SetDDS_AMP1(0)
                    self.SetDDS_FREQ2(self.ReadParameter('F_CavityCenter'))
                elif self.Beam==45:
                    self.SetDDS_FREQ1(self.ReadParameter('F_BlueOn'))
                    self.SetDDS_AMP1(self.ReadParameter('A_BlueOn'))
                    self.SetDDS_FREQ2(0)
                else:
                    print "Unrecognized beam. Will not change beams"
                time.sleep(2*self.inttime/1000)
                try:
                    rv=self.ReadIonPMTALL()[4]
                    self.MMAmp_i=float(rv) # This is actually fftmax!
                except Exception,e:
                    print "Exception occured reading from IonPMTALL:",e
                    raise e

	def VSetAndProbe(self,p):
                try:
                    if __main__.STOP_FLAG: return 0
                    # Set voltages
                    Topmid=p[0]
                    Comp=p[1]
                    Backquarter=p[2]
                    self.TopmidSet(Topmid)
                    self.CompSet(Comp)
                    self.BackquarterSet(Backquarter)
                    # Turn on the right beams:
                #   Turn of 674
                    self.SetDDS_FREQ0(0)
                    self.SetDDS_AMP0(0)
                #   Choose beam:
                    if self.Beam==0:
                        self.CavStab.CavLockCheck()
                        self.SetDDS_FREQ1(0)
                        self.SetDDS_AMP1(0)
                        self.SetDDS_FREQ2(self.ReadParameter('F_CavityCenter'))
                    elif self.Beam==45:
                        self.SetDDS_FREQ1(self.ReadParameter('F_BlueOn'))
                        self.SetDDS_AMP1(self.ReadParameter('A_BlueOn'))
                        self.SetDDS_FREQ2(0)
                    else:
                        print "Unrecognized beam. Will not change beams"
                    time.sleep(2*self.inttime/1000)
                    try:
                        rv=self.ReadIonPMTALL()[4]
#        		self.MMAmp_i=float(rv) # This is actually fftmax!
                    except Exception,e:
                        print "Exception occured reading from IonPMTALL:",e
                        raise e
                except Exception,e:
                    print "Exception occured in VSetandProbe:",e
                    raise e
#              self.mmamp=rv
                try:
                    self.purgatory(self.plot.add_point,Topmid,Comp,float(rv))
                    self.purgatory(self.plot.repaint)
                except Exception,e:
                    print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when adding plot point'
                    print e
                    raise e

                self.mydb.add_data_point([rv,Topmid,Comp,Backquarter])
		print "Topmid,Comp,Backquarter,MMAmp: %.4f %.4f %.4f %.4f"%(Topmid,Comp,Backquarter,float(rv))
		return rv
	def mmotion(self):
		Topmid=self.TopmidRead()
		Comp=self.CompRead()
                Backquarter=self.BackquarterRead()
		print "Initial values: Topmid=%.4f, Comp=%.4f, Backquarter=%.4f"%(Topmid,Comp,Backquarter)
		# Variation parameters:
		acc=self.acc #1e-4
		delta=self.delta #acc*30
		pi=sp.array([[Topmid,Comp,Backquarter],[Topmid-delta,Comp-delta,Backquarter-delta],[Topmid+delta,Comp+delta,Backquarter+delta],[Topmid+delta,Comp-delta,Backquarter]])
		
                try:
                        F=self.VSetAndProbe
#                        F(pi[0])
                except Exception,e:
                    print "Exception:",e
                    raise e
#    Run downhill alogrithm to find minimum in space of comp, top mid and back quarter
		try:
                    pf=downhill.amoeba(F,pi,acc)
                except Exception,e:
                    print time.strftime("%H:%M:%S"),"Exception occured in downhill amoeba:",e
                    raise e
		self.MMAmp_f=float(self.ReadIonPMTALL()[4])
		if None==pf:
                    improvement=-1
                    print "pf is not available!"
                else:
        		improvement=self.MMAmp_f-self.MMAmp_i
		print "Micromotion amplitude:",self.MMAmp_f, "Initially:",self.MMAmp_i
		print "Delta MMAmplitude:",improvement,improvement/abs(self.MMAmp_i)*100.,"in percent"
		
		self.InttimeSet(self.inttime_i)
		self.Magic(0)
                self.SetDDS_FREQ1(self.ReadParameter('F_BlueHi'))
                self.SetDDS_AMP1(self.ReadParameter('A_BlueHi'))
                self.SetDDS_FREQ2(0)
		if improvement>0:
			# Revert.
			print "Worse! Reverting to initial setttings"
			self.TopmidSet(self.Topmid_i)
			self.CompSet(self.Comp_i)
			self.BackquarterSet(self.Backquarter_i)
			#Minimize.RFSet(Minimize.RF_i)

def RunScript(filename, dirname,IntTime,acc,delta,Beam=45):
    MicroMotionMinimization(filename,dirname,IntTime,acc,delta,Beam)
def MicroMotionMinimization(filename,dirname,IntTime,acc,delta,Beam):
	reload (downhill)
	# Instantiate the workhorse:
	Minimize=MMMinimize(filename,dirname,IntTime,acc,delta,Beam)
	# Run workhorse
	try:
		Minimize.mmotion()
	except Exception,e: ### Clean up in case script broke!
		print time.strftime("%H:%M:%S:"), 'An exception occured in Minimize.mmotion:',e
		print "Setting inital values again Topmid,Comp",Minimize.Topmid_i,Minimize.Comp_i
		Minimize.TopmidSet(Minimize.Topmid_i)
		Minimize.CompSet(Minimize.Comp_i)
		Minimize.BackquarterSet(Minimize.Backquarter_i)
		raise e
	print "Done"
        Minimize.ScanDone()
