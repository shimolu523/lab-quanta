ARGS = ['ReadoutMode','ScanPoints','ScanRepeat','SCloops','us_DCtime','StartT','EndT','LockOption']
import sys
import numpy as np
import os
import time
def RunScript(filename, dirname, ReadoutMode,ScanPoints,ScanRepeat,SCloops,us_DCtime,StartT,EndT,LockOption):
    ScanDone = f_set['AudioAlert_scandone']
    Say = f_set['AudioAlert_say']
    if (os.access(dirname,os.F_OK)==0):
        os.mkdir(dirname)
    dirname = dirname + '/' + filename
    if (os.access(dirname, os.F_OK) == 0):
        os.mkdir(dirname)
    
    # inputs
# Which power levels should we check?
    DDS1AMP_list=np.array([30,25,20,30])      

    CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
    const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
    if True:
        StabCounts=np.array([40000,25000,17000,40000])
        print "NB: Using manually set StabCounts from DopplerCoolDataRun:",StabCounts
    else:
        StabCounts=DDS1AMP_list*0+const['BlueSet']
        print "NB: Using BlueSet from CavityStabilizationConstants:",const['BlueSet']
#    ScanPoints = 100
#    ScanRepeat = 3
#    SCloops=0#75
#    us_DCtime=2000
#    StartT = 0.
#    EndT=200 
# Ramseylock:
#    LockOption = 1
#    CavLockOn = 14
#   ProbeLockOn = 7
#    ProbeSet = -0.375
#    IonLockOn = 10
#    IonSet = 2
    
    # take the data
    
    ReadParameter = f_read['DDS_PARAM']
    SetParameter = f_set['DDS_PARAM']
    
# Read the secular frequencies and save them: 
    ReadoutDF_value = ReadParameter('F_StarkSec' + str(ReadoutMode)[0:str(ReadoutMode).find('.')])
    
# Should we cool on carrier as well? 
    ReadoutDF_list = [-ReadoutDF_value,ReadoutDF_value]
    print "Testing these offsets:",ReadoutDF_list
# Explicitly turning off SCloops:
    SetParameter('SCloops',SCloops )
    SetParameter('us_DCtime', us_DCtime)
    print "Testing these DDS1AMPs:",DDS1AMP_list 
    for i in range(len(DDS1AMP_list)):
        Say("Change threshold! You have 30 seconds to comply. I'll wait")
        time.sleep(15)
        Say("15 seconds left!")
        time.sleep(15)
        Say("Time is up. Starting scan.")
        
        for j in range(len(ReadoutDF_list)):
            if __main__.STOP_FLAG: return
            
	    DDS1AMP=DDS1AMP_list[i]
            StabCount=StabCounts[i]
            SetParameter('A_BlueOn',DDS1AMP)
            SetParameter('A_BlueMeas',DDS1AMP) 
	    ReadoutDF = ReadoutDF_list[j]
            
   #         if ReadoutDF == 0:
  #              EndT = 25.
#            elif us_CCtime <= 500:
#                EndT = 200.
 #           else:
#                EndT = 80.
#            CC = str(int(us_CCtime))
#            CDF = sign(CavityOnDF) + str(1000.*CavityOnDF)[0:str(1000.*CavityOnDF).find('.')]
            RDF = sign(ReadoutDF) + str(1000.*ReadoutDF)[0:str(1000.*ReadoutDF).find('.')]
#            hour = str(time.localtime()[3])
#            minute = str(time.localtime()[4])
#            if len(hour) < 2:
#                hour = '0' + hour

#               minute = '0' + minute
#            timestamp = hour + minute
            timestamp=time.strftime("%H%M")
            print "Scanning DDSAMP1=",DDS1AMP
            filename = 'DopplerCoolRabi-DDS1AMP' + str(int(DDS1AMP)) + '-RDF' + RDF + '-' + timestamp
            if not(alreadyRan(dirname, filename)):
                print '--------------------------------------------------'
                print filename
                print '--------------------------------------------------'
                DopplerCoolRabi(filename, dirname, StartT, EndT, ReadoutDF, ScanPoints, ScanRepeat, LockOption,StabCount)
    ScanDone()

    
def sign(x):
    if x < 0:
        return ''
    elif x > 0:
        return '+'
    else:
        return ''

def alreadyRan(dirname, filename):
    filename = filename[0:filename.rfind('-')]
    try:
        filenames = os.listdir(dirname)
    except Exception,e:
        print time.strftime('%H:%M:%S'),__file__,"Exception occured when opening directory"
        print e
        raise e
    for i in range(len(filenames)):
        if filenames[i].find(filename) != -1:
            return True
    return False
