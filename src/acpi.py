#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

__author__ 	= 'Federico Galli <fede@sideralis.net>'
__version__ = '0.1'
__date__    = '13-07-04'

import os

acpibattery_path='/proc/acpi/battery'

try:
    batDir=os.listdir(acpibattery_path)
    batDir.sort()
except OSError:
    import sys
    print >> sys.stderr, 'Could not find acpi battery directory'
    sys.exit(1)

def getValues(path,findMe):
    fp=file(path)
    text=fp.readlines()
    for line in text:
        if line.startswith(findMe):
            value=line.split()
            break
    fp.close()
    return value

bat_percent=[]

for batNum in batDir:
    startPath= acpibattery_path +'/'+ batNum
    isPresent=getValues(startPath+'/info','present:')[-1]
    if isPresent.lower()=='yes':
        totCapacity=getValues(startPath+'/info','design capacity:')[-2]
        remCapacity=getValues(startPath+'/state','remaining capacity:')[-2]
        bat_percent.append(int(remCapacity)*100/int(totCapacity))
    else:
        #print "Empty Slot Found"
        pass

from output import *
for i in bat_percent:
    if i>=70 :
        print green('%d%%' % i),
    elif i<=30 :
        print red('%d%%' % i),
    else :
        print yellow('%d%%' % i),
