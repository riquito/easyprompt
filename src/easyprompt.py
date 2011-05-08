#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__='Riccardo Attilio Galli <riccardo@sideralis.org>'
__organization__='Sideralis'
__version__='1.1.0'

import gtk,pango,gobject
import shell
import output, re
from math import floor,ceil
from output import codes

output.use4prompt=1

import os,sys
CONFIG_PATH  = os.path.join(os.getenv('HOME'),'.easyprompt')
PLUGINS_PATH = os.path.join(CONFIG_PATH,'plugins')

if not os.path.exists(PLUGINS_PATH):
    os.makedirs(PLUGINS_PATH)

#base[NORMAL] = "#000000"\
#text[NORMAL] = "#CCCCCC"\ 

gtk.rc_parse_string(\
 'style "default" { \
    GtkTextView::cursor_color    = "#cc0000" \
 } \
 class "GtkTextView" style "default"'
)


colors={}

colors['black']=(0,0,0)
colors['blue']=(0,0,204)
colors['green']=(0,204,0)
colors['cyan']=(0,204,204)
colors['red']=(204,0,0)
colors['purple']=(204,0,204)
colors['brown']=(204,204,0)
colors['gray']=(170,170,170)

COLORNAME_TO_RGB = colors
RGB_TO_COLORNAME = dict((a,b) for b,a in COLORNAME_TO_RGB.iteritems())


COLORS_8_FOREGROUND_FROM_NAME_TO_INT = {
    'black'  : 30,
    'red'    : 31,
    'green'  : 32,
    'brown'  : 33,
    'blue'   : 34,
    'purple' : 35,
    'cyan'   : 36,
    'gray'   : 37
}

COLORS_8_BACKGROUND_FROM_NAME_TO_INT = {
    'black'  : 40,
    'red'    : 41,
    'green'  : 42,
    'brown'  : 43,
    'blue'   : 44,
    'purple' : 45,
    'cyan'   : 46,
    'gray'   : 47
}

COLORS_8_FROM_INT_TO_NAME = {}
for name,val in COLORS_8_FOREGROUND_FROM_NAME_TO_INT.iteritems():
    COLORS_8_FROM_INT_TO_NAME[val]=name
for name,val in COLORS_8_BACKGROUND_FROM_NAME_TO_INT.iteritems():
    COLORS_8_FROM_INT_TO_NAME[val]=name

KEYWORDS={
    'dateLong': {
        'command':'$(date +"%d %b %Y")',
        'help':'data nel formato %d/%b/%Y',
        'example':'<span underline="double" color="red">28 Feb 2004</span> foo@mypc /var/log'
    },
    'dateShort': {
        'command':'$(date +"%d/%m/%y")',
        'help':'data nel formato %d/%m/%y',
        'example':'<span underline="double" color="red">28/02/04</span> foo@mypc /var/log'
    },
    'hourLong': {
        'command':'$(date +"%H:%M:%S")',
        'help':'ora nel formato %H:%M:%S',
        'example':'<span underline="double" color="red">15:23:59</span> foo@mypc /var/log'
    },
    'hourShort': {
        'command':'$(date +"%H:%M")',
        'help':'ora nel formato %H:%M',
        'example':'<span underline="double" color="red">15:23</span> foo@mypc /var/log'
    },
    'host': {
        'command':r'\h',
        'help':'hostname fino al primo punto',
        'example':'foo@<span underline="double" color="red">mypc</span> /var/log'
    },
    'user': {
        'command':r'\u',
        'help':'utente corrente',
        'example':'<span underline="double" color="red">foo</span>@mypc /var/log'
    },
    'newline': {
        'command':r'\n',
        'help':'a capo',
        'example':'foo@mypc /var/log <span underline="double" color="red">↵</span> $'
    },
    'shell': {
        'command':r'\s',
        'help':'nome della shell',
        'example':'foo@mypc <span underline="double" color="red">bash</span> /var/log  $'
    },
    'version': {
        'command':r'\v',
        'help':'versione della shell',
        'example':'foo@mypc <span underline="double" color="red">4.2</span> /var/log  $'
    },
    'release': {
        'command':r'\V',
        'help':'release della shell (versione + numero di patch)',
        'example':'foo@mypc <span underline="double" color="red">4.2.8</span> /var/log  $'
    },
    'abs_pwd': {
        'command':r'\w',
        'help':'path completa',
        'example':'foo@mypc <span underline="double" color="red">/var/log</span> $'
    },
    'base_pwd': {
        'command':r'\W',
        'help':'directory corrente',
        'example':'foo@mypc <span underline="double" color="red">log</span> $'
    },
    'history_num': {
        'command':r'\!',
        'help':'il numero nella cronologia del comando attuale',
        'example':'<span underline="double" color="red">508</span> foo@mypc /var/log $ cd\n<span underline="double" color="red">509</span> foo@mypc ~ $'
    },
    'cmd_num': {
        'command':r'\#',
        'help':'il numero di comando del comando attuale',
        'example':'<span underline="double" color="red">3</span> foo@mypc /var/log $ echo "hello"\nhello\n<span underline="double" color="red">4</span> foo@mypc /var/log $'
    },
    'prompt': {
        'command':r'\$',
        'help':'# se root, $ altrimenti',
        'example':'foo@mypc /var/log <span underline="double" color="red">$</span> sudo su -\nroot@mypc ~ <span underline="double" color="red">#</span>'
    },
    'backslash': {
        'command':r'\\',
        'help':'un backslash \\',
        'example':'foo<span underline="double" color="red">\\</span>mypc /var/log $'
    },
}


def rgb2hex(colorTuple):
    esa=['#']
    for col in colorTuple:
        ascii=str(hex(col))
        esa.append(len(ascii)==4 and ascii[-2:] or ('0'+ascii[-1:]))
    return ''.join(esa)

def hex2rgb(hexColor):
    if hexColor[0] == '#': hexColor = hexColor[1:]
    elif hexColor[0:2].lower() == '0x': hexColor = hexColor[2:]
    
    if len(hexColor) == 3:
        hexColor = ''.join(val for val in hexColor for i in range(2))
    elif len(hexColor) == 12:
        hexColor = hexColor[0]*2+hexColor[4]*2+hexColor[8]*2
    
    return int(hexColor[0:2], 16), int(hexColor[2:4], 16), int(hexColor[4:6], 16)

def get_tag_bounds(iter,tag):
    if not iter.has_tag(tag):
        return None
    
    startIter=iter.copy()
    endIter=iter.copy()
    
    endIter.forward_to_tag_toggle(tag)
    
    if not startIter.begins_tag(tag):
        startIter.backward_to_tag_toggle(tag)
    
    return (startIter,endIter)

def has_tag_in_range(tag,startIter,endIter):
    
    startIter = startIter.copy()
    
    taggedIter = None
    
    if startIter.has_tag(tag):
        taggedIter = startIter.copy()
        #must move once to search for previous toggle (we could be yet at start)
        taggedIter.forward_char() 
        taggedIter.backward_to_tag_toggle(tag)
        return taggedIter
    
    while 1:
        if not startIter.has_tag(tag):
            was_last = not startIter.forward_char()
            if was_last or startIter.equal(endIter): break
        else:
            taggedIter=startIter.copy()
            break
    
    
    return taggedIter


