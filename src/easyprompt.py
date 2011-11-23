#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Riccardo Attilio Galli <riccardo@sideralis.org>'
__organization__ = 'Sideralis'
__program_name__ = 'EasyPrompt'
__version__ = '1.1.0'
__copyright__ = 'Copyright © Riccardo Attilio Galli'
__website__ = 'http://www.sideralis.org'
__license__ = 'GPLv3'

import logging

import os,sys,re
import gtk,pango,gobject

from math import floor,ceil

import shell
from term_colors import (BashColor,ANSIColor,TERM_COLORS,ANSI_COLORS,GRAYSCALE,WHITE,BLACK,
                         lighter_rgb,darker_rgb,rgb2hex,TextStyle,parse_bash_code)
from colorPicker import ColorPicker,ColorWidget

from i18n import _

from easy_selection_textview import EasySelectionTextview

COLORS = ANSI_COLORS
#COLORS = TERM_COLORS

try:
    for idx,gdkColor in enumerate(shell.getGnomeTerminalColors()['palette']):
        # substitute initial colors with the palette colors
        
        hexCode = gdkColor.to_string()
        
        TERM_COLORS[idx] = BashColor(hexCode,idx)
        
        if idx < 16:
            ANSI_COLORS[idx] = ANSIColor(hexCode,idx)
        
except (Exception),e:
    raise e

gtk.rc_parse_string(\
 'style "default" { \
    GtkTextView::cursor_color    = "#cc0000" \
 } \
 class "GtkTextView" style "default"'
)

COMMANDS = []

class CommandPlugin(object):
    lang = 'en'
    _cache = {}
    
    def __init__(self,plugin):
        self.keyword = plugin['keyword']
        self.bash_command = plugin['command']
        self.example = plugin['example']
        self.tstyle  = GtkTextStyle()
        self._desc    = plugin['desc']
        
        self._lowerKeyword = self.keyword.lower()
        
        CommandPlugin._cache[self._lowerKeyword] = self
    
    def toBash(self):
        return self.bash_command
    
    @staticmethod
    def lookup(keyword):
        try:
            return CommandPlugin._cache[keyword.lower()]
        except (KeyError,AttributeError):
            return None
    
    def __lt__(self,otherPlugin):
        return self._lowerKeyword < otherPlugin._lowerKeyword
    
    def _getDesc(self):
        try:
            return self._desc[CommandPlugin.lang]
        except KeyError:
            return self.desc['en']
    
    def _setDesc(self,value):
        self._desc = value
    
    def __contains__(self,item):
        if isinstance(item,String):
            return self._lowerKeyword == item.lower()
        else:
            return item == self
    
    def __str__(self):
        return self.__unicode__().encode('utf-8')
    
    def __unicode__(self):
        return u'<plugin %s>' % self.keyword.decode('utf-8')
    
    desc = property(_getDesc,_setDesc)


def get_tag_bounds(iter,tag,word_length=None):
    if not iter.has_tag(tag):
        return None
    
    startIter=iter.copy()
    endIter=iter.copy()
    
    endIter.forward_to_tag_toggle(tag)
    
    
    if not startIter.begins_tag(tag):
        startIter.backward_to_tag_toggle(tag)
    
    """
    An example about how this works
    
    1 234567 89
    a bbbbbb cc
          x
    
    word_length = 2 # length of bb word
    
    iterOffset = iter.getOffset() #6
    
    startIter = iter.copy().backward_to_tag_toggle(b)
    
    startOffset = startIter.getOffset()  #2
    endOffset = endIter.getOffset()      #8
    
    (iterOffset - startOffset) == 4
    
    int(4 / word_length) * word_length == 4 # so the word start at startOffset+4
    """
    
    if word_length:
        iterOffset = iter.get_offset()
        startOffset = startIter.get_offset()
        gapOffset = startOffset
        startOffset = int((iterOffset - startOffset) / word_length) * word_length
        startIter = iter.get_buffer().get_iter_at_offset(startOffset + gapOffset)
        endIter = startIter.copy()
        endIter.forward_chars(word_length)
    
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

def get_color_tag_name(color,weight,background=False):
    return '%s_%s_%s' % ('bg' if background else 'fg',weight,color)


