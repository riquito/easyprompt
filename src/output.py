#!/bin/env python

#this file is an enhanced version of output file, which I found in a Gentoo distribution

#this was the notes in the original output.py file
# Copyright 1998-2003 Daniel Robbins, Gentoo Technologies, Inc.
# Distributed under the GNU Public License v2
# $Header: /home/cvsroot/gentoo-src/portage/pym/output.py,v 1.17 2003/12/08 15:11:28 nakano Exp $

__author__='Riccardo Attilio Galli <riccardo@sideralis.net>'
__organization__='Sideralis Programs' 

import os,sys

havecolor=1
dotitles=1

use4prompt=0

codes={}
codes["reset"]="\x1b[0m"
codes["bold"]="\x1b[01m"

codes["teal"]="\x1b[36;06m"
codes["turquoise"]="\x1b[36;01m"

codes["fucsia"]="\x1b[35;01m"
codes["purple"]="\x1b[35;06m"

codes["blue"]="\x1b[34;01m"
codes["darkblue"]="\x1b[34;06m"

codes["green"]="\x1b[32;01m"
codes["darkgreen"]="\x1b[32;06m"

codes["yellow"]="\x1b[33;01m"
codes["brown"]="\x1b[33;06m"

codes["red"]="\x1b[31;01m"
codes["darkred"]="\x1b[31;06m"

codes['black']='\033[30;06m'
codes['darkgray']='\033[30;01m'

codes['white']='\033[37;01m'
codes['gray']='\033[37;06m'

codes['bg_black']='\033[40;06m'
codes['bg_blue']='\033[44;06m'
codes['bg_green']='\033[42;06m'
codes['bg_teal']='\033[46;06m'
codes['bg_red']='\033[41;06m'
codes['bg_purple']='\033[45;06m'
codes['bg_brown']='\033[43;06m'
codes['bg_gray']='\033[47;06m'

def xtermTitle(mystr):
	if havecolor and dotitles and os.environ.has_key("TERM"):
		myt=os.environ["TERM"]
		if myt in ["xterm","Eterm","aterm","rxvt","screen"]:
			sys.stderr.write("\x1b]1;\x07\x1b]2;"+str(mystr)+"\x07")
			sys.stderr.flush()

def xtermTitleReset():
	if havecolor and dotitles and os.environ.has_key("TERM"):
		myt=os.environ["TERM"]
		xtermTitle(os.environ["TERM"])


def notitles():
	"turn off title setting"
	dotitles=0

def nocolor():
	"turn off colorization"
	havecolor=0
	for x in codes.keys():
		codes[x]=""

def resetColor():
	return codes["reset"]

def ctext(color,text):
	return codes[ctext]+text+codes["reset"]

glob=globals()
for codeName in codes:
    glob[codeName]=lambda text,codeName=codeName: \
        (use4prompt and '\[%s\]%s\[%s\]' or '%s%s%s') % (codes[codeName],text,codes['reset'])


def date(pattern=None):
    if pattern:
        return '\D{%s}' % pattern
    else: return '\d'

def show_colors():
    width=16
    for key in codes:
        if key.startswith('bg_') or key in ('reset','bold'): continue
        
        text='color '+key
        length=len(text)
        text+=' '*(width-len(text))
        print 'CODE',repr(codes[key])[1:-1],'  ',
        print codes[key]+text+codes['reset'],
        print '\033[47m'+codes[key]+text+codes['reset'],
        print '\033[40m'+codes[key]+text+codes['reset']


if __name__=='__main__':
    show_colors()
    print
    print "print green('example'),'of',red('usage')" 
    print ' -> ',green('example'),'of',red('usage')

