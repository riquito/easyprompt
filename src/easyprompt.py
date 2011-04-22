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
colors['darkblue']=(0,0,204)
colors['darkgreen']=(0,204,0)
colors['teal']=(0,204,204)
colors['darkred']=(204,0,0)
colors['purple']=(204,0,204)
colors['brown']=(204,204,0)
colors['gray']=(170,170,170)


KEYWORDS={
    'dateLong': {
        'command':'$(date +"%d %b %Y")',
        'help':'data nel formato %d/%b/%Y',
        'example':'<b>28 Feb 2004</b> foo@mypc /var/log'
    },
    'dateShort': {
        'command':'$(date +"%d/%m/%y")',
        'help':'data nel formato %d/%m/%y',
        'example':'<b>28/02/04</b> foo@mypc /var/log'
    },
    'hourLong': {
        'command':'$(date +"%H:%M:%S")',
        'help':'ora nel formato %H:%M:%S',
        'example':'<b>15:23:59</b> foo@mypc /var/log'
    },
    'hourShort': {
        'command':'$(date +"%H:%M")',
        'help':'ora nel formato %H:%M',
        'example':'<b>15:23</b> foo@mypc /var/log'
    },
    'host': {
        'command':'\h',
        'help':'hostname fino al primo punto',
        'example':'foo@<b>mypc</b> /var/log'
    },
    'user': {
        'command':'\u',
        'help':'utente corrente',
        'example':'<b>foo</b>@mypc /var/log'
    },
    'newline': {
        'command':'\n',
        'help':'a capo',
        'example':'foo@mypc /var/log <b>↵</b> $'
    },
    'shell': {
        'command':'\s',
        'help':'nome della shell',
        'example':'foo@mypc <b>bash</b> /var/log  $'
    },
    'version': {
        'command':'\v',
        'help':'versione della shell',
        'example':'foo@mypc <b>4.2</b> /var/log  $'
    },
    'release': {
        'command':'\V',
        'help':'release della shell (versione + numero di patch)',
        'example':'foo@mypc <b>4.2.8</b> /var/log  $'
    },
    'abs_pwd': {
        'command':'\w',
        'help':'path completa',
        'example':'foo@mypc <b>/var/log</b> $'
    },
    'base_pwd': {
        'command':'\W',
        'help':'directory corrente',
        'example':'foo@mypc <b>log</b> $'
    },
    'history_num': {
        'command':'\!',
        'help':'il numero nella cronologia del comando attuale',
        'example':'<b>508</b> foo@mypc /var/log $ cd\n<b>509</b> foo@mypc ~ $'
    },
    'cmd_num': {
        'command':'\#',
        'help':'il numero di comando del comando attuale',
        'example':'<b>3</b> foo@mypc /var/log $ echo "hello"\nhello\n<b>4</b> foo@mypc /var/log $'
    },
    'prompt': {
        'command':'\$',
        'help':'# se root, $ altrimenti',
        'example':'foo@mypc /var/log <b>$</b> sudo su -\nroot@mypc ~ <b>#</b>'
    },
    'backslash': {
        'command':'\\',
        'help':'un backslash \\',
        'example':'foo<b>\\</b>mypc /var/log $'
    },
}


def rgb2hex(colorTuple):
    esa=['#']
    for col in colorTuple:
        ascii=str(hex(col))
        esa.append(len(ascii)==4 and ascii[-2:] or ('0'+ascii[-1:]))
    return ''.join(esa)