class GtkTextStyle(TextStyle):
    
    @staticmethod
    def update_gtk_tag(tag,tstyle):
        if tstyle.invert and not tstyle.is_inconsistent('invert'):
            tag.invert = True;
        
        for attrName in (GtkTextStyle.BACKGROUND,GtkTextStyle.FOREGROUND):
            
            if tstyle.is_inconsistent(attrName):
                continue
            
            color = getattr(tstyle,attrName)
            
            attrTag = 'background' if attrName==GtkTextStyle.BACKGROUND else 'foreground'
            if tstyle.invert==True: # True to check for inconsistencies too
                attrTag = 'foreground' if attrTag=='background' else 'background'
            
            setattr(tag,'_%sColor' % attrTag, color)
            
            if color == None:
                tag.set_property(attrTag+'-set',False)
            else:
                
                if attrTag == 'foreground':
                    
                    if tstyle.weight == GtkTextStyle.WEIGHT_BOLD:
                        
                        if color.index<8:
                            rgb = COLORS[color.index+8].rgb
                        else:
                            rgb = lighter_rgb(color.rgb)
                        
                    elif tstyle.weight == GtkTextStyle.WEIGHT_FAINT:
                        rgb = darker_rgb(color.rgb)
                    else: # normal or inconsistent
                        rgb = color.rgb
                    
                    hexcolor = rgb2hex(rgb)
                else:
                    hexcolor = color.hexcolor
                
                tag.set_property(attrTag,hexcolor)
                tag.set_property(attrTag+'-set',True)
        
        for attrName in (GtkTextStyle.UNDERLINE,GtkTextStyle.STRIKETHROUGH):
            
            if tstyle.is_inconsistent(attrName):
                continue
            
            value = getattr(tstyle,attrName)
            
            tag.set_property(attrName,value)
            tag.set_property(attrName+'-set',value)
        
        if not tstyle.is_inconsistent('weight'):
            weight = tstyle.weight
            
            if weight == GtkTextStyle.WEIGHT_FAINT:
                pangoProp = pango.WEIGHT_ULTRALIGHT
            elif weight == GtkTextStyle.WEIGHT_BOLD:
                pangoProp = pango.WEIGHT_BOLD
            elif weight == GtkTextStyle.WEIGHT_NORMAL:
                pangoProp = pango.WEIGHT_NORMAL
            
            tag.set_property('weight',pangoProp)
            tag.set_property('weight-set',True)
        
        return tag
    
    
    @staticmethod
    def to_gtk_tags(tstyle,tag_table):
        
        tags=[]
        
        for attrName in (GtkTextStyle.BACKGROUND,GtkTextStyle.FOREGROUND):
            
            color = getattr(tstyle,attrName)
            
            if not color or tstyle.is_inconsistent(attrName):
                continue
            
            attrTag = 'background' if attrName==GtkTextStyle.BACKGROUND else 'foreground'
            if tstyle.invert==True: # True to check for inconsistencies too
                attrTag = 'foreground' if attrTag=='background' else 'background'
            
            weight = tstyle.weight if not tstyle.is_inconsistent('weight') else GtkTextStyle.WEIGHT_NORMAL
            
            tag = tag_table.lookup(get_color_tag_name(color,weight,attrTag=='background'))
            tags.append(tag)
            
            setattr(tag,'_%sColor' % attrTag, color)
        
        for attrName in (GtkTextStyle.UNDERLINE,GtkTextStyle.STRIKETHROUGH):
            
            value = getattr(tstyle,attrName)
            
            if not value or tstyle.is_inconsistent(attrName):
                continue
            
            tag = tag_table.lookup(attrName)
            tag.set_property(attrName,value)
            tags.append(tag)
        
        if not tstyle.is_inconsistent('weight'):
            weight = tstyle.weight
            tagName = None
            
            if weight == GtkTextStyle.WEIGHT_FAINT:
                tagName = 'weight_faint'
            elif weight == GtkTextStyle.WEIGHT_BOLD:
                tagName = 'weight_bold'
            elif weight == GtkTextStyle.WEIGHT_NORMAL:
                tagName = 'weight_normal'
            
            if tagName:
                tags.append(tag_table.lookup(tagName))
        
        if tstyle.invert and not tstyle.is_inconsistent('invert'):
            tags.append(tag_table.lookup('invert'))
        
        logging.debug('to_gtk_tags() %r',[tag.get_property('name') for tag in tags])
        
        return tags
    
    @staticmethod
    def from_gtk_tag(tag):
        
        tstyle = GtkTextStyle()
        tstyle.invert = tag.get_property('name') == 'invert'
        
        if tag.get_property('background-set'):
            attrName = 'foreground' if tstyle.invert else 'background'
            color = getattr(tag,'_%sColor' % attrName,None)
            setattr(tstyle,attrName,color)
        
        if tag.get_property('foreground-set'):
            attrName = 'background' if tstyle.invert else 'foreground'
            color = getattr(tag,'_%sColor' % attrName,None)
            setattr(tstyle,attrName,color)
        
        if tag.get_property('underline-set'):
            tstyle.underline = tag.get_property('underline')
        
        if tag.get_property('strikethrough-set'):
            tstyle.strikethrough = tag.get_property('strikethrough')
            
        if tag.get_property('weight-set'):
            
            pangoWeight = tag.get_property('weight')
            
            if pangoWeight == pango.WEIGHT_BOLD:
                tstyle.weight = GtkTextStyle.WEIGHT_BOLD
            elif pangoWeight == pango.WEIGHT_ULTRALIGHT:
                tstyle.weight = GtkTextStyle.WEIGHT_FAINT
            elif pangoWeight == pango.WEIGHT_NORMAL:
                tstyle.weight = GtkTextStyle.WEIGHT_NORMAL
        
        return tstyle
       
    @staticmethod
    def from_gtk_selection(startIter,endIter):
        
        text_styles = []
        
        currentIter = startIter.copy()
        while not currentIter.equal(endIter):
            
            singleCharStyles = []
            
            for tag in currentIter.get_tags():
                singleCharStyles.append(GtkTextStyle.from_gtk_tag(tag))
            
            text_styles.append(GtkTextStyle.merge_styles(singleCharStyles,fill_empty_properties=True))
            
            currentIter.forward_char()
        
        if len(text_styles) > 1:
            logging.debug('going to merge styles %r',text_styles)
        tstyle = GtkTextStyle.merge_styles(text_styles)
        if len(text_styles) > 1:
            logging.debug('styles merged as %s',tstyle)
        
        if tstyle.invert==True:
            tstyle.background, tstyle.foreground = tstyle.foreground, tstyle.background
            logging.debug('styles bg/fg inverted')
        
        return tstyle
        