class TextStyle:
    INCONSISTENT = -1
    
    WEIGHT_NORMAL = 'normal'
    WEIGHT_BOLD = 'bold'
    WEIGHT_FAINT = 'faint'
    
    def __init__(self):
        self.background = None
        self.foreground = None
        self.underline = None
        self.strikethrough = None
        self.weight = None
        self.invert = None
    
    def __str__(self):
        return self.__unicode__().encode('utf-8')
    
    def __unicode__(self):
        map = {}
        if self.background:
            if self.is_inconsistent('background'):
                map['background'] = TextStyle.INCONSISTENT
            else:
                map['background'] = RGB_TO_COLORNAME[self.background]
        
        if self.foreground:
            if self.is_inconsistent('foreground'):
                map['foreground'] = TextStyle.INCONSISTENT
            else:
                map['foreground'] = RGB_TO_COLORNAME[self.foreground]
        
        if self.underline: map['underline'] = self.underline
        if self.strikethrough: map['strikethrough'] = self.strikethrough
        if self.weight: map['weight'] = self.weight
        if self.invert: map['invert'] = self.invert
        
        return u'<TextStyle '+u' '.join(('%s="%s"' % (key,value)) for key,value in map.iteritems())+u'>'
    
    def _color_to_rgb(self,color):
        if isinstance(color,tuple): return color
        elif color.startswith('#'):
            return hex2rgb(color)
        else:
            try: return COLORNAME_TO_RGB[color]
            except Exception,e:
                raise Exception('not a color [%s]' % color)
    
    def calculate_background(self):
        return self.foreground if self.invert else self.background
    
    def calculate_foreground(self):
        return self.background if self.invert else self.foreground
        
    def set(self,attrName,value):
        if attrName == 'background' or attrName == 'foreground':
            if not (value == None or value == TextStyle.INCONSISTENT):
                value = self._color_to_rgb(value)
        
        setattr(self,attrName,value)
    
    def get(self,attrName):
        return getattr(self,attrName)
    
    def unset(self,attrName):
        setattr(self,attrName,None)
    
    def set_inconsistent(self,attrName):
        setattr(self,attrName,TextStyle.INCONSISTENT)
    
    def is_inconsistent(self,attrName):
        return getattr(self,attrName) == TextStyle.INCONSISTENT
    
    @staticmethod
    def to_gtk_tag(tstyle,tag = None):
        if not tag:
            tag = gtk.TextTag()
        
        if tstyle.invert and not tstyle.is_inconsistent('invert'):
            tag.invert = True;
        
        for attrName in ('underline','strikethrough','background','foreground'):
            
            if not tstyle.is_inconsistent(attrName):
                value = tstyle.get(attrName)
                
                if attrName == 'background' or attrName == 'foreground':
                    
                    fakeAttrName = attrName
                    
                    if attrName =='background' and tstyle.invert:
                        fakeAttrName = 'foreground'
                    elif attrName =='foreground' and tstyle.invert:
                        fakeAttrName = 'background'
                    
                    if value == None:
                        tag.set_property(fakeAttrName+'-set',False)
                    else:
                        tag.set_property(fakeAttrName,rgb2hex(value))
                        tag.set_property(fakeAttrName+'-set',True)
                    
                else:
                    if value == None: value = False
                    
                    tag.set_property(attrName,value)
                    tag.set_property(attrName+'-set',value)
        
        if not tstyle.is_inconsistent('weight'):
            value = tstyle.get('weight')
            
            if value == None:
                tag.set_property('weight',pango.WEIGHT_NORMAL)
                tag.set_property('weight-set',False)
            else:
                if value == TextStyle.WEIGHT_FAINT:
                    tag.set_property('weight',pango.WEIGHT_ULTRALIGHT)
                elif value == TextStyle.WEIGHT_BOLD:
                    tag.set_property('weight',pango.WEIGHT_BOLD)
                else:
                    tag.set_property('weight',pango.WEIGHT_NORMAL)
                
                tag.set_property('weight-set',True)
        
        return tag
    
    @staticmethod
    def to_gtk_tags(tstyle,tag_table):
        
        tags=[]
        
        for attrName in ('underline','strikethrough','background','foreground'):
            
            if not tstyle.is_inconsistent(attrName):
                value = tstyle.get(attrName)
                
                if attrName == 'background' or attrName == 'foreground':
                    
                    fakeAttrName = attrName
                    
                    if tstyle.invert and not tstyle.is_inconsistent('invert'):
                        
                        if attrName =='background':
                            fakeAttrName = 'foreground'
                        elif attrName =='foreground':
                            fakeAttrName = 'background'
                    
                    if value != None:
                        tag = tag_table.lookup({'foreground':'fg_','background':'bg_'}[attrName]+RGB_TO_COLORNAME[value])
                        tag.set_property(fakeAttrName,rgb2hex(value))
                        tags.append(tag)
                    
                elif value:
                    tag = tag_table.lookup(attrName)
                    tag.set_property(attrName,value)
                    tags.append(tag)
        
        if not tstyle.is_inconsistent('weight'):
            value = tstyle.get('weight')
            
            if value == TextStyle.WEIGHT_FAINT:
                tags.append(tag_table.lookup('weight_faint'))
            elif value == TextStyle.WEIGHT_BOLD:
                tags.append(tag_table.lookup('weight_bold'))
            elif value == TextStyle.WEIGHT_NORMAL:
                tags.append(tag_table.lookup('weight_normal'))
        
        return tags
    
    @staticmethod
    def from_gtk_tag(tag):
        
        tstyle = TextStyle()
        
        tagName = tag.get_property('name')
        
        if getattr(tag,'invert',False):
            tstyle.set('invert',True)
        
        if tag.get_property('background-set'):
            attrName = 'foreground' if tstyle.invert else 'background'
            print tag.get_property('background-gdk')
            tstyle.set(attrName,RGB_TO_COLORNAME[hex2rgb(tag.get_property('background-gdk').to_string())])
        
        if tag.get_property('foreground-set'):
            attrName = 'background' if tstyle.invert else 'foreground'
            print tag.get_property('foreground-gdk')
            tstyle.set(attrName,RGB_TO_COLORNAME[hex2rgb(tag.get_property('foreground-gdk').to_string())])
        
        if tag.get_property('underline-set'):
            tstyle.set('underline',tag.get_property('underline'))
        
        if tag.get_property('strikethrough-set'):
            tstyle.set('strikethrough',tag.get_property('strikethrough'))
            
        if tag.get_property('weight-set'):
            
            pangoWeight = tag.get_property('weight')
            
            if pangoWeight == pango.WEIGHT_BOLD:
                tstyle.set('weight',TextStyle.WEIGHT_BOLD)
            elif pangoWeight == pango.WEIGHT_ULTRALIGHT:
                tstyle.set('weight',TextStyle.WEIGHT_FAINT)
            else:
                tstyle.set('weight',TextStyle.WEIGHT_NORMAL)
        
        return tstyle
       
    @staticmethod
    def from_gtk_selection(startIter,endIter):
        
        text_styles = []
        
        currentIter = startIter.copy()
        while not currentIter.equal(endIter):
            
            singleCharStyles = []
            
            for tag in currentIter.get_tags():
                singleCharStyles.append(TextStyle.from_gtk_tag(tag))
                print 'single char tag style', singleCharStyles[-1]
            
            
            text_styles.append(TextStyle.merge_styles(singleCharStyles,fill_empty_properties=True))
            print 'fusion', text_styles[-1]
            
            currentIter.forward_char()
        
        return TextStyle.merge_styles(text_styles)
    
    @staticmethod
    def merge_styles(text_styles,fill_empty_properties=False):
        if not len(text_styles): return TextStyle()
        
        tstyle = text_styles[0]
        
        for ts in text_styles[1:]:
            
            for attrName in ('underline','strikethrough','background','foreground','weight','invert'):
                
                currentValue = tstyle.get(attrName)
                newValue = ts.get(attrName)
                
                if currentValue != newValue:
                    
                    if fill_empty_properties and (currentValue == None or newValue == None):
                        tstyle.set(attrName,currentValue if newValue == None else newValue)
                    else:
                        tstyle.set_inconsistent(attrName)
        
        return tstyle
    
    @staticmethod
    def to_bash_code(tstyle):
        
        codes = []
        
        if tstyle.weight and not tstyle.is_inconsistent('weight'):
            codes.append({
                TextStyle.WEIGHT_NORMAL : 0,
                TextStyle.WEIGHT_BOLD : 1,
                TextStyle.WEIGHT_FAINT : 2
                }[tstyle.weight]
            )
        
        if tstyle.underline and not tstyle.is_inconsistent('underline'):
            codes.append(4)
        
        if tstyle.strikethrough and not tstyle.is_inconsistent('strikethrough'):
            codes.append(9)
        
        if tstyle.invert and not tstyle.is_inconsistent('invert'):
            codes.append(7)
        
        if tstyle.background and not tstyle.is_inconsistent('background'):
            codes.append({
                'black'  : 40,
                'red'    : 41,
                'green'  : 42,
                'brown'  : 43,
                'blue'   : 44,
                'purple' : 45,
                'cyan'   : 46,
                'gray'   : 47
              }[RGB_TO_COLORNAME[tstyle.background]]
            )
        
        if tstyle.foreground and not tstyle.is_inconsistent('foreground'):
            codes.append({
                'black'  : 30,
                'red'    : 31,
                'green'  : 32,
                'brown'  : 33,
                'blue'   : 34,
                'purple' : 35,
                'cyan'   : 36,
                'gray'   : 37
              }[RGB_TO_COLORNAME[tstyle.foreground]]
            )
        
        if len(codes):
            return r'\e[%sm' % ';'.join(str(x) for x in codes)
        else:
            return ''
        
    @staticmethod
    def from_bash_code_values(values):
        tstyle = TextStyle()
        
        for val in values:
            
            if val == 0:
                tstyle.weight = TextStyle.WEIGHT_NORMAL
            elif val == 1:
                tstyle.weight = TextStyle.WEIGHT_BOLD
            elif val == 2:
                tstyle.weight = TextStyle.WEIGHT_FAINT
            elif val == 4:
                tstyle.underline = True
            elif val == 7:
                tstyle.invert = True
            elif val == 9:
                tstyle.strikethrough = True
            elif 30 <= val <= 37:
                name = COLORS_8_FROM_INT_TO_NAME[val]
                tstyle.foreground = COLORNAME_TO_RGB[name]
            elif 40 <= val <= 47:
                name = COLORS_8_FROM_INT_TO_NAME[val]
                tstyle.background = COLORNAME_TO_RGB[name]
        
        return tstyle

