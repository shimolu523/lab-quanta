import gobject
import gtk
import data
#import Numeric
import numpy as numeric
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
        self.table = helpers.typical_io_table([ ("X set", 'o'), ("Y set", "o"), ("X read", 'i'), ("Y read", 'i'), ("Z read", 'i')])
        self.tree = helpers.typical_ncol_tree([(gobject.TYPE_STRING, 'setting', 0),
                                          (gobject.TYPE_DOUBLE, 'value', 1)])
        self.tree.add_row("Start x at", 0)
        self.tree.add_row("End x at", 1)
        self.tree.add_row("Start y at", 0)
        self.tree.add_row("End y at", 1)
        self.tree.add_row("Steps in x dir", 1000)
        self.tree.add_row("Steps in y dir", 1000)
        self.tree.add_row("Z Scaling", 1.0)
        self.tree.add_row("Pause X", .01)
        self.tree.add_row("Pause Y", .01)
        self.tree.add_row("Finish X at", 0.0)
        self.tree.add_row("Finish Y at", 0.0)

        self.tree.restore_state("2DScan")
        self.table.restore_state("2DScan")

        self.topvbox.pack_start(self.tree.treeview, True, True, 0)
        self.topvbox.pack_start(self.table.table, False, False, 0)

        self.ui_target.add(self.topvbox)
        self.ui_target.show_all()
        return
        
    def unregister(self):
        self.tree.save_state("2DScan")
        self.table.save_state("2DScan")
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
        xkey = self.table.get_choice("X set", 'o')
        if (xkey != "<empty>"):
            X_set_function = self.open_io_set_streams[xkey]
        else:
            return -1
        
        ykey = self.table.get_choice("Y set", 'o')
        if (ykey != "<empty>"):
            Y_set_function = self.open_io_set_streams[ykey]
        else:
            return -1
                    
        xrkey = self.table.get_choice("X read", 'i')
        if (xrkey != "<empty>"):
            X_read_function = self.open_io_read_streams[xrkey]
        else:
            X_read_function = None
        
        yrkey = self.table.get_choice("Y read", 'i')
        if (yrkey != "<empty>"):
            Y_read_function = self.open_io_read_streams[yrkey]
        else:
            Y_read_function = None

        zkey = self.table.get_choice("Z read", 'i')
        if (zkey != "<empty>"):
            Z_read_function = self.open_io_read_streams[zkey]
        else:
            return -1
        
        run_desc = {'f_Xread' : X_read_function,                    
                    'f_Yread' : Y_read_function,
                    'f_Zread' : Z_read_function,
                    'zlabel' : '%s * %.2g'%(zkey, self.tree.get_data('Z Scaling', 1)),
                    'f_Xset' : X_set_function,
                    'xlabel' : '%s'%(xkey),
                    'f_Yset' : Y_set_function,
                    'ylabel' : '%s'%(ykey),
                    'filename' : filename, 'dirname' : dirname,
                    'Xstart' : self.tree.get_data('Start x at', 1),
                    'Xend' : self.tree.get_data('End x at', 1),
                    'Ystart' : self.tree.get_data('Start y at', 1),
                    'Yend' : self.tree.get_data('End y at', 1),
                    'xsteps' : self.tree.get_data('Steps in x dir', 1),
                    'ysteps' : self.tree.get_data('Steps in y dir', 1),
                    'xpause' : self.tree.get_data('Pause X', 1),
                    'ypause' : self.tree.get_data('Pause Y', 1),
                    'zscale' : self.tree.get_data('Z Scaling', 1),
                    'finishxat' : self.tree.get_data('Finish X at',1),
                    'finishyat' : self.tree.get_data('Finish Y at',1)}

        __main__.run_desc = run_desc
        return 0

    def run(self):
        worker.feed('''
try:
     latestdata = kernel_2DScan(run_desc, gui_exports)
finally:
     gui_exports['on_finished']()
''')   
        return
    