class Styling(gtk.VBox):
    __gsignals__ = {
        'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                ()),
        'keyword-request' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                (gobject.TYPE_STRING,)),
    }
    
    _memory={}
    
    COLORNAMES=['black','darkblue','darkgreen','teal','darkred','purple','brown','gray']
    
    class ColorsContainer(gtk.Frame):
        __gsignals__ = {
            'color-selected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT,)),
        }
        
        class ColorPreview(gtk.DrawingArea):

            # Draw in response to an expose-event
            __gsignals__ = { "expose-event": "override" }
            
            def __init__(self,colorTuple=None):
                super(Styling.ColorsContainer.ColorPreview,self).__init__()
                
                self.set_size_request(20,20)
                self.color=colorTuple
                
                if colorTuple:
                    self.draw=self._paint_color
                else:
                    self.draw=self._paint_transparent
        
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
                # Fill the background with white
                cr.set_source_rgb(*self.color)
                cr.rectangle(0, 0, width, height)
                cr.fill()
        
        def __init__(self,frameTitle,colorNames,rows=1):
            gobject.GObject.__init__(self)
            
            self.set_label(frameTitle)
            self.set_border_width(1)
            
            colorNames = ['transparent']+colorNames
            
            numColors = len(colorNames)
            
            columns=int(ceil(numColors/float(rows)))
            
            tableColors=gtk.Table(rows=rows,columns=columns,homogeneous=True)
            tableColors.set_row_spacings(1)
            tableColors.set_col_spacings(1)
            
            group=None
            
            self.currentColor = None
            self.colors2radio={}
            
            for row in range(rows):
                for col in range(columns):
                    
                    singleColorBox=gtk.VBox()
                    
                    colorName=colorNames[col];
                    
                    littleFrame=gtk.Frame()
                    littleFrame.set_border_width(2)
                    
                    if colorName == 'transparent':
                        singleColorPreview=Styling.ColorsContainer.ColorPreview(None)
                    else:
                        singleColorPreview=Styling.ColorsContainer.ColorPreview(colors[colorName])
                    
                    singleColorPreview.show()
                    
                    littleFrame.add(singleColorPreview)
                    littleFrame.show()
                    
                    singleColorBox.pack_start(littleFrame,0,0,2)
                    
                    radioButton=gtk.RadioButton(group)
                    if group == None: group = radioButton
                    radioButton.show()
                    singleColorBox.pack_start(radioButton,0,0,2)
                    
                    singleColorBox.show()
                    
                    self.colors2radio[colorName]=radioButton
                    
                    signal_id=radioButton.connect('toggled', self._on_color_selected,colorName)
                    radioButton._signal_id=signal_id
                    
                    tableColors.attach(singleColorBox,col,col+1,row,row+1)
            
            tableColors.show()
            
            self.add(tableColors)
        
        def _on_color_selected(self,widget,colorName):
            if not widget.get_active(): return
            self.currentColor = None if colorName=='transparent' else colorName
            self.emit('color-selected', self.currentColor)
        
        def get_color(self):
            return self.currentColor
        
        def set_color(self,colorName):
            
            self.currentColor = colorName
            
            if colorName == None: colorName = 'transparent'
            
            currentRadioBtn=self.colors2radio[self.get_color() if self.get_color() else 'transparent']
            newRadioBtn=self.colors2radio[colorName]
            
            currentRadioBtn.handler_block(currentRadioBtn._signal_id)
            newRadioBtn.handler_block(newRadioBtn._signal_id)
            
            newRadioBtn.set_active(True)
            
            currentRadioBtn.handler_unblock(currentRadioBtn._signal_id)
            newRadioBtn.handler_block(newRadioBtn._signal_id)
    
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
            
            self.normalRadio=gtk.RadioButton(None,'normal')
            self.boldRadio=gtk.RadioButton(self.normalRadio,'bold')
            self.faintRadio=gtk.RadioButton(self.normalRadio,'faint')
            
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
            
            
            tableStyles.attach(self.normalRadio,0,1,0,1)
            tableStyles.attach(self.boldRadio,0,1,1,2)
            tableStyles.attach(self.faintRadio,0,1,2,3)
            
            tableStyles.attach(self.underlineBtn,1,2,0,1)
            tableStyles.attach(self.strikethroughBtn,1,2,1,2)
            tableStyles.attach(self.invertBtn,1,2,2,3)
            
            tableStyles.show()
            
            self.add(tableStyles)
        
        def _send_changed_signal(self,*args):
            if self._can_send_signal:
                self.emit('style-changed')
        
        def get_styles(self):
            
            weight='normal'
            if self.boldRadio.get_active():
                weight='bold'
            elif self.faintRadio.get_active():
                weight='faint'
            
            return {
                'weight' : weight,
                'underline' : self.underlineBtn.get_active(),
                'strikethrough' : self.strikethroughBtn.get_active(),
                'invert' : self.invertBtn.get_active()
            }
        
        def set_styles(self,styles):
            self._can_send_signals=False
            
            self.underlineBtn.set_active(styles['underline'])
            self.strikethroughBtn.set_active(styles['strikethrough'])
            self.invertBtn.set_active(styles['invert'])
            self.normalRadio.set_active(styles['weight']=='normal')
            self.boldRadio.set_active(styles['weight']=='bold')
            self.faintRadio.set_active(styles['weight']=='faint')
            
            self._can_send_signals=True
    
    gobject.type_register(StylesContainer)
    
    def __init__(self,*args):
        gobject.GObject.__init__(self)
        
        mainFrame=gtk.Frame('Options')
        mainFrame.set_border_width(1)
        
        vbox=gtk.VBox()
        
        boxColorsAndStyle=gtk.VBox()
        
        self.keywordsBox=KeywordsBox()
        self.keywordsBox.connect('keyword-changed',self._on_keyword_changed)
        self.keywordsBox.connect('keyword-request',self._on_keyword_requested)
        self.keywordsBox.show()
        boxColorsAndStyle.pack_start(self.keywordsBox,0,0,3)
        
        ### COLORS ###
        
        self.frameBgColors=Styling.ColorsContainer('Background color',self.COLORNAMES)
        self.frameBgColors.connect('color-selected', lambda *args: self._on_style_changed())
        self.frameBgColors.show()
        
        self.frameFgColors=Styling.ColorsContainer('Foreground color',self.COLORNAMES)
        self.frameFgColors.connect('color-selected', lambda *args: self._on_style_changed())
        self.frameFgColors.show()
        
        ### END colors ###
        
        boxColorsAndStyle.pack_start(self.frameBgColors,0,0,2)
        boxColorsAndStyle.pack_start(self.frameFgColors,0,0,2)
        
        
        ### TABLE STYLES ###
        
        self.frameStyles=Styling.StylesContainer()
        self.frameStyles.connect('style-changed', lambda *args: self._on_style_changed())
        self.frameStyles.show()
        
        ### END TABLE STYLES ###
        
        boxColorsAndStyle.pack_start(self.frameStyles,0,0,2)
        
        boxColorsAndStyle.show()
        vbox.pack_start(boxColorsAndStyle,0,0,10)
        
        vbox.show()
        mainFrame.add(vbox)
        
        mainFrame.show()
        self.pack_start(mainFrame,1,1,0)
        
        from copy import deepcopy
        baseStyle=self._export_current_style()
        for keywordName in KEYWORDS:
            Styling._memory[keywordName]=deepcopy(baseStyle)
        
        self.keywordsBox.set_active(0)
    
    def _export_current_style(self):
        return {
            'bgColor' : self.frameBgColors.get_color(),
            'fgColor' : self.frameFgColors.get_color(),
            'styles' : self.frameStyles.get_styles()
        }
    
    def _on_style_changed(self):
        Styling._memory[self.keywordsBox.get_active()]=self._export_current_style()
        print 'changed',self.keywordsBox.get_active()
        self.emit('changed')
    
    def get_styling(self,keywordName):
        return Styling._memory[keywordName]
    
    def _on_keyword_requested(self,widget,key):
        self.emit('keyword-request',key)
    
    def _on_keyword_changed(self,keywordBox,keywordName):
        self.frameBgColors.set_color(Styling._memory[keywordName]['bgColor'])
        self.frameFgColors.set_color(Styling._memory[keywordName]['fgColor'])
        self.frameStyles.set_styles(Styling._memory[keywordName]['styles'])
    
    def get_current_keyword(self):
        return self.keywordsBox.get_active()
    
    def __str__(self):
        return self.__unicode__().encode('utf-8')
    
    def __unicode__(self):
        return repr(self.get_styling(self.get_current_keyword())).decode('utf-8')