class Styling(gtk.VBox):
    __gsignals__ = {
        'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                ()),
        'keyword-request' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                (gobject.TYPE_STRING,)),
    }
    
    _memory={}
    
    class ColorsContainer(gtk.Frame):
        __gsignals__ = {
            'color-selected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT,)),
        }
        
        class ColorPreview(gtk.DrawingArea):

            # Draw in response to an expose-event
            __gsignals__ = { "expose-event": "override" }
            
            def __init__(self,func_bright,colorTuple=None):
                super(Styling.ColorsContainer.ColorPreview,self).__init__()
                
                self.set_size_request(20,20)
                self.color=colorTuple
                
                if colorTuple:
                    self.draw=self._paint_color
                else:
                    self.draw=self._paint_transparent
                
                self.get_color_brightness = func_bright
        
            # Handle the expose-event by drawing
            def do_expose_event(self, event):
                # Create the cairo context
                cr = self.window.cairo_create()
        
                # Restrict Cairo to the exposed area; avoid extra work
                cr.rectangle(event.area.x, event.area.y,
                        event.area.width, event.area.height)
                cr.clip()
        
                self.draw(cr, *self.window.get_size())
        
            def _paint_transparent(self, cr, width, height):
                # Fill the background with white
                cr.set_source_rgb(1, 1, 1)
                cr.rectangle(0, 0, width, height)
                cr.fill()
                
                # a red line bottom left => top right
                cr.set_source_rgb(1.0, 0.0, 0.0)
                cr.move_to(0, height)
                cr.line_to(width,0)
                cr.stroke()
            
            def _paint_color(self, cr, width, height):
                
                def get_if_less_than_max(x,max=255):
                    return x if x < max else max;
                
                br = self.get_color_brightness()
                
                r,g,b = (int(round(get_if_less_than_max(x* {'dark':0.7,'normal':1,'bright':1.4}[br]))) for x in self.color)
                
                cr.set_source_color(gtk.gdk.color_parse(rgb2hex((r,g,b))))
                #cr.set_source_rgb(r,g,b)
                
                cr.rectangle(0, 0, width, height)
                cr.fill()
        
        def __init__(self,frameTitle,colorNames,rows=1):
            gobject.GObject.__init__(self)
            
            self.set_label(frameTitle)
            self.set_border_width(1)
            
            self._can_emit_toggle = True
            self.color_brightness = 'normal'
            
            colorNames = ['transparent']+colorNames
            
            numColors = len(colorNames)
            
            columns=int(ceil(numColors/float(rows)))
            
            tableColors=gtk.Table(rows=rows,columns=columns,homogeneous=True)
            tableColors.set_row_spacings(1)
            tableColors.set_col_spacings(1)
            
            group=None
            
            self.currentColor = None
            self.colors2radio={}
            
            def get_color_brigthness():
                return self.color_brightness
            
            for row in range(rows):
                for col in range(columns):
                    
                    singleColorBox=gtk.VBox()
                    
                    colorName=colorNames[col];
                    
                    littleFrame=gtk.Frame()
                    littleFrame.set_border_width(2)
                    
                    if colorName == 'transparent':
                        singleColorPreview=Styling.ColorsContainer.ColorPreview(get_color_brigthness,None)
                    else:
                        print colorName, colors[colorName]
                        singleColorPreview=Styling.ColorsContainer.ColorPreview(get_color_brigthness,colors[colorName])
                    
                    singleColorPreview.show()
                    
                    littleFrame.add(singleColorPreview)
                    littleFrame.show()
                    
                    singleColorBox.pack_start(littleFrame,0,0,2)
                    
                    radioButton=gtk.RadioButton(group)
                    if group == None: group = radioButton
                    radioButton.show()
                    
                    align=gtk.Alignment(0.5, 0.5, 0, 0)
                    align.add(radioButton)
                    align.show()
                    
                    singleColorBox.pack_start(align,0,0,2)
                    
                    singleColorBox.show()
                    
                    self.colors2radio[colorName]=radioButton
                    print colorName,radioButton
                    
                    signal_id=radioButton.connect('toggled', self._on_color_selected,colorName)
                    radioButton._signal_id=signal_id
                    
                    tableColors.attach(singleColorBox,col,col+1,row,row+1)
            
            self.invisibleRadioBtn = gtk.RadioButton(group)
            singleColorBox.pack_start(self.invisibleRadioBtn,0,0,0)
            
            tableColors.show()
            
            self.add(tableColors)
        
        def _on_color_selected(self,widget,colorName):
            if not widget.get_active() or not self._can_emit_toggle: return
            
            print '_on_color_selected()'
            self.currentColor = None if colorName=='transparent' else colorName
            self.emit('color-selected', self.currentColor)
        
        def set_color_brightness(self,brightness):
            self.color_brightness = brightness
            self.queue_draw()
        
        def get_color(self):
            '''Return the color name'''
            return self.currentColor
        
        def set_color(self,color=TextStyle.INCONSISTENT):
            print 'set_color',color
            if color == TextStyle.INCONSISTENT:
                self.invisibleRadioBtn.set_active(True)
                return
            
            if isinstance(color,tuple):
                colorName = RGB_TO_COLORNAME[color]
            else:
                colorName = color
            print 'setting colorname',colorName
            self.currentColor = colorName
            
            if colorName == None: colorName = 'transparent'
            print 'now colorName is',colorName
            
            newRadioBtn=self.colors2radio[colorName]
            
            self._can_emit_toggle = False
            
            newRadioBtn.set_active(True)
            
            self._can_emit_toggle = True
            
    
    gobject.type_register(ColorsContainer)
    
    class StylesContainer(gtk.Frame):
        __gsignals__ = {
            'style-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    ()),
        }
        
        def __init__(self):
            gobject.GObject.__init__(self)
            
            self._can_send_signal = True
            
            self.set_label('Styles')
            self.set_border_width(1)
            
            rows=3
            columns=2
            
            tableStyles=gtk.Table(rows=rows,columns=columns,homogeneous=True)
            tableStyles.set_row_spacings(1)
            tableStyles.set_col_spacings(1)
            
            self.underlineBtn=gtk.CheckButton('underline')
            self.strikethroughBtn=gtk.CheckButton('strikethrough')
            self.invertBtn=gtk.CheckButton('invert')
            
            self.normalRadio=gtk.RadioButton(None,TextStyle.WEIGHT_NORMAL)
            self.boldRadio=gtk.RadioButton(self.normalRadio,TextStyle.WEIGHT_BOLD)
            self.faintRadio=gtk.RadioButton(self.normalRadio,TextStyle.WEIGHT_FAINT)
            
            for widget in (
                      self.underlineBtn,
                      self.strikethroughBtn,
                      self.invertBtn,
                      self.normalRadio,
                      self.boldRadio,
                      self.faintRadio
                      ):
                widget.connect('toggled', self._send_changed_signal)
                widget.show()
            
            self.weightRadioInconsistent=gtk.RadioButton(self.normalRadio,None)
            
            tableStyles.attach(self.normalRadio,0,1,0,1)
            tableStyles.attach(self.boldRadio,0,1,1,2)
            tableStyles.attach(self.faintRadio,0,1,2,3)
            
            tableStyles.attach(self.underlineBtn,1,2,0,1)
            tableStyles.attach(self.strikethroughBtn,1,2,1,2)
            tableStyles.attach(self.invertBtn,1,2,2,3)
            
            tableStyles.show()
            
            self.add(tableStyles)
        
        def _send_changed_signal(self,toggleBtn,*args):
            toggleBtn.set_inconsistent(False)
            if self._can_send_signal:
                self.emit('style-changed')
        
        def get_styles(self):
            tstyle = TextStyle()
            
            if self.weightRadioInconsistent.get_active():
                tstyle.set_inconsistent('weight')
            elif self.boldRadio.get_active():
                tstyle.weight = TextStyle.WEIGHT_BOLD
            elif self.faintRadio.get_active():
                tstyle.weight = TextStyle.WEIGHT_FAINT
            else:
                tstyle.weight = TextStyle.WEIGHT_NORMAL
            
            for attrName in ('underline','strikethrough','invert'):
                toggleBtn = getattr(self,attrName+'Btn')
                if toggleBtn.get_inconsistent():
                    tstyle.set_inconsistent(attrName)
                else:
                    tstyle.set(attrName,toggleBtn.get_active())
            
            return tstyle
        
        def set_styles(self,tstyle):
            self._can_send_signals=False
            print 'set_styles',tstyle
            
            for attrName in ('underline','strikethrough','invert'):
                toggleBtn = getattr(self,attrName+'Btn')
                if tstyle.is_inconsistent(attrName):
                    toggleBtn.set_inconsistent(True)
                else:
                    toggleBtn.set_inconsistent(False)
                    toggleBtn.set_active(tstyle.get(attrName) == True)
            
            if tstyle.is_inconsistent('weight'):
                self.weightRadioInconsistent.set_active(True)
            else:
                self.normalRadio.set_active(tstyle.weight == TextStyle.WEIGHT_NORMAL)
                self.boldRadio.set_active(tstyle.weight == TextStyle.WEIGHT_BOLD)
                self.faintRadio.set_active(tstyle.weight == TextStyle.WEIGHT_FAINT)
            
            self._can_send_signals=True
    
    gobject.type_register(StylesContainer)
    
    def __init__(self,*args):
        gobject.GObject.__init__(self)
        
        self._is_keyword_active = True
        
        mainFrame=gtk.Frame('Options')
        mainFrame.set_border_width(1)
        
        
        boxColorsAndStyle=gtk.VBox()
        
        self.keywordsBox=KeywordsBox()
        self.keywordsBox.set_active_first()
        self.keywordsBox.connect('keyword-changed',self._on_keyword_changed)
        self.keywordsBox.connect('keyword-request',self._on_keyword_requested)
        self.keywordsBox.show()
        boxColorsAndStyle.pack_start(self.keywordsBox,0,0,3)
        
        hbox=gtk.HBox()
        
        ### TABLE STYLES ###
        
        self.frameStyles=Styling.StylesContainer()
        self.frameStyles.connect('style-changed', lambda *args: self._on_style_changed())
        self.frameStyles.show()
        
        ### END TABLE STYLES ###
        
        hbox.pack_start(self.frameStyles,0,0,2)
        
        ### COLORS ###
        
        vbox = gtk.VBox()
        
        print COLORNAME_TO_RGB.keys()
        
        self.frameBgColors=Styling.ColorsContainer('Background color',COLORNAME_TO_RGB.keys())
        self.frameBgColors.connect('color-selected', lambda *args: self._on_style_changed())
        self.frameBgColors.show()
        
        self.frameFgColors=Styling.ColorsContainer('Foreground color',COLORNAME_TO_RGB.keys())
        self.frameFgColors.connect('color-selected', lambda *args: self._on_style_changed())
        self.frameFgColors.show()
        
        vbox.pack_start(self.frameBgColors,0,0,2)
        vbox.pack_start(self.frameFgColors,0,0,2)
        
        vbox.show()
        
        ### END colors ###
        
        hbox.pack_start(vbox,1,1,2)
        hbox.show()
        
        boxColorsAndStyle.pack_start(hbox,0,0,2)
        
        boxColorsAndStyle.show()
        #vbox.pack_start(boxColorsAndStyle,0,0,10)
        
        mainFrame.add(boxColorsAndStyle)
        
        mainFrame.show()
        self.pack_start(mainFrame,1,1,0)
        
        self.reset()
    
    def reset(self):
        from copy import deepcopy
        
        for keywordName in KEYWORDS:
            Styling._memory[keywordName]=TextStyle()
        
        self.set_current_keyword(self.get_current_keyword())    
        self.emit('changed')
    
    def _export_current_style(self):
        tstyle = self.frameStyles.get_styles()
        tstyle.set('background',self.frameBgColors.get_color())
        tstyle.set('foreground',self.frameFgColors.get_color())
        return tstyle
    
    def _on_style_changed(self):
        tstyle = self._export_current_style()
        if self.keywordsBox.is_active():
            Styling._memory[self.keywordsBox.get_active()]= tstyle
        print '\nstyle changed',Styling._memory[self.keywordsBox.get_active()],"\n"
        
        self.frameFgColors.set_color_brightness({'normal':'normal','bold':'bright','faint':'dark'}[tstyle.weight])
        
        self.emit('changed')
    
    def get_styling(self,keywordName = None):
        if keywordName and self.keywordsBox.is_active():
            return Styling._memory[keywordName]
        else:
            return self._export_current_style()
    
    def set_styling(self,tstyle):
        self.frameBgColors.set_color(tstyle.background)
        self.frameFgColors.set_color(tstyle.foreground)
        self.frameStyles.set_styles(tstyle)
    
    def _on_keyword_requested(self,widget,key):
        self.emit('keyword-request',key)
    
    def _on_keyword_changed(self,keywordBox,keywordName):
        print 'keyword changed',keywordName,Styling._memory[keywordName]
        tstyle = Styling._memory[keywordName]
        self.frameBgColors.set_color(tstyle.background)
        self.frameFgColors.set_color(tstyle.foreground)
        self.frameStyles.set_styles(tstyle)
    
    def set_current_keyword(self,keywordName):
        self.keywordsBox.set_active(keywordName)
    
    def get_current_keyword(self):
        return self.keywordsBox.get_active()
    
    def activate_keyword(self):
        self._is_keyword_active = True
        self.frameStyles.set_sensitive(True)
        self.keywordsBox.activate_keyword()
        self._on_keyword_changed(self.keywordsBox,self.keywordsBox.get_active())
    
    def is_keyword_active(self):
        return self._is_keyword_active
    
    def deactivate_keyword(self,keepOnlyColors = False):
        self._is_keyword_active = False
        self.keywordsBox.deactivate_keyword()
        
        tstyle = TextStyle()
        tstyle.set_inconsistent('background')
        tstyle.set_inconsistent('foreground')
        
        self.frameBgColors.set_color(tstyle.background)
        self.frameFgColors.set_color(tstyle.foreground)
        self.frameStyles.set_styles(tstyle)
        
        if keepOnlyColors:
            self.frameStyles.set_sensitive(False)
    
    def __str__(self):
        return self.__unicode__().encode('utf-8')
    
    def __unicode__(self):
        return u'<type Styling>'+repr(self.get_styling(self.get_current_keyword())).decode('utf-8')+u'</type>'

