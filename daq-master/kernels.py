# kernels.py
#
# This file defines the functions that execute scans
# Each takes two parameters - run description, which defines
# boundaries, speed, number of points, filename to save to etc.
# and environment, which defines the plot to plot to, progressbar, and
# purgatory. Purgatory simply executes a function in the GUI thread
#########################################################################
import data
import time
import pyextfigure
import numpy
import math

#########################################################################
# Definition of Time Dependence scan
#########################################################################
def kernel_TimeDepScan(run_desc, environment):
    xstep = 0
    comment = "Time Dependence Scan. Measuring %s and %s for %.2g secs every %.2g secs. Impulse provided by %s, which was set at %.2g for %.2g, at %.2g for %.2g and then set at %.2g for duration of measurment."%(run_desc['y1label'], run_desc['y2label'], run_desc['meastime'], run_desc['interval'], run_desc['impulselabel'], run_desc['hysttop'], run_desc['hysttopwait'], run_desc['hystbot'], run_desc['hystbotwait'], run_desc['measureat'])

    mydatabase = data.database(run_desc['filename'], run_desc['dirname'], 1, 3, comment)
    environment['purgatory'](environment['plot'].set_labels,
                             run_desc['xlabel'], run_desc['y1label'], run_desc['y2label'])
    if (run_desc['f_Y2read']):
        environment['purgatory'](environment['plot'].set_mode, pyextfigure.DUALTWODPLOT)
    else:
        environment['purgatory'](environment['plot'].set_mode, pyextfigure.TWODPLOT)

    try:
        if run_desc['f_Xset']:
            run_desc['f_Xset'](run_desc['hysttop'])
            time.sleep(run_desc['hysttopwait'])
            run_desc['f_Xset'](run_desc['hystbot'])
            time.sleep(run_desc['hystbotwait'])
            run_desc['f_Xset'](run_desc['measureat'])
        
        STARTTIME = time.time()
        if (run_desc['pause'] > 0): time.sleep(run_desc['pause'])

        while ((time.time() - STARTTIME < run_desc['meastime']) and not STOP_FLAG):
            readval1 = run_desc['f_Y1read']()*run_desc['y1scale']
            if (run_desc['f_Y2read']):
                readval2 = run_desc['f_Y2read']()*run_desc['y2scale']
            else:
                readval2 = 0.0
            
            timenow = time.time() - STARTTIME
            mydatabase.add_data_point([timenow, readval1, readval2], xstep) 
            xstep = xstep + 1
            time.sleep(run_desc['interval'])
            
            environment['purgatory'](environment['plot'].add_point, timenow, readval1, readval2)
            environment['purgatory'](environment['plot'].repaint)
            
            environment['purgatory'](environment['progressbar'].set_fraction, \
                                         min(1.0, (1.0 * timenow)/run_desc['meastime']))
            
            while PAUSE_FLAG:
                time.sleep(0.1)
     
    finally:
        if (run_desc['f_Xset']):
            if ((run_desc['finishat'] <= max(run_desc['Xstart'], run_desc['Xend'])) and
                (run_desc['finishat'] >= min(run_desc['Xstart'], run_desc['Xend']))):
                run_desc['f_Xset'](run_desc['finishat'])
            else:
                print "SAFETY CHECK: Finish at out of bounds. Ignoring"

    return mydatabase
    
