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


commands={
'dateLong':'$(date +"%d %b %Y")',
'dateShort':'$(date +"%d/%m/%y")',
'hourLong':'$(date +"%H:%M:%S")',
'hourShort':'$(date +"%H:%M")',
'host':'\h',
#'host_complete':'\H',  #commentato perche' MANGIATO da host 
'user':'\u',
'newline':'\n',
'shell':'\s',
'version':'\v',
'release':'\V',
'abs_pwd':'\w',
'base_pwd':'\W',
'history_num':'\!',
'cmd_num':'\#',
'prompt':'\$',
'backslash':'\\',
}

helpDict={
'dateLong':'data nel formato %d/%b/%Y es\xb0 28 Feb 2004'.decode('iso-8859-1'),
'dateShort':'data nel formato %d/%m/%y es\xb0 28/02/04'.decode('iso-8859-1'),
'hourLong':'ora nel formato %H:%M:%S es\xb0 15:23:59'.decode('iso-8859-1'),
'hourShort':'ora nel formato %H:%M es\xb0 15:23'.decode('iso-8859-1'),
'host':'hostname fino al primo punto',
#'host_cmp':'hostname completo', #commentato perche' MANGIATO da host
'user':'utente corrente',
'newline':'a capo',
'shell':'nome della shell',
'version':'versione della shell',
'release':'release della shell',
'abs_pwd':'path completa',
'base_pwd':'directory corrente',
'history_num':'numero del comando nella history',
'cmd_num':'numero del comando',
'prompt':'# se root, $ altrimenti',
'backslash':'un backslash \\',
}

