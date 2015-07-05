import gobject
import gtk
import data
import numarray
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
        self.table = helpers.typical_io_table([
            ("Oven I set", 'o'),
            ("Egun V set", "o"),
            ("Egun bias set", 'o'),
            ("Endcap V set", 'o'),
            ("RFamp set", 'o'),
            ("RFfrq set", 'o')])
        self.tree = helpers.typical_ncol_tree([(gobject.TYPE_STRING, 'setting', 0),
                                          (gobject.TYPE_DOUBLE, 'value', 1)])
        self.tree.add_row("Oven time", 120)
        self.tree.add_row("Egun time", 10)
        self.tree.add_row("Oven I", 4.0)
        self.tree.add_row("Egun V", 2.5)
        self.tree.add_row("Egun bias", -20.0)
        self.tree.add_row("Endcaps V", 20)
        self.tree.add_row("RF amp", 6.0)
        self.tree.add_row("RF frq", 6.0)

        self.tree.restore_state("AutoLoad")
        self.table.restore_state("AutoLoad")

        self.topvbox.pack_start(self.tree.treeview, True, True, 0)
        self.topvbox.pack_start(self.table.table, False, False, 0)

        self.ui_target.add(self.topvbox)
        self.ui_target.show_all()
        return
        
    def unregister(self):
        self.tree.save_state("AutoLoad")
        self.table.save_state("AutoLoad")
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
        run_desc = {}
        key = self.table.get_choice("Oven I set", 'o')
        if (key != "<empty>"):
            run_desc['fset_OvenI'] = self.open_io_set_streams[key]
        else:
            return -1

        key = self.table.get_choice("Egun V set", 'o')
        if (key != "<empty>"):
            run_desc['fset_EgunV'] = self.open_io_set_streams[key]
        else:
            return -1

        key = self.table.get_choice("Egun bias set", 'o')
        if (key != "<empty>"):
            run_desc['fset_trode'] = self.open_io_set_streams[key]
        else:
            return -1

        key = self.table.get_choice("Endcap V set", 'o')
        if (key != "<empty>"):
            run_desc['fset_caps'] = self.open_io_set_streams[key]
        else:
            return -1

        key = self.table.get_choice("RFamp set", 'o')
        if (key != "<empty>"):
            run_desc['fset_RFamp'] = self.open_io_set_streams[key]
        else:
            return -1

        key = self.table.get_choice("RFfrq set", 'o')
        if (key != "<empty>"):
            run_desc['fset_RFfrq'] = self.open_io_set_streams[key]
        else:
            return -1

        run_desc.update({'oventime' : self.tree.get_data('Oven time', 1),
                    'eguntime' : self.tree.get_data('Egun time', 1),
                    'Ioven' : self.tree.get_data('Oven I', 1),
                    'Vegun' : self.tree.get_data('Egun V', 1),
                    'endcaps' : self.tree.get_data('Endcaps V', 1),
                    'sidetrode' : self.tree.get_data('Egun bias',1),
                    'rfamp' : self.tree.get_data('RF amp', 1),
                    'rffrq' : self.tree.get_data('RF frq',1)})
        
        __main__.run_desc = run_desc
        return 0

    def run(self):
        worker.feed('''
try:
    execfile("''' + __main__.DAQ_HOME + '''/scripts/autoload.py")
finally:
     gui_exports['on_finished']()
''')
        return
