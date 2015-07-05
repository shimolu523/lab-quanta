## put experiment-specific parameters list in ARGS
ARGS = ['PARAMETERS', 'ScanPoints', 'ScanRepeat', 'LockOption']

import Stabilization
import CavityStabilization

## same experiment-specific parameters list in RunScript arguments
def RunScript(filename, dirname, PARAMETERS, ScanPoints, ScanRepeat, LockOption):

    reload(Stabilization)
    reload(CavityStabilization)

    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    LockOption = int(LockOption)
    IonCount = 1
    CavLockRead = f_read['DMM_top_V']
    CavLockTreshold = 1.0
    try:
        Stab = Stabilization.Stabilization(f_set, f_read, gui_exports)
        const = Stab.LoadConstants(DAQ_HOME+'/scripts/StabilizationConstants')

        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        
        plotLabels = ['BlueCav', 'CavOffset', 'RedPiTime', 'RedPiTime']

        # Locking step

        # set up plotting
        print "Running..."
        purgatory(plot.clear)
        purgatory(plot.set_mode, pyextfigure.DUALTWODPLOT)  
        ## label the x-axis as appropriate
        purgatory(plot.set_labels, 'XLABEL', 'Shelving Rate', plotLabels[LockOption & 3])


        # Perform the experiment
        ## define local variables etc as needed
        ## save and then set some global parameters that aren't changed during scan
             
        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break
            
            print "Scan %d"%(i)
            time.sleep(1)
            CavLockOk=0
            CavLockPast=1
            #        print "CavLockRead()"
            while CavLockOk==0:
                if CavLockRead() > CavLockTreshold:
                    CavLockOk=1
                    if CavLockPast==0:
                        print "resuming measurement in 5 sec..."
                        time.sleep(1)
                        print "resuming measurement in 4 sec..."
                        time.sleep(1)
                        print "resuming measurement in 3 sec..."
                        time.sleep(1)
                        print "resuming measurement in 2 sec..."
                        time.sleep(1)
                        print "resuming measurement in 1 sec..."
                        time.sleep(1)
                        print "Cavity relocked"
                    else:
                        print "Cavity lock ok"
                else:
                    print "Cavity unlocked!"
                    CavLockPast=0
                
            for j in range(int(ScanPoints)*3):
                if __main__.STOP_FLAG: break


                # Science step
                ## more local var defs, iterators etc
                ## open the desired pulse sequence, e.g. Shelving.pp
                ## set some parameters



                ## identify the x-variable to plot

                ## anything else: fitting, etc

        ## restore global parameters and any other changed parameters to reasonable values

    except Exception,e:
        print "Exception occurred in RunScript:", e
        traceback.print_exc()
