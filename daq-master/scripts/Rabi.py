# Rabi.py
# Edited by Hans, 2011-02-25: Added exception handling for when DDS is too slow.
ARGS = ['StartT', 'EndT', 'ReadoutDF', 'ScanPoints', 'ScanRepeat', 'LockOption','SCloops']

import Stabilization
import time

def RunScript(filename, dirname, StartT, EndT, ReadoutDF, ScanPoints, ScanRepeat, LockOption,SCloops):
    Rabi(filename, dirname, StartT, EndT, ReadoutDF, ScanPoints, ScanRepeat, LockOption,SCloops)
def Rabi(filename, dirname, StartT, EndT, ReadoutDF, ScanPoints, ScanRepeat, LockOption,SCloops):

    reload(Stabilization)

    plot = gui_exports['plot']
    ScanDone = f_set['AudioAlert_scandone']
    purgatory = gui_exports['purgatory']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    ReadUnshelved = f_read['DDS_NBRIGHT']
    ReadAvgBright = f_read['DDS_LASTAVG']
    SetParameter  = f_set['DDS_PARAM']
    ReadParameter  = f_read['DDS_PARAM']
    LockOption = int(LockOption)
    IonCount = 1

    try:
        saved_redtime = ReadParameter('us_RedTime')

        Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
        const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        plotLabels = ['BlueCav', 'CavOffset', 'RedPiTime', 'CavOffset']

        # Locking step
        bluerv, BlueCav = Stab.BlueLock()
        ramseylockrv, CavOffset = Stab.RamseyLock(LockOption, True)
        rabilockrv, RedPiTime = Stab.RabiLock(LockOption, True)

        # set up plotting
        print "Running..."
        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.DUALTWODPLOT)  
        purgatory(plot.set_labels, 'Pulse Length', 'Shelving Rate', plotLabels[LockOption & 3])
        mydb = data.database(filename, dirname, 1, 10, 'RabiLength, P[0], P[1], P[2], Scatter, RamseyShelv, RabiShelv, BlueCav, CavOffset, RedPiTime')

        # Perform the experiment
        timestep = (1.0*EndT - StartT)/(ScanPoints - 1)

        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break

            print "Scan %d"%(i)
            for j in range(int(ScanPoints)):
                if __main__.STOP_FLAG: break
                CavStab.MonoLaserLockCheck('421')
                CavStab.MonoLaserLockCheck('1091')
                CavStab.MonoLaserLockCheck('674')
                CavStab.MonoLaserLockCheck('1033')
                ramseylockrv, CavOffset = Stab.RamseyLock(LockOption, False)
                rabilockrv, RedPiTime = Stab.RabiLock(LockOption, False)

                # Science step
                timeval = StartT + j * timestep;
                OpenDDS('prog/Shelving.pp')
                SetParameter('F_RedOn', CavOffset + ReadoutDF)
                SetParameter('us_RedTime',timeval)
                SetParameter('SCloops',SCloops)
                RunDDS()

                isok = 0
                while not isok:
                    try:
                        sciencerv = ReadUnshelved(hist=True)
                        if not len(sciencerv)<2:
                            isok = 1
                        else:
                            print "[",__file__,time.asctime(),"] Empty value in sciencerv? = ",sciencerv
                            print "[",__file__,"] Retrying"
                            sys.stdout.flush()
                            time.sleep(0.5)
                    except Exception, inst:
                        print "[",__file__, time.asctime(),"] Error in ReadUnshelved Exception: ", inst
                        sys.stdout.flush()
                        time.sleep(0.5)
                #sciencerv = ReadUnshelved(hist=True)
                if ((IonCount == 1) and (sciencerv[2] > 10)):
                    IonCount = 2
                    
                if (IonCount == 2):
                    plotrv = sciencerv[1]
                else:
                    plotrv = sciencerv[0]

                bluerv, BlueCav = Stab.BlueLockNoDDSRun()  

                mydb.add_data_point([timeval, sciencerv[0], sciencerv[1], sciencerv[2], bluerv, ramseylockrv, rabilockrv, BlueCav, CavOffset, RedPiTime], int(i*ScanPoints + j))
                purgatory(plot.add_point, timeval, plotrv, eval(plotLabels[LockOption]))
                purgatory(plot.repaint)

            # RUTHS CODE for fitting
            print 'Fitting...'
            expdata, mask = mydb.get_all_data_with_mask()
            timedata = expdata[i*int(ScanPoints):(i+1)*int(ScanPoints), 0]
            rabidata = expdata[i*int(ScanPoints):(i+1)*int(ScanPoints), 1]
            
            fitfunc = lambda p, x: p[0]*scipy.sin(scipy.pi/p[1]*x+p[2])**2
            errfunc = lambda p, x, y: fitfunc(p,x) - y           # Distance to the target function
            p0 = [50., EndT - StartT, 0.]                        # Initial guess for the parameters

            p1,success = scipy.optimize.leastsq(errfunc, p0, args = (timedata, rabidata))
            print 'amp: %g # Pi: %g us'%(p1[0], p1[1]/2)
        SetParameter('us_RedTime',saved_redtime)
        ScanDone()

    except Exception,e:
        print "Exception occurred in RunScript:", e
        traceback.print_exc()
