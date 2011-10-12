#!/usr/bin/env python

import gtk,gobject

import math
from colorsys import rgb_to_hsv, hsv_to_rgb


class PaletteWidget(gtk.DrawingArea):
    sqsize = 10

    # Draw in response to an expose-event
    __gsignals__ = {
        "expose-event": "override",
        'color-picked' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
    }
    
    def __init__(self,colors,num_cols=None):
        super(self.__class__,self).__init__()
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        
        colors = list(colors)
        num_colors = len(colors)
        self.cols = num_cols if num_cols!=None else int(num_colors/2)
        
        self.rows = int(math.ceil(num_colors/float(self.cols)))
        self.colors = colors
        self.orig_order = {}
        self.ord_colors = self._get_ordered_colors(colors)
        
        self.set_size_request(self.cols*self.sqsize,self.rows*self.sqsize)
        
        self.connect("button_press_event", self.on_button_press)
    
    def on_button_press(self,widget,ev):
        visibleIndex = int(math.floor(ev.x/self.sqsize)+math.floor(ev.y/self.sqsize)*self.cols)
        
        try:
            realIndex = self.orig_order[visibleIndex]
            rgb = self.colors[realIndex]
        except (KeyError,IndexError) as e:
            realIndex = None
            rgb = (255,255,255)
        
        self.emit('color-picked',ev.button,rgb,realIndex)
    
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
                (h,s,v),idx = elems[row]
                
                r,g,b = hsv_to_rgb(h,s,v)
                
                cr.set_source_rgb(r, g, b)
                cr.rectangle(column*self.sqsize, row*self.sqsize, self.sqsize, self.sqsize)
                cr.fill()
    
    def _get_ordered_colors(self,colors):
        
        hsv_colors = (rgb_to_hsv(r/255.,g/255.,b/255.) for r,g,b in colors)
        
        by_h = []
        
        # order colors in columns by hue, keeping the original index
        for i,(origIdx,(h,s,v)) in enumerate(sorted(enumerate(hsv_colors),key=lambda x:x[1][0])):
            if i % self.rows == 0:
                by_h.append([])
            
            by_h[-1].append(((h,s,v),origIdx))
        
        # sort each column by saturation
        for elems in by_h:
            elems.sort(key=lambda x:x[0][1])
        
        # build a map from the palette index to the orginal colors index
        for column in range(len(by_h)):
            
            elems = by_h[column]
            
            for row in range(len(elems)):
                (h,s,v),idx = elems[row]
                
                self.orig_order[len(by_h)*row+column] = idx
        
        return by_h

class ColorWidget(gtk.DrawingArea):

    # Draw in response to an expose-event
    __gsignals__ = {
        "expose-event": "override",
        'clicked' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                      (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)
                    ),
        'color-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
    }
    
    def __init__(self,rgb,data=None):
        super(self.__class__,self).__init__()
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.set_size_request(20,20)
        
        self.set_color(rgb,data)
        
        self.connect("button_press_event", self.on_button_press)
    
    def on_button_press(self,widget,ev):
        self.emit('clicked',ev.button,self.rgb,self.data)
    
    # Handle the expose-event by drawing
    def do_expose_event(self,event):
        # Create the cairo context
        cr = self.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()

        self.draw(cr, *self.window.get_size())
    
    # Overridable, to apply filters (e.g. darkening)
    def do_color_to_paint(self,rgb):
        return rgb
    
    def draw(self,cr,width,height):
        
        if self.rgb is None:
            # Fill the background with white
            cr.set_source_rgb(1, 1, 1)
            cr.rectangle(0, 0, width, height)
            cr.fill()
            
            # a red line bottom left => top right
            cr.set_source_rgb(1.0, 0.0, 0.0)
            cr.move_to(0, height)
            cr.line_to(width,0)
            cr.stroke()
        else:
            r,g,b = self.do_color_to_paint(self.rgb)
        
            cr.set_source_rgb(r/255.,g/255.,b/255.)
            cr.rectangle(0, 0, width, height)
            cr.fill()
    
    def set_color(self,rgb,data=None):
        self.rgb = rgb
        self.data = data
        
        self.emit('color-changed',rgb,self.data)
        self.queue_draw()


class ColorPicker(gtk.Window):

    def __init__(self,colors,num_columns,grayscale=None):
        super(self.__class__,self).__init__(gtk.WINDOW_TOPLEVEL)
        
        self.set_title("Color picker")
        self.set_resizable(True)

        # Attach to the "delete" and "destroy" events so we can exit
        self.connect("delete_event", gtk.main_quit)
        
        vbox = gtk.VBox()
        
        palette = PaletteWidget(colors,num_columns)
        palette.connect('color-picked',self.on_colorPalette_clicked)
        palette.show()
        
        vbox.pack_start(palette)
        
        if grayscale:
            grayscale = list(grayscale)
            grayscalePalette = PaletteWidget(grayscale,len(grayscale))
            grayscalePalette.show()
            grayscalePalette.connect('color-picked',self.on_grayscalePalette_clicked)
            vbox.pack_start(grayscalePalette)
        
        hbox = gtk.HBox()
        
        self.fgColor = ColorWidget(None)
        self.bgColor = ColorWidget(None)
        
        self.fgColor.connect('clicked',self.reset_color)
        self.bgColor.connect('clicked',self.reset_color)
        
        hbox.pack_start(self.fgColor)
        hbox.pack_start(self.bgColor)
        
        hbox.show_all()
        vbox.pack_start(hbox)
        
        vbox.show()
        self.add(vbox)
        
        
        self.show()
    
    def on_colorPalette_clicked(self,palette,button,rgb,paletteIndex):
        if button == 1:
            self.fgColor.set_color(rgb,paletteIndex)
        elif button ==3:
            self.bgColor.set_color(rgb,paletteIndex)
    
    def on_grayscalePalette_clicked(self,palette,button,rgb,paletteIndex):
        if button == 1:
            self.fgColor.set_color(rgb,paletteIndex)
        elif button ==3:
            self.bgColor.set_color(rgb,paletteIndex)
    
    def reset_color(self,widget,button,rgb,data):
        widget.set_color(None)
    
    def run(self):
        gtk.main()

if __name__ == "__main__":
    import term_colors
    
    colors = ((x.rgb[0],x.rgb[1],x.rgb[2]) for x in term_colors.TERM_COLORS[:232])
    num_columns = 26
    grayscaleColors = ((x.rgb[0],x.rgb[1],x.rgb[2]) for x in term_colors.GRAYSCALE)
    win = ColorPicker(colors,num_columns,grayscaleColors)
    
    def on_fgColor_changed(widget,color,data):
        print color,data
    
    def on_bgColor_changed(widget,color,data):
        print color,data
    
    win.fgColor.connect('color-changed',on_fgColor_changed)
    win.bgColor.connect('color-changed',on_bgColor_changed)
    
    win.run()
