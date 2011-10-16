#!/usr/bin/env python

import gtk,gobject,cairo

import math
from colorsys import rgb_to_hsv, hsv_to_rgb
import StringIO,base64

#data:image/png;base64,
pickerIcon = "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\n"

def get_pixbuf_from_base64(b64_string,mime="image/png"):
    """Encoded string to Pixbuf"""
    pixbuf_loader = gtk.gdk.pixbuf_loader_new_with_mime_type(mime)
    pixbuf_loader.write(base64.b64decode(b64_string))
    pixbuf_loader.close()
    return pixbuf_loader.get_pixbuf()

def get_base64_from_pixbuf(pixbuf,mime="image/png"):
    """Pixbuf to encoded string"""
    io = StringIO.StringIO()
    pixbuf.save_to_callback(io.write, mime.split('/')[1])
    return base64.b64encode(io.getvalue())


class PaletteWidget(gtk.DrawingArea):
    default_cell_width = 10
    default_cell_height = 10

    # Draw in response to an expose-event
    __gsignals__ = {
        "expose-event": "override",
        'color-picked' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
        'mouse-over' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT)),
    }
    
    def __init__(self,colors,num_cols=None,reorder=True):
        super(self.__class__,self).__init__()
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.POINTER_MOTION_MASK|gtk.gdk.LEAVE_NOTIFY_MASK)
        
        colors = list(colors)
        num_colors = len(colors)
        self.cols = num_cols if num_cols!=None else int(num_colors/2)
        
        self.rows = int(math.ceil(num_colors/float(self.cols)))
        self.colors = colors
        self.orig_order = {}
        self.ord_colors = self._get_ordered_colors(colors,reorder)
        
        self.set_color_mask()
        self._last_color = None
        
        self.set_cells_size(self.default_cell_width,self.default_cell_height)
        
        self.connect("button_press_event", self.on_button_press)
        self.connect("motion_notify_event", self.on_motion_notify)
        self.connect("leave_notify_event", self.on_leave_notify)
    
    def set_cells_size(self,width,height):
        self.cell_width = width
        self.cell_height = height
        self.set_size_request(self.cols*self.cell_width,self.rows*self.cell_height)
    
    def _get_color_at_coords(self,x,y):
        visibleIndex = int(math.floor(x/self.cell_width)+math.floor(y/self.cell_height)*self.cols)
        
        try:
            realIndex = self.orig_order[visibleIndex]
            rgb = self.colors[realIndex]
        except (KeyError,IndexError,TypeError) as e:
            realIndex = None
            rgb = (255,255,255)
        
        return (rgb,realIndex)
    
    def on_button_press(self,widget,ev):
        rgb,realIndex = self._get_color_at_coords(ev.x,ev.y)
        self.emit('color-picked',ev,rgb,realIndex)
    
    def on_motion_notify(self,widget,ev):
        rgb,realIndex = self._get_color_at_coords(ev.x,ev.y)
        if self._last_color==None or self._last_color!=realIndex:
            self._last_color = realIndex
            self.emit('mouse-over',ev,rgb,realIndex)
    
    def on_leave_notify(self,widget,ev):
        self._last_color = None
    
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
            by_h = [ [((0,0,1),None) for i in range(self.rows)] for x in range(self.cols)]
            
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
            
            # fill empty squares
            for k in range(self.cols*self.rows-len(colors)):
                by_h[-1].append(((0,0,1),None))
            
        
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
        self.emit('clicked',ev,self.rgb,self.data)
    
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