#########################################################################
# Definition of Multi Time Dependent scan
#########################################################################
def kernel_MultiTimeDepScan(run_desc, environment):
    xstep = 0
    comment = "Time Dependence Scan of Multiple Variables. Measuring for %.2g secs every %.2g secs.\n"%(run_desc['meastime'], run_desc['interval'])
    comment += "Hello World Filler."

    y_variables = len(run_desc['reads'])
    
    mydatabase = data.database(run_desc['filename'], run_desc['dirname'], 1, 1 + y_variables, comment)
    #environment['purgatory'](environment['plot'].set_labels,
    #                         run_desc['xlabel'], run_desc['y1label'], run_desc['y2label'])
    #if (run_desc['f_Y2read']):
    #    environment['purgatory'](environment['plot'].set_mode, pyextfigure.DUALTWODPLOT)
    #else:
    #    environment['purgatory'](environment['plot'].set_mode, pyextfigure.TWODPLOT)

    try:            
        STARTTIME = time.time()
        if (run_desc['pause'] > 0):
            time.sleep(run_desc['pause'])
        
        while ((time.time() - STARTTIME < run_desc['meastime']) and not STOP_FLAG):
            #readval1 = run_desc['f_Y1read']()*run_desc['y1scale']
            #if (run_desc['f_Y2read']):
            #    readval2 = run_desc['f_Y2read']()*run_desc['y2scale']
            #else:
            #    readval2 = 0.0
            
            y_values = []
            for read_function in run_desc['reads'].itervalues():
                y_values.append(read_function())
            
            timenow = time.time() - STARTTIME
            y_values.insert(0, timenow)
            mydatabase.add_data_point(y_values, xstep) 
            xstep = xstep + 1
            time.sleep(run_desc['interval'])
            
            #environment['purgatory'](environment['plot'].add_point, timenow, readval1, readval2)
            #environment['purgatory'](environment['plot'].repaint)
            
            environment['purgatory'](environment['progressbar'].set_fraction, \
                                         min(1.0, (1.0 * timenow)/run_desc['meastime']))     
            
            while PAUSE_FLAG:
                time.sleep(0.1)
                
    finally:
        pass

    return mydatabase

#########################################################################
# Definition of PID lock
#########################################################################
def kernel_PIDlock(run_desc, environment):
    xstep = 0
    comment = "PID Lock. Measuring %s, adjusting %s."%(run_desc['y1label'], run_desc['y2label'])

    mydatabase = data.database(run_desc['filename'], run_desc['dirname'], 1, 3, comment)
    environment['purgatory'](environment['plot'].set_labels,
                             run_desc['xlabel'], run_desc['y1label'], run_desc['y2label'])
    environment['purgatory'](environment['plot'].set_mode, pyextfigure.DUALTWODPLOT)

    try:
        STARTTIME = time.time()

        Pvalue = 0
        Ivalue = run_desc['xstart']
        step = 0
        while (not STOP_FLAG):
            readval = run_desc['read_func']()*run_desc['scale']
            timenow = time.time() - STARTTIME
            if (run_desc['pause'] > 0): time.sleep(run_desc['pause'])

            if ((readval > run_desc['setpoint']/2) and (readval < 2*run_desc['setpoint'])):
                Pvalue = (run_desc['setpoint'] - readval)*run_desc['pgain']
                Ivalue = Ivalue + Pvalue * run_desc['igain']
            setval = min(run_desc['ubound'], max(run_desc['lbound'], Pvalue + Ivalue))
            
            mydatabase.add_data_point([timenow, readval, setval], step) 
            step = step + 1

	    run_desc['set_func'](setval)
            
            environment['purgatory'](environment['plot'].add_point, timenow, readval, setval)
            environment['purgatory'](environment['plot'].repaint)
    finally:
        pass

    return mydatabase



