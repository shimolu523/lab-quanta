#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
ARGS = [
    'RF Frequency [MHz]',
    'RF Amplitude [Vpp]',
    '422 Frequency, Detuned [THz]',
    'Ion Threshold [Counts]',
    'Maximum Oven Time [s]',
    'Maximum Wait Time [s]',
    'Oven Current [A]',
    'Maximum Loading Time [s]',
    'Maximum Number Of Loads',
    ]
import time
import scipy as sp
import Stabilization
import CavityStabilization


class AutoloadIonRedCryoClass:

    def __init__(
        self,
        filename,
        dirname,
        Omega_rf,
        Vpp_rf,
        Freq422,
        Threshold,
        OvenTime,
        WaitTime,
        OvenCurrent,
        LoadingTime,
        MaxNumOfLoads,
        ):

        reload(Stabilization)
        try:
            self.plot = gui_exports['plot']
            self.purgatory = gui_exports['purgatory']
            self.Counts = f_read['XEM6001_PhotonCounter_counts']
            self.IntTimeFn = f_read['XEM6001_PhotonCounter_int_time']
            self.IntTime = 0
            self.TopmidRead = f_read['3631A_topmid_+6V']
            self.CompRead = f_read['3631A_comp_+6V']
            self.TopmidSet = f_set['3631A_topmid_+6V']

            self.Unshut422 = lambda : \
                f_set['PIShutter-RedCryo_422_set_open'](1)
            self.Shut422 = lambda : \
                f_set['PIShutter-RedCryo_422_set_open'](0)
            self.Unshut405 = lambda : \
                f_set['PIShutter-RedCryo_405_set_open'](1)
            self.Shut405 = lambda : \
                f_set['PIShutter-RedCryo_405_set_open'](0)
            self.Unshut461 = lambda : \
                f_set['PIShutter-RedCryo_461_set_open'](1)
            self.Shut461 = lambda : \
                f_set['PIShutter-RedCryo_461_set_open'](0)

            self.CompSet = f_set['3631A_comp_+6V']

            self.SetParameter = f_set['DDS_PARAM']
            self.SetDDS_FREQ1 = f_set['DDS_FREQ1']
            self.SetDDS_AMP1 = f_set['DDS_AMP1']
            self.SetDDS_FREQ0 = f_set['DDS_FREQ0']
            self.SetDDS_AMP0 = f_set['DDS_AMP0']
            self.SetDDS_FREQ2 = f_set['DDS_FREQ2']
            self.ReadParameter = f_read['DDS_PARAM']

            self.OvenI = f_set['PSUPdev6_p6I']

            self.F422 = f_read['WS7_F3']
            self.F461 = f_read['WS7_F1']
            self.F674 = f_read['WS7_F5']

            self.OvenTime = OvenTime
            self.LoadingTime = LoadingTime

            self.RFSetOn = f_set['AG33250ws2_OutPut']
            self.RFFreq = f_set['AG33250ws2_Freq']
            self.RFAmp = f_set['AG33250ws2_Vamp']

            self.Threshold = Threshold
            self.OvenCurrent = OvenCurrent
            self.Freq422 = Freq422
            self.WaitTime = WaitTime
            self.MaxNumOfLoads = MaxNumOfLoads
            self.NumberOfLoads = 0
            self.Omega_rf = Omega_rf
            self.Vpp_rf = Vpp_rf

            self.Stab = Stabilization.Stabilization(f_set, f_read,
                    gui_exports)
            self.const = self.Stab.LoadConstants(DAQ_HOME
                     + '/scripts/StabilizationConstants')
            self.CavStab = \
                CavityStabilization.CavityStabilization(f_set, f_read,
                    gui_exports)
            self.const = self.CavStab.LoadConstants(DAQ_HOME
                     + '/scripts/CavityStabilizationConstants')
            label = \
                'OvenCurrent=%f, WaitTime=%f, Threshold=%f, Freq422=%f, MaxNumOfLoads=%f, LoadingTime=%f, OvenTime=%f'\
                 % (
                OvenCurrent,
                WaitTime,
                Threshold,
                Freq422,
                MaxNumOfLoads,
                LoadingTime,
                OvenTime,
                )
            label = label\
                 + '\n#LoadingTime,Probability of ion loading, Oven voltage Start, Oven voltage End'
            self.mydb = data.database(filename, dirname, 1, 2, label)
            self.purgatory(self.plot.clear)
            self.purgatory(self.plot.set_mode, pyextfigure.TWODPLOT)
            self.purgatory(self.plot.set_labels, 'Exp no', 'Ion loaded?'
                           , '<empty>')
        except Exception, e:
            print 'Exception occured while instantiating AutoloadIonClass:', \
                e
            raise e

    def OvenOn(self):
        self.OvenI(self.OvenCurrent)

    def OvenOff(self):
        self.OvenI(0)

    def Autoload(self):
        self.IntTime = self.IntTimeFn()
        
        self.RFSetOn(0)
        self.RFFreq(float(Omega_rf) * 1e6)
        self.RFAmp(float(Vpp_rf))
        print 'I set the rf frequency to %.3f MHz and amplitude to %.3f Vpp.' % (Omega_rf, Vpp_rf)
        print 'If this is bad, you have 7 seconds to stop me before I turn on the output.'
        timestart = time.time()
        for i in xrange(7, 1, -1):
            print '%d seconds remaining...'%i
            time.sleep(1)
            if __main__.STOP_FLAG:
                return
        print '1 second remaining...'
        time.sleep(1)
        if __main__.STOP_FLAG:
            return
        print "Let's begin. Turning RF on..."
        # self.RFSetOn(1)
        
        try:

            self.F422target = self.Freq422
            if abs(self.F422() - self.F422target) > 0.00001:
                self.Stab.BlueLockFreq(freq=self.F422target)

            print '461 laser frequency: %.6f' % self.F461()
            while abs(650.50386 - self.F461()) > 0.00004:
                text = '461 laser is off resonance!'
                print text

                time.sleep(5)
                if __main__.STOP_FLAG:
                    break
        except Exception, e:

            print 'Exception occured while checking/setting laser frequencies:', \
                e
            raise e
        Counts = self.Counts()
        self.backgroundCounts = self.Counts()

        timestart = time.time()
        try:
            print 'Turning on oven',
            sys.stdout.flush()
            self.OvenOn()

            deltatime = time.time() - timestart
        except Exception, e:
            print 'Exception occured turning on oven and unshutting', e
            raise e
        try:
            self.SetDDS_FREQ1(self.ReadParameter('F_BlueHi'))
            self.SetDDS_AMP1(self.ReadParameter('A_BlueHi'))
        except Exception, e:

            print 'Exception occured when setting DDS', e
            raise e

        try:
            index = 0
            deltatime = 0
            while deltatime > self.OvenTime:
                if __main__.STOP_FLAG:
                    return
                time.sleep(0.1)
                if index < 0:
                    print '.'
                    index = 30
                    sys.stdout.flush()
                index = index - 1
                Counts = self.Counts()
                end_counts = Counts
                deltatime = time.time() - timestart

            print 'Oven on for deltatime=%.f seconds; will load for a maximum of %.f seconds'\
                 % (deltatime, self.LoadingTime)

            start_time = time.time()

            ionload = sp.zeros(self.MaxNumOfLoads)
            num_ions = []
            for self.MaxNumOfLoads in xrange(self.MaxMaxNumOfLoads):
                print 'Opening PI shutters.'
                self.Unshut405()
                self.Unshut461()

                timewaitstart = time.time()
                while self.Counts() - self.backgroundCounts\
                     <= self.IonThreshold:
                    time.sleep(0.05)
                    if self.WaitTime > time.time() - timewaitstart:
                        print 'Exceeded maximum wait time for this load attempt.'
                        break
                    if __main__.STOP_FLAG:
                        break

                self.Shut405()
                self.Shut461()
                num_ions.append(round(float(self.Counts()
                                 - self.backgroundCounts)
                                 / self.IonThreshold))
                if num_ions[-1] > 0:
                    ionload[i] = 1
                else:
                    ionload[i] = 0
                print 'Loaded %.f ion(s)' % num_ions[-1]
                if num_ions[-1] > 1:
                    shutter_delay = self.IntTime
                    while num_ions[-1] > 1:
                        self.Shut422()
                        time.sleep(shutter_delay)
                        self.Unshut422()
                        num_ions.append(round(float(self.Counts()
                                 - self.backgroundCounts)
                                 / self.IonThreshold))
                        shutter_delay += self.IntTime
                
                if num_ions[-1] == 1: # do not change to elif
                    print "We're done!"
                    return
                    
        except Exception, e:
            print 'Exception occured in loading loop', e
            raise e


def AutoloadIon(
    filename,
    dirname,
    Omega_rf,
    Vpp_rf,
    Freq422,
    Threshold,
    OvenTime,
    WaitTime,
    OvenCurrent,
    LoadingTime,
    MaxNumOfLoads,
    ):

    Loaderinst = AutoloadIonRedCryoClass(
        filename,
        dirname,
        Omega_rf,
        Vpp_rf,
        Freq422,
        Threshold,
        OvenTime,
        WaitTime,
        OvenCurrent,
        LoadingTime,
        MaxNumOfLoads,
        )

    try:
        Loaderinst.Autoload()
    except Exception, e:
        Loaderinst.OvenOff()
        __main__.STOP_FLAG = True
        raise e
    Loaderinst.OvenOff()
    return


RunScript = AutoloadIon