class BashColorPicker(ColorPicker):
    def __init__(self,bash_colors):
        
        if bash_colors == ANSI_COLORS:
            num_columns = 8
            colors = [x.rgb for x in bash_colors[:num_columns]]
            grayscaleColors = None
            reorder = False
            
            cells_width = cells_height = 30
            width = cells_width*num_columns
            height = cells_width*2
            
        else:
            num_columns = len(GRAYSCALE)
            # visible colors are all but grayscale colors (not counting white and black)
            colors = [x.rgb for x in bash_colors[:-(len(GRAYSCALE)-2)]]
            grayscaleColors = [x.rgb for x in GRAYSCALE]
            reorder = True
            
            width = 510
            num_rows = int(ceil(len(bash_colors)/float(num_columns)))
            cells_width = int(ceil(width/float(num_columns)))
            height = 170-cells_width
            cells_height = int(height/num_rows)
        
        self.bash_colors = bash_colors
        
        super(BashColorPicker,self).__init__(colors,grayscaleColors,{
            'num_columns':num_columns,
            'cells_width':cells_width,
            'cells_height':cells_height,
            'previewer_width':cells_width,
            'previewer_height':cells_width,
            'reorder':reorder
        })
        
        self.set_size_request(width,height+10)
        
        self._brightness = None
    
    def _get_rgb_for_brightness(self,rgb,idx,colorWidget):
        if colorWidget==self.fgColor and idx!=None and idx<8:
            if self._brightness:
                return self.bash_colors[idx+8].rgb
            else:
                return self.bash_colors[idx].rgb
        else:
            return rgb
    
    def on_mouseOver_palette(self,palette,ev,rgb,paletteIndex,colorWidget):
        if palette == self.grayscalePalette:
            index = GRAYSCALE[paletteIndex].index
        else:
            if paletteIndex >= len(self.bash_colors):
                index = WHITE.index
                rgb = WHITE.rgb
            else:
                index = paletteIndex
        
        colorWidget.set_color(self._get_rgb_for_brightness(rgb,index,colorWidget),index)
    
    def _get_bashColor(self,background=True):
        col_data = getattr(self,'get_%s' % ('background' if background else 'foreground'))()
        if col_data['rgb'] == ColorWidget.UNKNOWN:
            return GtkTextStyle.INCONSISTENT
        elif col_data['data'] is None:
            return None
        else:
            return self.bash_colors[col_data['data']]
    
    def get_bashColor_background(self):
        return self._get_bashColor(background=True)
    
    def get_bashColor_foreground(self):
        return self._get_bashColor(background=False)
    
    def set_bg_fg(self,bgBashColor,fgBashColor):
        
        for bashColor,method in ((bgBashColor,'set_background'),(fgBashColor,'set_foreground')):
            rgb,idx = ColorWidget.UNKNOWN,None
            
            if bashColor != GtkTextStyle.INCONSISTENT:
                if bashColor is None:
                    rgb = None
                else:
                    rgb = bashColor.rgb
                    idx = bashColor.index
            
            if bashColor == fgBashColor and self._brightness:
                rgb = self._get_rgb_for_brightness(rgb,idx,(self.fgColor if bashColor==fgBashColor else self.bgColor))
            
            getattr(super(self.__class__,self),method)(rgb,idx)
    
    def set_brightness(self,weight):
        self._brightness = weight
        
        if weight == GtkTextStyle.WEIGHT_BOLD:
            # the first 8 colors has always as bold counterpart the next 8 colors, whatever they are
            if self.selecting_foreground:
                func = lambda rgb,i: (i!=None and i<8) and tuple(x/255. for x in COLORS[i+8].rgb) or rgb
            else:
                func = None
            self.palette.set_color_mask(func)
            """
            if self.grayscalePalette:
                self.grayscalePalette.set_color_mask(lambda rgb,i: lighter_rgb(rgb))
            """
        else:
            self.palette.set_color_mask()
            if self.grayscalePalette:
                self.grayscalePalette.set_color_mask()
            
            self._brightness = None
        
        for colorWidget in (self.bgColor,self.fgColor):
            rgb,data = colorWidget.rgb,colorWidget.data
            rgb = self._get_rgb_for_brightness(rgb,data,colorWidget)
            colorWidget.set_color(rgb,data,emitSignal=False)
        
        """
        elif weight == GtkTextStyle.WEIGHT_FAINT:
            if self.bash_colors == ANSI_COLORS:
                self.palette.set_color_mask(lambda rgb,i: i<8 and darker_rgb(rgb) or rgb)
            
            if self.grayscalePalette:
                self.grayscalePalette.set_color_mask(lambda rgb,i: darker_rgb(rgb))
            
        """ 
    
    def get_brightness(self):
        return self._brightness

