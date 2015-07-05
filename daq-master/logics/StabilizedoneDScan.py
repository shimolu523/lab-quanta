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
        self.table = helpers.typical_io_table([ ("X set", 'o'), ("S set", 'o'), ("X read", "i"), ("Y read", 'i'), ("S read", "i")])
        self.tree = helpers.typical_ncol_tree([(gobject.TYPE_STRING, 'setting', 0),
                                          (gobject.TYPE_DOUBLE, 'value', 1)])
        self.tree.add_row("X start at", 0)
        self.tree.add_row("X end at", 1)
        self.tree.add_row("S start at", 0)
        self.tree.add_row("Steps", 1000)
        self.tree.add_row("Y Scaling", 1.)
        self.tree.add_row("Stabilize at", 10.)
        self.tree.add_row("I gain", .01)
        self.tree.add_row("Pause", .01)
        self.tree.add_row("Cycle?", 0)
        self.tree.add_row("Finish at", 0.0)

        self.tree.restore_state("Stab1DScan")
        self.table.restore_state("Stab1DScan")

        self.topvbox.pack_start(self.tree.treeview, True, True, 0)
        self.topvbox.pack_start(self.table.table, False, False, 0)

        self.ui_target.add(self.topvbox)
        self.ui_target.show_all()
        return
        
    def unregister(self):
        self.tree.save_state("Stab1DScan")
        self.table.save_state("Stab1DScan")
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

        skey = self.table.get_choice("S set", 'o')
        if (skey != "<empty>"):
            S_set_function = self.open_io_set_streams[skey]
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

        skey = self.table.get_choice("S read", 'i')
        if (skey != "<empty>"):
            S_read_function = self.open_io_read_streams[skey]
        else:
            return -1
        
    
        run_desc = {'f_Yread' : Y_read_function,
                    'ylabel' : '%s * %.2g'%(ykey, self.tree.get_data('Y Scaling', 1)),
                    'f_Sread' : S_read_function,
                    'slabel' : '%s'%(skey),
                    'igain' : self.tree.get_data('I gain', 1),
                    'f_Xread' : X_read_function,
                    'f_Xset' : X_set_function,
                    'f_Sset' : S_set_function,
                    'xlabel' : '%s'%(xkey),
                    'filename' : filename, 'dirname' : dirname,
                    'Xstart' : self.tree.get_data('X start at', 1), 'Xend' : self.tree.get_data('X end at', 1),
                    'Sstart' : self.tree.get_data('S start at', 1),
                    'steps' : self.tree.get_data('Steps', 1), 'pause' : self.tree.get_data('Pause', 1),
                    'yscale' : self.tree.get_data('Y Scaling', 1),
                    'Ssetpoint' : self.tree.get_data('Stabilize at', 1),
                    'cycle?' : self.tree.get_data('Cycle?', 1),
                    'finishat' : self.tree.get_data('Finish at',1)}

        __main__.run_desc = run_desc
        return 0

    def run(self):
        worker.feed('''
try:
     latestdata = kernel_Stab1DScan(run_desc, gui_exports)
finally:
     gui_exports['on_finished']()
''')
        return
