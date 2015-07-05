#################################################################################################
# LazyPhysicist.py										#
# Hans 2011-04-07										#
#								 				#
# The purpose of the script is to automate as much as possible of the daily routine		#
# when loading ions, optimizing Doppler cooling, 674 scan, Rabi flopping, Sidebandscans etc.	#
#												#
#################################################################################################
ARGS=['LoadIon','DoScan422','DoOptimize1092','DoMicroMotionMiniMization','DoScan674','DoScan1092','DoRabiShort','DoSidebandScan','DoRabiLong','DoCavityResonanceScan','DoCavityStandingWaveScan','DoCavitySidebandScan','DoCavityCoolingDataRun','BlueLockOn','BlueLockLoop','CavLockCheckOn','ProbeLockOn','DoFitAll','DoBlogAll']
import time
import scipy as sp
import sys
import Stabilization
import CavityStabilization
# Adding directory to path where fitting scripts are stored:
sys.path.append('/home/cavityexp/analysis/')
# Importing hansfit which is used to fit most of the taken data:
import hansfit
reload(hansfit)
####

def RunScript(filename, dirname,LoadIon,DoScan422,DoOptimize1092,DoMicroMotionMinimization,DoScan674,DoScan1092,DoRabiShort,DoSidebandScan,DoRabiLong,DoCavityResonanceScan,DoCavityStandingWaveScan,DoCavitySidebandScan,DoCavityCoolingDataRun,BlueLockOn,BlueLockLoop,CavLockCheckOn,ProbeLockOn,DoFitAll,DoBlogAll):
    timestart=time.time()
    plot=gui_exports['plot']
    purgatory=gui_exports['purgatory']
    dirname_Lazy=dirname+'/'+filename
    print "Welcome to the Lazy Physicist! Your one stop shop for all things automatic."
    print "Saving in:",dirname_Lazy
# Putting everything in a separate folder:
    if (os.access(dirname, os.F_OK) == 0):
        os.mkdir(dirname)
    if (os.access(dirname_Lazy, os.F_OK) == 0):
        os.mkdir(dirname_Lazy)
    ScanDone = f_set['AudioAlert_scandone']
    Say = f_set['AudioAlert_say']
    SetBlueCav  = f_set['MonoLasers_421']
    ReadBlueCav=f_read['MonoLasers_421']
    Set1092Cav  = f_set['MonoLasers_1091']
    Read1092Cav = f_read['MonoLasers_1091']
    SetDDS_FREQ1=f_set['DDS_FREQ1']
    SetDDS_AMP1=f_set['DDS_AMP1']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    reload(CavityStabilization)
    reload(Stabilization)
    Stab=Stabilization.Stabilization(f_set,f_read,gui_exports)
    CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
    const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
    success=1
################## List of tasks: ###################

# LoadIon:
    if LoadIon==1 and __main__.STOP_FLAG==False:
            AutoloadIon_filename='AutoloadIon'+time.strftime('-%H%M')
            __main__.app.wTree.plotframe.set_label(AutoloadIon_filename)
            Freq422=710.96304
            IntTime_Autoload=1000
            Threshold_Autoload=1500
            OvenTime=120
            WaitTime=15
            OvenCurrent=2.8
            LoadingTime=10
            NumberOfLoads=10
            DoScan422=1
            deltatime,NumberOfIons=AutoloadIon2(AutoloadIon_filename,dirname_Lazy,Freq422,IntTime_Autoload,Threshold_Autoload, OvenTime, WaitTime, OvenCurrent, LoadingTime, NumberOfLoads, DoScan422)
            if NumberOfIons==0:
                __main__.STOP_FLAG=True
# DoScan422:
    if DoScan422==1 and __main__.STOP_FLAG==False:
        timestamp=time.strftime('%H%M')
        Scan422_filename='Scan422-'+timestamp
        __main__.app.wTree.plotframe.set_label(Scan422_filename)
        SetDDS_FREQ1(ReadParameter('F_BlueHi'))
        SetDDS_AMP1(ReadParameter('A_BlueHi'))
        Stab.BlueLockFreq() 
        plot.clear()
        BlueCav=ReadBlueCav()
        ScanPoints=80
        ScanRepeat=1
        DDSFREQ=[ReadParameter('F_BlueHi'),ReadParameter('F_BlueOn')]
        DDSAMP=[ReadParameter('A_BlueHi'),ReadParameter('A_BlueOn')]
        daccalibration=149 # MHz/V
        delta=20./daccalibration # approximate calibration of 20 MHz. (to do both 251 and 231 scans)
        Width=0.70 # To get rigth width of scan
        offset=-0.10#0.08 # To get right start of scan
        for i in range(len(DDSFREQ)):
            if __main__.STOP_FLAG: break
            StartCav=BlueCav+offset+i*delta
            EndCav=BlueCav+offset-Width+i*delta
            FinishCav=BlueCav+offset+i*delta
            Scan422(Scan422_filename,dirname_Lazy,StartCav,EndCav,FinishCav,ScanPoints,ScanRepeat,DDSFREQ[i],DDSAMP[i])
            time.sleep(1)
        try:
            reload(hansfit)
            fit=hansfit.fitScan422s(dirname_Lazy,timestamp)
        except Exception,e:
            print "Exception occured while doing hansfit.fitScan422s:",e
            traceback.print_exc(file=sys.stdout)
            print "Continuing anyways"