class Styling(gtk.VBox):
    __gsignals__ = {
        'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                ()),
        'activate' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                (gobject.TYPE_PYOBJECT,)),
    }
    
    class StylesContainer(gtk.Frame):
        __gsignals__ = {
            'style-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    ()),
        }
        
        def __init__(self):
            gobject.GObject.__init__(self)
            
            self._can_send_signal = True
            
            self.set_label(_('OPTIONS'))
            self.set_border_width(1)
            
            rows=3
            columns=2
            
            tableStyles=gtk.Table(rows=rows,columns=columns,homogeneous=True)
            tableStyles.set_row_spacings(1)
            tableStyles.set_col_spacings(1)
            
            self.underlineBtn=gtk.CheckButton(_('UNDERLINE'))
            self.strikethroughBtn=gtk.CheckButton(_('STRIKETHROUGH'))
            self.invertBtn=gtk.CheckButton(_('INVERT'))
            
            self.normalRadio=gtk.RadioButton(None,_('TEXT_NORMAL'))
            self.boldRadio=gtk.RadioButton(self.normalRadio,_('TEXT_BOLD'))
            self.faintRadio=gtk.RadioButton(self.normalRadio,_('TEXT_FAINT'))
            
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
            tstyle = GtkTextStyle()
            
            if self.weightRadioInconsistent.get_active():
                tstyle.set_inconsistent('weight')
            elif self.boldRadio.get_active():
                tstyle.weight = GtkTextStyle.WEIGHT_BOLD
            elif self.faintRadio.get_active():
                tstyle.weight = GtkTextStyle.WEIGHT_FAINT
            else:
                tstyle.weight = GtkTextStyle.WEIGHT_NORMAL
            
            for attrName in ('underline','strikethrough','invert'):
                toggleBtn = getattr(self,attrName+'Btn')
                if toggleBtn.get_inconsistent():
                    tstyle.set_inconsistent(attrName)
                else:
                    setattr(tstyle,attrName,toggleBtn.get_active())
            
            return tstyle
        
        def set_styles(self,tstyle):
            self._can_send_signals=False
            
            for attrName in ('underline','strikethrough','invert'):
                toggleBtn = getattr(self,attrName+'Btn')
                if tstyle.is_inconsistent(attrName):
                    toggleBtn.set_inconsistent(True)
                else:
                    toggleBtn.set_inconsistent(False)
                    toggleBtn.set_active(getattr(tstyle,attrName) == True)
            
            if tstyle.is_inconsistent('weight'):
                self.weightRadioInconsistent.set_active(True)
            else:
                self.normalRadio.set_active(tstyle.weight == GtkTextStyle.WEIGHT_NORMAL)
                self.boldRadio.set_active(tstyle.weight == GtkTextStyle.WEIGHT_BOLD)
                self.faintRadio.set_active(tstyle.weight == GtkTextStyle.WEIGHT_FAINT)
            
            self._can_send_signals=True
    
    gobject.type_register(StylesContainer)
    
    def __init__(self,*args):
        gobject.GObject.__init__(self)
        
        self._is_command_active = True
        
        boxColorsAndStyle=gtk.VBox()
        
        self.gtkCommandsBox=GtkCommandsBox()
        self.gtkCommandsBox.set_active_command(COMMANDS[0])
        self.gtkCommandsBox.connect('command-changed',self._on_command_changed)
        self.gtkCommandsBox.connect('activate',self._on_command_requested)
        self.gtkCommandsBox.show()
        boxColorsAndStyle.pack_start(self.gtkCommandsBox,0,0,3)
        
        hbox=gtk.HBox()
        
        ### TABLE STYLES ###
        
        self.frameStyles=Styling.StylesContainer()
        self.frameStyles.connect('style-changed', lambda *args: self._on_style_changed())
        self.frameStyles.show()
        
        ### END TABLE STYLES ###
        
        hbox.pack_start(self.frameStyles,0,0,2)
        
        ### COLORS ###
        
        self.pickerBox = gtk.VBox()
        self.picker = None
        self.restore_picker()
        self.pickerBox.show()
        
        ### END colors ###
        
        hbox.pack_start(self.pickerBox,1,1,2)
        hbox.show()
        
        boxColorsAndStyle.pack_start(hbox,0,0,2)
        
        boxColorsAndStyle.show()
        self.pack_start(boxColorsAndStyle,1,1,0)
        
        self.reset()
    
    def restore_picker(self):
        brightness = None
        bg,fg = None,None
        if self.picker:
            brightness = self.picker.get_brightness()
            bg,fg = self.picker.get_bashColor_background(),self.picker.get_bashColor_foreground()
            self.pickerBox.remove(self.picker)
        
        self.picker = BashColorPicker(COLORS)
        self.picker.bgColor.connect('color-changed', lambda *args: self._on_style_changed())
        self.picker.fgColor.connect('color-changed', lambda *args: self._on_style_changed())
        
        if brightness:
            self.picker.set_brightness(brightness)
        
        self.picker.show()
        
        self.pickerBox.pack_start(self.picker,0,0,2)
        
        if bg or fg:
            if bg and not bg in COLORS:
                bg = None
            if fg and not fg in COLORS:
                fg = None
            
            self.picker.set_bg_fg(bg,fg)
        
    
    def reset(self):
        self.set_current_command(self.get_current_command())
        self.set_styling(GtkTextStyle()) 
        self.emit('changed')
    
    def _export_current_style(self):
        tstyle = self.frameStyles.get_styles()
        tstyle.background = self.picker.get_bashColor_background()
        tstyle.foreground = self.picker.get_bashColor_foreground()
        
        return tstyle
    
    def _on_style_changed(self):
        tstyle = self._export_current_style()
        
        cmdKeyword = ''
        if self.gtkCommandsBox.is_sensitive():
            self.gtkCommandsBox.get_active_command().tstyle = tstyle
            cmdKeyword = self.gtkCommandsBox.get_active_command().keyword
        
        logging.debug('class %s, style changed (cmd=%s) %s',self.__class__.__name__,cmdKeyword if cmdKeyword else 'None',tstyle)
        
        self.picker.set_brightness(tstyle.weight)
        
        self.emit('changed')
    
    def get_styling(self):
        return self._export_current_style()
    
    def set_styling(self,tstyle):
        self.picker.set_bg_fg(tstyle.background,tstyle.foreground)
        self.frameStyles.set_styles(tstyle)
        self._on_style_changed()
    
    def _on_command_requested(self,widget,key):
        self.emit('activate',key)
    
    def _on_command_changed(self,keywordBox,command):
        logging.debug('command changed %s (style is %s)',command,command.tstyle)
        
        tstyle = command.tstyle
        self.picker.set_bg_fg(tstyle.background,tstyle.foreground)
        self.frameStyles.set_styles(tstyle)
    
    def set_current_command(self,command):
        self.gtkCommandsBox.set_active_command(command)
    
    def get_current_command(self):
        return self.gtkCommandsBox.get_active_command()
    
    def activate_command(self):
        self._is_command_active = True
        self.frameStyles.set_sensitive(True)
        self.gtkCommandsBox.set_sensitive(True)
        self._on_command_changed(self.gtkCommandsBox,self.gtkCommandsBox.get_active_command())
    
    def is_command_active(self):
        return self._is_command_active
    
    def deactivate_command(self,keepOnlyColors = False):
        self._is_command_active = False
        self.gtkCommandsBox.set_sensitive(False)
        
        tstyle = GtkTextStyle()
        tstyle.set_inconsistent('background')
        tstyle.set_inconsistent('foreground')
        
        self.picker.set_bg_fg(tstyle.background,tstyle.foreground)
        self.frameStyles.set_styles(tstyle)
        
        if keepOnlyColors:
            self.frameStyles.set_sensitive(False)
    
    def __str__(self):
        return self.__unicode__().encode('utf-8')
    
    def __unicode__(self):
        return u'<type Styling>'+repr(self.get_styling(self.get_current_command())).decode('utf-8')+u'</type>'

gobject.type_register(Styling)


