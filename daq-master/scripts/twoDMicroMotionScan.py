# twoDMicroMotionScan.py
# 2011-05-04 Hans Harhoff Andersen
# Purpose: To do 422 scan automatically.
ARGS = ['StartX','EndX','FinishX','StartY','EndY','FinishY','StepsX','StepsY','Pause','Beam']
import Stabilization
import CavityStabilization
import time
import sys
import scipy as sp

def twoDMicroMotionScan(filename,dirname,StartX,EndX,FinishX,StartY,EndY,FinishY,StepsX,StepsY,Pause,Beam):

# Import functions:
    reload(Stabilization)
    Beam=int(Beam)
    plot=gui_exports['plot']
    purgatory=gui_exports['purgatory']
    ScanDone = f_set['AudioAlert_scandone']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    ReadUnshelved = f_read['DDS_NBRIGHT']
    ReadAvgBright = f_read['DDS_LASTAVG']
    SetBlueCav  = f_set['MonoLasers_421']
    ReadBlueCav  = f_read['MonoLasers_421']
    Quiet = f_set['MonoLasers_Quiet421']
    SetDDS_FREQ1=f_set['DDS_FREQ1']
    SetDDS_FREQ2=f_set['DDS_FREQ2']
    SetDDS_AMP1=f_set['DDS_AMP1']
    SetDDS_FREQ0=f_set['DDS_FREQ0']
    SetDDS_AMP0=f_set['DDS_AMP0']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    ReadIonPMT = f_read['IonPhotonCounter_COUNT']
    ReadMMAMP = f_read['IonPhotonCounter_MMAMP']
    ReadIonPMTALL=f_read['IonPhotonCounter_ALL']
    InttimeSet=f_set['IonPhotonCounter_INTTIME']
    InttimeRead=f_read['IonPhotonCounter_INTTIME']
    inttime_i=InttimeRead()
    Magic=f_set['IonPhotonCounter_MAGIC']
#####    
#    xlabel='3631A_topright_+25V' # Back quarter
    xlabel='3631A_topmid_+6V' # Top mid
    ylabel='3631A_comp_+6V' # Comp
    print time.strftime("%H:%M:%S"),"Scanning",xlabel," and ", ylabel
#####
    SetX = f_set[xlabel]
    SetY = f_set[ylabel]
    Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
    const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
    plotlabelz='fftmax'
    #### Locking #######
    BlueLockOn=0
    if BlueLockOn==1:
        bluelockrv, BlueCav = Stab.BlueLock()
    
    CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
    const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
# Set up plotting:
    try:
        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.THREEDPLOT)  
        purgatory(plot.set_labels, xlabel,ylabel,plotlabelz)
        StepSizeX=(EndX-StartX)/(StepsX)
        StepSizeY=(EndY-StartY)/(StepsY)
        purgatory(plot.set_spot_shape,abs(StepSizeX),abs(StepSizeY))
    except Exception,e:
        print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when setting up plot'
	print e
    comment='StepsX=%s,StepsY=%s,Beam=%s,Pause=%s\nX,Y,counts,mmamp,mmphase,maxmin,fftmax'%(StepsX,StepsY,Beam,Pause)
    mydb = data.database(filename, dirname, 2, 7,comment)

    CavStab.CavLockCheck()
#   Turn of 674
    SetDDS_FREQ0(0)
    SetDDS_AMP0(0)
#   Choose beam:
    if Beam==0:
        SetDDS_FREQ1(0)
        SetDDS_AMP1(0)
        SetDDS_FREQ2(ReadParameter('F_CavityCenter'))
    elif Beam==45:
        SetDDS_FREQ1(ReadParameter('F_BlueOn'))
        SetDDS_AMP1(ReadParameter('A_BlueOn'))
        SetDDS_FREQ2(0)
# Turn on 0 degree beam:
    Quiet(1)
    Magic(1)
# Prepare for scan:
    Inttime=1000
    InttimeSet(Inttime)
    Xs=sp.linspace(StartX,EndX,StepsX)
    Ys=sp.linspace(StartY,EndY,StepsY)
    try:
        for i in range(len(Xs)):
            if __main__.STOP_FLAG: break
            Y=Ys[i]
            j=0
            while j<len(Ys):
                if __main__.STOP_FLAG: break
                X=Xs[j]
                isok=0
                while isok==0:
                    if __main__.STOP_FLAG: break
                    try:
                        SetX(X)
                        SetY(Y)
                        Quiet(1)
                        time.sleep(2.*Inttime/1000)
#                        counts=ReadIonPMT()
#                        mmamp=ReadMMAMP()
                        val=ReadIonPMTALL()
                        [counts,mmamp,mmphase,maxmin,fftmax]=sp.array(val)
                        if counts=='NA':
                            print "counts=",counts
                        elif counts=='':
                            print "counts=",counts
                        else:
                            isok=1
                    except Exception,e:
                        print time.strftime('%H:%M:%S'),__file__,"Exception occured in getting counts and mmamp from IonPhotonCounter. Trying again!"
                        print e
                        time.sleep(1)
                Quiet(0)
                if CavStab.CavLockCheck():
                    mydb.add_data_point([X,Y,counts,mmamp,mmphase,maxmin,fftmax])
                    try:
                        purgatory(plot.add_point,X,Y,float(fftmax))
                        purgatory(plot.repaint)
                    except Exception,e:
                        print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when adding plot point'
                        print e
                    j=j+1
    finally:
        SetX(FinishX)
        SetY(FinishY)
        Magic(0)
        InttimeSet(inttime_i)
        Quiet(0)
        SetDDS_FREQ1(ReadParameter('F_BlueHi'))
        SetDDS_AMP1(ReadParameter('A_BlueHi'))
    print time.strftime("%H:%M:%S"),"Done\n"
    ScanDone()

def RunScript(filename,dirname,StartX,EndX,FinishX,StartY,EndY,FinishY,StepsX,StepsY,Pause,Beam):
    twoDMicroMotionScan(filename,dirname,StartX,EndX,FinishX,StartY,EndY,FinishY,StepsX,StepsY,Pause,Beam)
