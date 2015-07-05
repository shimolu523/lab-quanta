#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
ARGS = [
    'RF Frequency [MHz]',
    'RF Amplitude [Vpp]',
    'Freq422',
    'Threshold',
    'OvenTime',
    'WaitTime',
    'Oven Current [A]',
    'Loading Time',
    'NumberOfLoads',
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
            Freq422,
            Threshold,
            OvenTime,
            WaitTime,
            OvenCurrent,
            LoadingTime,
            NumberOfLoads,
            ):
        reload(Stabilization)
        try:
            self.plot = gui_exports['plot']
            self.purgatory = gui_exports['purgatory']
            self.Counts = f_read['XEM6001_PhotonCounter_counts']
            self.TopmidRead = f_read['3631A_topmid_+6V']
            self.CompRead = f_read['3631A_comp_+6V']
            self.TopmidSet = f_set['3631A_topmid_+6V']
            
            self.Unshut422 = lambda: f_set['PIShutter-RedCryo_422_set_open'](1)
            self.Shut422 = lambda: f_set['PIShutter-RedCryo_422_set_open'](0)
            self.Unshut405 = lambda: f_set['PIShutter-RedCryo_405_set_open'](1)
            self.Shut405 = lambda: f_set['PIShutter-RedCryo_405_set_open'](0)
            self.Unshut461 = lambda: f_set['PIShutter-RedCryo_461_set_open'](1)
            self.Shut461 = lambda: f_set['PIShutter-RedCryo_461_set_open'](0)
            
            # self.Say = f_set['AudioAlert_say']
            # self.ScanDone = f_set['AudioAlert_scandone']
            
            self.CompSet = f_set['3631A_comp_+6V']
            
            self.SetParameter = f_set['DDS_PARAM']
            self.SetDDS_FREQ1 = f_set['DDS_FREQ1']
            self.SetDDS_AMP1 = f_set['DDS_AMP1']
            self.SetDDS_FREQ0 = f_set['DDS_FREQ0']
            self.SetDDS_AMP0 = f_set['DDS_AMP0']
            self.SetDDS_FREQ2 = f_set['DDS_FREQ2']
            self.ReadParameter = f_read['DDS_PARAM']
            
            self.OvenVoltage = f_read['PSUP_3633A_V']
            self.OvenI = f_set['PSUP_3633A_I']
            
            self.F422 = f_read['WS7_F3']
            self.F461 = f_read['WS7_F1']
            self.F674 = f_read['WS7_F5']
            
            self.OvenTime = OvenTime
            self.LoadingTime = LoadingTime
            self.OvenThreshold = 0.460
            
            self.RFFreq = f_set['AG33250ws2_Freq']
            self.RFAmp = f_set['AG33250ws2_Vamp']
            
            self.Threshold = Threshold
            self.OvenCurrent = OvenCurrent
            self.Freq422 = Freq422
            self.WaitTime = WaitTime
            self.NumberOfLoads = NumberOfLoads
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
                'OvenCurrent=%f, WaitTime=%f, Threshold=%f, Freq422=%f, NumberOfLoads=%f, LoadingTime=%f, OvenTime=%f'\
                 % (
                OvenCurrent,
                WaitTime,
                Threshold,
                Freq422,
                NumberOfLoads,
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
        self.IonThreshold = self.backgroundCounts + self.Threshold
        timestart = time.time()
        try:
            print 'Turning on oven',
            sys.stdout.flush()
            self.OvenOn()
            OvenVoltageStart = self.OvenVoltage()
            deltatime = time.time() - timestart
        except Exception, e:
            print 'Exception occured turning on oven and unshutting', e
            raise e
        try:
            self.SetDDS_FREQ1(self.ReadParameter('F_BlueHi'))
            self.SetDDS_AMP1(self.ReadParameter('A_BlueHi'))

            self.SetDDS_FREQ0(0)
            self.SetDDS_AMP0(0)

            self.SetDDS_FREQ2(0)
        except Exception, e:
            print 'Exception occured when setting DDS', e
            raise e
        numberofions = -1
        try:
            index = 0
            while True:
                OvenVoltage = self.OvenVoltage()
                if __main__.STOP_FLAG:
                    return (deltatime, -1, OvenVoltageStart,
                            OvenVoltage)
                time.sleep(0.1)
                if index < 0:
                    print '.',
                    index = 30
                    sys.stdout.flush()
                index = index - 1
                Counts = self.Counts()
                end_counts = Counts
                deltatime = time.time() - timestart

                if OvenVoltage > self.OvenThreshold:
                    print '\nOven voltage:', OvenVoltage, \
                        ' above OvenThreshold=', self.OvenThreshold
                    print 'Too hot! Aborting.'
                    return (deltatime, -1, OvenVoltageStart,
                            OvenVoltage)
                if deltatime > self.OvenTime:
                    break
            print 'Oven on for deltatime=%.f seconds; will load for %.f seconds'\
                 % (deltatime, self.LoadingTime)

            ionload = sp.zeros(self.NumberOfLoads)
            for i in range(self.NumberOfLoads):
                print 'Opening shutters.'
                self.Unshut()
                timewaitstart = time.time()
                while self.LoadingTime > time.time() - timewaitstart:
                    time.sleep(0.05)
                    if __main__.STOP_FLAG:
                        break
                self.Shut()
                timewaitstart = time.time()
                OvenVoltage = self.OvenVoltage()
                while self.WaitTime > time.time() - timewaitstart:
                    time.sleep(0.05)
                    if __main__.STOP_FLAG:
                        break
                if self.Counts() > self.IonThreshold:
                    ionload[i] = 1
                else:
                    ionload[i] = 0
                self.RFOutput(0)
                self.RFOutput(1)
                print 'and loaded %.f ion(s)' % ionload[i]
                self.mydb.add_data_point([i, ionload[i]])
                self.purgatory(self.plot.add_point, i, ionload[i], 0)
                self.purgatory(self.plot.repaint)
                OvenVoltage = self.OvenVoltage()
            self.OvenOff()
            ProbIon = sum(ionload) / self.NumberOfLoads

            print 'Probability of loading ion (for loadingtime=%f) is: %f'\
                 % (self.LoadingTime, ProbIon)

            return (self.LoadingTime, ProbIon, OvenVoltageStart,
                    OvenVoltage)
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
        NumberOfLoads,
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
        NumberOfLoads,
        )

    try:
        (deltatime, numberofions, OvenVoltageStart, OvenVoltage) = \
            Loaderinst.Autoload()
    except Exception, e:
        Loaderinst.OvenOff()
        __main__.STOP_FLAG = True
        raise e
    Loaderinst.OvenOff()
    return (deltatime, numberofions)

RunScript = AutoloadIon

