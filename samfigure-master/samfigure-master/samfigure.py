########################################################
#Written by Zach Fisher
#Edited 2012-11-26 by Michael Gutierrez
#Edited 2013-07-18 by Sam Bader
#
# Once upon a time there was a student name Zach.. who dreamed.
#...To remove pyextfigure.
#
# AND HE DIDN'T COMMENT ANY OF HIS CODE.  JERK.
########################################################


#import pyextfigure
import numpy
import gtk
import threading
from matplotlib.figure import Figure as MPLFigure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
import matplotlib.patches
import mpl_toolkits.mplot3d.axes3d as p3
import sys
import time
import ListCompressor

# plot types
TWODPLOT = 1
DUALTWODPLOT = 2
THREEDPLOT = 3
CONTOURPLOT = 4
# 3D plot methods
WIREFRAME = 10
CONTOUR = 11
SURFACE = 12

# Long-plotting parameters
LC_LENGTH=1000
COUNT_REPLOT=1000

class Figure(gtk.VBox):
    def __init__(self):
        print "Starting up SamFigure!"
        gtk.VBox.__init__(self)
        self.figure = MPLFigure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.ax = self.figure.add_subplot(111)
        self.ax2 = None
        self.mode = TWODPLOT
        self.new_data()
        self.xlabel = ''
        self.y1label = ''
        self.y2label = ''
        self.xsize = 0
        self.ysize = 0
        self.packed = False
        self.count_since_replot=0

        self.set_colors()


    def on_click(self,event):
        # If left button, 
        if event.button==1:
                # screen coordinates of click
                xclick,yclick= event.x, event.y
                top_ax=event.inaxes
                if top_ax is None: return

                # display coordinates of nearest point in ax
                data1=self.ax.transData.transform(\
                    zip(self.listing.getX(),self.listing.getY(1)))
                distances1=\
                    [(x-xclick)**2+(y-yclick)**2 \
                    for (x,y) in data1]
                ind_sel1=numpy.argmin(distances1)
                dist1 = distances1[ind_sel1]
                xsel,ysel= data1[ind_sel1]
                label_ax=self.ax
                label_color='b'

                # if DUAL, then also check ax2 for nearer points
                if self.mode==DUALTWODPLOT:
                    data2=self.ax2.transData.transform(\
                        zip(self.listing.getX(),self.listing.getY(2)))
                    distances2=\
                        [(x-xclick)**2+(y-yclick)**2 \
                        for (x,y) in data2]
                    ind_sel2=numpy.argmin(distances2)
                    dist2 = distances2[ind_sel2]
                    if dist2<dist1:
                        xsel,ysel= data2[ind_sel2]
                        label_color='g'
                        label_ax=self.ax2

                # Clear off old labels
                if hasattr(self,"label_text"):
                    self.label_text.remove()
                    self.label_point.remove()
                    del(self.label_text)
                
                # Coordinates to show ( data coordinates of the selected axes)
                xlabel,ylabel=label_ax.transData.inverted().transform((xsel,ysel))

                # Coordinates to place label (on top set of axes)
                xloc,yloc=top_ax.transData.inverted().transform((xsel,ysel))

                # Label the point
                if (xloc > sum(self.ax.get_xlim())/2): h_align='right'
                else: h_align='left'
                self.label_text=\
                    top_ax.text(xloc,yloc,'({0:.3g},{1:.3g})'\
                        .format(xlabel,ylabel),\
                        backgroundcolor='white', color=label_color,\
                        verticalalignment='bottom', horizontalalignment=h_align,\
                        bbox={'facecolor': 'white', 'boxstyle':
                              'round'},zorder=100 )
                self.label_point,=\
                        top_ax.plot(xloc,yloc,'ro',\
                        zorder=self.label_text.get_zorder()+1)
                self.repaint()

        # Otherwise, just clear off old labels
        else:
            self.label_text.remove()
            self.label_point.remove()
            del(self.label_text)
            self.repaint()

    def replot(self):
        if self.mode == TWODPLOT:
                self.ax.clear()
                self.ax.plot(self.listing.getX(),self.listing.getY(1),self.color1+'.-')
                self.count_since_replot=0
        elif self.mode == DUALTWODPLOT:
                self.ax.clear()
                self.ax2.clear()
                self.ax.plot(self.listing.getX(),self.listing.getY(1),self.color1+'.-')
                self.ax2.plot(self.listing.getX(),self.listing.getY(2),self.color2+'.-')
                self.count_since_replot=0

    def show(self):
        try:
            if not self.packed:
                self.pack_start(self.canvas, expand=True)
                toolbar = NavigationToolbar(self.canvas, self.get_parent_window())

                next = 8
                button = gtk.Button('Lin y')
                button.show()
                button2 = gtk.Button('Lin x')
                button2.show()
                # linear/log
                def clicked(button):
                    self.adjust_axis_margins()
                    self.set_axis_labels()
                    self.color_labels()
                    self.canvas.draw_idle()
                    self.canvas.show()
                    if self.ax.get_yscale() == 'log':
                        button.set_label('Lin y')
                        self.ax.set_yscale('linear')
                    else:
                        button.set_label('Log y')
                        self.ax.set_yscale('log')
                    self.show()


                def clicked2(button):
                    self.adjust_axis_margins()
                    self.set_axis_labels()
                    self.color_labels()
                    self.canvas.draw_idle()
                    self.canvas.show()
                    if self.ax.get_xscale() == 'log':
                        button.set_label('Lin x')
                        self.ax.set_xscale('linear')
                    else:
                        button.set_label('Log x')
                        self.ax.set_xscale('log')
                    self.show()


                button.connect('clicked', clicked)
                button2.connect('clicked', clicked2)

                toolitem=gtk.ToolItem()
                toolitem.show()
                toolitem.add(button)
                toolbar.insert(toolitem, next)
                next +=1
                toolitem2=gtk.ToolItem()
                toolitem2.show()
                toolitem2.add(button2)
                toolbar.insert(toolitem2, next)


                self.pack_start(toolbar, expand=False)
                self.packed = True
            super(Figure, self).show()
        except Exception, e:
            print 'Exception: ', e
            raise

    # xnew, y1new, and y2new can all be scalars or lists
    def add_point(self, xnew, y1new, y2new = None, no_replot=False, connect=True):
        if (self.mode==TWODPLOT or self.mode==DUALTWODPLOT) and type(xnew)==type([]):
            for (x,y1,y2) in zip(xnew,y1new,y2new):
                self.listing.append(float(x),[float(y1),float(y2)])
            self.count_since_replot=COUNT_REPLOT
        else:
            self.x.append(xnew)
            self.y1.append(y1new)
            self.y2.append(y2new)
            self.z1.append(y2new)
            if (self.mode==TWODPLOT or self.mode==DUALTWODPLOT):
                self.listing.append(xnew,[y1new,y2new])

        if self.mode == TWODPLOT:
            if not no_replot and (self.count_since_replot==COUNT_REPLOT):
                self.replot()
            else:
                if len(self.x) >= 2:
                    if connect:
                        self.ax.plot(self.x[-2:], self.y1[-2:], self.color1+'.-')
                    self.x = self.x[-2:]
                    self.y1 = self.y1[-2:]
                self.count_since_replot+=1
        elif self.mode == DUALTWODPLOT:
            if not no_replot and (self.count_since_replot==COUNT_REPLOT):
                self.replot()
            else:
                if len(self.x) >= 2:
                    if connect:
                        self.ax.plot( self.x[-2:], self.y1[-2:], self.color1+'.-')
                        self.ax2.plot(self.x[-2:], self.y2[-2:], self.color2+'.-')
                    self.x = self.x[-2:]
                    self.y1 = self.y1[-2:]
                    self.y2 = self.y2[-2:]
                    self.count_since_replot+=1
        elif self.mode == THREEDPLOT:
            X,Y = numpy.meshgrid(self.xgrid, self.ygrid)
            # if Z doesn't exist yet, initialize it with zeroes
            if len(self.x) <= 1:
                self.Z = numpy.zeros((len(X),len(Y)))
            for i in range(len(self.x)):
                # generate the Z values
                self.Z[(self.y1[i]-self.ymin)/self.ystep,(self.x[i]-self.xmin)/self.xstep] = self.y2[i]
            # options: plot_wireframe, plot_surface, plot_contour
            if self.plotmethod == WIREFRAME:
                self.im=self.ax.plot_wireframe(X,Y,self.Z)
            elif self.plotmethod == CONTOUR:
                self.im=self.ax.plot_contour(X,Y,self.Z)
            elif self.plotmethod == SURFACE:
                self.im=self.ax.plot_surface(X,Y,self.Z)
        elif self.mode == CONTOURPLOT:
            X,Y = numpy.meshgrid(self.xgrid, self.ygrid)
            # if Z doesn't exist yet, initialize it with zeroes
            if len(self.x) <= 1:
                self.Z = numpy.zeros((len(X)+1,len(Y)+1))
            for i in range(len(self.x)):
                # generate the Z values from the input array
                self.Z[(self.y1[i]-self.ymin)/self.ystep,(self.x[i]-self.xmin)/self.xstep] = self.y2[i]

            self.im=self.ax.pcolormesh(X,Y,self.Z, vmax=self.Z.max(), vmin=self.Z[numpy.nonzero(self.Z)].min())
            self.ax.axis([self.xmin, self.xmax, self.ymin, self.ymax])

    def set_colors(self, color1='b', color2='g'):
        self.color1=color1
        self.color2=color2

    def set_labels(self, xlabel = None, y1label = None, y2label = None):
        if xlabel is not None:
            self.xlabel = xlabel
        if y1label is not None:
            self.y1label = y1label
        if y2label is not None:
            self.y2label = y2label

    # if data is not None, it should be numpy arrays
    def new_data(self,data=None):
        if self.mode == TWODPLOT:
            self.listing=ListCompressor.ListCompressor(LC_LENGTH,1)
        elif self.mode == DUALTWODPLOT:
            self.listing=ListCompressor.ListCompressor(LC_LENGTH,2)
        self.x = []
        self.y1 = []
        self.y2 = []
        self.z1 = []

        # Clear off old labels
        if hasattr(self,"label_text"):
            del(self.label_text)
        
        self.COUNT_REPLOT=0
        if (data!=None):
            self.add_point(data[:,0].tolist(),data[:,1].tolist(),data[:,2].tolist())

    def set_spot_shape(self, xsize, ysize):
        pass

    def reset_axes(self):
        self.COUNT_REPLOT=0
        if self.mode != THREEDPLOT:
            self.figure.clf()
        # delete current axes
        for axis in self.figure.axes:
            pass
            #self.figure.delaxes(axis)
        if self.mode == TWODPLOT:
            self.ax = self.figure.add_subplot(111)
            self.ax.hold(True)
            self.ax2 = None
        elif self.mode == DUALTWODPLOT:
            self.ax = self.figure.add_subplot(111)
            self.ax.hold(True)
            self.ax2 = self.ax.twinx()
            self.ax2.hold(True)
        elif self.mode == THREEDPLOT:
            self.ax.cla()
            self.ax = self.figure.add_subplot(111, projection='3d')
            self.ax.hold(True)
            self.ax2 = None
        elif self.mode == CONTOURPLOT:
            self.ax = self.figure.add_subplot(111)
            #self.ax.hold(True)
            self.ax2 = None

    def adjust_axis_margins(self):
        self.figure.subplots_adjust(top=0.95)
        self.figure.subplots_adjust(left=0.15)
        if self.mode == TWODPLOT:
            self.figure.subplots_adjust(right=0.95)
        else:
            self.figure.subplots_adjust(right=0.85)

    def set_axis_labels(self):
        if self.xlabel != '':
            self.ax.set_xlabel(self.xlabel)
        if self.y1label != '':
            self.ax.set_ylabel(self.y1label)
        if self.y2label != '' and self.ax2 is not None:
            self.ax2.set_ylabel(self.y2label)
        if self.y2label != '' and (self.mode == CONTOURPLOT or self.mode == THREEDPLOT):
            self.ax.set_title(self.y2label)

    def color_labels(self):
        for tl in self.ax.get_yticklabels():
            tl.set_color('b')
        if self.ax2 is not None:
            for tl in self.ax2.get_yticklabels():
                tl.set_color('g')

    def repaint(self):
        # adjusting axes in contour plot causes graph to overlap with color bar
        if self.mode != CONTOURPLOT:
            self.adjust_axis_margins()
        self.set_axis_labels()
        self.color_labels()
        # contour plot: draw color bar if it doesn't already exist
        #if self.mode == CONTOURPLOT and hasattr(self, 'im') and hasattr(self, 'cb')==0:
        #       self.cb=self.figure.colorbar(self.im)
        # contour plot: update color bar
        if self.mode == CONTOURPLOT and hasattr(self, 'cb'):
            try:
                self.cb.update_bruteforce(self.im) #works in test script but not in daq--why??
            except:
                print "Unexpected error:", sys.exc_info()[0]
        self.canvas.draw_idle()
        self.canvas.show()
        self.show()

    def draw_colorbar(self):
        self.cb=self.figure.colorbar(self.im)


    def clear(self):
        self.reset_axes()
        # delete colorbar or it won't redraw
        if hasattr(self, 'cb'):
            del self.cb
        self.new_data()
        self.repaint()

    def set_mode(self, newmode):
        self.mode = newmode
        self.reset_axes()
        self.new_data()  #Sam added this
        self.repaint()

    def set_plotmethod(self, newmethod):
        self.plotmethod = newmethod

    def set_x(self, xmin, xmax, xstep):
        self.xmin = xmin
        self.xmax = xmax
        self.xstep = xstep
        self.xgrid = numpy.arange(xmin, xmax+xstep, xstep)

    def set_y(self, ymin, ymax, ystep):
        self.ymin = ymin
        self.ymax = ymax
        self.ystep = ystep
        self.ygrid = numpy.arange(ymin, ymax+ystep, ystep)

    def save(self, save_path):
        self.figure.savefig(save_path)