gobject.type_register(Styling)

class PromptToken:
    def __init__(self):
        self.text=None
        self.styling=None

class PromptKeywordToken(PromptToken):
    def __init__(self):
        super(PromptKeywordToken,self).__init__()
        

class FormatPromptTextView(gtk.TextView):
    __gsignals__ = {
        'selection-toggle' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_BOOLEAN,)),
        'selection-change' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                ())
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
        
        for colorName in Styling.COLORNAMES:
            
            hexCode=rgb2hex(colors[colorName])
            
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
        self.buffer.connect('notify::has-selection', self.on_selection_toggle)
        self.connect_after('move-cursor', self.on_move_cursor)
        self.connect('button-release-event', self._on_mouse_button_released)
        
        self.buffer.connect('notify::cursor-position', self.on_cursor_position_change)
        self.buffer.connect('changed', self.on_content_change)
    
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
    
    def change_keyword_appearance(self,keywordName,styleObj):
        
        tagTable=self.buffer.get_tag_table()
        tag=tagTable.lookup(keywordName)
        
        styling = styleObj.get_styling(keywordName)
        
        # XXX check if the 'invert' attribute is preserved on tag lookup
        tag.invert = styling['styles']['invert'];
        if styling['styles']['invert']:
            styling['bgColor'],styling['fgColor']=styling['fgColor'],styling['bgColor']
        
        background = self.__class__.DEFAULT_BACKGROUND if not styling['bgColor'] else colors[styling['bgColor']]
        tag.set_property('background',rgb2hex(background))
        
        foreground = self.__class__.DEFAULT_FOREGROUND if not styling['fgColor'] else colors[styling['fgColor']]
        tag.set_property('foreground',rgb2hex(foreground))
        
        tag.set_property('strikethrough',styling['styles']['strikethrough'])
        tag.set_property('underline',styling['styles']['underline'])
        
        for weightName,pangoValue in (
                 ('faint',pango.WEIGHT_ULTRALIGHT),
                 ('normal',pango.WEIGHT_NORMAL),
                 ('bold',pango.WEIGHT_BOLD)
                ):
            
            if weightName == styling['styles']['weight']:
                tag.set_property('weight',pangoValue)
                break
        
    
    def on_cursor_position_change(self,buffer,*args):
        print 'cursor pos changed'
    
    def _on_mouse_button_released(self,textview,event):
        ## XXX check me
        if self._has_selection:
            self._on_selection_changed()
        
    def on_move_cursor(self,textview,step_size,count,extend_selection):
        if extend_selection:
            try:
                start, end = self.buffer.get_selection_bounds()
                selected_text = self.buffer.get_text(start, end)
                if len(selected_text) > 0: # when is 0 the 'selection-end' signal is automatically emitted
                    self._on_selection_changed()
            except ValueError, e:
                pass
    
    def on_selection_toggle(self,textBuffer,*args):
        self._has_selection = not self._has_selection
        self.emit('selection-toggle',self._has_selection)
    
    def _on_selection_changed(self):
        self.emit('selection-change')
    