#########################################################################
# Definition of 1D scan
#########################################################################
def kernel_1DScan(run_desc, environment):
    step = 0
    datastep = 0
    MAX_STEPS = run_desc['steps']
    increment = 1

    comment = "1D Scan of %s and %s against %s. X starts at %.2g and ends at %.2g, with %d steps."%(run_desc['y1label'], run_desc['y2label'], run_desc['xlabel'], run_desc['Xstart'], run_desc['Xend'], run_desc['steps'])  

    mydatabase = data.database(run_desc['filename'], run_desc['dirname'], 1, 3, comment)
    environment['purgatory'](environment['plot'].set_labels,
                             run_desc['xlabel'], run_desc['y1label'], run_desc['y2label'])

    if (run_desc['f_Y2read']):
        environment['purgatory'](environment['plot'].set_mode, pyextfigure.DUALTWODPLOT)
    else:
        environment['purgatory'](environment['plot'].set_mode, pyextfigure.TWODPLOT)

    try:
        run_desc['f_Xset'](run_desc['Xstart'])
        time.sleep(2*run_desc['pause'] + 1)

        while (((step <= MAX_STEPS) or run_desc['cycle?'] > 0.) and not STOP_FLAG):
            Xsetval = (run_desc['Xend'] - run_desc['Xstart']) * (1.0*step)/MAX_STEPS + run_desc['Xstart']
            run_desc['f_Xset'](Xsetval)
            if (run_desc['pause'] > 0): time.sleep(run_desc['pause'])
                
            if (run_desc['f_Xread']):
                Xreadval = run_desc['f_Xread']()
            else:
                Xreadval = Xsetval
                
            Y1readval = run_desc['f_Y1read']() * run_desc['y1scale']
            if (run_desc['f_Y2read']):
                Y2readval = run_desc['f_Y2read']() * run_desc['y2scale']
            else:
                Y2readval = 0.0

            mydatabase.add_data_point([Xreadval, Y1readval, Y2readval], datastep)
            datastep = datastep + 1

            environment['purgatory'](environment['plot'].add_point, Xreadval, Y1readval, Y2readval)
            environment['purgatory'](environment['plot'].repaint)

            if (step % (MAX_STEPS/100 + 1) == 0):
                environment['purgatory'](environment['progressbar'].set_fraction, (1.0*step)/MAX_STEPS)

            step = step + increment
            if (((step == MAX_STEPS) or (step == 0)) and (run_desc['cycle?'] > 0.)):
                increment = -increment
            
            while PAUSE_FLAG:
                time.sleep(0.1)
                
    finally:
        if ((run_desc['finishat'] <= max(run_desc['Xstart'], run_desc['Xend'])) and
            (run_desc['finishat'] >= min(run_desc['Xstart'], run_desc['Xend']))):
            run_desc['f_Xset'](run_desc['finishat'])
        else:
            print "SAFETY CHECK: Finish at out of bounds. Ignoring"

    return mydatabase


#########################################################################
# Definition of stabilized 1D scan
#########################################################################
def kernel_Stab1DScan(run_desc, environment):
    step = 0
    datastep = 0
    MAX_STEPS = run_desc['steps']
    increment = 1

    comment = "Stab 1D Scan of %s against %s. Stabilizing %s. X starts at %.2g and ends at %.2g, with %d steps."%(run_desc['ylabel'], run_desc['xlabel'], run_desc['slabel'], run_desc['Xstart'], run_desc['Xend'], run_desc['steps'])  

    mydatabase = data.database(run_desc['filename'], run_desc['dirname'], 1, 3, comment)
    environment['purgatory'](environment['plot'].set_labels,
                             run_desc['xlabel'], run_desc['ylabel'], run_desc['slabel'])
    
    environment['purgatory'](environment['plot'].set_mode, pyextfigure.DUALTWODPLOT)

    try:
        run_desc['f_Xset'](run_desc['Xstart'])
        run_desc['f_Sset'](run_desc['Sstart'])
        time.sleep(2*run_desc['pause'] + 1)

        Ssetval = run_desc['Sstart']

        while (((step <= MAX_STEPS) or run_desc['cycle?'] > 0.) and not STOP_FLAG):
            Xsetval = (run_desc['Xend'] - run_desc['Xstart']) * (1.0*step)/MAX_STEPS + run_desc['Xstart']
            run_desc['f_Xset'](Xsetval)
            run_desc['f_Sset'](Ssetval)
            if (run_desc['pause'] > 0): time.sleep(run_desc['pause'])
                
            if (run_desc['f_Xread']):
                Xreadval = run_desc['f_Xread']()
            else:
                Xreadval = Xsetval
                
            Yreadval = run_desc['f_Yread']() * run_desc['yscale']
            Sreadval = run_desc['f_Sread']()

            if ((Sreadval > run_desc['Ssetpoint']/2) and (Sreadval < 2*run_desc['Ssetpoint'])):
                Ssetval = Ssetval + run_desc['igain']*(run_desc['Ssetpoint'] - Sreadval)

            mydatabase.add_data_point([Xreadval, Yreadval, Sreadval], datastep)
            datastep = datastep + 1

            environment['purgatory'](environment['plot'].add_point, Xreadval, Yreadval, Sreadval)
            environment['purgatory'](environment['plot'].repaint)

            if (step % (MAX_STEPS/100 + 1) == 0):
                environment['purgatory'](environment['progressbar'].set_fraction, (1.0*step)/MAX_STEPS)

            step = step + increment
            if (((step == MAX_STEPS) or (step == 0)) and (run_desc['cycle?'] > 0.)):
                increment = -increment
            
            while PAUSE_FLAG:
                time.sleep(0.1)
                
    finally:
        if ((run_desc['finishat'] <= max(run_desc['Xstart'], run_desc['Xend'])) and
            (run_desc['finishat'] >= min(run_desc['Xstart'], run_desc['Xend']))):
            run_desc['f_Xset'](run_desc['finishat'])
        else:
            print "SAFETY CHECK: Finish at out of bounds. Ignoring"

    return mydatabase