class FormatPromptTextView(EasySelectionTextview):
    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                ()),
        'cursor-moved': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,())
        
    }
    
    DEFAULT_BACKGROUND=(0,0,0)
    DEFAULT_FOREGROUND=(255,255,255)
    
    def __init__(self,*args):
        super(FormatPromptTextView,self).__init__(*args)
        self.modify_font(pango.FontDescription('Monospace 11'))
        self.set_property('left-margin',2) 
        self.modify_base(gtk.STATE_NORMAL,gtk.gdk.color_parse('#000000'))
        self.modify_text(gtk.STATE_NORMAL,gtk.gdk.color_parse('#FFFFFF'))
        self.buffer=self.get_buffer()
        
        table=self.buffer.get_tag_table()
        
        for color in TERM_COLORS:
            
            for weight in (
                GtkTextStyle.WEIGHT_FAINT,
                GtkTextStyle.WEIGHT_NORMAL,
                GtkTextStyle.WEIGHT_BOLD
                ):
                
                if weight == GtkTextStyle.WEIGHT_BOLD:
                    if color.index<8:
                        rgb = TERM_COLORS[color.index+8].rgb
                    else:
                        rgb = lighter_rgb(color.rgb)
                elif weight ==GtkTextStyle.WEIGHT_FAINT:
                    rgb = darker_rgb(color.rgb)
                else:
                    rgb = color.rgb
                
                hexCode = rgb2hex(rgb)
                
                tag=gtk.TextTag(get_color_tag_name(color,weight,background=True))
                tag.set_property('background',hexCode)
                table.add(tag)
                tag._backgroundColor = color
                
                tag=gtk.TextTag(get_color_tag_name(color,weight,background=False))
                tag.set_property('foreground',hexCode)
                table.add(tag)
                tag._foregroundColor = color
        
        for weight in (
                ('faint',pango.WEIGHT_ULTRALIGHT),
                ('normal',pango.WEIGHT_NORMAL),
                ('bold',pango.WEIGHT_BOLD)
                 ):
            tag=gtk.TextTag('weight_'+weight[0])
            tag.set_property('weight',weight[1])
            table.add(tag)
        
        for command in COMMANDS:
            tag=gtk.TextTag(command.keyword)
            tag._foregroundColor = None
            tag._backgroundColor = None
            table.add(tag)
        
        tag=gtk.TextTag('underline')
        tag.set_property('underline',True)
        table.add(tag)
        
        tag=gtk.TextTag('strikethrough')
        tag.set_property('strikethrough',True)
        table.add(tag)
            
        tag=gtk.TextTag('invert')
        table.add(tag)
        
        self._last_pos = 0
        self._selected_keyword = None
        
        self.id_delete_range = self.buffer.connect('delete-range',self._on_delete_range)
        
        self._id_move_cursor = self.buffer.connect_after('notify::cursor-position',self._on_cursor_position_changed)
        self._id_selection_change = self.connect('selection-change',self._on_selection_changed)
        
        self.id_buf_changed = self.buffer.connect('changed',self._on_content_change)
    
    
    def _on_delete_range(self,buffer,startIter,endIter):
        res = self.get_command_at_iter(startIter)
        if res:
            buffer.handler_block(self.id_delete_range)
            buffer.delete(res['start'],res['end'])
            buffer.handler_unblock(self.id_delete_range)
            
            buffer.emit_stop_by_name('delete-range')
    
    def change_base_colors(self,tstyle):
        if not tstyle.is_inconsistent('background'):
            if tstyle.background:
                self.modify_base(gtk.STATE_NORMAL,gtk.gdk.color_parse(tstyle.background.hexcolor))
            else:
                self.modify_base(gtk.STATE_NORMAL,gtk.gdk.color_parse(rgb2hex(FormatPromptTextView.DEFAULT_BACKGROUND)))
        
        if not tstyle.is_inconsistent('foreground'):
            if tstyle.foreground:
                self.modify_text(gtk.STATE_NORMAL,gtk.gdk.color_parse(tstyle.foreground.hexcolor))
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
    
    def _on_content_change(self,buffer,*args):
        text = buffer.get_text(*buffer.get_bounds())
        
        for command in COMMANDS:
            positions = self._find_keyword_pos(text,command.keyword)
            
            for start,end in positions:
                startIter = buffer.get_iter_at_offset(start)
                endIter = buffer.get_iter_at_offset(end)
                
                buffer.remove_all_tags(startIter,endIter)
                buffer.apply_tag_by_name(command.keyword,startIter,endIter)
        
        self.emit('changed')
    
    def change_command_appearance(self,command,styleObj):
        tagTable=self.buffer.get_tag_table()
        tag=tagTable.lookup(command.keyword)
        
        GtkTextStyle.update_gtk_tag(tag,command.tstyle)
    
    def change_selection_appearance(self,tstyle,startIter,endIter):
        tag_table = self.buffer.get_tag_table()
        
        def get_inconsistent_tags(tstyle,tag_table):
            tags = []
            if tstyle.is_inconsistent('background'):
                for color in COLORS:
                    for weight in (
                        GtkTextStyle.WEIGHT_FAINT,
                        GtkTextStyle.WEIGHT_NORMAL,
                        GtkTextStyle.WEIGHT_BOLD
                        ):
                        tags.append(tag_table.lookup(get_color_tag_name(color,weight,background=True)))
            
            if tstyle.is_inconsistent('foreground'):
                for color in COLORS:
                    for weight in (
                        GtkTextStyle.WEIGHT_FAINT,
                        GtkTextStyle.WEIGHT_NORMAL,
                        GtkTextStyle.WEIGHT_BOLD
                        ):
                        tags.append(tag_table.lookup(get_color_tag_name(color,weight,background=False)))
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
        
        tags = GtkTextStyle.to_gtk_tags(tstyle,tag_table)
        for tag in tags:
            self.buffer.apply_tag(tag,startIter,endIter)
    
    def reset_colors(self):
        self.buffer.handler_block(self.id_buf_changed)
        self.buffer.remove_all_tags(*self.buffer.get_bounds())
        self.buffer.handler_unblock(self.id_buf_changed)
        self.buffer.emit('changed')
    
    def _on_cursor_position_changed(self,buffer,position):
        # XXX position is a GParamInt : how can you access the value ?
        current_pos = buffer.get_property("cursor-position")
        
        if current_pos != self._last_pos:
            self._last_pos = current_pos
            if not self.selecting():
                self._try_to_select_keyword(self.buffer,True)
                self.emit('cursor-moved')
    
    def _on_selection_changed(self,widget,startIter,endIter,selectingDirection):
        self._try_to_select_keyword(self.buffer,selectingDirection)
    
    def _try_to_select_keyword(self,buffer,move_left_to_right):
        
        self.buffer.disconnect(self._id_move_cursor)
        self.disconnect(self._id_selection_change)
        
        selectedKeyword = None
        current_iter = buffer.get_iter_at_mark(buffer.get_insert())
        startIter,endIter = None,None
        
        try:
            startIter,endIter = buffer.get_selection_bounds()
        except ValueError,e:
            startIter = buffer.get_iter_at_mark(buffer.get_insert())
        
        tag_table = buffer.get_tag_table()
        for command in COMMANDS:
            tag = tag_table.lookup(command.keyword)
            iter = None
            
            if endIter:
                iter = has_tag_in_range(tag,startIter,endIter)
            elif not current_iter.begins_tag(tag) and current_iter.has_tag(tag):
                iter = current_iter
            
            if not iter: continue
            
            # there could be the same keyword more than once, ensure we stop at the first one
            startIter,endIter = get_tag_bounds(iter,tag,len(command.keyword))
            
            if move_left_to_right > 0:
                buffer.select_range(startIter,endIter)
            else:
                buffer.select_range(endIter,startIter)
            
            selectedKeyword = command.keyword
            
            break
        
        
        self._selected_keyword = selectedKeyword
        
        self._id_move_cursor = self.buffer.connect('notify::cursor-position',self._on_cursor_position_changed)
        self._id_selection_change = self.connect('selection-change',self._on_selection_changed)
        
        return selectedKeyword
    
    
    @property
    def selected_keyword(self):
        return self._selected_keyword
    
    def get_command_at_iter(self,current_iter):
        
        res = None
        
        for tag in current_iter.get_tags():
            tagName = tag.get_property('name')
            command = CommandPlugin.lookup(tagName)
            if command:
                
                startIter,endIter = get_tag_bounds(current_iter,tag,len(command.keyword))
                
                res = {
                    'start' : startIter,
                    'end'   : endIter,
                    'command' : command
                }
                
                break
        
        return res
    