gobject.type_register(Styling)

class FormatPromptTextView(gtk.TextView):
    __gsignals__ = {
        'selection-toggle' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_BOOLEAN,)),
        'selection-change' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,)),
        'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                ()),
    }
    
    DEFAULT_BACKGROUND=(0,0,0)
    DEFAULT_FOREGROUND=(255,255,255)
    
    def __init__(self,*args):
        gtk.TextView.__init__(self,*args)
        self.modify_font(pango.FontDescription('Courier 14'))
        self.set_property('left-margin',2) 
        self.modify_base(gtk.STATE_NORMAL,gtk.gdk.color_parse('#000000'))
        self.modify_text(gtk.STATE_NORMAL,gtk.gdk.color_parse('#FFFFFF'))
        self.buffer=self.get_buffer()
        
        table=self.buffer.get_tag_table()
        
        for colorName,rgb in COLORNAME_TO_RGB.iteritems():
            
            hexCode=rgb2hex(rgb)
            
            tag=gtk.TextTag('bg_'+colorName)
            tag.set_property('background',hexCode)
            table.add(tag)
            
            tag=gtk.TextTag('fg_'+colorName)
            tag.set_property('foreground',hexCode)
            table.add(tag)
        
        for weight in (
                ('faint',pango.WEIGHT_ULTRALIGHT),
                ('normal',pango.WEIGHT_NORMAL),
                ('bold',pango.WEIGHT_BOLD)
                 ):
            tag=gtk.TextTag('weight_'+weight[0])
            tag.set_property('weight',weight[1])
            table.add(tag)
        
        for keywordName in KEYWORDS:
            tag=gtk.TextTag(keywordName)
            table.add(tag)
        
        tag=gtk.TextTag('underline')
        tag.set_property('underline',True)
        table.add(tag)
        
        tag=gtk.TextTag('strikethrough')
        tag.set_property('strikethrough',True)
        table.add(tag)
            
        tag=gtk.TextTag('invert')
        table.add(tag)
        
        # add selection change capabilities
        self._has_selection = False
        self.id_has_sel=self.buffer.connect('notify::has-selection', self.on_selection_toggle)
        self.id_move_cursor=self.connect_after('move-cursor', self.on_move_cursor)
        
        self.connect('button-release-event', self._on_mouse_button_released)
        
        self.connect('button-press-event', self.on_mouseBtn_down)
        
        self.id_buf_changed=self.buffer.connect('changed', self.on_content_change)
    
    def on_mouseBtn_down(self,*args):
        print 'mouse down (has selection %s)' % self._has_selection,self.buffer.get_has_selection()
        
        if self._has_selection:
            self._skip_mouse_release = True
        else:
            self._skip_mouse_release = False
    
    def change_base_colors(self,tstyle):
        if not tstyle.is_inconsistent('background'):
            if tstyle.background:
                self.modify_base(gtk.STATE_NORMAL,gtk.gdk.color_parse(rgb2hex(tstyle.background)))
            else:
                self.modify_base(gtk.STATE_NORMAL,gtk.gdk.color_parse(rgb2hex(FormatPromptTextView.DEFAULT_BACKGROUND)))
        
        if not tstyle.is_inconsistent('foreground'):
            if tstyle.foreground:
                self.modify_text(gtk.STATE_NORMAL,gtk.gdk.color_parse(rgb2hex(tstyle.foreground)))
            else:
                self.modify_text(gtk.STATE_NORMAL,gtk.gdk.color_parse(rgb2hex(FormatPromptTextView.DEFAULT_FOREGROUND)))
            
    
    def _find_keyword_pos(self,text,keywordName):
        
        lenText=len(text)
        lenKeywordName=len(keywordName)
        
        positions=[]
        idx = 0
        while True:
            idx=text.find(keywordName,idx)
            if idx == -1 : break
            
            positions.append((idx,idx+lenKeywordName))
            idx = idx+lenKeywordName
        
        return positions
    
    def on_content_change(self,buffer,*args):
        
        text=buffer.get_text(*buffer.get_bounds())
        
        for keywordName in KEYWORDS:
            positions=self._find_keyword_pos(text,keywordName)
            
            for start,end in positions:
                buffer.apply_tag_by_name(
                                 keywordName,
                                 buffer.get_iter_at_offset(start),
                                 buffer.get_iter_at_offset(end))
        
        self.emit('changed')
    
    def change_keyword_appearance(self,keywordName,styleObj):
        
        tagTable=self.buffer.get_tag_table()
        tag=tagTable.lookup(keywordName)
        
        tstyle = styleObj.get_styling(keywordName)
        
        # XXX check if the 'invert' attribute is preserved on tag lookup
        print '>> change_keyword_appearance()',tstyle,tag
        TextStyle.to_gtk_tag(tstyle,tag)
    
    def change_selection_appearance(self,tstyle,startIter,endIter):
        print 'change_selection_appearance()',tstyle
        
        tag_table = self.buffer.get_tag_table()
        
        def get_inconsistent_tags(tstyle,tag_table):
            tags = []
            if tstyle.is_inconsistent('background'):
                for colorName in COLORNAME_TO_RGB:
                    tags.append(tag_table.lookup('bg_'+colorName))
            if tstyle.is_inconsistent('foreground'):
                for colorName in COLORNAME_TO_RGB:
                    tags.append(tag_table.lookup('fg_'+colorName))
            if tstyle.is_inconsistent('strikethrough'):
                tags.append(tag_table.lookup('strikethrough'))
            if tstyle.is_inconsistent('underline'):
                tags.append(tag_table.lookup('underline'))
            if tstyle.is_inconsistent('weight'):
                for i in ('bold','faint','normal'):
                    tags.append(tag_table.lookup('weight_bold'))
            
            return tags
        
        inc_tags = get_inconsistent_tags(tstyle,tag_table)
        
        currentIter = startIter.copy()
        while not currentIter.equal(endIter):
            nextIter = currentIter.copy()
            nextIter.forward_char()
            
            curTags = currentIter.get_tags()
            for singleTag in curTags:
                if singleTag not in inc_tags:
                    self.buffer.remove_tag(singleTag,currentIter,nextIter)
            
            currentIter.forward_char()
        
        tags = TextStyle.to_gtk_tags(tstyle,tag_table)
        for tag in tags:
            self.buffer.apply_tag(tag,startIter,endIter)
        
    def _on_mouse_button_released(self,textview,event):
        if self._skip_mouse_release:
            return
        
        if self._has_selection:
            self._on_selection_changed()
        else:
            selectedKeyword = self._try_to_select_keyword(self.buffer,True)
            if selectedKeyword: self._on_selection_changed(selectedKeyword)
    
    def reset_colors(self):
        self.buffer.handler_block(self.id_buf_changed)
        self.buffer.remove_all_tags(*self.buffer.get_bounds())
        self.buffer.handler_unblock(self.id_buf_changed)
        self.buffer.emit('changed')
        
    def on_move_cursor(self,textview,step_size,count,extend_selection):
        if extend_selection:
            try:
                start, end = self.buffer.get_selection_bounds()
                selected_text = self.buffer.get_text(start, end)
                if len(selected_text) > 0: # when is 0 the 'selection-end' signal is automatically emitted
                    self._on_selection_changed()
            except ValueError, e:
                pass
        else:
            selectedKeyword = self._try_to_select_keyword(textview.buffer,count > 0)
            self._on_selection_changed(selectedKeyword)
    
    def _try_to_select_keyword(self,buffer,move_left_to_right):
        self.handler_block(self.id_move_cursor)
        
        selectedKeyword = None
        
        cursor_pos = buffer.get_property('cursor-position')
        current_iter = buffer.get_iter_at_offset(cursor_pos)
        
        for tag in current_iter.get_tags():
            tagName = tag.get_property('name')
            if not current_iter.begins_tag(tag) and tagName in KEYWORDS:
                
                startIter,endIter = get_tag_bounds(current_iter,tag)
                if move_left_to_right > 0:
                    buffer.select_range(startIter,endIter)
                else:
                    buffer.select_range(endIter,startIter)
                
                selectedKeyword = tagName
                
                break
        
        self.handler_unblock(self.id_move_cursor)
        
        return selectedKeyword
    
    def on_selection_toggle(self,buffer,*args):
        self._has_selection = not self._has_selection
        self.emit('selection-toggle',self._has_selection)
        if not self._has_selection:
            self._on_selection_changed()
    
    def _on_selection_changed(self,selectedKeyword=None):
        buffer = self.buffer
        
        print '_on_selection_changed()',self.buffer.get_has_selection(),self.buffer.get_selection_bounds()
        #if not self.buffer.get_has_selection():
        #    1/0
        
        if self._has_selection and not selectedKeyword:
            tagTable = buffer.get_tag_table()
            
            for keywordName in KEYWORDS:
                tag = tagTable.lookup(keywordName)
                
                startSel,endSel = buffer.get_selection_bounds()
                
                tagIter = has_tag_in_range(tag,startSel,endSel)
                if not tagIter: continue
                
                self.handler_block(self.id_move_cursor)
                
                newStartSel = tagIter.copy()
                newEndSel = tagIter.copy()
                newEndSel.forward_to_tag_toggle(tag)
                
                buffer.select_range(newStartSel,newEndSel)
                
                self.handler_unblock(self.id_move_cursor)
                
                selectedKeyword = keywordName
        
        self.emit('selection-change',selectedKeyword)
    
    def get_keyword_at_iter(self,current_iter):
        
        res = None
        
        for tag in current_iter.get_tags():
            tagName = tag.get_property('name')
            if tagName in KEYWORDS:
                
                startIter,endIter = get_tag_bounds(current_iter,tag)
                
                res = {
                    'start' : startIter,
                    'end'   : endIter,
                    'keyword' : tagName
                }
                
                break
        
        return res
    