class KeywordsBox(gtk.VBox):
    __gsignals__ = {
        'keyword-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,)),
        'keyword-request' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,))
    }
    
    def __init__(self):
        gtk.VBox.__init__(self)
        
        for txt in ('Per colorare una parola selezionarla e cliccare su un colore',
                    'Le seguenti parole chiave verranno espanse nelle relative informazioni\n'):
            labelHelp=gtk.Label(txt)
            labelHelp.show()
            align=gtk.Alignment(0,0,0,0.5)
            align.add(labelHelp)
            align.show()
            self.pack_start(align)
            
        
        mainBox=gtk.HBox()
        
        liststore = gtk.ListStore(gobject.TYPE_STRING)
        for key in KEYWORDS:
            liststore.append((key,))
        combobox = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)
        combobox.set_wrap_width(2)
        
        combobox.connect('changed',self._on_combobox_changed)
        
        self.combobox=combobox
        
        combobox.show()
        
        mainBox.pack_start(combobox,0,0,2)
        
        insertBtn=gtk.Button('Insert')
        insertBtn.connect('clicked',self._on_insertBtn_clicked)
        insertBtn.show()
        mainBox.pack_start(insertBtn,0,0,2)
        
        helpBox=gtk.VBox()
        
        self.exampleLabel=gtk.Label()
        self.exampleLabel.show()
        
        helpBox.pack_start(self.exampleLabel)
        
        self.descLabel=gtk.Label()
        self.descLabel.show()
        helpBox.pack_start(self.descLabel)
        
        
        helpBox.show()
        mainBox.pack_start(helpBox,0,0,2)
        
        mainBox.show()
        self.pack_start(mainBox)
    
    def _on_insertBtn_clicked(self,*args):
        self.emit('keyword-request',self.get_active())
    
    def _on_combobox_changed(self,combobox):
        keywordName=self.get_active()
        keywordData=KEYWORDS[keywordName]
        self.exampleLabel.set_markup(keywordData['example'])
        self.descLabel.set_markup(keywordData['help'])
        self.emit('keyword-changed',keywordName)
    
    def get_active(self):
        model = self.combobox.get_model()
        index = self.combobox.get_active()
        return model[index][0]
    
    def set_active(self,index):
        index = self.combobox.set_active(index)

gobject.type_register(KeywordsBox)