class GtkCommandsBox(gtk.VBox):
    __gsignals__ = {
        'command-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,)),
        'activate' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,))
    }
    
    def __init__(self):
        gtk.VBox.__init__(self)
        
        labelHelp=gtk.Label(_("HELP_TEXT"))
        labelHelp.show()
        align=gtk.Alignment(0,0,0,0)
        align.add(labelHelp)
        align.show()
        self.pack_start(align,1,1,0)
        
        mainBox=gtk.HBox()
        
        self.commandIndex = {}
        
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
        
        liststore = gtk.ListStore(gobject.TYPE_PYOBJECT,gobject.TYPE_STRING)
        idx = 0
        for command in COMMANDS:
            liststore.append((command,command.keyword))
            self.commandIndex[command] = idx
            idx += 1
        
        combobox = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)
        combobox.set_wrap_width(2)
        
        combobox.connect('changed',self._on_combobox_changed)
        
        self.combobox=combobox
        
        combobox.show()
        
        #mainBox.pack_start(combobox,0,0,2)
        tmpHbox.pack_start(combobox,0,0,2)
        
        insertBtn=gtk.Button(_('INSERT'))
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
        
        combobox.set_active(0)
    
    def _on_insertBtn_clicked(self,*args):
        self.emit('activate',self.get_active_command())
    
    def _on_combobox_changed(self,combobox):
        command = self.get_active_command()
        
        ### XXX follows an ugly hack to have a fixed height help zone
        ### It needs to be fixed: the sooner the better
        
        exampleText = command.example
        exampleLines = 1 + exampleText.count('\n')
        if exampleLines < 3:
            exampleText+= '\n'*(3-exampleLines)
        
        self.descLabel.set_markup(command.desc)
        self.exampleLabel.set_markup('<span background="black" foreground="white">'+exampleText+"</span>")
        
        self.emit('command-changed',command)
    
    def get_active_command(self):
        model = self.combobox.get_model()
        index = self.combobox.get_active()
        if index < 0: return None
        else: return model[index][0]
    
    def set_active_command(self,command):
        index = self.commandIndex[command]
        self.combobox.set_active(index)
    
    def is_sensitive(self):
        return self.get_property('sensitive')
    

gobject.type_register(GtkCommandsBox)

