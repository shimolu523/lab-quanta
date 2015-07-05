import gobject
import gtk
import data
import numpy as Numeric
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
        self.table = helpers.typical_io_table([ ("X Set", 'o'), ("Y1 Read", 'i'), ("Y2 Read", 'i')])
        self.tree = helpers.typical_ncol_tree([(gobject.TYPE_STRING, 'setting', 0),
                                          (gobject.TYPE_DOUBLE, 'value', 1)])

        self.tree.add_row("Hysteresis top point", 0)
        self.tree.add_row("Hysteresis top point wait", 0)
        self.tree.add_row("Hysteresis bottom point", 0)
        self.tree.add_row("Hysteresis bottom point wait", 0)
        self.tree.add_row("Measure point", 0)
        self.tree.add_row("Measure interval", 0.1)
        self.tree.add_row("Measure time", 60)
        self.tree.add_row("Y1 Scaling", 1.0)
        self.tree.add_row("Y2 Scaling", 1.0)
        self.tree.add_row("Pause", .05)
        self.tree.add_row("Finish at", 0.0)

        self.tree.restore_state("TimeDepScan")
        self.table.restore_state("TimeDepScan")

        self.topvbox.pack_start(self.tree.treeview, True, True, 0)
        self.topvbox.pack_start(self.table.table, False, False, 0)

        self.ui_target.add(self.topvbox)
        self.ui_target.show_all()
        return
        
    def unregister(self):
        self.tree.save_state("TimeDepScan")
        self.table.save_state("TimeDepScan")
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
        ikey = self.table.get_choice("X Set", 'o')
        if (ikey != "<empty>"):
	    set_function = self.open_io_set_streams[ikey]
        else:
            set_function = None
            
        y1key = self.table.get_choice("Y1 Read", 'i')
        if (y1key != "<empty>"):
            Y1_read_function = self.open_io_read_streams[y1key]
        else:
            return -1

        y2key = self.table.get_choice("Y2 Read", 'i')
        if (y2key != "<empty>"):
            Y2_read_function = self.open_io_read_streams[y2key]
        else:
            Y2_read_function = None 

        run_desc = {'f_Y1read' : Y1_read_function, 
                    'y1label' : '%s * %.2g'%(y1key, self.tree.get_data('Y1 Scaling', 1)),
                    'f_Y2read' : Y2_read_function,
                    'y2label' : '%s * %.2g'%(y2key, self.tree.get_data('Y2 Scaling', 1)),
                    'f_Xset' : set_function,
                    'xlabel' : 'time [s]',
                    'filename' : filename, 'dirname' : dirname,
                    'hysttop' : self.tree.get_data('Hysteresis top point', 1),
                    'hysttopwait' : self.tree.get_data('Hysteresis top point wait', 1),
                    'hystbot' : self.tree.get_data('Hysteresis bottom point', 1),
                    'hystbotwait' : self.tree.get_data('Hysteresis bottom point wait', 1),
                    'measureat' : self.tree.get_data('Measure point', 1),
                    'meastime' : self.tree.get_data('Measure time', 1),
                    'interval' : self.tree.get_data('Measure interval', 1),
                    'pause' : self.tree.get_data('Pause', 1),
                    'y1scale' : self.tree.get_data('Y1 Scaling', 1),
                    'y2scale' : self.tree.get_data('Y2 Scaling', 1),
                    'finishat' : self.tree.get_data('Finish at',1),
                    'impulselabel' : "%s"%(ikey)}

        __main__.run_desc = run_desc
        return 0

    def run(self):
        worker.feed('''
try:
     latestdata = kernel_TimeDepScan(run_desc, gui_exports)
finally:
     gui_exports['on_finished']()
''')
        return