class Window(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_size_request(600,800)
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
        
        self.checkBtn=gtk.CheckButton('usa i colori per modificare sfondo e colore del testo di EasyPrompt')
        self.checkBtn.show()
        vbox.pack_start(self.checkBtn,0,0,2)
        
        btn=gtk.Button('Reset colors')
        btn.connect('clicked', lambda *x: self.reset_colors())
        btn.show()
        vbox.pack_start(btn,0,0,2)
        
        self.textview=FormatPromptTextView()
        self.textview.connect('selection-change',self.on_formatPrompt_selection_change)
        self.texviewChangedId=self.textview.buffer.connect('changed',self.convert_to_bash_and_preview)
        self.textview.show()
        
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.textview)
        sw.show()
        
        vbox.pack_start(sw,0,0,2)
        
        codePreviewBox=gtk.HBox()
        label=gtk.Label()
        label.set_markup("<b>Generated code</b>");
        codePreviewBox.pack_start(label,0,0,2)
        self.codePreview=gtk.Label()
        codePreviewBox.pack_start(self.codePreview,0,0,2)
        codePreviewBox.show_all()
        vbox.pack_start(codePreviewBox,0,0,2)
        
        self.term=self.create_terminal()
        self.term.show()
        vbox.pack_start(self.term,0,0,2)
        
        btn=gtk.Button('Save')
        btn.connect('clicked', lambda *x: self.write_on_disk(self.convert_to_bash()))
        btn.show()
        vbox.pack_start(btn,0,0,2)
        
        vbox.show()
        self.add(vbox)
        
        self.textview.set_size_request(-1,self.textview.get_line_yrange(self.textview.buffer.get_start_iter())[1]*3)
        
        self.show()
    
    def create_terminal(self):
        term=shell.ShellWidget()
        term.loadColors(shell.getGnomeTerminalColors())
        term.set_size(term.get_column_count(),10)
        return term
    
    def on_formatPrompt_selection_change(self,textview):
        try:
            start,end = textview.buffer.get_selection_bounds()
            print textview.buffer.get_text(start,end)
            
        except ValueError, e:
            pass
    
    def convert_to_bash_and_preview(self,*args):
        return
        
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
        
        self.textview.buffer.handler_block(self.texviewChangedId)
        
        buffer=self.textview.buffer
        
        iter1=buffer.get_start_iter()

        text=[]

        last_tags=[]
        mustReset=False
        while 1:
            tags=iter1.get_tags()
            for tag in tags:
                name=tag.get_property('name')
                if not last_tags:
                    text.append('\[%s\]' % codes[name])
                    last_tags.append(name)
                elif last_tags and not (name in last_tags):
                    for i in last_tags[:]:
                        if i[:3]==name[:3]=='bg_' or \
                            (i[:3]!='bg_' and name[:3]!='bg_'): #devo cambiare back o fore ground
                            #print 'i:',i,'name:',name,'last_tags:',last_tags
                            #print '-',i[:3],name[:3]
                            last_tags.remove(i)
                            last_tags.append(name)
                            mustReset=True
                            break
                    else:
                        text.append('\[%s\]' % codes[name])
                        last_tags.append(name)

            if mustReset:
                text.append('\[%s\]' % codes['reset'])
                for name in last_tags:
                     text.append('\[%s\]' % codes[name])
                mustReset=False

            if not tags and last_tags:
                text.append('\[%s\]' % codes['reset'])
                last_tags=[]
            text.append(iter1.get_char().replace('\\','\\\\').replace('"','\\"'))
            
            if not iter1.forward_char(): break
        if last_tags: text.append('\[%s\]' % codes['reset'])
        
        #now convert every \x1b char with the octal equivalen \033
        line=''.join(text).replace('\x1b','\\'+str(oct(ord('\x1b'))))
        
        for keywordName in KEYWORDS: #convert commands in bash equivalent -> BAD use of strings. to re-write
            line=line.replace(keywordName,KEYWORDS[keywordName]['command'])
        
        for module in re.findall('plug_(.+\.py)',line):
            line=line.replace('plug_%s' % module,'\\$(python %s/%s)' % (PLUGINS_PATH,module))
        
        
        self.textview.buffer.handler_unblock(self.texviewChangedId)
        
        return line.replace("\n","\\n")
    
    def reset_colors(self):
        self.textview.buffer.handler_block(self.texviewChangedId)
        self.textview.buffer.set_text(self.textview.buffer.get_text(
            self.textview.buffer.get_start_iter(),
            self.textview.buffer.get_end_iter()
        ))
        self.textview.buffer.handler_unblock(self.texviewChangedId)
        self.textview.buffer.emit('changed')
    
    def write_on_disk(self,line):
        fp=file(os.path.join(CONFIG_PATH,'temp.txt'),'w')
        fp.write(line)
        fp.write(' ')
        fp.close()

        dialog=gtk.MessageDialog(self,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_INFO,
            gtk.BUTTONS_OK,
            'ho scritto il codice in "%s"\nProvalo con PS1=`cat temp.txt`' % os.path.join(CONFIG_PATH,'temp.txt')
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
        
        keywordName=self.stylingBox.get_current_keyword()
        self.textview.change_keyword_appearance(keywordName,stylingObj)
    
    def on_delete_event(self,*args):
        gtk.main_quit()
        
    
    def run(self):
        gtk.main()

if __name__=='__main__':
    win=Window()
    win.run()