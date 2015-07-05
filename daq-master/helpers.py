# helpers.py
#
# Defines few utilities used throughout the code
################################################################################
import gtk
import gobject
import os
import __main__

CONFIG_FILE = os.path.join(__main__.DAQ_HOME, "config.data_acq")
DEVMAP_FILE = os.path.join(__main__.DAQ_HOME, "devmap.data_acq")

################################################################################
# class Bunch
#
# Lets you define an object with a set of internal values. Useful for
# grouping together related objects, numbers etc. Similar to dictionary.
################################################################################
class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
        
################################################################################
# class typical_ncol_tree
#
# Generates a GTK tree (a table), with column header and data type determined
# by the passed arguments. For an example how it looks like, see any of my logics
################################################################################
class typical_ncol_tree:
    def __init__(self, tree_def):
	# Create a liststore to hold the data. 
	# Use tree_def = [(type, name, editable) ...] to determina data type
        self.model = gtk.ListStore(*map(lambda x:x[0], tree_def))
        self.rows = {}

	# Create a treeview
        self.treeview = gtk.TreeView(self.model)
        # Add all the columns
        for col in range(len(tree_def)):
            # New renderer for the column
            renderer = gtk.CellRendererText()
            (type, name, c_edit) = tree_def[col]
            # should the column be editable?
            if (c_edit > 0):
                renderer.connect('edited', self.cell_edited_callback, col)
                renderer.set_property('editable', True)
            # If the cell is not float, render it as text
            if (type != gobject.TYPE_DOUBLE and type != gobject.TYPE_FLOAT): 
                self.treeview.insert_column_with_attributes(-1, name, renderer, text=col)
            # If the cell is float/double, use a custom renderer
            else:
                tvcol = gtk.TreeViewColumn(name, renderer)
                tvcol.set_cell_data_func(renderer, self.render_floats, col)
                self.treeview.append_column(tvcol)
    ###############################################################################
    # cell_edited_callback
    #
    # called anytime data is changed in the tree. Changes the data in
    # underlying model
    ###############################################################################
    def cell_edited_callback(self, cell, path, text, col=0):
        iter = self.model.get_iter(path)
        self.set_data_from_text(iter, col, text)
        return gtk.TRUE

    ##############################################################################
    # add_row
    #
    # add a row to the tree, the row_data tuple must match columns data types
    # saves a pointer to the new row in self.rows
    ##############################################################################
    def add_row(self, *row_data):
        iter = self.model.append(row=row_data)
        self.rows[row_data[0]] = iter
        return

    ##############################################################################
    # clean
    #
    # Cleans the model
    ##############################################################################
    def remove_rows(self):
        for row in self.rows.keys():
            self.model.remove(self.rows[row])
        self.rows = {}
        return

    ##############################################################################
    # get_data
    #
    # Retrieve data from a specified row/column
    ##############################################################################
    def get_data(self, name, col):
        iter = self.rows[name]
        return self.model.get_value(iter, col)

    ##############################################################################
    # set_data_from_text
    #
    # Parses the text in a cell as an int or float, and changes teh value in
    # underlying model
    #############################################################################
    def set_data_from_text(self, iter, col, text):
        type = self.model.get_column_type(col)
        try:
            if (type in [gobject.TYPE_INT, gobject.TYPE_UINT]):
                val = int(text)
            elif (type in [gobject.TYPE_DOUBLE, gobject.TYPE_FLOAT]):
                val = float(text)
            return self.model.set_value(iter, col, val)
        except:
            print "Invalid value passed to tree!"
        return

    #############################################################################
    # render_floats
    #
    # Converts a float to a text value, and updates the cell text
    #############################################################################
    def render_floats(self, column, cell, model, iter, col_no = None):
        value = model.get_value(iter, col_no)
        return cell.set_property('text', "%.12g"%value)

    #############################################################################
    # save_state
    #
    # saves all the values in the tree to a file using save_to_config
    #############################################################################
    def save_state(self, root):
        for key in self.rows:
            for col in range(1, self.model.get_n_columns()):
                save_to_config(root + ':tree:' + key + ':' + str(col), self.get_data(key, col))
        return

    #############################################################################
    # restore_state
    #
    # restores all the values from file using read_from_config
    #############################################################################
    def restore_state(self, root):
        for key in self.rows:
            iter = self.rows[key]
            for col in range(1, self.model.get_n_columns()):
                val = read_from_config(root + ':tree:' + key + ':' + str(col))
                if (val): self.set_data_from_text(iter, col, val)
        return
    