class ColorPicker(gtk.Fixed):

    def __init__(self,colors,grayscale=None,options=None):
        super(ColorPicker,self).__init__()
        
        _options = {
          'num_columns':16,
          'cells_width': PaletteWidget.default_cell_width,
          'cells_height': PaletteWidget.default_cell_height,
          'previewer_width': ColorWidget.default_width,
          'previewer_height': ColorWidget.default_height,
          'reorder' : True
        }
        _options.update(options or {})
        
        vbox = gtk.VBox()
        
        self._window = None
        
        self.palette = PaletteWidget(colors,_options['num_columns'],_options['reorder'])
        self.palette.set_cells_size(_options['cells_width'],_options['cells_height'])
        self.palette.show()
        
        vbox.pack_start(self.palette)
        
        self.grayscalePalette = None
        if grayscale:
            grayscale = list(grayscale)
            self.grayscalePalette = grayscalePalette = PaletteWidget(grayscale,len(grayscale))
            grayscalePalette.set_cells_size(_options['cells_width'],_options['cells_height'])
            grayscalePalette.show()
            vbox.pack_start(grayscalePalette)
        
        hbox = gtk.HBox()
        
        self.fgColor = ColorWidget(None,_options['previewer_width'],_options['previewer_height'])
        self.bgColor = ColorWidget(None,_options['previewer_width'],_options['previewer_height'])
        
        self._previewersSignals = {
            self.fgColor : {
                'clicked_id' : self.fgColor.connect('clicked',self.on_previewer_clicked)
            },
            self.bgColor : {
                'clicked_id' : self.bgColor.connect('clicked',self.on_previewer_clicked)
            }
        }
        
        hbox.pack_start(self.fgColor)
        hbox.pack_start(self.bgColor)
        hbox.show_all()
        
        halign = gtk.Alignment(1, 0, 0, 0)
        halign.show()
        halign.add(hbox)
        
        vbox.pack_start(halign,False,False,0)
        
        vbox.show()
        self.add(vbox)
        
        self.show()
    
    def on_previewer_clicked(self,colorWidget,ev,rgb,data):
        orig_ev = ev.copy()
        gtkWindow = self._getWindow()
        
        self._prevColor = (colorWidget.rgb,colorWidget.data)
        
        def on_click_anywhere(w_ev,data=None):
            if w_ev.type != gtk.gdk.BUTTON_PRESS:
                gtk.main_do_event(w_ev)
                return
            
            if hash(w_ev)==hash(ev) and w_ev.x==orig_ev.x and w_ev.y==orig_ev.y:
                # this check exists because the function would be triggered by
                # the click on the previewer color. Because hash is not enough,
                # we must check if we moved too (the event was copied because it
                # will be modified internally)
                return
            
            if w_ev.window != self.palette.window and w_ev.window != (self.grayscalePalette and self.grayscalePalette.window):
                # clicked outside of the palette, restore original color
                colorWidget.set_color(*self._prevColor)
            
            self.palette.disconnect(self._mouseOverPalette_id)
            self.palette.disconnect(self.palette_leave_id)
            
            if self.grayscalePalette:
                self.grayscalePalette.disconnect(self._mouseOverGrayscale_id)
                self.grayscalePalette.disconnect(self.grayscalePalette_leave_id)
            
            self.toggle_picker_icon(False)
            gtk.gdk.event_handler_set(gtk.main_do_event)
            
            for widget in self._previewersSignals:
                # reconnect all the previewers 'onclick' signals
                self._previewersSignals[widget]['clicked_id'] = widget.connect('clicked',self.on_previewer_clicked)
            
            gtk.main_do_event(w_ev)
        
        for widget in self._previewersSignals:
            # disconnect all the previewers 'onclick' signals until the mouse is pressed on something
            widget.disconnect(self._previewersSignals[widget]['clicked_id'])
        
        self._mouseOverPalette_id = self.palette.connect('mouse-over',self.on_mouseOver_palette,colorWidget)
        if self.grayscalePalette:
            self._mouseOverGrayscale_id = self.grayscalePalette.connect('mouse-over',self.on_mouseOver_palette,colorWidget)
        
        self.palette_leave_id = self.palette.connect('leave_notify_event',lambda *x: colorWidget.set_color(*self._prevColor))
        if self.grayscalePalette:
                self.grayscalePalette_leave_id = self.grayscalePalette.connect('leave_notify_event',lambda *x: colorWidget.set_color(*self._prevColor))
        
        
        gtkWindow.window.set_events(gtkWindow.window.get_events()|gtk.gdk.BUTTON_PRESS_MASK)
        gtk.gdk.event_handler_set(on_click_anywhere)
        #self._window_clicked_id = gtkWindow.connect("button-press-event", on_click_anywhere)
        self.toggle_picker_icon(True)
    
    def on_mouseOver_palette(self,palette,ev,rgb,paletteIndex,colorWidget):
        colorWidget.set_color(rgb,paletteIndex)
    
    def _getWindow(self):
        if not self._window:
            for w in gtk.window_list_toplevels():
                if not w.is_active(): continue
                self._window = w
                break
        
        return self._window
    
    def toggle_picker_icon(self,toggle):
        if toggle:
            cursor = gtk.gdk.Cursor(gtk.gdk.display_get_default(),get_pixbuf_from_base64(pickerIcon),0,0)
        else:
            cursor = gtk.gdk.Cursor(gtk.gdk.ARROW)
        
        gtkWindow = self._getWindow()
        gtkWindow.window.set_cursor(cursor)
    
    def set_foreground(self,rgb,data):
        self.fgColor.set_color(rgb,data)
    
    def set_background(self,rgb,data):
        self.bgColor.set_color(rgb,data)
    
    def get_foreground(self):
        return {"rgb":self.fgColor.rgb,"data":self.fgColor.data}
    
    def get_background(self):
        return {"rgb":self.bgColor.rgb,"data":self.bgColor.data}
    
    def _reset_color(self,widget,button,rgb,data):
        widget.set_color(None)
    

if __name__ == "__main__":
    import term_colors
    
    COLORS = term_colors.ANSI_COLORS
    COLORS = term_colors.TERM_COLORS
    
    if COLORS == term_colors.TERM_COLORS:
        colors = ((x.rgb[0],x.rgb[1],x.rgb[2]) for x in term_colors.TERM_COLORS[:232])
        num_columns = 26
        grayscaleColors = ((x.rgb[0],x.rgb[1],x.rgb[2]) for x in term_colors.GRAYSCALE)
        reorder = True
    else:
        colors = ((x.rgb[0],x.rgb[1],x.rgb[2]) for x in term_colors.ANSI_COLORS)
        num_columns = 8
        grayscaleColors = None
        reorder = False
    
    picker = ColorPicker(colors,grayscaleColors,{
        'num_columns':num_columns,
        'reorder':reorder,
        'cells_width':20,
        'cells_height':20
    })
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
