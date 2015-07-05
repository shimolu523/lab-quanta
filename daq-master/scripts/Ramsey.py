# Ramsey.py
# Edited by Hans, 2011-02-25: Added exception handling for when DDS is to slow.
ARGS = ['StartT', 'EndT', 'ReadoutDF', 'RamseyPh', 'ScanPoints', 'ScanRepeat', 'LockOption', 'OnSideband']

import Stabilization
import time

def RunScript(filename, dirname, StartT, EndT, ReadoutDF, RamseyPh, ScanPoints, ScanRepeat, LockOption, OnSideband):

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
    IonCount = 1

    try:
        Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
        const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')
        plotLabels = ['BlueCav', 'CavOffset', 'RedPiTime', 'CavOffset']

        # Locking step
        bluerv, BlueCav = Stab.BlueLock()
        ramseylockrv, CavOffset = Stab.RamseyLock(LockOption, True)
        rabilockrv, RedPiTime = Stab.RabiLock(LockOption, True)

        # set up plotting
        print "Running..."
        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.DUALTWODPLOT)  
        purgatory(plot.set_labels, 'Pulse Length', 'Shelving Rate', plotLabels[LockOption])
        mydb = data.database(filename, dirname, 1, 10, 'RamseyTime, P[0], P[1], P[2], Scatter, RamseyShelv, RabiShelv, BlueCav, CavOffset, RedPiTime')

        # Perform the experiment
        timestep = (1.0*EndT - StartT)/(ScanPoints - 1)
        saved_RamseyDly = ReadParameter('us_RamseyDly')

        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break

            print "Scan %d"%(i)
            for j in range(int(ScanPoints)):
                if __main__.STOP_FLAG: break

                ramseylockrv, CavOffset = Stab.RamseyLock(LockOption, False)
                rabilockrv, RedPiTime = Stab.RabiLock(LockOption, False)

                # Science step
                timeval = StartT + j * timestep;
                if (OnSideband):
                    OpenDDS('prog/SRamsey.pp')
                else:
                    OpenDDS('prog/Ramsey.pp')
                SetParameter('F_RedOn', CavOffset + ReadoutDF)
                SetParameter('us_RamseyDly', timeval)
                SetParameter('Ph_Ramsey', RamseyPh)
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
#               sciencerv = ReadUnshelved(hist=True)
                if ((IonCount == 1) and (sciencerv[2] > 10)):
                    IonCount = 2
                    
                if (IonCount == 2):
                    plotrv = sciencerv[1]
                else:
                    plotrv = sciencerv[0]

                bluerv, BlueCav = Stab.BlueLockNoDDSRun()  

                mydb.add_data_point([timeval, sciencerv[0], sciencerv[1], sciencerv[2], bluerv, ramseylockrv, rabilockrv, BlueCav, CavOffset, RedPiTime], int(i*ScanPoints + j))
                purgatory(plot.add_point, timeval, plotrv, eval(plotLabels[LockOption]) )
                purgatory(plot.repaint)

                ## anything else: fitting, etc

        SetParameter('us_RamseyDly', saved_RamseyDly)
        SetParameter('Ph_Ramsey', 0.)

    except Exception,e:
        print "Exception occurred in RunScript:", e
        traceback.print_exc()
