#!/usr/bin/env python

import gtk,gobject

import math
from colorsys import rgb_to_hsv, hsv_to_rgb


class ColorPicker(gtk.DrawingArea):
    sqsize = 10

    # Draw in response to an expose-event
    __gsignals__ = {
        "expose-event": "override",
        'color-selected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT,)),
    }
    
    def __init__(self,colors,num_cols=None):
        super(self.__class__,self).__init__()
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        
        colors = list(colors)
        num_colors = len(colors)
        self.cols = num_cols if num_cols!=None else int(num_colors/2)
        
        self.rows = int(math.ceil(num_colors/float(self.cols)))
        self.colors = colors
        self.ord_colors = self._get_ordered_colors(colors)
        
        self.set_size_request(self.cols*self.sqsize,self.rows*self.sqsize)
        
        self.connect("button_press_event", self.on_button_press)
    
    def on_button_press(self,widget,ev):
        colorIndex = int(math.floor(ev.x/self.sqsize)+math.floor(ev.y/self.sqsize)*self.cols)
        
        try:
            color = self.colors[colorIndex]
        except IndexError:
            color = (255,255,255)
        
        self.emit('color-selected',{'button':ev.button,'color': color,'index':colorIndex})
    
    # Handle the expose-event by drawing
    def do_expose_event(self, event):
        # Create the cairo context
        cr = self.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()

        self.draw(cr, *self.window.get_size())

    def draw(self, cr, width, height):
        
        for column in range(len(self.ord_colors)):
            
            elems = self.ord_colors[column]
            
            for row in range(len(elems)):
                h,s,v = elems[row]
                
                r,g,b = hsv_to_rgb(h,s,v)
                
                cr.set_source_rgb(r, g, b)
                cr.rectangle(column*self.sqsize, row*self.sqsize, self.sqsize, self.sqsize)
                cr.fill()
    
    def _get_ordered_colors(self,colors):
        
        hsv_colors = (rgb_to_hsv(r/255.,g/255.,b/255.) for r,g,b in colors)
        
        by_h = []
        
        for i,(h,s,v) in enumerate(sorted(hsv_colors,key=lambda x:x[0])):
            if i % self.rows == 0:
                by_h.append([])
            
            by_h[-1].append((h,s,v))
        
        for elem in by_h:
            elem.sort(key=lambda x:x[1])
        
        return by_h

class ColorPickerExample(gtk.Window):

    def __init__(self,colors,num_columns):
        super(self.__class__,self).__init__(gtk.WINDOW_TOPLEVEL)
        
        self.set_title("Color selection test")
        self.set_resizable(True)

        # Attach to the "delete" and "destroy" events so we can exit
        self.connect("delete_event", gtk.main_quit)
        
        self.picker = ColorPicker(colors,num_columns)
        self.picker.show()
        self.add(self.picker)
        
        self.show()
  
    def run(self):
        gtk.main()

if __name__ == "__main__":
    import term_colors
    
    colors = ((x.rgb[0],x.rgb[1],x.rgb[2]) for x in term_colors.TERM_COLORS[:232])
    num_columns = 26
    win = ColorPickerExample(colors,num_columns)
    
    def on_color_selected(widget,info):
        print info
    
    win.picker.connect('color-selected',on_color_selected)
    
    win.run()