#########################################################################
# Definition of 2D Scan
#########################################################################
def kernel_2DScan(run_desc, environment):
    xstep = 0
    ystep = 0
    MAX_XSTEPS = run_desc['xsteps']
    xstep_size = (run_desc['Xend'] - run_desc['Xstart'])/MAX_XSTEPS
    MAX_YSTEPS = run_desc['ysteps']
    ystep_size = (run_desc['Yend'] - run_desc['Ystart'])/MAX_YSTEPS

    comment = "2D Scan of %s against %s and %s. X starts at %.2g and ends at %.2g, with %d steps. Y starts at %.2g and ends at %.2g with %d steps"%(run_desc['zlabel'], run_desc['xlabel'], run_desc['ylabel'], run_desc['Xstart'], run_desc['Xend'], run_desc['xsteps'], run_desc['Ystart'], run_desc['Yend'], run_desc['ysteps'])  
    mydatabase = data.database(run_desc['filename'], run_desc['dirname'], 2, 3, comment)

    environment['purgatory'](environment['plot'].set_labels,
                             run_desc['xlabel'], run_desc['ylabel'], run_desc['zlabel'])
    environment['purgatory'](environment['plot'].set_mode, pyextfigure.THREEDPLOT)
    environment['purgatory'](environment['plot'].set_spot_shape, abs(xstep_size), abs(ystep_size))

    try:
        Xsetval = run_desc['Xstart']
        Ysetval = run_desc['Ystart']
        run_desc['f_Xset'](Xsetval)
        time.sleep(2*run_desc['xpause'] + 1)
        run_desc['f_Yset'](Ysetval)
        time.sleep(2*run_desc['ypause'] + 1)

        while (not STOP_FLAG):
            Ysetval = ystep * ystep_size + run_desc['Ystart']
            run_desc['f_Yset'](Ysetval)
            if (run_desc['ypause'] > 0): time.sleep(run_desc['ypause'])
            
            if (run_desc['f_Xread']):
                Xreadval = run_desc['f_Xread']()
            else:
                Xreadval = Xsetval
            if (run_desc['f_Yread']):
                Yreadval = run_desc['f_Yread']()
            else:
                Yreadval = Ysetval

            Zreadval = run_desc['f_Zread']() * run_desc['zscale']
                
            mydatabase.add_data_point([Xreadval, Yreadval, Zreadval], xstep, ystep) 

            environment['purgatory'](environment['plot'].add_point, Xsetval, Ysetval, Zreadval)
            environment['purgatory'](environment['plot'].repaint)

            ystep = int((ystep + 1)%(MAX_YSTEPS + 1))
            if (ystep == 0):
                xstep = int(xstep + 1)
                if (xstep > MAX_XSTEPS): break
                Xsetval = xstep*xstep_size + run_desc['Xstart']
                run_desc['f_Xset'](Xsetval)
                run_desc['f_Yset'](run_desc['Ystart'])
                if (run_desc['xpause'] > 0): time.sleep(run_desc['xpause'])
                
                environment['purgatory'](environment['progressbar'].set_fraction, (1.0*xstep)/MAX_XSTEPS)
                
            while PAUSE_FLAG:
                time.sleep(0.1)
                
    finally:
        if ((run_desc['finishxat'] <= max(run_desc['Xstart'], run_desc['Xend'])) and
            (run_desc['finishxat'] >= min(run_desc['Xstart'], run_desc['Xend']))):
            run_desc['f_Xset'](run_desc['finishxat'])
        else:
            print "SAFETY CHECK: Finish X at out of bounds. Ignoring"

        if ((run_desc['finishyat'] <= max(run_desc['Ystart'], run_desc['Yend'])) and
            (run_desc['finishyat'] >= min(run_desc['Ystart'], run_desc['Yend']))):
            run_desc['f_Yset'](run_desc['finishyat'])
        else:
            print "SAFETY CHECK: Finish Y at out of bounds. Ignoring"

    return mydatabase

