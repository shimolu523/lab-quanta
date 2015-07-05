import gobject
import gtk
import data
import helpers
import time
import pyextfigure
import worker
import __main__

class logic_circuit:
    def __init__(self, ui_target):
        self.ui_target = ui_target;
        return

    def register(self):
        self.topvbox = gtk.VBox(False, 0)
        self.table = helpers.typical_io_table([ ("Set", 'o'), ("Read", "i")])
        self.tree = helpers.typical_ncol_tree([(gobject.TYPE_STRING, 'setting', 0),(gobject.TYPE_DOUBLE, 'value', 1)])
        self.tree.add_row("Start at", 0)
        self.tree.add_row("Setpoint", 0)
        self.tree.add_row("Upper Bound", 10.0)
        self.tree.add_row("Lower Bound", -10.0)
        self.tree.add_row("Read Scaling", 1.)
	self.tree.add_row("Lower Read Cutoff", 1.)
        self.tree.add_row("Upper Read Cutoff", 710.96500)
        self.tree.add_row("P Gain", -200.)
        self.tree.add_row("I Gain", .1)
        self.tree.add_row("Pause", 1.)

        self.tree.restore_state("PIDlock")
        self.table.restore_state("PIDlock")

        self.topvbox.pack_start(self.tree.treeview, True, True, 0)
        self.topvbox.pack_start(self.table.table, False, False, 0)

        self.ui_target.add(self.topvbox)
        self.ui_target.show_all()
        return
        
    def unregister(self):
        self.tree.save_state("PIDlock")
        self.table.save_state("PIDlock")
        self.topvbox.destroy()
        
    def hooks_register(self, hooks_set, hooks_read):
        self.open_io_set_streams = hooks_set
        self.open_io_read_streams = hooks_read
        self.table.set_strings(hooks_set.keys(), hooks_read.keys())
        return

    def reset(self):
        __main__.gui_exports['plot'].clear()
        __main__.gui_exports['purgatory'](__main__.gui_exports['progressbar'].set_fraction, 0.0)
        return
    
    def initialize(self, filename, dirname):
        setkey = self.table.get_choice("Set", 'o')
        if (setkey != "<empty>"):
            set_function = self.open_io_set_streams[setkey]
        else:
            return -1
        
        readkey = self.table.get_choice("Read", 'i')
        if (readkey != "<empty>"):
            read_function = self.open_io_read_streams[readkey]
        else:
            return -1
    
        run_desc = {'read_func' : read_function,
                    'y1label' : '%s'%(readkey),
                    'set_func' : set_function,
                    'y2label' : '%s'%(setkey),
                    'xlabel' : 'Time [s]',
                    'filename' : filename, 'dirname' : dirname,
                    'xstart' : self.tree.get_data('Start at', 1),
                    'setpoint' : self.tree.get_data('Setpoint', 1),
                    'ubound' : self.tree.get_data('Upper Bound', 1),
                    'lbound' : self.tree.get_data('Lower Bound', 1),
                    'scale' : self.tree.get_data('Read Scaling', 1),
		    'lcutoff' : self.tree.get_data('Lower Read Cutoff', 1),
                    'ucutoff' : self.tree.get_data('Upper Read Cutoff', 1),
                    'pgain' : self.tree.get_data('P Gain', 1),
                    'igain' : self.tree.get_data('I Gain', 1),
                    'pause' : self.tree.get_data('Pause', 1)}

        __main__.run_desc = run_desc
        return 0

    def run(self):
        worker.feed('''
try:
     latestdata = kernel_PIDlock(run_desc, gui_exports)
finally:
     gui_exports['on_finished']()
''')
        return
