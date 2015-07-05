# CavityResonanceScan.py
# 2011-04-20 Hans Harhoff Andersen
# Purpose: To see Cavity spectrum. Replaces manual OneDScan.
ARGS = ['StartF','EndF','ScanPoints','ScanRepeat','ProbePower']
import CavityStabilization
import time
import sys
import scipy as sp
# Adding directory to path where fitting scripts are stored:
sys.path.append('/home/cavityexp/analysis/')
# Importing hansfit which is used to fit most of the taken dat:
import hansfit
reload(hansfit)
####

def RunScript(filename,dirname,StartF,EndF,ScanPoints,ScanRepeat,ProbePower):
    CavityResonanceScan(filename,dirname,StartF,EndF,ScanPoints,ScanRepeat,ProbePower)
def CavityResonanceScan(filename,dirname,StartF,EndF,ScanPoints,ScanRepeat,ProbePower):

# Import functions:
    reload(CavityStabilization)
    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDSandReadTotal = f_read['DDS_RUNNTOTAL'] 
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    CavFreqSet = f_set['DDS_FREQ2']
    CavBeamSet = f_set['3631A_botleft_+25V']
    ProbePowerRead = f_read['3631A_leftmost_+25V']
    ProbePowerSet = f_set['3631A_leftmost_+25V']
    f421quiet = f_set['MonoLasers_Quiet421']

    ReadCavPMT = f_read['CavityPhotonCounter_COUNT']
    beam0 = 24.
    beam90 = 0.
    maxProbePower = 15.
# Check that Cavity is locked:
    CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
    const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
    CavStab.CavLockCheck()
# Set up plotting:
    try:
#        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.TWODPLOT)  
        purgatory(plot.set_labels, 'DDS2 FREQ [MHz]', 'Scatter into cavity [photons]','<empty>')
    except Exception,e:
        print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when setting up plot'
    mydb = data.database(filename, dirname, 1, 3, 'DDS FREQ2, Scatter into cavity [photons]')
    print "Running CavityResonanceScan:"
    freqs=sp.linspace(StartF,EndF,ScanPoints)
    f421quiet(1)
    CavBeamSet(beam0)
    ProbePowerSet(ProbePower)
    for i in range(int(ScanRepeat)):
        if __main__.STOP_FLAG: break
        print "Scan %d"%(i)
        j=0
        # Checking CavityLock again:
        CavStab.CavLockCheck()
        while j<len(freqs):
            if __main__.STOP_FLAG: break

            freq=freqs[j]
            CavFreqSet(freq)
            time.sleep(0.6)
            try:
                cavrv=ReadCavPMT()
            except Exception,e:
                print time.strftime('%H:%M:%S'),__file__,"Exception occured in ReadCavPMT(). Trying again!"
                cavrv=ReadCavPMT()
            mydb.add_data_point([freq,cavrv,0.0])
            try:
                purgatory(plot.add_point,freq,cavrv,0.0)
                purgatory(plot.repaint)
            except Exception,e:
                print time.strftime('%H:%M:%S'),__file__,'Exception occured in purgatory when adding plot point'
            j=j+1
    f421quiet(0)
    CavFreqSet(0)
    try:
        reload(hansfit)
        fit=hansfit.CavityResonanceScan(dirname,filename)
    except Exception,e:
        print "Exception occured while doing hansfit.CavityResonanceScan:",e
        traceback.print_exc(file=sys.stdout)
        print "Continuing anyways"
    print "Done"
