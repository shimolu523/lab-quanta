#!/bin/csh
#
# File:   daq_blogger.sh
# Date:   28-Mar-05
# Author: I. Chuang <ichuang@mit.edu>
#
# Shell script to add a data file from Jarek's DAQ to the data blog
#
# Usage:   daq_blogger.sh filename
#
# Creates a new entry in the ionsearch MT-exptdata blog
# 29-Mar-05 ILC: also blogs the latest experiment status report

set filename = $1
set fnpng = `echo $filename | sed -e s:/:_:`
set fndata = `echo $filename | sed -e s:\.png::`
set fndata = "${fndata}*"

set fnxwd = "daq-windowdump.xwd"
set fnwin = "daq-windowdump.gif"

# Let's dump Jarek's daq program window and blog that also
xwd -name "DATA ACQ" >! $fnxwd
rm -rf $fnwin		# remove old window dump if it exists
convert $fnxwd $fnwin
rm $fnxwd
mv \#screenimage\# daq-output.png

/home/blog/bin/blogit -blogid 6 -title "[DAQ] $filename" daq-output.png $fnwin $fndata
rm daq-output.png

# blog experiment status devices
# set stat = `echo '' | nc -w 1 bloch 18101 | sed -e 's|$|</td></tr>|;s|:|</td><td>|;s|^|<tr><td>|'`
# set stat = "<table border=1>$stat</table>"
# /home/blog/bin/blogit -append -blogid 6 -entryid -1 -text "$stat"

touch LOG
echo "-----" >> LOG
echo "args = $*" >> LOG
echo "fn = $filename" >> LOG
echo "fnpng = $fnpng" >> LOG
echo "fndata = $fndata" >> LOG

#rm \#screenimage\#
rm $fnwin
