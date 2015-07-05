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
        self.table = helpers.typical_io_table([ ("X set", 'o'), ("X read", "i"), ("Y1 read", 'i'), ("Y2 read", "i")])
        self.tree = helpers.typical_ncol_tree([(gobject.TYPE_STRING, 'setting', 0),
                                          (gobject.TYPE_DOUBLE, 'value', 1)])
        self.tree.add_row("Start at", 0)
        self.tree.add_row("End at", 1)
        self.tree.add_row("Steps", 1000)
        self.tree.add_row("Y1 Scaling", 1.)
        self.tree.add_row("Y2 Scaling", 1.)
        self.tree.add_row("Pause", .01)
        self.tree.add_row("Cycle?", 0)
        self.tree.add_row("Finish at", 0.0)

        self.tree.restore_state("1DScan")
        self.table.restore_state("1DScan")

        self.topvbox.pack_start(self.tree.treeview, True, True, 0)
        self.topvbox.pack_start(self.table.table, False, False, 0)

        self.ui_target.add(self.topvbox)
        self.ui_target.show_all()
        return
        
    def unregister(self):
        self.tree.save_state("1DScan")
        self.table.save_state("1DScan")
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
            
        y1key = self.table.get_choice("Y1 read", 'i')
        if (y1key != "<empty>"):
            Y1_read_function = self.open_io_read_streams[y1key]
        else:
            return -1

        y2key = self.table.get_choice("Y2 read", 'i')
        if (y2key != "<empty>"):
            Y2_read_function = self.open_io_read_streams[y2key]
        else:
            Y2_read_function = None
        
    
        run_desc = {'f_Y1read' : Y1_read_function,
                    'y1label' : '%s * %.2g'%(y1key, self.tree.get_data('Y1 Scaling', 1)),
                    'f_Y2read' : Y2_read_function,
                    'y2label' : '%s * %.2g'%(y2key, self.tree.get_data('Y2 Scaling', 1)),
                    'f_Xread' : X_read_function,
                    'f_Xset' : X_set_function,
                    'xlabel' : '%s'%(xkey),
                    'filename' : filename, 'dirname' : dirname,
                    'Xstart' : self.tree.get_data('Start at', 1), 'Xend' : self.tree.get_data('End at', 1),
                    'steps' : self.tree.get_data('Steps', 1), 'pause' : self.tree.get_data('Pause', 1),
                    'y1scale' : self.tree.get_data('Y1 Scaling', 1),
                    'y2scale' : self.tree.get_data('Y2 Scaling', 1),
                    'cycle?' : self.tree.get_data('Cycle?', 1),
                    'finishat' : self.tree.get_data('Finish at',1)}

        __main__.run_desc = run_desc
        return 0

    def run(self):
        worker.feed('''
try:
     latestdata = kernel_1DScan(run_desc, gui_exports)
finally:
     gui_exports['on_finished']()
''')
        return
