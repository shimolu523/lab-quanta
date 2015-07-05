ARGS = ['SecFRQ', 'StartT', 'EndT', 'ScanPoints', 'ScanRepeat', 'LockOption','CavLockCheck']

import Stabilization
import numpy as numarray
import scipy as sp
def RunScript(filename, dirname, SecFRQ, StartT, EndT, ScanPoints, ScanRepeat, LockOption,CavLockCheck):

    reload(Stabilization)

    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    ReadUnshelved = f_read['DDS_NBRIGHT']
    ReadAvgBright = f_read['DDS_LASTAVG']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    LockOption = int(LockOption)
    ScanDone = f_set['AudioAlert_scandone']
    IonCount = 1

    try:
        saved_StarkSec = ReadParameter('F_StarkSec1')
# FIXME: I don't need this?
#SetParameter('F_StarkSec1', SecFRQ)

        Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
        const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
        plotLabels = ['BlueCav', 'CavOffset', 'RedPiTime', 'RedPiTime']

        # Locking step
        bluerv, BlueCav = Stab.BlueLock()
        ramseylockrv, CavOffset = Stab.RamseyLock(LockOption, True)
        rabilockrv, RedPiTime = Stab.RabiLock(LockOption, True)

        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        if CavLockCheck==1:
            CavStab.CavLockCheck()

        # set up plotting
        print "Running..."
        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.DUALTWODPLOT)  
        purgatory(plot.set_labels, 'Delay Time', 'Red Shelving', 'Blue Shelving')
        mydb = data.database(filename, dirname, 1, 9, 'Heating rate scan at sec freq %g\n#DelayTime, RedShelv, BlueShelv, Scatter, RamseyShelv, RabiShelv, BlueCav, CavOffset, RedPiTime'%(SecFRQ * 2))

        # Perform the experiment
        timestep = (1.0*EndT - StartT)/(ScanPoints - 1)
        
        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break

            print "Scan %d"%(i)
            j=0
            while j <= int(ScanPoints):
#for j in range(int(ScanPoints)):
                if __main__.STOP_FLAG: break

                ramseylockrv, CavOffset = Stab.RamseyLock(LockOption, False)
                rabilockrv, RedPiTime = Stab.RabiLock(LockOption, False)

                # Science step
                OpenDDS('prog/Shelving.pp')
                timeval = StartT+ j*timestep
                SetParameter('ms_ReadoutDly', timeval)
                SetParameter('F_RedOn', CavOffset - SecFRQ)

                RunDDS()
                bsrv = ReadUnshelved(hist=True)

                SetParameter('F_RedOn', CavOffset + SecFRQ)

                RunDDS()
                rsrv = ReadUnshelved(hist=True)

                if ((IonCount == 1) and (bsrv[2] + rsrv[2] > 20)):
                    IonCount = 2

                if (IonCount == 2):
                    bsrv = bsrv[1]
                    rsrv = rsrv[1]
                else:
                    bsrv = bsrv[0]
                    rsrv = rsrv[0]
                
                bluerv, BlueCav = Stab.BlueLockNoDDSRun()
                SaveDataPoint=False
                if CavLockCheck==1:
                    if CavStab.CavLockCheck():
                        SaveDataPoint=True
                    else:
                        SaveDataPoint=False
                else:
                     SaveDataPoint=True
                if SaveDataPoint:
                    mydb.add_data_point([timeval, rsrv, bsrv, bluerv, ramseylockrv, rabilockrv, BlueCav, CavOffset, RedPiTime], int(i*ScanPoints + j))

                    purgatory(plot.add_point, timeval, rsrv, bsrv)
                    purgatory(plot.repaint)
                    j=j+1
            try:
                expdata, mask = mydb.get_all_data_with_mask()
                fitdataX = expdata[0:int((i+1)*int(ScanPoints)), 0]
                fitdataR = expdata[0:int((i+1)*int(ScanPoints)), 1]
                fitdataB = expdata[0:int((i+1)*int(ScanPoints)), 2]
                # Becomes infinite sometimes! ie. when data is bad.
                fitdataY = fitdataR/(fitdataB - fitdataR)

                fitdata = numarray.transpose(numarray.array([fitdataX, fitdataY]))
                fit = linear_fit(fitdata)
                if sp.isnan(fit).any():
                    print "Fit returned:",fit
                    print "Printing raw data:"
                    print fitdata
                print "Fit after %d runs: n(t) = %g t + %g"%(i+1, fit[1]*1000*(2*SecFRQ)**2, fit[0])
            except Exception, e:
                print "Exception in Heating.py while fitting:",e

        SetParameter('ms_ReadoutDly', 0)
	SetParameter('F_StarkSec1', saved_StarkSec)
        return mydb
        ScanDone()

    except Exception,e:
        print "Exception occurred in RunScript:", e
        traceback.print_exc()
