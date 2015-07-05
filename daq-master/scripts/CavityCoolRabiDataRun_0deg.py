# CavityCoolRabiDataRun_0deg.py
# Forked from CavityCoolRabiDataRun.py by Hans on 2011-06-22
# Cavity Cooling with 0deg beam.
ARGS = ['ReadoutMode','ScanPoints','ScanRepeat','LockOption','CavLockOn','ProbeLockOn','ProbeSet','ProbeSet_SB','IonLockOn','IonSet','EndT_SB']

def RunScript(filename, dirname, ReadoutMode,ScanPoints,ScanRepeat,LockOption,CavLockOn,ProbeLockOn,ProbeSeti,ProbeSet_SB,IonLockOn,IonSet,EndT_SB):
    dirname = dirname + '/' + filename
    if (os.access(dirname, os.F_OK) == 0):
        os.mkdir(dirname)
    
    # inputs
#   us_CCtimes=[0,500,1000,1500,2000,3000]
    us_CCtimes=[100,300,500,1000,2000]#,3000,4000]
#   us_CCtimes=[2000]
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
    ReadoutDF_value = ReadParameter('F_StarkSec' + str(ReadoutMode)[0:str(ReadoutMode).find('.')])
    for k in range(len(us_CCtimes)):
        if __main__.STOP_FLAG: return
        us_CCtime=us_CCtimes[k]  
        StartT = 0.
        if us_CCtime == 0:
            CavityOnDF_list = [0]
            ReadoutDF_list = [0, ReadoutDF_value, -ReadoutDF_value]
#        ReadoutDF_list = [0]
#        ReadoutDF_list = [ReadoutDF_value, -ReadoutDF_value]
        elif ReadoutMode != 1:
            CavityOnDF_list = [0]
            ReadoutDF_list = [ReadoutDF_value, -ReadoutDF_value]
        else:
            CavityOnDF_list = [0, -CavityOnDF_value, CavityOnDF_value]
#        CavityOnDF_list = [CavityOnDF_value]
            ReadoutDF_list = [ReadoutDF_value, -ReadoutDF_value]

        SetParameter('SCloops', 75)
        SetParameter('us_DCtime', 2000)
        SetParameter('us_CCtime', us_CCtime)
        
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
                
                if not(alreadyRan(dirname, filename)):
                    print '--------------------------------------------------'
                    print filename
                    print '--------------------------------------------------'
                    # Change header on daq plot to reflect current scan:
                    __main__.app.wTree.plotframe.set_label(filename)
                    CavityCoolRabi_0deg(filename, dirname, StartT, EndT, CavityOnDF, ReadoutDF, ScanPoints, ScanRepeat, LockOption, CavLockOn, ProbeLockOn, ProbeSet_SB, IonLockOn, IonSet)
    ScanDone()
    text="Cavity Cool Rabi Data Run (0 degree) is now complete."
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