class KeywordsBox(gtk.VBox):
    __gsignals__ = {
        'keyword-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,)),
        'keyword-request' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,))
    }
    
    def __init__(self):
        gtk.VBox.__init__(self)
        
        labelHelp=gtk.Label("Scegli una parola chiave dall'elenco qui sotto o scrivi quello che preferisci\n"
                            "Ricorda che su un terminale una parola in bold avrà un colore più brillante, una in faint più scuro\n")
        labelHelp.show()
        align=gtk.Alignment(0,0,0,0)
        align.add(labelHelp)
        align.show()
        self.pack_start(align,1,1,0)
        
        mainBox=gtk.HBox()
        
        self.keywordToIndex = {}
        
        '''
        HHHHHHHHHHHHHHHHHHHHHHHH
          
          VVVVVVVVVVVVVVVVVVVV
          
            HHHHHHHHHHHHHHHHHH
            
              combo | button
            
            HHHHHHHHHHHHHHHHHH
            ---
            HHHHH
            H ^ H
            H ^ H
            HHHHH
          
          VVVVVVVVVVVVVVVVVVVVV
        
        HHHHHHHHHHHHHHHHHHHHHHHH
        '''
        
        tmpHbox=gtk.HBox()
        
        liststore = gtk.ListStore(gobject.TYPE_STRING)
        idx = 0
        for key in KEYWORDS:
            liststore.append((key,))
            self.keywordToIndex[key] = idx
            idx += 1
        
        combobox = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)
        combobox.set_wrap_width(2)
        
        combobox.connect('changed',self._on_combobox_changed)
        
        self.combobox=combobox
        
        combobox.show()
        
        #mainBox.pack_start(combobox,0,0,2)
        tmpHbox.pack_start(combobox,0,0,2)
        
        insertBtn=gtk.Button('Insert')
        insertBtn.connect('clicked',self._on_insertBtn_clicked)
        insertBtn.show()
        #mainBox.pack_start(insertBtn,0,0,2)
        tmpHbox.pack_start(insertBtn,0,0,2)
        
        tmpHbox.show()
        
        vbox=gtk.VBox()
        vbox.show()
        vbox.pack_start(tmpHbox,0,0,0)
        zbox=gtk.HBox() # dummy box that fill the vertical space
        zbox.show()
        vbox.pack_start(zbox,0,1,1)
        
        mainBox.pack_start(vbox,0,0,0)
        
        helpBox=gtk.VBox()
        
        self.descLabel=gtk.Label()
        self.descLabel.show()
        self.descLabel.set_justify(gtk.JUSTIFY_LEFT)
        align = gtk.Alignment(0,0,0,0)
        align.add(self.descLabel)
        align.show()
        
        helpBox.pack_start(align)
        
        self.exampleLabel=gtk.Label()
        self.exampleLabel.show()
        align = gtk.Alignment(0,0,0,0)
        align.add(self.exampleLabel)
        align.show()
        helpBox.pack_start(align)
        
        
        helpBox.show()
        mainBox.pack_start(helpBox,0,0,2)
        
        mainBox.show()
        self.pack_start(mainBox)
    
    def _on_insertBtn_clicked(self,*args):
        self.emit('keyword-request',self.get_active())
    
    def _on_combobox_changed(self,combobox):
        keywordName=self.get_active()
        keywordData=KEYWORDS[keywordName]
        
        ### XXX follows an ugly hack to have a fixed height help zone
        ### It needs to be fixed: the sooner the better
        
        descText = keywordData['help']
        
        exampleText = keywordData['example']
        exampleLines = 1 + exampleText.count('\n')
        if exampleLines < 3:
            exampleText+= '\n'*(3-exampleLines)
        
        self.descLabel.set_text(descText)
        self.exampleLabel.set_markup('<span background="black" foreground="white">'+exampleText+"</span>")
        
        self.emit('keyword-changed',keywordName)
    
    def get_active(self):
        model = self.combobox.get_model()
        index = self.combobox.get_active()
        return model[index][0]
    
    def set_active(self,keywordName):
        index = self.keywordToIndex[keywordName]
        self.combobox.set_active(index)
    
    def is_active(self):
        return self.get_property('sensitive')
    
    def set_active_first(self):
        self.combobox.set_active(0)
    
    def activate_keyword(self):
        self.set_sensitive(True)
    
    def deactivate_keyword(self):
        self.set_sensitive(False)

