###
# ListCompressor.py
#
# Author: Sam Bader (samuel.james.bader@gmail.com)
# Company: Quanta Lab, MIT
# Revision: 15 July 2013
###
import math

# ListCompressor
#
# Stores lists to be plotted, compressing the list as necessary to ensure that
# no more than max_length points are kept for each series.  Points are added to
# the series using the append function, and the x and y lists for the series are
# returned using the getX and getY functions.  Mulitple y series can be stored
# for each x.
#
# To keep the algorithm fast, the assumption was made that elements should only
# be added in order of monotonically increasing x-value, and an exception will
# be thrown by the append function if a violation is detected.
#
# Compression details:
#
# The compression works by keeping two y values for x-value bin, that is, a
# maximum and a minimum y of the bin, so the lists might look something like
# this:
#
# x: 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, ...
# y: 3, 5, 4, 6, 7, 7, 8, 9, 9, 10, ...
# 
# ie a plot of this series would contain a bunch of vertical lines, one at each
# center-bin x value connecting the minimum and maximum y observed during that
# bin.  If the plot is low resolution enough compared to number of data points,
# then this is what the plot looks like anyway; this just expresses that with
# fewer points.
#
# The algorithm just keeps building up the lists with binning, until max_length
# is reached, at which point it rebins the entire series to be half as large.
#
class ListCompressor():

    # __init__
    #
    # max_length: the guaranteed maximum number of points which will be in the
    # series returned by getX() or getY().
    # numY: how many y series are there
    #
    # Note: internally, the upper-bound might be set a little bit lower,
    # specifically to the nearest multiple of four that is less than or equal to
    # the supplied max_length.  This just makes the compression easier.
    def __init__(self,max_length,numY=1):
        # Limit the max length
        self._max_length = max_length - (max_length % 4)

        #Complain if max_length got zeroed
        if max_length == 0:
            raise Exception("max_length is too low")

        # Create the empty lists
        self._x = []
        self._y = [[]] * numY
        self._numY=numY

        # No binning yet, so each point is its own bin
        self._bin_size=0

        # We'll track total x distance (for setting bin sizes)
        self._distance=0

    # append
    #
    # Adds the (x,y) value to the series, calling __compress() if necessary to
    # ensure that the lists never pass their maximum length.  Returns True iff
    # appending this pair forced a rebinning.
    #
    # If there are multiple y series being stored, the y argument should be a
    # list or tuple [y1, y2, y3...].
    #
    def append(self,x,y):
        # So you don't have to wrap individual additions in a list
        if (type(y) is not type([])) and (type(y) is not type(())):
	    y=[y]

        # Tracks whether compression was needed for this appendage
        compressed=False

        # If its the first point, just add it
        if not self._x:
            self._x=[x,x]
            self._distance=x
            for i in range(self._numY):
                self._y[i]=[y[i],y[i]]
        # Otherwise
        else:
            # If the point belongs in the current bin, then update the ymin/ymax
            # values for the bin.
            if abs(x-self._x[-1])<=self._bin_size/2:
                for i in range(self._numY):
                    self._y[i][-2]= min(self._y[i][-2],y[i])
                    self._y[i][-1]= max(self._y[i][-1],y[i])
            # Otherwise, we'll need to make a new bin, so check that we aren't
            # at the maximum length.  If we are at max, then we'll need to
            # compress
            elif len(self._x) == self._max_length:
                self.__compress()
                self.append(x,y)
                compressed=True
            # If we're safe, then add the new bin
            else:
                # If there has been no rebinning yet, then add the point at the
                # stated x value
                if self._bin_size==0:
                    # Add the point
                    self._x.extend([x,x])
                    for i in range(self._numY):
                        self._y[i].extend([y[i],y[i]])

                    # Track the total distance travelled
                    self._distance=self._distance+abs(x-self._x[-3])

                # If there has been rebinning, round to the nearest next bin
                # value.
                else:
                    # Add the bin
                    new_x=\
                        round(x/self._bin_size)*self._bin_size
                    self._x.extend([new_x,new_x])
                    for i in range(self._numY):
                        self._y[i].extend([y[i],y[i]])

                    # Track the total distance travelled
                    self._distance=self._distance+abs(new_x-self._x[-3])

        # Return whether rebinning was required
        return compressed

    # __compress
    #
    # Rebins the data to take up half as long a list
    def __compress(self):

        # For re-adjusting the distance, we track how the last point compresses
        old_last_x=self._x[-1]

        # The new bin_size (we want to have max_length/2 points at the end of
        # this, so that's max_length/4 bins.)
        self._bin_size = float(self._distance)/(self._max_length)*4;
        
        # Preallocate new lists
        new_x  =  [None] * self._max_length
        new_y  = [[None] * self._max_length for i in range(self._numY)]

        # index most recently added to of new list
        # starting negative avoids having a special case for the first addition
        new_index=-2

        # number of the bin most recently added to
        # starting negative avoids having a special case for the first addition
        bin_of_new_index=-1

        # Step through each pair of elements of the old list
        for old_index in range(0,self._max_length,2):

            # Old values
            x = self._x[old_index]
            y_min= [ None ] * self._numY
            y_max= [ None ] * self._numY
            for i in range(self._numY):
                y_min[i]= self._y[i][old_index];
                y_max[i]= self._y[i][old_index+1];

            # what new bin does the old value belong two
            bin_of_old_index= math.floor(x/self._bin_size);
            bin_of_old_index= min(bin_of_old_index, self._max_length/4-1)

            # if it's the most recently filled bin, then update y values
            if bin_of_new_index==bin_of_old_index:
                for i in range(self._numY):
                    new_y[i][new_index]=min(new_y[i][new_index],y_min[i])
                    new_y[i][new_index+1]=max(new_y[i][new_index+1],y_max[i])
            # otherwise start a new bin
            else:
                bin_of_new_index = bin_of_old_index
                new_index+=2
                new_x[new_index]    = (bin_of_new_index+.5)*self._bin_size
                new_x[new_index+1]  = (bin_of_new_index+.5)*self._bin_size
                for i in range(self._numY):
                    new_y[i][new_index]    = y_min[i]
                    new_y[i][new_index+1]  = y_max[i]

        # clear out any unnecessary Nones from the new list
        self._x=new_x[0:(new_index+2)]
        for i in range(self._numY):
            self._y[i]=new_y[i][0:(new_index+2)]

        # Readjust distance
        self._distance -= abs(self._x[-1]-old_last_x)

    # getX
    #
    # Returns the x list for plotting
    def getX(self):
        return self._x

    # getY
    #
    # Returns the y list for plotting
    #
    # index - which y series to return (numbering starts at 1)
    def getY(self,index):
        return self._y[index-1]

