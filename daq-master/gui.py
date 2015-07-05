# gui.py
#
# Very long and boring file describing the user interface. It defines all the buttons,
# callback functions, menus etc.
##########################################################################################
import sys
import gtk, gobject
import helpers
import pyextfigure
import zachfigure
import os
import posix
import time
import worker
import traceback
import __main__

# Defines where I expect to see io and logic modules
LOGIC_MOD_DIR = __main__.DAQ_HOME + "/logics"
IO_MOD_DIR = __main__.DAQ_HOME + "/ios"

######################################################################################
# class gui
#
# User interface definition
######################################################################################
class gui:
  def __init__(self):
    # Create all the elements, put them together in wTree object
    self.wTree = helpers.Bunch(mainwindow = gtk.Window(),
                               statusbar = gtk.Statusbar(),
                               progressbar = gtk.ProgressBar(),
                               bstartstop = gtk.Button("Start"),
                               breset = gtk.Button("Reset"),
                               babort = gtk.ToggleButton("ABORT"),
                               bpause = gtk.ToggleButton("Pause"),
                               binitialize = gtk.Button("Initialize"),
                               controlframe = gtk.Frame("Control"),
                               ioframe = gtk.Frame("I/O"),
                               iotargetbox = gtk.VBox(False, 0), 
                               logicframe = gtk.Frame("Logic"),
                               plotframe = gtk.Frame("GFX"),
                               dirlabel = gtk.Label("Device (directory)"),
                               filelabel = gtk.Label("Run (file)"),
                               direntry = gtk.Entry(40),
                               fileentry = gtk.Entry(40),
                               plot = zachfigure.ZachFigureCanvas(),#pyextfigure.Figure(),
                               menu = self.generate_menu(),
                               bsave = gtk.Button(None, gtk.STOCK_SAVE),
                               bprint = gtk.Button(None, gtk.STOCK_PRINT),
                               bdelete = gtk.Button(None, gtk.STOCK_DELETE),
                               bblog = gtk.Button("Blog"),
                               busyindicator = gtk.Image())

    # Set some properties of objects just created
    self.wTree.mainwindow.set_title('DATA ACQ')
    self.wTree.bstartstop.set_sensitive(False)
    self.wTree.bpause.set_sensitive(False)
    self.wTree.binitialize.set_sensitive(False)
    self.wTree.breset.set_sensitive(False)

    self.wTree.direntry.set_width_chars(40)
    self.wTree.fileentry.set_width_chars(40)

    # Creation and align the "control" frame. Lots of containers etc. 
    controlhbox = gtk.HBox(False, 0)
    controlleftvbox = gtk.VBox(False, 0)
    controlmidvbox = gtk.VBox(False, 0)
    controlrightvbox = gtk.VButtonBox()
    controlrightvbox.set_layout(gtk.BUTTONBOX_SPREAD)
    # Pack it all in. First the save/print/blog buttons
    controlbuttons = gtk.HBox(False, 5)
    controlbuttons.pack_start(self.wTree.bsave, False, False, 0)
    controlbuttons.pack_start(self.wTree.bprint, False, False, 0)
    controlbuttons.pack_start(self.wTree.bdelete, False, False, 0)
    controlbuttons.pack_start(self.wTree.bblog, False, False, 0)
    # Then the rest of the buttons and entry boxes
    controlleftvbox.pack_start(self.wTree.dirlabel, True, True, 0)
    controlleftvbox.pack_start(self.wTree.direntry, True, True, 0)
    controlleftvbox.pack_start(self.wTree.filelabel, True, True, 0)
    controlleftvbox.pack_start(self.wTree.fileentry, True, True, 0)
    controlleftvbox.pack_start(controlbuttons, False, False, 5)
    controlrightvbox.pack_start(self.wTree.babort,  True, True, 5)
    controlrightvbox.pack_start(self.wTree.bpause,  True, True, 0)
    controlrightvbox.pack_start(self.wTree.breset,  True, True, 0)
    controlrightvbox.pack_start(self.wTree.binitialize,  True, True, 0)
    controlrightvbox.pack_start(self.wTree.bstartstop,  True, True, 0)
    controlhbox.pack_start(controlleftvbox, False, True, 5)
    controlhbox.pack_start(controlmidvbox, True, True, 0)
    controlhbox.pack_start(controlrightvbox, False, True, 5)
    # Add the top box to controlframe
    self.wTree.controlframe.add(controlhbox)

    # Add plot to plotframe
    self.wTree.plotframe.add(self.wTree.plot)

    # Create a scrolled window for io displays, add it to ioframe
    iowindow = gtk.ScrolledWindow()
    iowindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    iowindow.add_with_viewport(self.wTree.iotargetbox)
    self.wTree.ioframe.add(iowindow)
    
    #ZKF - Add a pane so that we can resize logic/io boxes
    rpane = gtk.VPaned()
    rpane.add1(self.wTree.logicframe)
    rpane.add2(self.wTree.ioframe)

    # Pack all the frames into a box
    midhbox = gtk.HBox(False, 0)
    midleftvbox = gtk.VBox(False, 0)
    midrightvbox = gtk.VBox(False, 0)
    midleftvbox.pack_start(self.wTree.controlframe, False, True, 0)
    midleftvbox.pack_start(self.wTree.plotframe, True, True, 0)
    #ZKF - Add the pane to the box
    midrightvbox.pack_start(rpane, True, True, 0)
    ##midrightvbox.pack_start(self.wTree.logicframe, True, True, 0)
    ##midrightvbox.pack_start(self.wTree.ioframe, False, True, 0)
    midhbox.pack_start(midleftvbox, True, True, 0)
    midhbox.pack_start(midrightvbox, False, True, 0)

    # Add progress bar, busy icon, statusbar to the bottom
    bottomhbox = gtk.HBox(False, 0)
    bottomhbox.pack_start(self.wTree.busyindicator, False, True, 0)
    bottomhbox.pack_start(self.wTree.progressbar, False, True, 0)
    bottomhbox.pack_start(self.wTree.statusbar, True, True, 0)
    pixbufanim = gtk.gdk.PixbufAnimation("%s/busy.gif"%(__main__.DAQ_HOME))
    self.wTree.busyindicator.set_from_animation(pixbufanim)

    # Add a menu on the top, and add all of it to the window
    topvbox = gtk.VBox(False, 0)
    topvbox.pack_start(self.wTree.menu, False, True, 0)
    topvbox.pack_start(midhbox, True, True, 0)
    topvbox.pack_start(bottomhbox, False, True, 0)
    self.wTree.mainwindow.add(topvbox)

    # Set some default sizes
    self.wTree.controlframe.set_size_request(450,180)
    self.wTree.plotframe.set_size_request(450,440)
    self.wTree.logicframe.set_size_request(300,420)
    self.wTree.ioframe.set_size_request(300,200)
    self.wTree.statusbar.set_size_request(450, -1)
    self.wTree.progressbar.set_size_request(300, -1) 

    # Connect signals to buttons!
    self.wTree.mainwindow.connect("delete_event", self.on_smtgui_delete_event, None)
    self.wTree.mainwindow.connect("destroy", self.on_quit_activate, None)
    self.wTree.bstartstop.connect("clicked", self.on_bstartstop_clicked, None)
    self.wTree.bpause.connect("clicked", self.on_bpause_clicked, None)
    self.wTree.babort.connect("clicked", self.on_babort_clicked, None)
    self.wTree.breset.connect("clicked", self.on_breset_clicked, None)
    self.wTree.binitialize.connect("clicked", self.on_binitialize_clicked, None)
    self.wTree.bsave.connect("clicked", self.on_bsave_clicked, None)
    self.wTree.bprint.connect("clicked", self.on_bprint_clicked, None)
    self.wTree.bdelete.connect("clicked", self.on_bdelete_clicked, None)
    self.wTree.bblog.connect("clicked", self.on_bblog_clicked, None)

    # Done, show it
    self.wTree.mainwindow.show_all()
    self.wTree.busyindicator.hide()
    gobject.timeout_add(500, self.busycheck)
    
    self.logic = None
    self.io_streams = {}
    self.io_set_hooks = {}
    self.io_read_hooks = {}
    return

  ##############################################################
  # SIGNAL HANDLERS
  ##############################################################

  ###################################################################
  # purgatory
  #
  # executes a function in an idle callback of GTK. This allows one
  # to pass a function from outside thread, to be evaluated by gui
  # Thread safer, and protects the other thread from (possibly)
  # lenghty Xwindows interaction
  ###################################################################
  def purgatory(self, function, *data):
    gobject.idle_add(self.dummycallback, function, *data)
    return

  ###################################################################
  # dummycallback
  #
  # Grabs gtk lock, runs a function, releases the lock, returns false.
  # Used only by purgatory. The funny structure is necessary to keep
  # locks happy
  ###################################################################
  def dummycallback(self, function, *data):
    gtk.gdk.threads_enter()
    try:
      function(*data)
    except Exception,e:
      print "Caught exception in purgatory!", e
    gtk.gdk.threads_leave()
    return False

  ####################################################################
  # busycheck
  #
  # Called every 500ms to check if the worker thread from daq.c
  # is executing some code. If yes, it displays a tiny movable icon
  ####################################################################
  def busycheck(self, data=None):
    gtk.gdk.threads_enter()
    if (worker.is_busy()):
      self.wTree.busyindicator.show()
    else:
      self.wTree.busyindicator.hide()
    gtk.gdk.threads_leave()
    return True

  ####################################################################
  # on_quit_activate
  #
  # Activated when file/quit is hit. Check if it is safe to quit,
  # then unregister all of the hardware and logics, and quit
  ####################################################################
  def on_quit_activate(self, widget, data=None):
    if (worker.is_busy()):
      print "Worker busy, ignoring quit request!"
      return

    try:
      if (self.logic):
        self.unregister_logic()
      for iostream in self.io_streams.keys():
        self.unregister_io(iostream)
    finally:
      gtk.main_quit()
    return

  ####################################################################
  # on_smtgui_delete_event
  #
  # Activated when the close button on window frame is hit. Here, it is
  # captured and ignored. Use file/quit
  ####################################################################
  def on_smtgui_delete_event(self, widget, event, data=None):
    self.on_quit_activate(widget, data) # screw that, i like the close button. ZKF
    return True

  ####################################################################
  # on_logic_finished
  #
  # Should be called when a logic finishes. Returns start, initialize,
  # reset buttons to their normal states
  ####################################################################
  def on_logic_finished(self):
    self.purgatory(self.wTree.bstartstop.set_label, 'Start')
    self.purgatory(self.wTree.bstartstop.set_sensitive, False)
    if (self.logic):
      self.purgatory(self.wTree.binitialize.set_sensitive, True)
      self.purgatory(self.wTree.breset.set_sensitive, True)
    return

  ####################################################################
  # on_bsave_clicked
  #
  # Activated when the save button is clicked. Asks the plot to save
  # current image to a file
  ####################################################################
  def on_bsave_clicked(self, widget, data=None):
    filename = self.wTree.fileentry.get_text()
    dirname = self.wTree.direntry.get_text()
    if (dirname == ""): dirname = "."
    if (filename == ""): filename = "blank"
    filename = dirname+"/"+filename+".png"
    self.wTree.plot.save("#screenimage#")
    posix.system('mv \#screenimage\# ' + filename)
    return

  ####################################################################
  # on_bblog_clicked
  #
  # Activated when the save button is clicked. Asks the plot to save
  # current image to a file
  ####################################################################
  def on_bblog_clicked(self, widget, data=None):
    filename = self.wTree.fileentry.get_text()
    dirname = self.wTree.direntry.get_text()
    if (dirname == ""): dirname = "."  
    if (filename == ""): filename = "blank"
    filename = dirname+"/"+filename
    self.wTree.plot.save("#screenimage#")
    posix.system("daq_blogger.sh " + filename)
    return

  ####################################################################
  # on_bprint_clicked
  #
  # Activated when the print button is clicked. Asks the plot to save
  # current image to a file, then prints it using png_printer.sh
  ####################################################################
  def on_bprint_clicked(self, widget, data=None):
    filename = self.wTree.fileentry.get_text()
    dirname = self.wTree.direntry.get_text()
    if (filename == ""): filename = "blank"
    filename = "tmp#" + filename + ".png"
    self.wTree.plot.save(filename)
    posix.system("png_printer.sh " + filename)
    return

  ####################################################################
  # on_bdelete_clicked
  #
  # Activated when delete button is hit. It erases the dataset
  # corresponding to values in file and dir entries in control frame
  ####################################################################
  def on_bdelete_clicked(self, widget, data=None):
    filename = self.wTree.fileentry.get_text()
    dirname = self.wTree.direntry.get_text()
    if (filename == ""): filename = "blank"
    if (dirname == ""): dirname = "."
    filetoerase = dirname + "/" + filename

    if (os.access(filetoerase, os.F_OK) != 1):
      print "File %s does not exist!"%(filename)
      return

    # Find the file with specified name, followed by largest number (file.number)
    # This is the scheme I use to avoid collisions
    tmpcounter = 1
    while (os.access(dirname + "/" + filename + ".%d"%(tmpcounter), os.F_OK) == 1):
      filetoerase = dirname + "/" + filename + ".%d"%(tmpcounter)
      tmpcounter = tmpcounter + 1

    # Ask to make sure user wants to delete the file
    dialog = gtk.Dialog("Are you sure?", None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                         gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
    banner = gtk.Label("Delete file %s?"%(filetoerase))
    dialog.vbox.pack_start(banner, False, False, 0)
    banner.show()
    result = dialog.run()

    if (result == gtk.RESPONSE_ACCEPT):
      print "Deleting %s"%(filetoerase)
      os.remove(filetoerase)

    dialog.destroy()
    return

  ######################################################################
  # on_babort_clicked
  #
  # Called when abort button is hit. Sets ABORT and STOP flags in global
  # (__main__) context
  ######################################################################
  def on_babort_clicked(self, widget, data=None):
    if widget.get_active():
      __main__.ABORT_FLAG = True
      __main__.STOP_FLAG = True
    else:
      __main__.ABORT_FLAG = False
    return

  ######################################################################
  # on_bpause_clicked
  #
  # Called when abort button is hit. Sets PAUSE flag in global
  # (__main__) context
  ######################################################################
  def on_bpause_clicked(self, widget, data=None):
    if widget.get_active():
      __main__.PAUSE_FLAG = True
    else:
      __main__.PAUSE_FLAG = False
    return

  #######################################################################
  # on_bstartstop_clicked
  #
  # Called when start button is hit. If it is start, change the label to
  # stop, and run the logic. If it is stop, set the STOP_FLAG, and disable
  # teh button (on_logic_finished will rename it to start again)
  #######################################################################
  def on_bstartstop_clicked(self, widget, data=None):
    button = self.wTree.bstartstop

    if (worker.is_busy() and (button.get_label() == 'Stop')):
      __main__.STOP_FLAG = True
      button.set_sensitive(False)
      self.wTree.bpause.set_sensitive(False)	# [01sep09 ichuang] disable pause button
      __main__.PAUSE_FLAG = False
      button.set_label('Start')
    elif (self.logic and not worker.is_busy() and (button.get_label() == 'Start')):
      __main__.STOP_FLAG = False
      self.wTree.binitialize.set_sensitive(False)
      self.wTree.breset.set_sensitive(False)
      self.wTree.bpause.set_sensitive(True)	# [01sep09 ichuang] enable pause button
      __main__.PAUSE_FLAG = False
      button.set_label('Stop')
      self.logic.run()
    return

  ########################################################################
  # on_breset_clicked
  #
  # calles reset function of the logic
  #########################################################################
  def on_breset_clicked(self, widget, data=None):
    self.logic.reset()
    return

  ########################################################################
  # on_binitialize_clicked
  #
  # calles initialize function of the logic with appriopriate filename, 
  # enables the start button
  #########################################################################    
  def on_binitialize_clicked(self, widget, data=None):
    filename = self.wTree.fileentry.get_text()
    dirname = self.wTree.direntry.get_text()
    if (filename == ""): filename = "blank"
    if (dirname == ""): dirname = "."
    if (self.logic.initialize(filename, dirname) == 0):
      self.wTree.bstartstop.set_sensitive(True)
    return True

  ########################################################################
  # on_logicmenu_activate
  #
  # Activated by changing the radiobuttons in logics menu. Unregisters
  # old logic, and registers newly choosen one
  ########################################################################
  def on_logicmenu_activate(self, received, current, data=None):
    if (self.logic):
      self.unregister_logic()
    if (current.get_name() != 'None'):
      self.register_logic(current.get_name())
      
    return True    

  #########################################################################
  # on_iomenu_activate
  #
  # Activated by changing the check buttons in ios menu. Depending on whether
  # The button was selected, or deselected, it registers or unregisters
  # new io module
  ##########################################################################
  def on_iomenu_activate(self, current, data=None):
    if (worker.is_busy()):
      print "Worker busy, ignoring io request!"
      return

    if (current.get_active()):
      self.register_io(current.get_name())
    else:
      self.unregister_io(current.get_name())
    return True

  #########################################################################
  # on_registerAllIOs_activate
  #
  # Activated by the "register all IOs" item in the file menu. 
  # registers or unregisters all io modules (but does not add the checkmark
  # in the IOs menu)
  ##########################################################################
  def on_registerAllIOs_activate(self, data=None):
    if (worker.is_busy()):
      print "Worker busy, ignoring io request!"
      return

    io_modules = os.listdir(IO_MOD_DIR)
    io_modules.sort()

    for name in io_modules:
      if (not name.endswith(".py")): continue
      current = name[:-3]
      self.register_io(current)
    return True

  #########################################################
  # END OF SIGNAL HANDLERS
  #########################################################
  ###########################################################################
  # status_message
  #
  # Changes the message in statusbar
  ###########################################################################
  def status_message(self, msg):
    context_id = self.wTree.statusbar.get_context_id('status_message')
    self.wTree.statusbar.pop(context_id)
    self.wTree.statusbar.push(context_id, msg)
    return

  #######################################################################
  # register_logic
  #
  # Import a new logic module, created the logic_circuit contained therein
  # and call it's register function. In case of failure, unregister the logic.
  # If it worked, regenerate the hooks (known input/output functions) to update
  # the logic on what's available. Enable start and reset buttons.
  ########################################################################
  def register_logic(self, circuit):
    if (self.logic): return
    try:
      module = __import__(circuit)
      self.logic = module.logic_circuit(self.wTree.logicframe)
      self.logic.register()
    except Exception, e:
      print "Exception occured", e
      traceback.print_exc()
      try:
        self.unregister_logic();
      except:
        pass
      return None
    
    self.regenerate_hooks()
    if not worker.is_busy():
      self.wTree.binitialize.set_sensitive(True)
      self.wTree.breset.set_sensitive(True)
      
    self.status_message("Registered logic %s"%(circuit))
    return True

  ####################################################################
  # unregister_logic
  #
  # If there's a logic registered, call it's unregister method, and
  # zero out the self.logic variable. Changed the start, init, reset
  # buttons to disabled
  ####################################################################
  def unregister_logic(self):
    if (self.logic):
      try:
        self.wTree.progressbar.set_fraction(0.0)
        self.logic.unregister()
        self.logic = None
        if not worker.is_busy():
          self.wTree.bstartstop.set_sensitive(False)
      
        self.wTree.binitialize.set_sensitive(False)
        self.wTree.breset.set_sensitive(False)
        self.status_message("Unregistered logic")
      except Exception, e:
        print "Exception occured", e
        traceback.print_exc()
    return

  ####################################################################
  # register_io
  #
  # Finds out if there is such io already. If not, finds the module
  # (all io modules are preloaded), creates the io_stream class contained
  # therein, and calls it's register method. In case of failure, tries
  # to unregister. Regenerates known hooks (i/o functions)
  ####################################################################
  def register_io(self, stream):
    if (self.io_streams.has_key(stream) and self.io_streams[stream]): return
    try:
      module = __main__.__dict__[stream]
      self.io_streams[stream] = module.io_stream(self.wTree.iotargetbox)
      self.io_streams[stream].register()
    except Exception, e:
      print "Exception occured: ", e
      traceback.print_exc()
      try:
        self.unregister_io(stream)
      except:
        pass

      return None

    self.regenerate_hooks()
    self.status_message("Registered io stream %s"%(stream))
    return True

  ###################################################################
  # unregister_io
  #
  # If such io is registered, calles it's unregister method, and
  # removes it from io_streams
  ###################################################################
  def unregister_io(self, stream):
    if (self.io_streams.has_key(stream) and self.io_streams[stream]):
      try:
        self.io_streams[stream].unregister()
        self.status_message("Unregistered io stream %s"%(stream))
      except Exception, e:
        print "Exception occured: ", e
        traceback.print_exc()
      
      self.io_streams.pop(stream, None)
      self.regenerate_hooks()

    return

  ###################################################################
  # regenerate_hooks
  #
  # Asks every io_stream from io_streams for exported functions,
  # then (if there's a logic registered) calls the logics hooks_register
  # function to register available functions with it
  ###################################################################
  def regenerate_hooks(self):    
    __main__.f_set = {}
    __main__.f_read = {}
    for i in self.io_streams:
      (dict_set, dict_read) = self.io_streams[i].hooks_provides()
      __main__.f_set.update(dict_set)
      __main__.f_read.update(dict_read)
    if self.logic: self.logic.hooks_register(__main__.f_set, __main__.f_read)

  #####################################################################
  # generate_menu
  #
  # Generates the menu based on the content of LOGIC_MOD_DIR and IO_MOD_DIR
  # Black magic.
  ######################################################################
  def generate_menu(self):
    menu_skeleton = """
    <ui><menubar name='Menubar'>
    <menu action='FileMenu'><menuitem action='RegisterAllIOs'/><menuitem action='Quit'/></menu>
    <menu action='LogicsMenu' name='Logics'><menuitem action='None'/></menu>
    <menu action='IosMenu' name='Ios'></menu>
    </menubar></ui>"""
    basic_actions = [
      ('FileMenu', None, '_File'),
      ('LogicsMenu', None, '_Logic'),
      ('IosMenu', None, '_IO'),
      ('RegisterAllIOs', None, '_RegisterAllIOs', None, 'Register all IOs', self.on_registerAllIOs_activate),
      ('Quit', gtk.STOCK_QUIT, '_Quit', None, 'Quit application', self.on_quit_activate),
      ]
    logics_actions = [('None', None, 'None', None, None, 0),]
    ios_actions = []

    logic_modules = os.listdir(LOGIC_MOD_DIR)
    logic_modules.sort()
    io_modules = os.listdir(IO_MOD_DIR)
    io_modules.sort()
    
    ui = gtk.UIManager()
    ui.add_ui_from_string(menu_skeleton)
    ag = gtk.ActionGroup('WindowActions')
    ag.add_actions(basic_actions)
      
    for name in logic_modules:
      if (not name.endswith(".py")): continue
      ui.add_ui(ui.new_merge_id(), '/Menubar/Logics', name[:-3], name[:-3], gtk.UI_MANAGER_MENUITEM, False)
      logics_actions.append((name[:-3], None, name[:-3], None, None, 1))
      
    ag.add_radio_actions(logics_actions, 0, self.on_logicmenu_activate)
      
    for name in io_modules:
      if (not name.endswith(".py")): continue
      ui.add_ui(ui.new_merge_id(), '/Menubar/Ios', name[:-3], name[:-3], gtk.UI_MANAGER_MENUITEM, False)
      ios_actions.append((name[:-3], None, name[:-3], None, None, self.on_iomenu_activate, False))

    ag.add_toggle_actions(ios_actions)
    
    ui.insert_action_group(ag, 0)
    return ui.get_widget('/Menubar')
    

############################################################
# END OF GUI CLASS DEFINITION
############################################################
