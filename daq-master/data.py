# data.py
#
# Defines a simple database, which saves data to a file
################################################################################
import time
import helpers
import numpy
import os

VALID = 1

################################################################################
# class database
#
# Creates an array with index_dims dimensions, and data_size datapoint. Opens
# a file associated_file in associated_dir to mirror the data on harddrive.
################################################################################
class database:
    def __init__(self, associated_file, associated_dir, index_dims, data_size, comment = None, params = None):
        self.data_array = numpy.zeros([1]*index_dims+[data_size + 1], "d")
        self.valid_mask = numpy.zeros([1]*index_dims, 'l')

        if (os.access(associated_dir, os.F_OK) == 0):
            os.mkdir(associated_dir)
        # Get an unused filename, in case the provided already exists
        # The way I do it is by appending a number, i.e. ".176"
        unused_name = self.get_unused_file_name(associated_dir + "/" + associated_file)
        self.datafile_fd = file(unused_name, "w")
        self.cache = helpers.Bunch(C_DATASIZE=(data_size + 1),
                                   C_STARTTIME=(time.time()))
        self.datafile_fd.write("#Starting data acquisition on %s\n"%(time.asctime()))
        self.datafile_fd.write("#%s\n"%(comment))
        if params:
            self.datafile_fd.write("#%s\n"%(params))    

        return

    def __del__(self):
        try:
            self.datafile_fd.close()
        except:
            pass
        return

    #######################################################################
    # get_unused_file_name
    #
    # takes the associated_file, and returns the first associated_file.n
    # which doesn't yet exist
    ######################################################################
    def get_unused_file_name(self, associated_file):
        tmpcounter = 1
        tmpfilename = associated_file
        while (tmpcounter < 500):
            if (os.access(tmpfilename, os.F_OK) == 1):
                tmpfilename = "%s.%d"%(associated_file, tmpcounter)
                tmpcounter = tmpcounter + 1
            else:
                return tmpfilename
        
        raise "Bad File Name!"

    ######################################################################
    # get_data_point
    #
    # returns a single datapoint, or None if it doesn't exist
    ######################################################################
    def get_data_point(self, *index):
        if (self.valid_mask[index] == VALID):
            return self.data_array[index]
        return None

    ######################################################################
    # get_all_data_with_mask
    #
    # returns all data, and a mask indicating which datapoints are valid
    # (the data_array may be larger than actual data count, to speed it up)
    ######################################################################
    def get_all_data_with_mask(self):
        data = self.data_array
        valid = self.valid_mask
        return (data, valid)

    ######################################################################
    # add_data_point
    #
    # Adds a datapoint to the array at index index. Sets the valid_mask for
    # that index. It grows the array if necessary by a factor of 2
    # Finally, it saves the index:datapoint tuple to harddrive
    ######################################################################
    def add_data_point(self, values, *index):
        newval = values + [(time.time() - self.cache.C_STARTTIME)]
        try:
            self.data_array[index] = newval
            self.valid_mask[index] = VALID
        except:
            for i in range(len(index)):
                if index[i] >= self.data_array.shape[i]:
                    padding = numpy.zeros(self.data_array.shape)
                    self.data_array = numpy.concatenate((self.data_array, padding), i)
                    self.valid_mask = numpy.concatenate((self.valid_mask, padding[...,0]), i)           
            self.data_array[index] = newval
            self.valid_mask[index] = VALID

        self.datafile_fd.write(":".join([str(i) for i in index]) +
                               ": " +
                               " ".join([str(i) for i in newval]) +
                               "\n")
        self.datafile_fd.flush()
        return
