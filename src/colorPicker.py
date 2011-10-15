#!/usr/bin/env python

import gtk,gobject,cairo

import math
from colorsys import rgb_to_hsv, hsv_to_rgb


class PaletteWidget(gtk.DrawingArea):
    default_cell_width = 10
    default_cell_height = 10

    # Draw in response to an expose-event
    __gsignals__ = {
        "expose-event": "override",
        'color-picked' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
    }
    
    def __init__(self,colors,num_cols=None,reorder=True):
        super(self.__class__,self).__init__()
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        
        colors = list(colors)
        num_colors = len(colors)
        self.cols = num_cols if num_cols!=None else int(num_colors/2)
        
        self.rows = int(math.ceil(num_colors/float(self.cols)))
        self.colors = colors
        self.orig_order = {}
        self.ord_colors = self._get_ordered_colors(colors,reorder)
        
        self.set_color_mask()
        
        self.set_cells_size(self.default_cell_width,self.default_cell_height)
        
        self.connect("button_press_event", self.on_button_press)
    
    def set_cells_size(self,width,height):
        self.cell_width = width
        self.cell_height = height
        self.set_size_request(self.cols*self.cell_width,self.rows*self.cell_height)
    
    def on_button_press(self,widget,ev):
        visibleIndex = int(math.floor(ev.x/self.cell_width)+math.floor(ev.y/self.cell_height)*self.cols)
        
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
        
    def set_color_mask(self,func=None):
        self.color_mask = func or (lambda rgb,i: rgb)
        self.queue_draw()

    def draw(self, cr, width, height):
        
        for column in range(len(self.ord_colors)):
            
            elems = self.ord_colors[column]
            
            for row in range(len(elems)):
                (h,s,v),idx = elems[row]
                
                r,g,b = self.color_mask(hsv_to_rgb(h,s,v),self.orig_order[row*self.cols+column])
                
                cr.set_source_rgb(r, g, b)
                cr.rectangle(column*self.cell_width, row*self.cell_height, self.cell_width, self.cell_height)
                cr.fill()
    
    def _get_ordered_colors(self,colors,reorder):
        
        hsv_colors = (rgb_to_hsv(r/255.,g/255.,b/255.) for r,g,b in colors)
        
        by_h = []
        
        # order colors in columns by hue, keeping the original index
        
        if not reorder:
            # create a matrix
            by_h = [ [((255,255,255),None) for i in range(self.rows)] for x in range(self.cols)]
            
            # insert colors in rows, from left to right, one row at a time
            for origIdx,(h,s,v) in enumerate(hsv_colors):
                by_h[origIdx-((origIdx/self.cols)*self.cols)][origIdx/self.cols] = ((h,s,v),origIdx)
            
        else:
            # order by hue first
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
    UNKNOWN = -1
    default_width = 20
    default_height = 20

    # Draw in response to an expose-event
    __gsignals__ = {
        "expose-event": "override",
        'clicked' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                      (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)
                    ),
        'color-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
    }
    
    def __init__(self,rgb,data=None,width=None,height=None):
        super(self.__class__,self).__init__()
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        
        self.set_size_request(width or self.default_width,height or self.default_height)
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
        elif self.rgb != self.UNKNOWN:
            # Fill the background with the saved color
            r,g,b = self.rgb
            cr.set_source_rgb(r/255.,g/255.,b/255.)
            cr.rectangle(0, 0, width, height)
            cr.fill()
        else:
            # Color unknown, print '?' on white background
            cr.set_source_rgb(1, 1, 1)
            cr.rectangle(0, 0, width, height)
            cr.fill()
            cr.move_to(width/2,height)
            cr.set_font_size(height)
            cr.select_font_face('Arial', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_source_rgb(0,0,0)
            cr.show_text('?')
    
    def set_color(self,rgb,data=None):
        self.rgb = rgb
        self.data = data
        
        self.emit('color-changed',rgb,self.data)
        self.queue_draw()


class ColorPicker(gtk.VBox):

    def __init__(self,colors,grayscale=None,options=None):
        super(ColorPicker,self).__init__()
        
        _options = {
          'num_columns':16,
          'cells_width': PaletteWidget.default_cell_width,
          'cells_height': PaletteWidget.default_cell_height,
          'selected_width': ColorWidget.default_width,
          'selected_height': ColorWidget.default_height,
          'reorder' : True
        }
        _options.update(options or {})
        
        vbox = self
        
        self.palette = PaletteWidget(colors,_options['num_columns'],_options['reorder'])
        self.palette.set_cells_size(_options['cells_width'],_options['cells_height'])
        self.palette.connect('color-picked',self.on_colorPalette_clicked)
        self.palette.show()
        
        vbox.pack_start(self.palette)
        
        self.grayscalePalette = None
        if grayscale:
            grayscale = list(grayscale)
            self.grayscalePalette = grayscalePalette = PaletteWidget(grayscale,len(grayscale))
            grayscalePalette.set_cells_size(_options['cells_width'],_options['cells_height'])
            grayscalePalette.show()
            grayscalePalette.connect('color-picked',self.on_grayscalePalette_clicked)
            vbox.pack_start(grayscalePalette)
        
        hbox = gtk.HBox()
        
        self.fgColor = ColorWidget(None,_options['selected_width'],_options['selected_height'])
        self.bgColor = ColorWidget(None,_options['selected_width'],_options['selected_height'])
        
        self.fgColor.connect('clicked',self._reset_color)
        self.bgColor.connect('clicked',self._reset_color)
        
        hbox.pack_start(self.fgColor)
        hbox.pack_start(self.bgColor)
        
        hbox.show_all()
        vbox.pack_start(hbox)
        
        vbox.show()
        
        self.show()
    
    def set_foreground(self,rgb,data):
        self.fgColor.set_color(rgb,data)
    
    def set_background(self,rgb,data):
        self.bgColor.set_color(rgb,data)
    
    def get_foreground(self):
        return {"rgb":self.fgColor.rgb,"data":self.fgColor.data}
    
    def get_background(self):
        return {"rgb":self.bgColor.rgb,"data":self.bgColor.data}
    
    def on_colorPalette_clicked(self,palette,button,rgb,paletteIndex):
        if button == 1:
            self.set_foreground(rgb,paletteIndex)
        elif button == 3:
            self.set_background(rgb,paletteIndex)
    
    def on_grayscalePalette_clicked(self,palette,button,rgb,paletteIndex):
        if button == 1:
            self.set_foreground(rgb,paletteIndex)
        elif button == 3:
            self.set_background(rgb,paletteIndex)
    
    def _reset_color(self,widget,button,rgb,data):
        widget.set_color(None)
    

if __name__ == "__main__":
    import term_colors
    
    colors = ((x.rgb[0],x.rgb[1],x.rgb[2]) for x in term_colors.TERM_COLORS[:232])
    num_columns = 26
    grayscaleColors = ((x.rgb[0],x.rgb[1],x.rgb[2]) for x in term_colors.GRAYSCALE)
    
    picker = ColorPicker(colors,grayscaleColors,{'num_columns':num_columns,'reorder':True})
    picker.show()
    
    dialog = gtk.Dialog()
    dialog.vbox.pack_start(picker)
    
    def on_fgColor_changed(widget,color,data):
        print color,data
    
    def on_bgColor_changed(widget,color,data):
        print color,data
    
    picker.fgColor.connect('color-changed',on_fgColor_changed)
    picker.bgColor.connect('color-changed',on_bgColor_changed)
    
    dialog.show()
    dialog.run()