##########################################################################
# typical_io_table
#
# This defines a set of combo boxes, one for input functions, another
# for output functins
##########################################################################
class typical_io_table:
    def __init__(self, names_type):
        # Create a set of combos, using names_type = [(name, direction) ...]
        # where direction is either 'i' or 'o'
        self.set_combos = {}
        self.set_combos_preference = {}
        self.read_combos = {}
        self.read_combos_preference = {}
        # Create a table for all the boxes
        self.table = gtk.Table(len(names_type), 2)

        # Create all combo boxes
        for i in range(len(names_type)):
            # Create a label
            name, type = names_type[i] 
            self.table.attach(gtk.Label(name), 0, 1, i, i+1, gtk.EXPAND|gtk.FILL, 0)
            # Create a liststore to store all the options
	    liststore = gtk.ListStore(gobject.TYPE_STRING)
            # Create a combobox
            combo = gtk.ComboBoxEntry(liststore, 0)
            # Stick it in the table
            self.table.attach(combo, 1, 2, i, i+1, gtk.EXPAND|gtk.FILL, 0)
            # Save it in read_combos, or save_combos 
            if (type == 'i'):
                self.read_combos[name] = combo
                self.read_combos_preference[name] = "<empty>"
            elif (type == 'o'):
                self.set_combos[name] = combo
                self.set_combos_preference[name] = "<empty>"

    ########################################################################
    # set_strings
    #
    # Sets the allowed values for read and set combos to read_ and set_keys
    ########################################################################
    def set_strings(self, set_keys, read_keys):
        # Sort the keys
        set_keys.sort()
        read_keys.sort()
        # Do all the read combos
        for name in self.read_combos.keys():
            combo = self.read_combos[name]
            pref = self.read_combos_preference[name]

            # Figure out if there's a valid value already selected. If so
            # save that value, we'll want to preserve it. Else, if there's
            # a prefered value (set by restore_state)
	    liststore = combo.get_model()
            if combo.get_active_iter():
                select = liststore.get_value(combo.get_active_iter(), 0)
            else:
                select = pref
            
            # Wipe all the strings from combo box
	    liststore.clear()
            # add "empty" string, and select it
            combo.set_active_iter(liststore.append(["<empty>"]))
            # Add the other keys, making sure we select the one we want
            # active
            for key in read_keys:
                idx = liststore.append([key])	
                if (select == key):
                    combo.set_active_iter(idx)

        # Same for set combos, look up comments above
        for name in self.set_combos.keys():
            combo = self.set_combos[name]
            pref = self.set_combos_preference[name]
            
	    liststore = combo.get_model()
            if combo.get_active_iter():
                select = liststore.get_value(combo.get_active_iter(), 0)
            else:
                select = pref
                
            liststore.clear()
            combo.set_active_iter(liststore.append(["<empty>"]))
            
            for key in set_keys:
                idx = liststore.append([key])	
                if (select == key):
                    combo.set_active_iter(idx)
                    
    ##################################################################
    # get_choice
    #
    # return the currently selected text in the combo box named key
    # in direction ('i' or 'o') direction
    #################################################################
    def get_choice(self, key, direction):
        if (direction == 'i'):
            return self.read_combos[key].child.get_text()
        elif (direction == 'o'):
            return self.set_combos[key].child.get_text()
        return "<empty>"

    ##################################################################
    # save_state
    #
    # save currently selected values to a config file, using save_to_config
    ##################################################################
    def save_state(self, root):
        for key in self.read_combos:
            save_to_config(root + ':i:' + key, self.get_choice(key, 'i'))
        for key in self.set_combos:
            save_to_config(root + ':o:' + key, self.get_choice(key, 'o'))    
        return

    ##################################################################
    # restore_state
    #
    # restore state from file using read_from_config. Don't actually set
    # any values (they may not be valid anymore), but save the read values
    # as preferences to be taken into account next time set_strings is
    # called
    ##################################################################
    def restore_state(self, root):
        for key in self.read_combos.keys():
            val = read_from_config(root + ':i:' + key)
            if (val): self.read_combos_preference[key] = val
        for key in self.set_combos.keys():
            val = read_from_config(root + ':o:' + key)
            if (val): self.set_combos_preference[key] = val
        return

######################################################################
# save_to_config
#
# saves a value to a CONFIG_FILE file, under header root. It either
# updates the value, if such header is already present, or adds
# both the header and value
######################################################################
def save_to_config(root, value):
    if (os.access(CONFIG_FILE, os.F_OK) == 1):
        fd = file(CONFIG_FILE, "r+")
    else:
        fd = file(CONFIG_FILE, "w+")
    
    fd.seek(0,2)
    filesize = fd.tell()
    fd.seek(0,0)

    # Look for the header root
    start = 0
    for line in fd:
        if line.startswith(root):
            end = start + len(line)
            break
        start = start + len(line)
    else:
        start = filesize
        end = filesize

    fd.seek(end, 0)

    newtext = root + ":" + str(value) + '\n'
    # save all after the header root
    oldcontent = fd.read(filesize - end)
    fd.seek(start)
    # truncate the file at the header root
    fd.truncate(start)
    # Write new data, and rest of file
    # (effectively replacing old data with new)
    fd.write(newtext + oldcontent)
    fd.close()

################################################################
# read_from_config
#
# Reads the value saved under header root from CONFIG_FILE
################################################################
def read_from_config(root):
    if (os.access(CONFIG_FILE, os.F_OK) == 0): return
    fd = file(CONFIG_FILE, "r")
    for line in fd:
        if line.startswith(root + ':'):
            return line[len(root + ':'):-1]
    return

################################################################
# devmap_remap
#
# Same as read_from_config, but uses a different file. used to save
# aliases and dev numbers of hardware
################################################################
def devmap_remap(root):
    if (os.access(DEVMAP_FILE, os.F_OK) == 0): return
    fd = file(DEVMAP_FILE, "r")
    for line in fd:
        if line.startswith(root + ':'):
            return line[len(root + ':'):-1]
    return
