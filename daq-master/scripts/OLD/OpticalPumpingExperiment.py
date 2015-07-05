ARGS = ['ScanRepeat', 'BlueLockOn']

import scipy
import CavityStabilization
import ReadDDSmemory

def RunScript(filename, dirname, ScanRepeat, BlueLockOn):

    reload(CavityStabilization)
    reload(ReadDDSmemory)
    
    plot = gui_exports['plot']
    purgatory = gui_exports['purgatory']
    ReadParameter  = f_read['DDS_PARAM']
    SetParameter  = f_set['DDS_PARAM']
    OpenDDS = f_set['DDS_SETPROG']
    RunDDS = f_set['DDS_RUNPROG']
    RunDDSandReadTotal = f_read['DDS_RUNNTOTAL']

    try:
        ##################################################
        # Set up locks
        ##################################################
        CavStab = CavityStabilization.CavityStabilization(f_set, f_read, gui_exports)
        const = CavStab.LoadConstants(DAQ_HOME+'/scripts/CavityStabilizationConstants')
        
        bluelockrv, BlueCav = CavStab.BlueLock(BlueLockOn, True)

        ##################################################
        # Perform the experiment
        ##################################################
        print "Running ..."
        
        bins = range(100)
        counts = scipy.zeros(100)
        
        for i in range(int(ScanRepeat)):
            if __main__.STOP_FLAG: break
            
            print i

            ##################################################
            # Lock step
            ##################################################
            bluelockrv, BlueCav = CavStab.BlueLock(BlueLockOn, False)
            
            ##################################################
            # Measurement step
            ##################################################
            # time.sleep(0.2)
            
            OpenDDS('prog/OpticalPumpingExperiment.pp')
            RunDDS()
            counts = counts + ReadDDSmemory.ReadDDSmemory()
            
            ##################################################
            # Update the plot
            ##################################################
            purgatory(plot.clear)
            purgatory(plot.set_mode, pyextfigure.TWODPLOT)  
            purgatory(plot.set_labels, 'Bin', 'Counts', '')
            for ii in bins:
                purgatory(plot.add_point, bins[ii], counts[ii], 0.0)
            purgatory(plot.repaint)
            
        ##################################################
        # Store the results
        ##################################################
        
        mydb = data.database(filename, dirname, 1, 1, 'Counts')
        for ii in bins:
            mydb.add_data_point([counts[ii]], bins[ii])
           
    except Exception,e:
        print "Exception occurred in RunScript:", e
        traceback.print_exc()