#########################################################################
# Definition of AutoLoad
#########################################################################
def kernel_AutoLoad(run_desc, environment = None):
    environment['purgatory'](environment['plot'].set_labels, 'Time', 'Ph Counts', '')
    environment['purgatory'](environment['plot'].set_mode, pyextfigure.TWODPLOT)
    # Set endcaps, compensation electrodes, rf
    run_desc['fset_RFamp'](.01)
    run_desc['fset_caps'](run_desc['endcaps'])
    run_desc['fset_RFfrq'](run_desc['rffrq'])
  
    # Set oven
    run_desc['fset_OvenI'](run_desc['Ioven'])

    # Talk to user
    print 'The oven current has been set to %f.'%(run_desc['Ioven'])
    print 'Waiting for %d seconds.'%(run_desc['oventime'])

    try:
        tstart = time.time()
        dark_count = []
        icount = run_desc['fread_ions']
        while (time.time() - tstart < int(run_desc['oventime'])):
            if (icount):
                count = icount()
                dark_count.append(count)
                environment['purgatory'](environment['plot'].add_point, time.time() - tstart, count, count)
                environment['purgatory'](environment['plot'].repaint)
                
            time.sleep(.2);

        dark_s = stats(dark_count)
        print 'Dark counts %f (+-%f)'%(dark_s[0], dark_s[1])
    
        while not STOP_FLAG:
            print "loading an ion..."
            run_desc['fset_RFamp'](0.01)
            time.sleep(.2)
            run_desc['fset_RFamp'](run_desc['rfamp'])
            run_desc['fset_Ebias'](run_desc['egunbias'])
            run_desc['fset_EgunV'](run_desc['Vegun'])
            time.sleep(int(run_desc['eguntime']));

            # Are we actually looking for ions?
            if not icount: break
      
            run_desc['fset_EgunV'](0.0)
            time.sleep(1);
      
            bright_count = []
            for i in range(50):
                count = icount()
                # Wait to cool egun
                if (i > 10):
                    bright_count.append(count)
                environment['purgatory'](environment['plot'].add_point, time.time() - tstart, count, count)
                environment['purgatory'](environment['plot'].repaint)

                time.sleep(.2);
        
            bright_s = stats(bright_count)

            print 'Bright counts %f (+-%f)'%(bright_s[0], bright_s[1])
            if (bright_s[0] - dark_s[0] > run_desc['thresh']): 
                print "Ion observed"
                break
            
    except Exception, e:
        print e

    # Finish
    print "Shutting off oven and egun"
    run_desc['fset_Ebias'](0.)
    run_desc['fset_OvenI'](0.)
    run_desc['fset_EgunV'](0.)

