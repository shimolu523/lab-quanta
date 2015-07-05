# run_gui.py
# 
# Init script, meant to generate gui. Called by gui thread of daq. When this
# terminates, the whole app will terminate. It is run as a text file, not a 
# module (this affects the scope of variables defined/changed)
#
import gtk
import posix
import gui

app = gui.gui()

# These variables are used to change the state of user interface upon 
# completion of a task, to plot data, change progressbar val etc. 
gui_exports = {'purgatory' : app.purgatory,
               'on_finished' : app.on_logic_finished,
               'plot' : app.wTree.plot,
               'progressbar' : app.wTree.progressbar}

gtk.gdk.threads_init()
gtk.gdk.threads_enter()
gtk.main()
gtk.gdk.threads_leave()
