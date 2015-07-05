from __future__ import division
# AutoloadIon-PvstDataRun.py
# Hans 2012-04-08
# 
ARGS=['Waittime','NumberOfRepeats','Threshold','OvenTimeStart','OvenTimeEnd','NumberOfOvenTimes','OvenCurrent']
import time
import scipy as sp
import Stabilization


def RunScript(filename,dirname,WaitTime, NumberOfRepeats,Threshold,OvenTimeStart,OvenTimeEnd,NumberOfOvenTimes,OvenCurrent):
    AutoloadIonPvstDataRun(filename,dirname,WaitTime, NumberOfRepeats,Threshold,OvenTimeStart,OvenTimeEnd,NumberOfOvenTimes,OvenCurrent)
def AutoloadIonPvstDataRun(filename,dirname,WaitTime, NumberOfRepeats,Threshold,OvenTimeStart,OvenTimeEnd,NumberOfOvenTimes,OvenCurrent):
    print "Starting!!!"
    RFOutput=f_set['AGfungen1_OutPut']    
    OvenTimes=sp.linspace(OvenTimeStart,OvenTimeEnd,NumberOfOvenTimes)
    plot=gui_exports['plot']
    purgatory=gui_exports['purgatory']
    #Constants:
    Freq422=710.96302 # THz
    IntTime=3000 # ms 
    label='OvenCurrent=%f, WaitTime=%f, Threshold=%f, NumberofRepeats=%.f, Freq422=%f, IntTime=%.f'%(OvenCurrent,WaitTime, Threshold,NumberOfRepeats,Freq422,IntTime)
    label=label+'\n#OvenTime,Probability of ion loading, Oven voltage Start, Oven voltage End'
    mydb = data.database(filename, dirname, 1, 4, label )
    purgatory(plot.clear)
    purgatory(plot.set_mode,pyextfigure.TWODPLOT)
    purgatory(plot.set_labels,'Oven time [s]','Probability of ion loading','Oven Voltage End')
    for i in range(NumberOfOvenTimes):
        if __main__.STOP_FLAG: break

        OvenTime=OvenTimes[i]
        
        numberofions=0
        OvenVoltageStart=0
        OvenVoltageEnd=0
        for i in range(int(NumberOfRepeats)):
            if __main__.STOP_FLAG: break
            # Dump ion:
            RFOutput(0)
            time.sleep(1)
            RFOutput(1)
            # Instantiate the workhorse:
            Loaderinst=AutoloadIonClassPvst(filename,dirname,Freq422,IntTime,Threshold,OvenTime,WaitTime,OvenCurrent)
            # Run workhorse
            try:
                    print "Loading for %.f seconds [i=%.f]"%(OvenTime,i)
                    deltatime, tmpions, OvenVoltageStartTMP, OvenVoltageEndTMP=Loaderinst.Autoload()
                    numberofions=numberofions+tmpions
                    OvenVoltageStart=OvenVoltageStart+OvenVoltageStartTMP
                    OvenVoltageEnd=OvenVoltageEnd+OvenVoltageEndTMP
            except Exception,e:
                Loaderinst.OvenOff()
                __main__.STOP_FLAG=True
                raise e
            Loaderinst.OvenOff()
        if not __main__.STOP_FLAG:
            probabilityion=numberofions/NumberOfRepeats
            OvenVoltageEndAVG=OvenVoltageEnd/NumberOfRepeats
            OvenVoltageStartAVG=OvenVoltageStart/NumberOfRepeats
            mydb.add_data_point([deltatime,probabilityion,OvenVoltageStart,OvenVoltageEnd])
            purgatory(plot.add_point,deltatime,probabilityion,OvenVoltageEnd)
            purgatory(plot.repaint)
