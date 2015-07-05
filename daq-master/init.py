# init.py
#
# Init script, called by main thread of daq. Reads in all the io modules,
# sets up some paths. It is read as a simple file, not a module (this
# affects the scope of variables defined/changed)
#
import sys, os, traceback, __main__, scipy, scipy.optimize, math, cmath, numpy

STOP_FLAG = False
ABORT_FLAG = False
PAUSE_FLAG = False

sys.argv = ['']

if ("DAQ_HOME" in os.environ.keys()):
    DAQ_HOME = os.environ['DAQ_HOME']
else:
    DAQ_HOME = "."

# Defines where I expect to see io and logic modules
LOGIC_MOD_DIR = os.path.join(__main__.DAQ_HOME, "logics")
IO_MOD_DIR = os.path.join(__main__.DAQ_HOME, "ios")
if not os.path.exists(IO_MOD_DIR):
	IO_MOD_DIR = "/usr/local/data_acq/ios" # Retained for backwards compatibility

sys.path = [DAQ_HOME, LOGIC_MOD_DIR, DAQ_HOME + '/scripts', IO_MOD_DIR] + sys.path
execfile(DAQ_HOME + "/kernels.py")

# Import all the io modules
io_modules = os.listdir(IO_MOD_DIR)
for name in io_modules:
    if name.endswith('.py'):
        try:
	    globals()[name[:-3]] =__import__(name[:-3], globals(), locals(), [''])
	except Exception, e:
	    print "Failed to interpret %s"%(name)
	    print e
	    traceback.print_exc()

# remove unnecessary variables
globals().pop('io_modules')
globals().pop('name')

print "Embedded Python interpreter"
