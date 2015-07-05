import gobject
import gtk
import data
#import numarray
import numpy as numarray
import math
import helpers
import time
import pyextfigure
import worker
import __main__

RUNNING = 1
WAITING = 0
SHOULDSTOP = -1

class logic_circuit:
    def __init__(self, ui_target):
        self.ui_target = ui_target
        return
    
    def register(self):
        self.topvbox = gtk.VBox(False, 0)
        self.table = helpers.typical_io_table([ ("X set", 'o'), ("X read", "i"), ("Y read", 'i')])
        self.tree = helpers.typical_ncol_tree([(gobject.TYPE_STRING, 'setting', 0),
                                          (gobject.TYPE_DOUBLE, 'value', 1)])
        self.tree.add_row("Start at", 0)
        self.tree.add_row("End at", 1)
        self.tree.add_row("Steps", 1000)
        self.tree.add_row("Y Scaling", 1.0)
        self.tree.add_row("Pause", .01)
        self.tree.add_row("Finish at", 0.0)

        self.tree.restore_state("LinFit")
        self.table.restore_state("LinFit")

        self.topvbox.pack_start(self.tree.treeview, True, True, 0)
        self.topvbox.pack_start(self.table.table, False, False, 0)

        self.ui_target.add(self.topvbox)
        self.ui_target.show_all()
        return
        
    def unregister(self):
        self.tree.save_state("LinFit")
        self.table.save_state("LinFit")
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
        
        xrkey = self.table.get_choice("X read", 'i')
        if (xrkey != "<empty>"):
            X_read_function = self.open_io_read_streams[xrkey]
        else:
            X_read_function = None
            
        ykey = self.table.get_choice("Y read", 'i')
        if (ykey != "<empty>"):
            Y_read_function = self.open_io_read_streams[ykey]
        else:
            return -1
        
        run_desc = {'f_Xset' : X_set_function,
                    'xlabel' : '%s'%(xkey),
                    'f_Xread' : X_read_function,
                    'y1label' : '%s * %.2g'%(ykey, self.tree.get_data('Y Scaling', 1)),
                    'f_Y1read' : Y_read_function,
                    'y2label' : '',
                    'f_Y2read' : None, 'cycle?' : 0,
                    'filename' : filename, 'dirname' : dirname,
                    'Xstart' : self.tree.get_data('Start at', 1), 'Xend' : self.tree.get_data('End at', 1),
                    'steps' : self.tree.get_data('Steps', 1), 'pause' : self.tree.get_data('Pause', 1),
                    'y1scale' : self.tree.get_data('Y Scaling', 1),
                    'y2scale' : 0.0,
                    'finishat' : self.tree.get_data('Finish at',1)}
        
        __main__.run_desc = run_desc
        return 0

    def run(self):
        worker.feed('''
try:
     database = kernel_1DScan(run_desc, gui_exports)

     (datapoints, validmask) = database.get_all_data_with_mask()
            
     for i in range(datapoints.shape[0]):
         if (validmask[i] != data.VALID):
             datapoints = datapoints[1:i]
             break
        
     fit  = linear_fit(datapoints[:,0:2])
                
     print "Obtained fit: y = %g + %g*x, with std dev %g and %g respectively"%(fit[0], fit[1], fit[2], fit[3])
            
finally:
     gui_exports['on_finished']()
''')
        return