class Window(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_size_request(770,700)
        self.set_border_width(5)
        self.connect('delete-event',self.on_delete_event)
        
        vbox=gtk.VBox()
        
        menu_bar_ui = \
        """
        <ui>
            <menubar name="MenuBar">
                <menu action="File">
                    <menuitem action="Colors"/>
                    <menuitem action="Quit"/>
                </menu>
                <menu action="About" name="AboutMenu">
                    <menuitem action="Version"/>
                </menu>
            </menubar>
        </ui>
        """
        action_group = gtk.ActionGroup("MenuBarActionGroup")
        action_group.add_actions([
            ("File", None, "_File"),
            ("About", None, "_About"),
            ("Quit", gtk.STOCK_QUIT, "_Quit", None, "Quit application", gtk.mainquit),
            ("Version", gtk.STOCK_ABOUT, "_Version", None, "Show current version", self.show_about_dialog)
        ])
        
        action_group.add_toggle_actions([
            ("Colors", None, "_256 colors",None,None,self.on_menu_colors_toggled)
        ])
        
        ui_manager = gtk.UIManager()
        accel_group = ui_manager.get_accel_group()
        self.add_accel_group(accel_group)
        ui_manager.insert_action_group(action_group, 0)
        ui_manager.add_ui_from_string(menu_bar_ui)
        
        menu_bar = ui_manager.get_widget("/MenuBar")
        menu_bar.show()
        vbox.pack_start(menu_bar,0,0,0)
        
        self.ignoreStyleChange = False
        
        topBox=gtk.VBox()
        
        self.stylingBox=Styling()
        self.stylingBox.connect('changed',self.on_style_changed)
        self.stylingBox.connect('activate',self.on_command_requested)
        self.stylingBox.show()
        topBox.pack_start(self.stylingBox,0,0,2)
        
        topBox.show()
        vbox.pack_start(topBox,0,0,2)
        
        self.baseColorsCheckBtn=gtk.CheckButton(_('CLICK_TO_USE_COLORS_FOR_BACKGROUND_FOREGROUND'))
        self.baseColorsCheckBtn.connect('toggled',self.on_checkBtn_baseColors_clicked)
        self.baseColorsCheckBtn.show()
        vbox.pack_start(self.baseColorsCheckBtn,0,0,2)
        
        txtBox=gtk.HBox()
        
        self.textview=FormatPromptTextView()
        self.fpt_sel_changed_id=self.textview.connect('selection-end',self.on_formatPrompt_selection_end)
        #self.textview.connect('cursor-moved',self.on_formatPrompt_selection_end)
        
        self.fpt_changed_id=self.textview.connect('changed',self.convert_to_bash_and_preview)
        self.textview.show()
        
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.textview)
        sw.show()
        
        txtBox.pack_start(sw,1,1,2)
        
        tmpVBox = gtk.VBox()
        btn=gtk.Button(_('IMPORT'))
        btn.show()
        btn.connect('clicked', self.on_importBtn_clicked)
        tmpVBox.pack_start(btn,0,0,0)
        tmpVBox.show()
        
        txtBox.pack_start(tmpVBox,0,0,2)
        txtBox.show()
        
        vbox.pack_start(txtBox,0,0,2)
        
        codePreviewBox=gtk.HBox()
        
        btn=gtk.Button(_('RESET'))
        btn.show()
        btn.connect('clicked', lambda *x: self.stylingBox.reset())
        btn.connect('clicked', lambda *x: self.textview.reset_colors())
        codePreviewBox.pack_start(btn,0,0,2)
        
        label=gtk.Label()
        label.set_markup(_('GENERATED_CODE'));
        codePreviewBox.pack_start(label,0,0,2)
        self.codePreview=gtk.Label()
        self.codePreview.set_selectable(True)
        codePreviewBox.pack_start(self.codePreview,0,0,2)
        codePreviewBox.show_all()
        vbox.pack_start(codePreviewBox,0,0,2)
        
        self.term=self.create_terminal()
        self.term.show()
        vbox.pack_start(self.term,1,1,2)
        
        btn=gtk.Button(_('SAVE'))
        btn.connect('clicked', lambda *x: self.write_on_disk(self.convert_to_bash()))
        btn.show()
        vbox.pack_start(btn,0,0,2)
        
        vbox.show()
        self.add(vbox)
        
        txtBox.set_size_request(-1,self.textview.get_line_yrange(self.textview.buffer.get_start_iter())[1]*3)
        
        self.get_system_prompt(self.set_prompt_from_bash_string)
        
        self.show()
    
    def on_menu_colors_toggled(self,menuItem):
        global COLORS
        if menuItem.get_active():
            COLORS = TERM_COLORS
        else:
            COLORS = ANSI_COLORS
        
        self.stylingBox.restore_picker()
        self.on_style_changed(self.stylingBox)
    
    def show_about_dialog(self,menuItem):
        dialog = gtk.AboutDialog()
        dialog.set_modal(True)
        dialog.set_transient_for(self)
        dialog.set_destroy_with_parent(True)
        dialog.set_name(__program_name__)
        dialog.set_version(__version__)
        dialog.set_copyright(__copyright__)
        dialog.set_license(file(os.path.join(os.path.dirname(os.path.realpath(__file__)),'LICENSE')).read())
        dialog.set_website(__website__)
        dialog.run()
        dialog.destroy()
    
    def get_system_prompt(self,callback):
        import vte
        
        v = vte.Terminal()
        v.fork_command('bash')
        v.feed_child('echo $(expr 1 + 1)${PS1}2\n')
        
        def on_content_changed(term):
            text= term.get_text(lambda *a: True)
            match = re.match(r'.*PS1.*2\n2(.+?)2\n',text,re.S)
            if match:
                callback(match.group(1))
        
        v.connect('contents-changed', on_content_changed)
    
    def set_prompt_from_bash_string(self,bash_code):
        self.textview.handler_block(self.fpt_sel_changed_id)
        self.textview.handler_block(self.fpt_changed_id)
        
        buffer = self.textview.buffer
        tag_table = buffer.get_tag_table()
        
        buffer.set_text('')
        
        parts = parse_bash_code(bash_code,COMMANDS,GtkTextStyle)
        
        for tstyle,text in parts:
            currentIter = buffer.get_end_iter()
            
            ### really inefficient
            for command in COMMANDS:
                if command.keyword in text:
                    self.stylingBox.set_current_command(command)
                    self.stylingBox.activate_command()
                    self.stylingBox.set_styling(tstyle)
            ### ###
            
            buffer.insert_with_tags(currentIter,text,*GtkTextStyle.to_gtk_tags(tstyle,tag_table))
        
        self.textview.handler_unblock(self.fpt_sel_changed_id)
        self.textview.handler_unblock(self.fpt_changed_id)
        
        self.textview.emit('changed')
    
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
        
        dialog.set_markup(_('ENTER_BASH_PROMPT_CODE'))
        entry = gtk.Entry()
        entry.connect("activate",on_entry_activated,dialog)
        
        dialog.vbox.pack_end(entry)
        
        dialog.show_all()
        
        response = dialog.run()
        
        text = entry.get_text()
        dialog.destroy()
        
        if response == gtk.RESPONSE_OK:
            self.set_prompt_from_bash_string(text)
        
    
    def on_checkBtn_baseColors_clicked(self,btn):
        if btn.get_active():
            self.stylingBox.deactivate_command(True)
        else:
            self.stylingBox.activate_command()
    
    def create_terminal(self):
        term=shell.ShellWidget()
        try:
            gdkColors = shell.getGnomeTerminalColors()
        except:
            gdkColors = {
                'foreground' : gtk.gdk.color_parse(WHITE.hexcolor),
                'background' : gtk.gdk.color_parse(BLACK.hexcolor),
                'palette'    : [gtk.gdk.color_parse(col.hexcolor) for col in ANSI_COLORS]
            }
        
        term.set_colors(gdkColors['foreground'],gdkColors['background'],gdkColors['palette'])
        term.set_size(term.get_column_count(),10)
        return term
    
    def on_formatPrompt_selection_end(self,textview,*args):
        if textview.selecting() or self.baseColorsCheckBtn.get_active():
            return
        
        logging.debug('Selection end')
        try:
            command = CommandPlugin.lookup(textview.selected_keyword)
            start,end = textview.buffer.get_selection_bounds()
            
            if command:
                logging.debug('Selected a keyword')
                self.stylingBox.activate_command()
                self.stylingBox.set_current_command(command)
            else:
                self.ignoreStyleChange = True
                
                self.stylingBox.deactivate_command()
                tstyle = GtkTextStyle.from_gtk_selection(start,end)
                logging.debug('Selected free text, style is %s',tstyle)
                self.stylingBox.set_styling(tstyle)
                
                self.ignoreStyleChange = False
            
        except ValueError, e:
            logging.debug('Empty selection, call stylingBox.activate_command()')
            self.stylingBox.activate_command()
    
    def convert_to_bash_and_preview(self,*args):
        converted=self.convert_to_bash()
        self.preview(converted)
        self.code_preview(converted)
    
    def preview(self,prompt_format):
        self.term.set_prompt(prompt_format)
        self.term.clear()
    
    def code_preview(self,prompt_format):
        self.codePreview.set_text(prompt_format.strip(u'\x00'))
    
    def on_command_requested(self,widget,command):
        self.textview.buffer.insert_at_cursor(command.keyword)
    
    def convert_to_bash(self):
        
        buffer=self.textview.buffer
        
        currentIter = buffer.get_start_iter()
        endIter = buffer.get_end_iter()
        
        prev_bash_code = r'\e[0m'
        
        result = []
        while not currentIter.equal(endIter):
            
            nextIter = currentIter.copy()
            nextIter.forward_char()
            
            tstyle = GtkTextStyle.from_gtk_selection(currentIter,nextIter)
            
            bash_code = GtkTextStyle.to_bash_code(tstyle)
            
            if bash_code == '': bash_code = r'\e[0m'
            
            if bash_code != prev_bash_code:
                
                result.append(bash_code)
                prev_bash_code = bash_code
            
            command_coords = self.textview.get_command_at_iter(currentIter)
            
            if command_coords:
                nextIter = command_coords['end']
                result.append(command_coords['command'].toBash())
            else:
                result.append(currentIter.get_char())
            
            currentIter = nextIter
        
        
        bash_ps1 = ''.join(result)
        
        idx = bash_ps1.rfind(r'\e[')
        if idx != -1 and not bash_ps1[idx:].startswith(r'\e[0m'):
            bash_ps1 += r'\e[0m'
        
        
        # XXX remove any ending backslash until I find the right way to handle it
        bash_ps1 = re.sub(r'\\+$','',bash_ps1)
        
        '''
        match = re.match(r'\\+$',bash_ps1)
        if match:
            numBackslashes = len(match.group(0))
            bash_ps1 = r'\\'*(numBackslashes-1) + '\\\\'
        '''
        
        # add \[ \] around escaping sequences to ensure aren't counted as printable characters
        bash_ps1 = re.sub(r'(\\e\[[0-9;]+?m)',r'\[\1\]',bash_ps1)
        
        # escape ' for using ps1 as a strong quoted string
        bash_ps1 = bash_ps1.replace("'","'\\''")
        
        logging.debug('Terminal prompt format: %r',bash_ps1)
        
        return bash_ps1
    
    def write_on_disk(self,line):
        bashrc_path = os.path.join(os.environ['HOME'],'.bashrc')
        
        bashrc = file(bashrc_path).read()
        
        startLine = '\n### START EASYPROMPT CODE DO NOT EDIT THIS LINE ###\n'
        endLine = '\n### END EASYPROMPT CODE DO NOT EDIT THIS LINE ###\n'
        ps1Line = "\nPS1='%s'\n" % line
        
        start_idx = bashrc.find(startLine)
        end_idx = -1
        
        if start_idx != -1:
            end_idx = bashrc.find(endLine,start_idx)
            
        if end_idx != -1:
            bashrc = bashrc[:start_idx] + startLine + ps1Line + endLine + bashrc[end_idx+len(endLine):]
        else:
            bashrc += startLine + ps1Line + endLine
        
        fp=file(bashrc_path,'wb')
        fp.write(bashrc)
        fp.close()

        dialog=gtk.MessageDialog(self,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_INFO,
            gtk.BUTTONS_OK,
            _('SAVE_MESSAGE')
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
    
    def _change_term_bg_fg(self,tstyle):
        hexBg = hexFg = None
        
        if not tstyle.background:
            hexBg = rgb2hex(FormatPromptTextView.DEFAULT_BACKGROUND)
        elif not tstyle.is_inconsistent('background'):
            hexBg = tstyle.background.hexcolor
        
        if not tstyle.foreground:
            hexFg = rgb2hex(FormatPromptTextView.DEFAULT_FOREGROUND)
        elif not tstyle.is_inconsistent('foreground'):
            hexFg = tstyle.foreground.hexcolor
        
        if hexBg:
            self.term.set_color_background(gtk.gdk.color_parse(hexBg))
        
        if hexFg:
            self.term.set_color_foreground(gtk.gdk.color_parse(hexFg))
    
    def on_style_changed(self,stylingObj):
        if self.ignoreStyleChange:
            return
        
        tstyle = stylingObj.get_styling()
        
        if self.baseColorsCheckBtn.get_active():
            # terminal bg/fg have changed
            self.textview.change_base_colors(tstyle)
            self._change_term_bg_fg(tstyle)
        elif stylingObj.is_command_active():
            # keyword style has changed
            command = self.stylingBox.get_current_command()
            self.textview.change_command_appearance(command,stylingObj)
        else:
            # free text style has changed
            start,end  = self.textview.buffer.get_selection_bounds()
            self.textview.change_selection_appearance(tstyle,start,end)
    
        self.convert_to_bash_and_preview()
    
    def on_delete_event(self,*args):
        gtk.main_quit()
        
    
    def run(self):
        gtk.main()


if __name__ == '__main__':
    import locale,shutil,json
    import i18n
    
    logLevel = logging.WARN
    if os.getenv('EASYPROMPT_DEBUG',False):
        logLevel = logging.DEBUG
    
    logging.basicConfig(format='%(levelname)s %(asctime)s %(message)s',level=logLevel)
    
    language_code,encoding = locale.getdefaultlocale()
    if language_code.upper() == 'C':
        language_code = 'en'
    
    simple_language_code = language_code.split('_')[0]
    if simple_language_code in i18n.AVAILABLE_LANGUAGES:
        i18n.CURRENT_LANG = simple_language_code
    
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    
    CONFIG_PATH  = os.path.join(os.getenv('HOME'),'.easyprompt')
    PLUGINS_PATH = os.path.join(CONFIG_PATH,'plugins')
    
    if not os.path.exists(PLUGINS_PATH):
        os.makedirs(PLUGINS_PATH)
        
        for fileName in os.listdir('plugins'):
            shutil.copy(os.path.join('plugins',fileName),PLUGINS_PATH)
    
    for fileName in os.listdir(PLUGINS_PATH):
        if fileName.endswith('.json'):
            plugins = json.load(file(os.path.join(PLUGINS_PATH,fileName)))
            for plugin in plugins:
                COMMANDS.append(CommandPlugin(plugin))
    
    COMMANDS.sort()
    
    win=Window()
    win.run()