# DoOptimize1092:
    if DoOptimize1092==1 and __main__.STOP_FLAG==False:
        timestamp=time.strftime('%H%M')
        SetDDS_FREQ1(ReadParameter('F_BlueOn'))
        SetDDS_AMP1(ReadParameter('A_BlueOn'))
        Stab.BlueLockFreq() 
        plot.clear()
        BlueCav=ReadBlueCav()
        ScanPoints=50
        ScanRepeat=1
        DDSFREQ=[ReadParameter('F_BlueOn')]#,ReadParameter('F_BlueOn')]
        DDSAMP=[ReadParameter('A_BlueOn')]#,ReadParameter('A_BlueOn')]
        delta=0.134 # approximate calibration of 20 MHz. (to do both 251 and 231 scans)
        Width=0.66 # To get rigth width of scan
        offset=0.08 # To get right start of scan
#Detuning1092s=sp.linspace(1.45,1.95,6)
# Save the initial state of the 1092 DAC2 piezo such that we can return to it at the end of the scan.
        Detuning1092_Saved=Read1092Cav()
#        Detuning1092s=sp.linspace(1.85,2.1,6)
        Delta1092=0.2
        Detuning1092s=Detuning1092_Saved+sp.linspace(-Delta1092,Delta1092,5)
        for j in range(len(Detuning1092s)):
            Detuning1092=Detuning1092s[j]
            Set1092Cav(Detuning1092)
            Scan422_filename='Scan422-IRDF'+str(Detuning1092)+'-'+timestamp
            for i in range(len(DDSFREQ)):
                if __main__.STOP_FLAG: break
                StartCav=BlueCav+offset+i*delta
                EndCav=BlueCav+offset-Width+i*delta
                FinishCav=BlueCav+offset+i*delta
                __main__.app.wTree.plotframe.set_label(Scan422_filename)
                Scan422(Scan422_filename,dirname_Lazy,StartCav,EndCav,FinishCav,ScanPoints,ScanRepeat,DDSFREQ[i],DDSAMP[i])
                time.sleep(1)
        Set1092Cav(Detuning1092_Saved)
        try: 
           fit=hansfit.fitScan422s(dirname_Lazy,timestamp)
        except Exception,e:
            text="Exception occured while doing hansfit.fitScan422s:",e
            print text
# DoMicroMotionMinimization:
    if DoMicroMotionMinimization==1 and __main__.STOP_FLAG==False:         
        print "MicroMotionMinimization script is disabled! -Hans (2012-04-13)"
    '''        MicroMotionMinimization_filename='MicroMotionMinimization'+time.strftime('-%H%M')
            __main__.app.wTree.plotframe.set_label(MicroMotionMinimization_filename)
            IntTime=1000
            acc=0.00001
            delta=0.003
            Beam=0
            MicroMotionMinimization(MicroMotionMinimization_filename,dirname_Lazy,IntTime,acc,delta,Beam)'''
    if DoScan674==1 and __main__.STOP_FLAG==False:
        Scan674_filename='Scan674'+time.strftime('-%H%M')
        __main__.app.wTree.plotframe.set_label(Scan674_filename)
        print "Adjusting 422 frequency (to make sure that we are on the right side of resonance for (231,60) setting"
        Stab.BlueLockFreq(710.96307) 
        print "Doing CavStab.BlueLock to get to the right number of counts"
        CavStab.BlueLock(1,1)
        StartF=195
        EndF=200
        ScanPoints=1000
        ScanRepeat=1
        us_RedTime=30
        SCloops=0
        BlueLockOn=1
        print("Starting Scan674...")
        Scan674(Scan674_filename,dirname_Lazy,StartF,EndF,ScanPoints,ScanRepeat,us_RedTime,SCloops,BlueLockOn)
        
    if DoScan1092==1 and __main__.STOP_FLAG==False:
        print "FIXME: Do Scan1092!"
        Scan1092_filename=time.strftime('Scan1092-%H%M')
        __main__.app.wTree.plotframe.set_label(Scan1092_filename)
    if DoRabiShort==1 and __main__.STOP_FLAG==False:
        Rabi_filename=time.strftime('RabiShort-%H%M')
        __main__.app.wTree.plotframe.set_label(Rabi_filename)
        StartT=0
        EndT=12
        ReadoutDF=0
        ScanPoints=EndT
        ScanRepeat=5
        LockOption=1
        SCloops=75
        Rabi(Rabi_filename, dirname_Lazy, StartT, EndT, ReadoutDF, ScanPoints, ScanRepeat, LockOption,SCloops)
# SidebandScan
    if DoSidebandScan==1 and __main__.STOP_FLAG==False:
        print "Reading StarkSecFRQs from DDScon!"
        StarkSecFRQ1=ReadParameter('F_StarkSec1')
        StarkSecFRQ2=ReadParameter('F_StarkSec2')
        StarkSecFRQ3=ReadParameter('F_StarkSec3')