gobject.type_register(KeywordsBox)

class Window(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_size_request(700,700)
        self.set_border_width(5)
        self.connect('delete-event',self.on_delete_event)
        
        vbox=gtk.VBox()
        
        topBox=gtk.VBox()
        
        self.stylingBox=Styling()
        self.stylingBox.connect('changed',self.on_style_changed)
        self.stylingBox.connect('keyword-request',self.on_keyword_requested)
        self.stylingBox.show()
        topBox.pack_start(self.stylingBox,0,0,2)
        
        topBox.show()
        vbox.pack_start(topBox,0,0,2)
        
        self.baseColorsCheckBtn=gtk.CheckButton('usa i colori per modificare sfondo e colore del testo di EasyPrompt')
        self.baseColorsCheckBtn.connect('toggled',self.on_checkBtn_baseColors_clicked)
        self.baseColorsCheckBtn.show()
        vbox.pack_start(self.baseColorsCheckBtn,0,0,2)
        
        txtBox=gtk.HBox()
        
        self.textview=FormatPromptTextView()
        self.fpt_sel_changed_id=self.textview.connect('selection-change',self.on_formatPrompt_selection_change)
        self.fpt_changed_id=self.textview.connect('changed',self.convert_to_bash_and_preview)
        self.textview.show()
        
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.textview)
        sw.show()
        
        txtBox.pack_start(sw,1,1,2)
        
        tmpVBox = gtk.VBox()
        btn=gtk.Button('Import...')
        btn.show()
        btn.connect('clicked', self.on_importBtn_clicked)
        tmpVBox.pack_start(btn,0,0,0)
        tmpVBox.show()
        
        txtBox.pack_start(tmpVBox,0,0,2)
        txtBox.show()
        
        vbox.pack_start(txtBox,0,0,2)
        
        codePreviewBox=gtk.HBox()
        
        btn=gtk.Button('Reset')
        btn.show()
        btn.connect('clicked', lambda *x: self.stylingBox.reset())
        btn.connect('clicked', lambda *x: self.textview.reset_colors())
        codePreviewBox.pack_start(btn,0,0,2)
        
        label=gtk.Label()
        label.set_markup("<b>Generated code</b>");
        codePreviewBox.pack_start(label,0,0,2)
        self.codePreview=gtk.Label()
        self.codePreview.set_selectable(True)
        codePreviewBox.pack_start(self.codePreview,0,0,2)
        codePreviewBox.show_all()
        vbox.pack_start(codePreviewBox,0,0,2)
        
        self.term=self.create_terminal()
        self.term.show()
        vbox.pack_start(self.term,1,1,2)
        
        btn=gtk.Button('Save')
        btn.connect('clicked', lambda *x: self.write_on_disk(self.convert_to_bash()))
        btn.show()
        vbox.pack_start(btn,0,0,2)
        
        vbox.show()
        self.add(vbox)
        
        txtBox.set_size_request(-1,self.textview.get_line_yrange(self.textview.buffer.get_start_iter())[1]*3)
        
        self.set_prompt_from_bash_string(self.get_system_prompt())
        
        self.show()
    
    def get_system_prompt(self):
        return os.environ.get('PS1','')
    
    def set_prompt_from_bash_string(self,bash_code):
        self.textview.handler_block(self.fpt_sel_changed_id)
        self.textview.handler_block(self.fpt_changed_id)
        
        buffer = self.textview.buffer
        tag_table = buffer.get_tag_table()
        
        buffer.set_text('')
        
        bash_code  = re.sub(r'(\\\[|\\\])','',bash_code) # strip \[ and \]
        
        ### this is incredibly inefficient ###
        for keywordName in KEYWORDS:
            bash_code = bash_code.replace(KEYWORDS[keywordName]["command"],keywordName)
        ### ###
        
        pattern = re.compile(r'(?:\\033|\\e)\[((?:\d*[;m])*)')
        
        tstyles = []
        for groupMatch in pattern.findall(bash_code):
            
            groupMatch = groupMatch[:-1]
            
            if groupMatch == '':
                tstyles.append(TextStyle())
            else:
                tstyles.append(TextStyle.from_bash_code_values(int(x) for x in groupMatch.split(';')))
        
        parts = pattern.split(bash_code) # having groups, splitting contains the splitting part too at even indexes
        
        buffer.insert(buffer.get_end_iter(),parts[0])
        for i in range(1,len(parts)-1,2):
            currentIter = buffer.get_end_iter()
            tstyle = tstyles[(i-1)/2]
            buffer.insert_with_tags(currentIter,parts[i+1],*TextStyle.to_gtk_tags(tstyle,tag_table))
        
        self.textview.handler_unblock(self.fpt_sel_changed_id)
        self.textview.handler_unblock(self.fpt_changed_id)
    
    def on_importBtn_clicked(self,btn):
        
        def on_entry_activated(entry,dialog):
            dialog.response(gtk.RESPONSE_OK)
        
        dialog = gtk.MessageDialog(
            self,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_OK_CANCEL,
            None
        )
        
        dialog.set_markup('Please enter your bash prompt code:')
        entry = gtk.Entry()
        entry.connect("activate",on_entry_activated,dialog)
        
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label("Name:"), False, 5, 5)
        hbox.pack_end(entry)
        
        dialog.format_secondary_markup("This will be used for <i>identification</i> purposes")
        
        dialog.vbox.pack_end(hbox, True, True, 0)
        dialog.show_all()
        
        response = dialog.run()
        
        text = entry.get_text()
        dialog.destroy()
        
        if response == gtk.RESPONSE_OK:
            self.set_prompt_from_bash_string(text)
        
    
    def on_checkBtn_baseColors_clicked(self,btn):
        if btn.get_active():
            self.stylingBox.deactivate_keyword(True)
        else:
            self.stylingBox.activate_keyword()
    
    def create_terminal(self):
        term=shell.ShellWidget()
        term.loadColors(shell.getGnomeTerminalColors())
        term.set_size(term.get_column_count(),10)
        return term
    
    def on_formatPrompt_selection_change(self,textview,keywordSelected):
        if self.baseColorsCheckBtn.get_active():
            return
        
        try:
            start,end = textview.buffer.get_selection_bounds()
            
            if keywordSelected:
                self.stylingBox.activate_keyword()
                self.stylingBox.set_current_keyword(keywordSelected)
            else:
                self.stylingBox.deactivate_keyword()
                tstyle = TextStyle.from_gtk_selection(start,end)
                print 'selected. style is ',tstyle
                self.stylingBox.set_styling(tstyle)
            
        except ValueError, e:
            print 'NO SELECTION, call stylingBox.activate_keyword()'
            self.stylingBox.activate_keyword()
    
    def convert_to_bash_and_preview(self,*args):
        converted=self.convert_to_bash()
        self.preview(converted)
        self.code_preview(converted)
    
    def preview(self,prompt_format):
        self.term.set_prompt(prompt_format)
        self.term.clear()
    
    def code_preview(self,prompt_format):
        self.codePreview.set_text(prompt_format.strip(u'\x00'))
    
    def on_keyword_requested(self,widget,key):
        self.textview.buffer.insert_at_cursor(key)
    
    def convert_to_bash(self):
        
        buffer=self.textview.buffer
        
        currentIter = buffer.get_start_iter()
        endIter = buffer.get_end_iter()
        
        prev_bash_code = ''
        
        result = []
        x = 0
        while not currentIter.equal(endIter):
            
            nextIter = currentIter.copy()
            nextIter.forward_char()
            
            tstyle = TextStyle.from_gtk_selection(currentIter,nextIter)
            bash_code = TextStyle.to_bash_code(tstyle)
            print x,tstyle,bash_code
            x += 1
            if bash_code != prev_bash_code:
                prev_bash_code = bash_code
                if bash_code == '':
                    bash_code = r'\e[0m'
                result.append(bash_code)
            
            
            keyword_found = self.textview.get_keyword_at_iter(currentIter)
            if keyword_found:
                nextIter = keyword_found['end']
                result.append(KEYWORDS[keyword_found['keyword']]['command'])
            else:
                result.append(currentIter.get_char())
            
            currentIter = nextIter
        
        
        bash_ps1 = ''.join(result)
        
        idx = bash_ps1.rfind(r'\e[')
        if idx != -1 and not bash_ps1[idx:].startswith(r'\e[0m'):
            bash_ps1 += r'\e[0m'
        
        return bash_ps1
    
    def write_on_disk(self,line):
        fp=file(os.path.join(os.environ['HOME'],'.bashrc'),'a')
        fp.write('\nPS1="%s"' % line)
        fp.close()

        dialog=gtk.MessageDialog(self,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_INFO,
            gtk.BUTTONS_OK,
            'ho aggiunto il codice in fondo a ~/.bashrc, apri un nuovo terminale o usa "source ~/.bashrc" per provarlo'
        )
        dialog.run()
        dialog.destroy()
    
    def on_table_color_selected(self,table,colorName):
        if self.checkBtn.get_active():
            if colorName.startswith('bg_'):
                self.textview.modify_base(gtk.STATE_NORMAL,gtk.gdk.color_parse(rgb2hex(colors[colorName])))
            else:
                self.textview.modify_text(gtk.STATE_NORMAL,gtk.gdk.color_parse(rgb2hex(colors[colorName])))
        else:
            self.apply_tag_to_template(self.textview,colorName)
    
    def on_style_changed(self,stylingObj):
        if stylingObj.is_keyword_active():
            keywordName=self.stylingBox.get_current_keyword()
            self.textview.change_keyword_appearance(keywordName,stylingObj)
        else:
            tstyle = stylingObj.get_styling()
            if self.baseColorsCheckBtn.get_active():
                self.textview.change_base_colors(tstyle)
                
                if tstyle.background:
                    if not tstyle.is_inconsistent('background'):
                        self.term.set_color_background(gtk.gdk.color_parse(rgb2hex(tstyle.background)))
                else:
                    self.term.set_color_background(gtk.gdk.color_parse(rgb2hex(FormatPromptTextView.DEFAULT_BACKGROUND)))
                
                if tstyle.foreground:
                    if not tstyle.is_inconsistent('foreground'):
                        self.term.set_color_foreground(gtk.gdk.color_parse(rgb2hex(tstyle.foreground)))
                else:
                    self.term.set_color_foreground(gtk.gdk.color_parse(rgb2hex(FormatPromptTextView.DEFAULT_FOREGROUND)))
                
            else:
                start,end  = self.textview.buffer.get_selection_bounds()
                self.textview.change_selection_appearance(tstyle,start,end)
        self.convert_to_bash_and_preview()
    
    def on_delete_event(self,*args):
        gtk.main_quit()
        
    
    def run(self):
        gtk.main()

if __name__=='__main__':
    win=Window()
    win.run()