#########################################################################
# Definition of AutoLoadYag
#########################################################################
def kernel_AutoLoadYag(run_desc, environment = None):
    environment['purgatory'](environment['plot'].set_labels, 'Time', 'Ph Counts', '')
    environment['purgatory'](environment['plot'].set_mode, pyextfigure.TWODPLOT)
    # Set endcaps, compensation electrodes, rf
    try:
        run_desc['fset_RFamp'](run_desc['rfamp1'])
        run_desc['fset_tend'](run_desc['tend1'])
        run_desc['fset_bend'](run_desc['bend1'])
        run_desc['fset_lmid'](run_desc['lmid1'])
        run_desc['fset_rmid'](run_desc['rmid1'])
  
        tstart = time.time()
        dark_count = []
        icount = run_desc['fread_ions']
        if (icount):
            for i in range(50):
                count = icount()
                dark_count.append(count)
                environment['purgatory'](environment['plot'].add_point, time.time() - tstart, count, count)
                environment['purgatory'](environment['plot'].repaint)
                time.sleep(.2);
            dark_s = stats(dark_count)
            print 'Dark counts %f (+-%f)'%(dark_s[0], dark_s[1])
    
        while not STOP_FLAG:
            print "loading an ion..."
            run_desc['fset_yag'](run_desc['qsdly'])
            # Are we actually looking for ions?
            if not icount: break
      
            time.sleep(1);      
            bright_count = []
            for i in range(10):
                count = icount()

                bright_count.append(count)
                environment['purgatory'](environment['plot'].add_point, time.time() - tstart, count, count)
                environment['purgatory'](environment['plot'].repaint)

                time.sleep(.2);
        
            bright_s = stats(bright_count)

            print 'Bright counts %f (+-%f)'%(bright_s[0], bright_s[1])
            if (bright_s[0] - dark_s[0] > run_desc['thresh']): 
                print "Ion observed"
                break
            
        # Finish
        print "Closing the trap"
        for i in range(51):
            x = i/50.
            y = 1 - i/50.
            run_desc['fset_RFamp'](y*run_desc['rfamp1'] + x*run_desc['rfamp2'])
            run_desc['fset_tend'](y*run_desc['tend1'] + x*run_desc['tend2'])
            run_desc['fset_bend'](y*run_desc['bend1'] + x*run_desc['bend2'])
            run_desc['fset_lmid'](y*run_desc['lmid1'] + x*run_desc['lmid2'])
            run_desc['fset_rmid'](y*run_desc['rmid1'] + x*run_desc['rmid2'])
            if STOP_FLAG:
	        break
	    time.sleep(.2)
            
    except Exception, e:
        print e
        
    return 