#       StarkSecFRQ2=0.43043
#       StarkSecFRQ2=0.65315
#       StarkSecFRQ3=0.78078
        Width=0.05
        ReadoutDLY=0
        ScanPoints=31
        ScanRepeat=1
        LockOption=1
        SCloops=75
        SidebandScan_filename=time.strftime('SidebandScan-%H%M')
        __main__.app.wTree.plotframe.set_label(SidebandScan_filename)
        print("Doing %s"%SidebandScan_filename)
#        print "NOTE! Secular frequencies are hard coded in LazyPhysicist.py. Adjust them here to match the fit from Scan674.py"
        SidebandScan(SidebandScan_filename,dirname_Lazy,StarkSecFRQ1,StarkSecFRQ2,StarkSecFRQ3,Width,ReadoutDLY,ScanPoints,ScanRepeat,LockOption,SCloops)

# Long Rabi scan:
    if DoRabiLong==1 and __main__.STOP_FLAG==False:
        Rabi_filename=time.strftime('Rabi-%H%M')
        __main__.app.wTree.plotframe.set_label(Rabi_filename)
        StartT=0
        EndT=200
        ReadoutDF=0
        ScanPoints=EndT
        ScanRepeat=1
        LockOption=1
        SCloops=75
        Rabi(Rabi_filename, dirname_Lazy, StartT, EndT, ReadoutDF, ScanPoints, ScanRepeat, LockOption,SCloops)

# CavityResonanceScan
    if DoCavityResonanceScan==1 and __main__.STOP_FLAG==False:
        CavityResonanceScan_filename=time.strftime('CavityResonanceScan-%H%M')
        __main__.app.wTree.plotframe.set_label(CavityResonanceScan_filename)
        StartF=230.7
        EndF=231.7
        ScanPoints=100
        ScanRepeat=1
        ProbePower=7 # 
        CavityResonanceScan(CavityResonanceScan_filename,dirname_Lazy,StartF,EndF,ScanPoints,ScanRepeat,ProbePower)
    if DoCavityStandingWaveScan==1 and __main__.STOP_FLAG==False:
        CavityStandingWaveScan_filename=time.strftime('CavityStandingWaveScan-%H%M')
        __main__.app.wTree.plotframe.set_label(CavityStandingWaveScan_filename)
        StartV=0
        EndV=12
        ScanPoints=13
        ScanRepeat=1
        ProbeLockOn_local=1 # Named this variable local so not to confuse it with the "global" ProbeLockOn which decides whether LazyPhyscist should do a separate Probelock step.
        ProbeSet=8.6
        BlueLockOn=1
        CavLockOn=1
        IonLockOn=0
        IonSet=0
        SBcool=0
        CavityStandingWaveScan(CavityStandingWaveScan_filename,dirname_Lazy,StartV,EndV,ScanPoints,ScanRepeat,ProbeLockOn_local,ProbeSet,BlueLockOn,CavLockOn,IonLockOn,IonSet,SBcool)
    if 0:
        print "FIXME: Optimize , alignment, Power?"
        print "FIXME: Do 674 scan and read resonances"
        print "FIXME: Do rabi flopping read necessary values"
#        print "FIXME: Do Ramsey spectroscopy"
        print "FIXME: Do essential Cavity stuff"
        print "FIXME: Set all values for Cavity Cooling"
        print "FIXME: Log all essential values"
        print "FIXME: Fit and blog all essential values"
    if not BlueLockOn==0:
        loopmore=1
        while loopmore:
            if __main__.STOP_FLAG: break
            loop=1
            print "Doing CavStab.BlueLock"
            CavStab.BlueLock(BlueLockOn,loop)
            loopmore=0
            if BlueLockLoop==1:
                loopmore=1
# CavLockCheck
    if CavLockCheckOn==1 and __main__.STOP_FLAG==False:
        CavStab.CavLockCheck()
# ProbeLockOn:
    if ProbeLockOn==1 and __main__.STOP_FLAG==False:
        ProbeSet=8.6
        loop=1
        print "Locking ProbePower :%f"%(ProbeSet)
        CavStab.ProbeLock_0deg(ProbeLockOn,ProbeSet,loop)


    if DoFitAll==1 and __main__.STOP_FLAG==False:
        reload(hansfit)
        try:
            hansfit.fitall(dirname_Lazy+'/')
        except Exception,e:
            text="Exception occured while doing hansfit.fitall:",e
            print text
    timeend=time.time()
    deltatime=timeend-timestart
    text="Lazy Physicist is Done."# 
    print "Scan took %d seconds to run."%(deltatime)
    if DoBlogAll==1 and __main__.STOP_FLAG==False:
        reload(hansfit)
        print "Blogging all fitted data and data files"
        try:
            hansfit.BlogAll(dirname_Lazy)
        except Exception,e:
            print "Exception occurred in LazyPhysicist while doing hansfit.BLogAll:",e
#  ScanDone()
    time.sleep(1)
    Say(text)
    print(text)
# The End.
