# CavityCoolRabiDataRun3D.py
# Forked from CavityCoolRabiDataRun_0deg_Doppler.py by Hans on 2011-08-25
# Cavity Cooling with 90deg beam from the limit set by SCloops and SHloops (possbily CC recoil time)
# This is done without Blue sideband and Carrier since the cooling itself is enough to show.
ARGS = ['ScanPoints','ScanRepeat','LockOption','CavLockOn','ProbeLockOn','ProbeSet','ProbeSet_SB','IonLockOn','IonSet','EndT_SB','CCloops','SCloops','SHloops','sec1fraction','sec2fraction','sec3fraction']
import time

def RunScript(filename, dirname,ScanPoints,ScanRepeat,LockOption,CavLockOn,ProbeLockOn,ProbeSet, ProbeSet_SB,IonLockOn,IonSet,EndT_SB,CCloops,SCloops,SHloops,sec1fraction,sec2fraction,sec3fraction):
    dirname = dirname + '/' + filename
    if (os.access(dirname, os.F_OK) == 0):
        os.mkdir(dirname)
    
    # inputs
    us_CCtimes=[2500,15000,0,25000,7500]
#    ScanPoints = 50
#    ScanRepeat = 3
    
#    LockOption = 1
#    CavLockOn = 14
#    ProbeLockOn = 7
#    ProbeSet = -2.05
#    IonLockOn = 10
#    IonSet = 2
#    EndT_SB=80 
    # take the data
    
    ScanDone=f_set['AudioAlert_scandone']
    Say=f_set['AudioAlert_say']
    ReadParameter = f_read['DDS_PARAM']
    SetParameter = f_set['DDS_PARAM']
    
    CavityOnDF_value = 2*ReadParameter('F_StarkSec1')
#    ReadoutDF_value = ReadParameter('F_StarkSec' + str(ReadoutMode)[0:str(ReadoutMode).find('.')])
    DoRabi=0        # Don't do Rabi initially!
    for k in range(len(us_CCtimes)):
        if __main__.STOP_FLAG: return
        us_CCtime=us_CCtimes[k]  
        StartT = 0.
        if us_CCtime == 0:
            CavityOnDF_list = [0]
            ReadoutDF_list = [0, ReadoutDF_value, -ReadoutDF_value]
#        ReadoutDF_list = [0]
#        ReadoutDF_list = [ReadoutDF_value, -ReadoutDF_value]
#        elif ReadoutMode != 1:
#           CavityOnDF_list = [0]
#           ReadoutDF_list = [ReadoutDF_value, -ReadoutDF_value]
        else:
#            CavityOnDF_list = [0, -CavityOnDF_value, CavityOnDF_value] # Choosing red, blue and carrier sideband of cavity.
            CavityOnDF_list = [CavityOnDF_value] ## Choosing only red sideband.
# Read out on all sidebands!
#            ReadoutDF_list = [ReadoutDF_value, -ReadoutDF_value]
            ReadoutDF_list = [ReadParameter('F_StarkSec1'), -ReadParameter('F_StarkSec1'),ReadParameter('F_StarkSec2'),-ReadParameter('F_StarkSec2'),ReadParameter('F_StarkSec3'),-ReadParameter('F_StarkSec3')]

        SetParameter('us_DCtime', 2000)
        SetParameter('us_CCtime', us_CCtime)
        SetParameter('CCloops',CCloops)
# Setting us_CCtimes for sidebands: This is where a ratio should go!
#        sec1fraction=1./3
#        sec2fraction=1./3
#        sec3fraction=1./3
        fractioncheck=sec1fraction+sec2fraction+sec3fraction
        print "fractioncheck =%.3f, should be 1"%fractioncheck
        us_CCtime_sec1=(us_CCtime*sec1fraction)/CCloops
        us_CCtime_sec2=(us_CCtime*sec2fraction)/CCloops
        us_CCtime_sec3=(us_CCtime*sec3fraction)/CCloops
        SetParameter('us_CCtime_sec1', us_CCtime_sec1)
        SetParameter('us_CCtime_sec2', us_CCtime_sec2)
        SetParameter('us_CCtime_sec3', us_CCtime_sec3)
        
        # Do Rabi flops at regular intervals:   (eg. before each us_CCtime)
        # This gives us time to stop scan if Red laser is off resonance.
        if DoRabi==1 and __main__.STOP_FLAG==False:
            text='Doing Rabi flops to check that 674 nanometer laser is on resonance'
            try:
                print(text)
                Say(text)
            except Exception,e:
                print "Exception occured in CavityCoolRabiDataRun_0deg_Doppler while Say()'ing:",text,":",e
            Rabi_filename=time.strftime('RabiShort-%H%M')
            __main__.app.wTree.plotframe.set_label(Rabi_filename)
            RabiStartT=0
            RabiEndT=20
            RabiReadoutDF=0
            RabiScanPoints=RabiEndT
            RabiScanRepeat=3
            RabiLockOption=1
            RabiSCloops=75
            Rabi(Rabi_filename, dirname, RabiStartT, RabiEndT, RabiReadoutDF, RabiScanPoints, RabiScanRepeat, RabiLockOption,RabiSCloops)
            DoRabi=0
        for i in range(len(CavityOnDF_list)):
            for j in range(len(ReadoutDF_list)):
                if __main__.STOP_FLAG: return
                
                CavityOnDF = CavityOnDF_list[i]
                ReadoutDF = ReadoutDF_list[j]
                
                if ReadoutDF == 0:
                    EndT = 25.
#            elif us_CCtime <= 500:
#                EndT = 200.
                else:
                    EndT = EndT_SB
                
                CC = str(int(us_CCtime))
                CDF = sign(CavityOnDF) + str(1000.*CavityOnDF)[0:str(1000.*CavityOnDF).find('.')]
                RDF = sign(ReadoutDF) + str(1000.*ReadoutDF)[0:str(1000.*ReadoutDF).find('.')]
                hour = str(time.localtime()[3])
                minute = str(time.localtime()[4])
                if len(hour) < 2:
                    hour = '0' + hour
                if len(minute) < 2:
                    minute = '0' + minute
                timestamp = hour + minute
                filename = 'CavityCoolRabi-CC' + CC + '-CDF' + CDF + '-RDF' + RDF + '-' + timestamp
                SetParameter('SCloops', SCloops ) # Sideband Cooling
                SetParameter('SHloops', SHloops ) # Sideband Heating
                
                if not(alreadyRan(dirname, filename)):
                    print '--------------------------------------------------'
                    print filename
                    print '--------------------------------------------------'
                    # Change header on daq plot to reflect current scan:
                    __main__.app.wTree.plotframe.set_label(filename)
                    CavityCoolRabi3D(filename, dirname, StartT, EndT, ReadoutDF, ScanPoints, ScanRepeat, LockOption, CavLockOn, ProbeLockOn, ProbeSet, ProbeSet_SB, IonLockOn, IonSet)
                    DoRabi=1
    ScanDone()
    text="Cavity Cool Rabi Data Run 3D is now complete."
    time.sleep(1)
    Say(text)
    print(text)
    print("Files are in %s and filenames are eg. %s"%(dirname,filename))
def sign(x):
    if x < 0:
        return ''
    elif x > 0:
        return '+'
    else:
        return ''

def alreadyRan(dirname, filename):
    filename = filename[0:filename.rfind('-')]
    filenames = os.listdir(dirname)
    for i in range(len(filenames)):
        if filenames[i].find(filename) != -1:
            return True
    return False