#########################################################################
# Definition of Wirebreak
#########################################################################
def kernel_WireBreak2(run_desc, environment):
    # Define two helpers
    def measure_background(run_desc):
        Izero = run_desc['I offset']
        data = []
        for i in range(50):
            if STOP_FLAG:
                break
            V = i * run_desc['Vsafe']/50.0
            run_desc['f_set'](V)
            time.sleep(run_desc['pause'])
            I = run_desc['f_read']() * run_desc['iscale'] - Izero
            data.append([I, V])
            run_desc['mydatabase'].add_data_point([V, I], run_desc['step'])
            run_desc['step'] = run_desc['step'] + 1
            
        fit = linear_fit(numarray.array(data))
        return (fit[0], fit[1], fit[2], fit[3])

    def get_wire_res(run_desc, V, Rzero, Vzero):
        Inow = run_desc['f_read']() * run_desc['iscale'] - run_desc['I offset']
        run_desc['mydatabase'].add_data_point([V, Inow], run_desc['step'])
        run_desc['step'] = run_desc['step'] + 1
        
        if (Inow < 1e-9):
            print "Current too low (%g A at %g V), quitting!"%(Inow, V)
            return (-1, 1e12, 1e12)

        if ((V - Vzero)/Inow < 1.0 + Rzero):
            Rzero = (V - Vzero)/Inow - 1.0
            print "Readjusting resistance of leads to %g"%(Rzero)
        
        Rnow = (V - Vzero)/Inow - Rzero

        if (Rzero < 0 or Rnow < 1):
            print "Negative resistance (imprecise offset correction?), quitting!"
            return (-1, 1, 0)
        else:
            return (0, Rnow, Rzero)

    # ACTUAL CODE STARTS HERE

    comment = "Wirebreak2 data. Setting %s, reading %s. The break rate is set to %.2g, small and large step to %.2g and %.2g. Safe value is %.2g, max value is %.2g"%(run_desc['xlabel'], run_desc['ylabel'], run_desc['rate'], run_desc['smallstep'], run_desc['bigstep'], run_desc['Vsafe'], run_desc['Vmax'])

    run_desc.update({'step' : 0, 'mydatabase' : data.database(run_desc['filename'], run_desc['dirname'], 1, 2, comment)})
    environment['purgatory'](environment['plot'].set_labels,
                             run_desc['xlabel'], run_desc['ylabel'], '')
    environment['purgatory'](environment['plot'].set_mode, pyextfigure.TWODPLOT)
    tempsafeV = run_desc['Vsafe']

    try:
        [Vzero, Rzero, sigmaVzero, sigmaRzero] = measure_background(run_desc)
        print "Voltage offset is %g (+- %g)"%(Vzero, sigmaVzero)
        print "Leads resistance is %g (+- %g)"%(Rzero, sigmaRzero)

        Rzero = Rzero - 1.0 # Wire has less than an ohm, assume an ohm
        if run_desc['Rzero'] > .1:
            Rzero = run_desc['Rzero']
            print "Overriding leads resistance to %f"%(Rzero)
        Vnow = run_desc['Vsafe'] # start at safe V
	updateV = 1
        lastdata = []
    	START_TIME = time.time()
            
        print "BREAK STARTED"
        while (not STOP_FLAG):
            # set new voltage 
	    if (updateV == 1):
            	run_desc['f_set'](Vnow)
		updateV = 0
            	time.sleep(run_desc['pause'])

            # Measure wire resistance, taking care of offsetts
            [status, Rnow, Rzero] = get_wire_res(run_desc, Vnow, Rzero, Vzero)
            if (status == -1): break
                    
            environment['purgatory'](environment['plot'].add_point, Vnow, math.log10(Rnow), 1.0)
            environment['purgatory'](environment['plot'].repaint)
                
            # Are we done?
            if (Rnow + Rzero > run_desc['target']):
                print "Exceeded target (Wire %g Ohm, Leads %g), quitting!"%(Rnow, Rzero)
                break

            # If something crazy happened, reset data, and ramp back quite a bit
            if ((len(lastdata) > 1) and (abs(math.log10(Rnow) - lastdata[len(lastdata) - 1][1]) > .3)):
                print "Jump in data, restarting fit"
                Vnow = tempsafeV
                tempsafeV = (tempsafeV + run_desc['Vsafe'])/2
                lastdata = []
		updateV = 1
                continue

            # Add data point, shifting old data out if needed
            lastdata.append([time.time() - START_TIME, math.log10(Rnow)])
            if ((lastdata[len(lastdata) - 1][0] - lastdata[0][0]) < .2): 
		continue
            while ((lastdata[len(lastdata) - 1][0] - lastdata[0][0]) > .5): 
		lastdata = lastdata[1:]

            # Find out the rate of change
            [a, rate, sigma_a, sigma_rate]  = linear_fit(numarray.array(lastdata))
            
            # Are we good?
            if ((rate > .1 * run_desc['rate']) and (rate < run_desc['rate'])):
                continue

            # Nope, what should we do?
            if ((rate < .01 * run_desc['rate']) and (Vnow < run_desc['Vmax'])):
                tempsafeV = (.9 * Vnow + 3.0*tempsafeV)/4.0
                Vnow = Vnow + run_desc['bigstep']
            elif ((rate < .1 * run_desc['rate']) and (Vnow < run_desc['Vmax'])):
                Vnow = Vnow + run_desc['smallstep']
            elif (rate > run_desc['rate'] + 3.0 * sigma_rate):
                Vnow = tempsafeV + (Vnow - tempsafeV) * (10.0/((rate/run_desc['rate'])**2 + 10.0))
                tempsafeV = (tempsafeV + run_desc['Vsafe'])/2

            # voltage change, reset data
	    updateV = 1
            lastdata = []
                
    finally:
        run_desc['f_set'](0.0)

    return run_desc['mydatabase']

