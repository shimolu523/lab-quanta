# CavityLock.py
# Hans 2011-03-02
# Script to automatically lock the cavity. Useful for automatic relocking when cavity falls out of lock...
ARGS=[]
import time
import scipy as sp
import downhill
class MMMinimize:
	def __init__(self):
		print "Initiating"
		self.plot=gui_exports['plot']
		self.purgatory=gui_exports['purgatory']
		self.MMAmp=f_read['IonPhotonCounter_MMAMP']
		self.TopmidRead=f_read['3631A_topmid_+6V']
		self.CompRead=f_read['3631A_comp_+6V']
		self.TopmidSet=f_set['3631A_topmid_+6V']
		self.CompSet=f_set['3631A_comp_+6V']
		self.RFSet=f_set['AGfungen1_Freq']
	# saving initial values in case something goes wrong:
		self.Topmid_i=self.TopmidRead()
		self.Comp_i=self.CompRead()
		self.RF_i=14.32e6
	# No such thing yet:
#		self.RFRead=f_read['?']
	def VSetAndProbe(self,p):
		# Set voltages
		Topmid=p[0]
		Comp=p[1]
		self.TopmidSet(Topmid)
		self.CompSet(Comp)
		time.sleep(1)
		rv = abs(self.MMAmp())
		print "Topmid,Comp,MMamp",Topmid,Comp,rv
		return rv
	def mmotion(self):
		print "Minimizing micromotion. Initially MMamp:",self.MMAmp()
		print "Remember that integration time should be 'long'"
		Topmid=self.TopmidRead()
		Comp=self.CompRead()
#		Topmid=3.6
#		Comp=3.4
		print "Initial values: Topmid=%f, Comp=%f"%(Topmid,Comp)
		# Variation parameters:
#		nsteps=50 # number of steps for each dimension
#		stepsize=0.001 # volts
#		stepdelay=0.5 # seconds	
		acc=1e-3
		delta=acc*10
		pi=sp.array([[Topmid,Comp],[Topmid+delta,Comp+delta],[Topmid-delta,Comp-delta]])
		
		F=self.VSetAndProbe
		F(pi[0])
		# Run downhill algorithm (for one RF setting):
		# Let's assume RF=14.32 MHz
		pf=downhill.amoeba(F,pi,acc)
		print "Final values: Topmid=%f, Comp=%f"%(Topmid,Comp)
		print "Micromotion amplitude:",self.MMAmp()


def RunScript(filename, dirname):
	reload (downhill)
	# Instantiate the workhorse:
	Minimize=MMMinimize()
	# Run workhorse
	try:
		Minimize.mmotion()
	except Exception,e:
		print "[",__file__,time.asctime(),"] An exception occured:",e
		print "Setting inital values again Topmid,Comp",Minimize.Topmid_i,Minimize.Comp_i
		Minimize.TopmidSet(Minimize.Topmid_i)
		Minimize.CompSet(Minimize.Comp_i)
		Minimize.RFSet(Minimize.RF_i)
		raise e
	print "Done"
# Does not work in Python version<2.5:
#	finally:
#		self.RFSet(14.32e6)

# Test running:
#RunScript('MMMtesting','/home/data/MMMtesting')
