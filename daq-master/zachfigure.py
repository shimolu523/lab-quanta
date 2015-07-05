import pyextfigure
import numpy
import gtk
import threading
from matplotlib.figure import Figure as MPLFigure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

TWODPLOT = pyextfigure.TWODPLOT
DUALTWODPLOT = pyextfigure.DUALTWODPLOT
THREEDPLOT = pyextfigure.THREEDPLOT

class ZachFigureCanvas (gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        self.figure = MPLFigure()
        self.canvas = FigureCanvas(self.figure)
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
    
    def show(self):
        try:
            if not self.packed:
                #print 'packing'
                self.pack_start(self.canvas, expand=True)
                toolbar = NavigationToolbar(self.canvas, self.get_parent_window())
                self.pack_start(toolbar, expand=False)
                self.packed = True
            #print 'packed'
            super(ZachFigureCanvas, self).show()
        except Exception, e:
            print 'Exception: ', e
            raise
    
    def add_point(self, xnew, y1new, y2new = None):
        self.x.append(xnew)
        self.y1.append(y1new)
        self.y2.append(y2new)
        
        if self.mode == TWODPLOT:
            self.ax.plot([xnew], [y1new], 'b.')
            if len(self.x) >= 2:
                self.ax.plot(self.x[-2:], self.y1[-2:], 'b-')
                self.x = self.x[-2:]
                self.y1 = self.y1[-2:]
        elif self.mode == DUALTWODPLOT:
            self.ax.plot([xnew], [y1new], 'b.')
            self.ax2.plot([xnew], [y2new], 'g.')
            if len(self.x) >= 2:
                self.ax.plot(self.x[-2:], self.y1[-2:], 'b-')
                self.ax2.plot(self.x[-2:], self.y2[-2:], 'g-')
                self.x = self.x[-2:]
                self.y1 = self.y1[-2:]
                self.y2 = self.y2[-2:]
        elif self.mode == THREEDPLOT:
            pass
            #ax = self.figure.add_subplot(111)
            #X, Y = numpy.meshgrid(numpy.array(self.x), numpy.array(self.y1))
            #z = numpy.array(self.y2)
    
    def set_labels(self, xlabel = None, y1label = None, y2label = None):
        if xlabel is not None:
            self.xlabel = xlabel
        if y1label is not None:
            self.y1label = y1label
        if y2label is not None:
            self.y2label = y2label
    
    def new_data(self):
        self.x = []
        self.y1 = []
        self.y2 = []
        
    def set_spot_shape(self, xsize, ysize):
        pass
        
    def reset_axes(self):
        self.figure.clf()
        # delete current axes
        for axis in self.figure.axes:
            self.figure.delaxes(axis)
        
        if self.mode == TWODPLOT:
            self.ax = self.figure.add_subplot(111)
            self.ax.hold(True)
            self.ax2 = None
        elif self.mode == DUALTWODPLOT:
            self.ax = self.figure.add_subplot(111)
            self.ax.hold(True)
            self.ax2 = self.ax.twinx()
            self.ax2.hold(True)
        
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
            
    def color_labels(self):
        for tl in self.ax.get_yticklabels(): 
            tl.set_color('b')
        if self.ax2 is not None:
            for tl in self.ax2.get_yticklabels(): 
                tl.set_color('g')
    
    def repaint(self):
        self.adjust_axis_margins()
        self.set_axis_labels()
        self.color_labels()
        self.canvas.draw_idle()
        self.canvas.show()
        self.show()
        
    def clear(self):
        self.reset_axes()
        self.new_data()
        self.repaint()
        
    def set_mode(self, newmode):
        self.mode = newmode
        self.reset_axes()
        self.repaint()
        
    def save(self, save_path):
        self.figure.savefig(save_path)

"""
    { "add_point", (PyCFunction)_wrap_ext_figure_add_point, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "new_data", (PyCFunction)_wrap_ext_figure_new_data, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "set_spot_shape", (PyCFunction)_wrap_ext_figure_set_spot_shape, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "set_labels", (PyCFunction)_wrap_ext_figure_set_labels, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "repaint", (PyCFunction)_wrap_ext_figure_repaint, METH_NOARGS,
      NULL },
    { "clear", (PyCFunction)_wrap_ext_figure_clear, METH_NOARGS,
      NULL },
    { "set_mode", (PyCFunction)_wrap_ext_figure_set_mode, METH_VARARGS|METH_KEYWORDS,
      NULL },
    { "save", (PyCFunction)_wrap_ext_figure_save, METH_VARARGS|METH_KEYWORDS,
"""
