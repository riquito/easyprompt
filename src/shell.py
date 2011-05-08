#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

try:
  import sys
  import gtk, pango
except:
  print("You need to install the python gtk and pango bindings",file=sys.stderr)
  sys.exit(1)

try:
  import vte
except:
  error = gtk.MessageDialog (None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
    'You need to install python bindings for libvte')
  error.run()
  sys.exit (1)

def getGnomeTerminalColors(profile="Default"):
    import gconf
    
    x=gconf.client_get_default()
    GCONF_PROFILE_DIR = "/apps/gnome-terminal/profiles/"+profile
    palette = x.get_string(GCONF_PROFILE_DIR + "/palette")
    gdk_palette = [] 
    for col in palette.split(':'):
        newcol = gtk.gdk.color_parse(col)
        gdk_palette.append(newcol)
        
    fg_color = x.get_string(GCONF_PROFILE_DIR + "/foreground_color")
    bg_color = x.get_string(GCONF_PROFILE_DIR + "/background_color")
    
    return {
        "palette": gdk_palette,
        "background":gtk.gdk.color_parse (bg_color),
        "foreground":gtk.gdk.color_parse (fg_color)
    }

class ShellWidget(vte.Terminal):
    def __init__(self,*args):
        super(ShellWidget,self).__init__(*args)
        
        self.set_font(pango.FontDescription())
        self.connect('child-exited', lambda term: gtk.main_quit())
        self.fork_command()
    
    def loadColors(self,colors):
        self.set_colors(colors["foreground"],colors["background"],colors["palette"])
    
    def set_prompt(self,prompt_format):
        self.feed_child('''export PS1='%s' \n ''' % prompt_format)
    
    def clear(self):
        self.feed_child("clear\n")

if __name__ == '__main__':
  
  window = gtk.Window()
  
  shell=ShellWidget()
  shell.loadColors(getGnomeTerminalColors())
  window.add(shell)
  window.connect('delete-event', lambda window, event: gtk.main_quit())
  window.show_all()
  gtk.main()