KEYWORDS={
    'dateLong': {
        'command':'$(date +"%d %b %Y")',
        'help':'',
        'example':''
    },
    'dateShort': {
        'command':'$(date +"%d/%m/%y")',
        'help':'',
        'example':''
    },
    'hourLong': {
        'command':'$(date +"%H:%M:%S")',
        'help':'',
        'example':''
    },
    'hourShort': {
        'command':'$(date +"%H:%M")',
        'help':'',
        'example':''
    },
    'host': {
        'command':'\h',
        'help':'',
        'example':''
    },
    'user': {
        'command':'\u',
        'help':'bla bla bla bla bla',
        'example':'<u>foo</u>@mypc /var/log'
    },
    'newline': {
        'command':'\n',
        'help':'',
        'example':''
    },
    'shell': {
        'command':'\s',
        'help':'',
        'example':''
    },
    'version': {
        'command':'\v',
        'help':'',
        'example':''
    },
    'release': {
        'command':'\V',
        'help':'',
        'example':''
    },
    'abs_pwd': {
        'command':'\w',
        'help':'',
        'example':''
    },
    'base_pwd': {
        'command':'\W',
        'help':'',
        'example':''
    },
    'history_num': {
        'command':'\!',
        'help':'',
        'example':''
    },
    'cmd_num': {
        'command':'\#',
        'help':'',
        'example':''
    },
    'prompt': {
        'command':'\$',
        'help':'',
        'example':''
    },
    'backslash': {
        'command':'\\',
        'help':'',
        'example':''
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
        'keyword-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
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
            
            self.pixmap = None
            self.colour = "#FF0000"
            self.gc = None
            self.currentColor = None
            
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
                    
                    radioButton.connect('toggled',self._on_color_selected,colorName)
                    
                    tableColors.attach(singleColorBox,col,col+1,row,row+1)
            
            tableColors.show()
            
            self.add(tableColors)
        
        def _on_color_selected(self,widget,colorName):
            if not widget.get_active(): return
            self.currentColor = None if colorName=='transparent' else colorName
            self.emit('color-selected', self.currentColor)
        
        def get_color(self):
            return self.currentColor
    
    gobject.type_register(ColorsContainer)
    
    class StylesContainer(gtk.Frame):
        __gsignals__ = {
            'style-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    ()),
        }
        
        def __init__(self):
            gobject.GObject.__init__(self)
            
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
                widget.connect('toggled', lambda w: self.emit('style-changed'))
                widget.show()
            
            
            tableStyles.attach(self.normalRadio,0,1,0,1)
            tableStyles.attach(self.boldRadio,0,1,1,2)
            tableStyles.attach(self.faintRadio,0,1,2,3)
            
            tableStyles.attach(self.underlineBtn,1,2,0,1)
            tableStyles.attach(self.strikethroughBtn,1,2,1,2)
            tableStyles.attach(self.invertBtn,1,2,2,3)
            
            tableStyles.show()
            
            self.add(tableStyles)
        
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
    
    gobject.type_register(StylesContainer)
    
    def __init__(self,*args):
        gobject.GObject.__init__(self)
        
        mainFrame=gtk.Frame('Options')
        mainFrame.set_border_width(1)
        
        vbox=gtk.VBox()
        
        boxColorsAndStyle=gtk.VBox()
        
        self.keywordsBox=KeywordsBox()
        self.keywordsBox.connect('keyword-changed',self._on_keyword_changed)
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
        self.emit('changed')
    
    def get_styling(self):
        return Styling._memory[self.keywordsBox.get_active()]
    
    def _on_keyword_changed(self,widget,key):
        self.emit('keyword-changed',key)
    
    
    def __str__(self):
        return self.__unicode__().encode('utf-8')
    
    def __unicode__(self):
        return repr(self.get_styling()).decode('utf-8')

gobject.type_register(Styling)

class PromptToken:
    def __init__(self):
        self.text=None
        self.styling=None

class PromptKeywordToken(PromptToken):
    def __init__(self):
        super(PromptKeywordToken,self).__init__()
        

class FormatPromptTextView(gtk.TextView):
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
        
        tag=gtk.TextTag('underline')
        tag.set_property('underline',True)
        table.add(tag)
            
        tag=gtk.TextTag('strikethrough')
        tag.set_property('strikethrough',True)
        table.add(tag)
            
        tag=gtk.TextTag('invert')
        table.add(tag)
    

class KeywordsBox(gtk.VBox):
    __gsignals__ = {
        'keyword-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
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
        helpBox=gtk.VBox()
        
        
        self.exampleLabel=gtk.Label()
        #label.set_markup('<span foreground="blue"><u>%s</u></span>' % keyword)
        #label.set_tooltip_text(helpDict[keyword])
        self.exampleLabel.show()
        
        helpBox.pack_start(self.exampleLabel)
        
        self.descLabel=gtk.Label()
        self.descLabel.show()
        helpBox.pack_start(self.descLabel)
        
        
        helpBox.show()
        mainBox.pack_start(helpBox,0,0,2)
        
        mainBox.show()
        self.pack_start(mainBox)
    
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
        
        stylingBox=Styling()
        stylingBox.connect('changed',self.on_style_changed)
        stylingBox.connect('keyword-changed',self.on_keyword_changed)
        stylingBox.show()
        topBox.pack_start(stylingBox,0,0,2)
        
        
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
        
        self.texviewChangedId=self.textview.buffer.connect('changed',self.convert_to_bash_and_preview)
        #colorBox.connect('color-selected',self.convert_to_bash_and_preview)
        
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
    
    def convert_to_bash_and_preview(self,*args):
        converted=self.convert_to_bash()
        self.preview(converted)
        self.code_preview(converted)
    
    def preview(self,prompt_format):
        self.term.set_prompt(prompt_format)
        self.term.clear()
    
    def code_preview(self,prompt_format):
        self.codePreview.set_text(prompt_format.strip(u'\x00'))
    
    def on_keyword_changed(self,widget,key):
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
        
        for elem in commands: #convert commands in bash equivalent -> BAD use of strings. ro re-write
            line=line.replace(elem,commands[elem])
        
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
        self.apply_style_to_template(self.textview,stylingObj)
    
    def apply_style_to_template(self,textview,stylingObj):
        buffer=textview.buffer
        tagTable=buffer.get_tag_table()
        styling=stylingObj.get_styling()
        
        try:
            selectionStart,selectionEnd=buffer.get_selection_bounds()
            
            buffer.remove_all_tags(selectionStart,selectionEnd)
            
            to_apply=[]
            
            if styling['styles']['invert']:
                to_apply.append('invert')
                styling['bgColor'],styling['fgColor']=styling['fgColor'],styling['bgColor']
            
            if styling['bgColor']: to_apply.append("bg_"+styling['bgColor'])
            
            if styling['fgColor']: to_apply.append("fg_"+styling['fgColor'])
            
            if styling['styles']['strikethrough']: to_apply.append('strikethrough')
            
            if styling['styles']['underline']: to_apply.append('underline')
            
            if styling['styles']['weight']: to_apply.append('weight_'+styling['styles']['weight'])
            
            for tagName in to_apply:
                buffer.apply_tag_by_name(tagName,selectionStart,selectionEnd)
            
        except ValueError: pass #nothing selected
    
    def on_delete_event(self,*args):
        gtk.main_quit()
        
    
    def run(self):
        gtk.main()

if __name__=='__main__':
    win=Window()
    win.run()