#########################################################################
# Definition of DCCompShift
#########################################################################
def kernel_DCCompShift(run_desc, environment = None):
    environment['purgatory'](environment['plot'].set_labels, 'Time', 'Ph Counts', '')
    environment['purgatory'](environment['plot'].set_mode, pyextfigure.TWODPLOT)
    # Set endcaps, compensation electrodes, rf
    try:
        run_desc['fset_RFamp'](run_desc['rfamp1'])
        run_desc['fset_end_cm'](run_desc['end_cm1'])
        run_desc['fset_end_df'](run_desc['end_df1'])
        run_desc['fset_mid_cm'](run_desc['mid_cm1'])
        run_desc['fset_mid_df'](run_desc['mid_df1'])

        tstart = time.time()
        dark_count = []
        icount = run_desc['fread_ions']
	init_count = icount()

        print "Reshaping the trap"
        for i in range(101):
            count = icount()
            environment['purgatory'](environment['plot'].add_point, time.time() - tstart, count, count)
            environment['purgatory'](environment['plot'].repaint)

            if ((STOP_FLAG) or (count < init_count/2.)):
                break
            time.sleep(.5)

            x = i/100.
            y = 1 - i/100.
            run_desc['fset_RFamp'](y*run_desc['rfamp1'] + x*run_desc['rfamp2'])
            run_desc['fset_end_cm'](y*run_desc['end_cm1'] + x*run_desc['end_cm2'])
            run_desc['fset_end_df'](y*run_desc['end_df1'] + x*run_desc['end_df2'])
            run_desc['fset_mid_cm'](y*run_desc['mid_cm1'] + x*run_desc['mid_cm2'])
            run_desc['fset_mid_df'](y*run_desc['mid_df1'] + x*run_desc['mid_df2'])
            
            while PAUSE_FLAG:
                time.sleep(0.1)
    except Exception, e:
        print e

    return 

#########################################################################################
# Helper function - does standard linear fit to a set of data.
# Data should be a numpy array
#########################################################################################
def linear_fit(data):
    samples = 1.0 * data.shape[0]
    if samples <= 2:
        return (0.0, 0.0, 1e12, 1e12)

    (avgx, avgy) = numpy.add.reduce(data)/samples
    (ssxx, ssyy) = numpy.add.reduce(numpy.power(numpy.subtract(data, [avgx, avgy]), 2))/samples
    ssxy = numpy.multiply(numpy.subtract(data[:,0], avgx), numpy.subtract(data[:,1], avgy)).sum()/samples

    b = ssxy/ssxx
    a = avgy - b*avgx
    s = math.sqrt((ssyy - b*ssxy)/(samples - 2))
    sigma_b = s / math.sqrt(ssxx)
    sigma_a = s * math.sqrt(1/samples + math.pow(avgx, 2)/ssxx)

    return (a, b, sigma_a, sigma_b)

#########################################################################################
# Helper function - does average and stdev.
#########################################################################################
def stats(data):
  if not data: return (0,0)
  tot = sum(data)
  n = len(data)
  avg = 1.0*tot/n
  stdev = math.sqrt(1.0*sum(map((lambda x: x**2), data))/n - avg**2)
  return (avg, stdev)
