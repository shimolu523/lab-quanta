#!/usr/bin/python
#
# File:   ReadSetValues3.py
# Date:   01-Sep-09
# Author: J. Labaziewicz <labaziew@mit.edu>
#
# 01-Sep-09 ichuang: This version is based on Jarek's ReadSetValues.py
#                    and is a logic module for DAQ.  It provides the set
#                    value in a spin box and lets the "enter" key also
#                    actuate the setting.

import gobject
import gtk
import helpers
import random
import math
import worker

class logic_circuit:
    def __init__(self, ui_target):
        self.ui_target = ui_target;
        return

    def register(self):
        topvbox = gtk.VBox(False, 0)

        iotable = helpers.typical_io_table([ ("Set", 'o'), ("Read", 'i')])
        iotable.restore_state("ReadSetValues")

 	buttonset = gtk.Button("Set")
        buttonset.connect("clicked", self.set_value_clicked, None)
        buttonread = gtk.Button("Read")
        buttonread.connect("clicked", self.read_value_clicked, None)

        #setentry = gtk.Entry(10)
        # 01sep09 ike
        #setentry.connect("activate", self.set_value_clicked, None)

        climb_rate = 1
        digits = 2
        stepsize = 1.0
        setentry = gtk.SpinButton(None, climb_rate, digits)
        setentry.set_range(-1000000, 10000000)
        setentry.set_increments(stepsize, stepsize)
        setentry.set_wrap(0)
        setentry.set_value(0)
        setentry.connect("value-changed", self.set_value_clicked, None)

        steplabel = gtk.Label("Set stepsize:")
        stepvalue = gtk.Entry(10)
        stepvalue.connect("activate", self.set_stepsize, None)
        stepvalue.set_text('1.0')

        readlabel = gtk.Label("<value>")
        readlabel.set_line_wrap(True)

        filler = gtk.VBox(False, 0)

        readsettable = gtk.Table(2,2, False)
        readsettable.set_row_spacing(0,5)
        readsettable.set_col_spacing(0,5)
        readsettable.attach(buttonset, 0,1,0,1, gtk.FILL|gtk.EXPAND,gtk.FILL|gtk.EXPAND)
        readsettable.attach(setentry, 1,2,0,1, gtk.FILL|gtk.EXPAND,gtk.FILL|gtk.EXPAND)
        readsettable.attach(steplabel, 0,1,1,2, gtk.FILL|gtk.EXPAND,gtk.FILL|gtk.EXPAND)
        readsettable.attach(stepvalue, 1,2,1,2, gtk.FILL|gtk.EXPAND,gtk.FILL|gtk.EXPAND)
        readsettable.attach(buttonread, 0,1,2,3, gtk.FILL|gtk.EXPAND,gtk.FILL|gtk.EXPAND)
        readsettable.attach(readlabel, 1,2,2,3, gtk.FILL|gtk.EXPAND,gtk.FILL|gtk.EXPAND)

 	buttonzero = gtk.Button("Zero All")
        buttonzero.connect("clicked", self.zeroall_value_clicked, None)
 	buttonread = gtk.Button("Read All")
        buttonread.connect("clicked", self.readall_value_clicked, None)

	topvbox.pack_start(readsettable, False, False, 5)
        topvbox.pack_start(buttonread, False, False, 5)
        topvbox.pack_start(buttonzero, False, False, 5)
        topvbox.pack_start(filler, True, True, 0)
        topvbox.pack_start(iotable.table, False, False, 5)

        tophbox = gtk.HBox(False, 0)
        tophbox.pack_start(topvbox, True, True, 5)

        self.my_widgets = {'toplevel': tophbox,
                           'iotable' : iotable,
                           'setentry' : setentry,
                           'stepvalue' : stepvalue,
                           'readlabel': readlabel}
        self.ui_target.add(tophbox)
        self.ui_target.show_all()
        return
        
    def unregister(self):
        try:
            self.my_widgets['iotable'].save_state("ReadSetValues")
            self.my_widgets['toplevel'].destroy()
        except:
            pass

    def hooks_register(self, hooks_set, hooks_read):
        self.open_io_set_streams = hooks_set
        self.open_io_read_streams = hooks_read
        self.my_widgets['iotable'].set_strings(hooks_set.keys(), hooks_read.keys())
        return

    def stop(self):
        return

    def reset(self):
	import __main__
        __main__.gui_exports['plot'].clear()
	__main__.gui_exports['purgatory'](__main__.gui_exports['progressbar'].set_fraction, 0.0)
	return
    
    def initialize(self, filename, dirname):
        return -1

    def run(self):
        return
    
    def set_stepsize(self, widget, data=None):
        stepsize = float(self.my_widgets['stepvalue'].get_text())
        self.my_widgets['setentry'].set_increments(stepsize,stepsize)
        return
    
    def set_value_clicked(self, widget, data=None):
        key = self.my_widgets['iotable'].get_choice("Set", 'o')
        if (key == "<empty>"): return

        value = float(self.my_widgets['setentry'].get_text())
        worker.feed('''f_set['%s'](%f)'''%(key, value))
        return

    def read_value_clicked(self, widget, data=None):
        key = self.my_widgets['iotable'].get_choice("Read", 'i')
        if (key == "<empty>"): return

        read_function = self.open_io_read_streams[key]
        rv = read_function()
        self.my_widgets['readlabel'].set_text("%g"%(rv))
        return

    def zeroall_value_clicked(self, widget, data=None):
        for key in self.open_io_set_streams.keys():
            if (('Magnet' in key) or ('ITC' in key)):
                continue
            worker.feed('''f_set['%s'](0.0)'''%(key))
        return

    def readall_value_clicked(self, widget, data=None):
        read_str = ""
        for key, read_function in self.open_io_read_streams.items():
            read_str = read_str + key + ": %g"%(read_function()) + "\n"
        self.my_widgets['readlabel'].set_text(read_str.rstrip())
        return
