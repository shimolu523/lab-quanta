import gobject
import gtk
import data
import helpers
import time
import os
import pyextfigure
import worker
import __main__

SCRIPT_DIR = __main__.DAQ_HOME+'/scripts'

class logic_circuit:
    def __init__(self, ui_target):
        self.ui_target = ui_target;
        return

    def register(self):
        self.active_script = None
        self.script_args = None
        self.topvbox = gtk.VBox(False, 0)
	scripts = os.listdir(SCRIPT_DIR)
        # Create a liststore to store all the options
        liststore = gtk.ListStore(gobject.TYPE_STRING)

        self.tree = helpers.typical_ncol_tree([(gobject.TYPE_STRING, 'setting', 0),
                                               (gobject.TYPE_DOUBLE, 'value', 1)])

        iter = None
        for name in scripts:
            if (not name.endswith(".py")): continue
            name = name[:-3]
            if not iter: iter = liststore.append([name])
            else: liststore.append([name])
                    
        # Create a combobox
        combo = gtk.ComboBoxEntry(liststore, 0)
        combo.connect("changed", self.combo_changed, None)
        combo.set_active_iter(iter)

        self.topvbox.pack_start(combo, False, False, 0)
        self.topvbox.pack_start(self.tree.treeview, True, True, 0)

        self.ui_target.add(self.topvbox)
        self.ui_target.show_all()
        return

    def combo_changed(self, widget, data = None):
        liststore = widget.get_model()
        select = liststore.get_value(widget.get_active_iter(), 0)

        module = __import__(select)
        reload(module)
        self.script_arg_names = module.ARGS

        if self.active_script:
            self.tree.save_state("Scripts:" + self.active_script)
            self.tree.remove_rows()
            
        for name in self.script_arg_names:
            self.tree.add_row(name, 0)

        self.active_script = select
        self.tree.restore_state("Scripts:" + self.active_script)
# Fill out filename entry:
        __main__.app.wTree.fileentry.set_text(time.strftime(self.active_script+'-%H%M'))
        __main__.app.wTree.plotframe.set_label(self.active_script)
        return True
    
    def unregister(self):
        if self.active_script:
            self.tree.save_state("Scripts:" + self.active_script)
        self.topvbox.destroy()
        
    def hooks_register(self, hooks_set, hooks_read):
        return

    def reset(self):
        __main__.gui_exports['plot'].clear()
        __main__.gui_exports['purgatory'](__main__.gui_exports['progressbar'].set_fraction, 0.0)
        return
    
    def initialize(self, filename, dirname):
        args = [filename, dirname]
        for arg in self.script_arg_names:
            args.append(self.tree.get_data(arg,1))
        __main__.script_args = args
        
        return 0

    def run(self):
        worker.feed('execfile("%s/%s.py")'%(SCRIPT_DIR, self.active_script))
        
        worker.feed('''
try:
     RunScript(*script_args)
finally:
     gui_exports['on_finished']()
''')
        return

    
