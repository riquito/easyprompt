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

'''
colors['darkgray']=(51,51,51)
colors['blue']=(0,0,255)
colors['green']=(0,255,0)
colors['fucsia']=(255,0,255)
colors['red']=(255,0,0)
colors['turquoise']=(0,255,255)
colors['yellow']=(255,255,0)
colors['white']=(255,255,255)

colors['bg_black']=colors['black']
colors['bg_blue']=colors['darkblue']
colors['bg_green']=colors['darkgreen']
colors['bg_teal']=colors['teal']
colors['bg_red']=colors['darkred']
colors['bg_purple']=colors['purple']
colors['bg_brown']=colors['brown']
colors['bg_gray']=colors['gray']
'''

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
    }
    
    
    COLORNAMES=['black','darkblue','darkgreen','teal','darkred','purple','brown','gray']
    
    class ColorsContainer(gtk.Frame):
        __gsignals__ = {
            'color-selected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                    (gobject.TYPE_PYOBJECT,)),
        }
        
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
                    
                    da=gtk.DrawingArea()
                    da.set_size_request(20,20)
                    da.set_events(gtk.gdk.BUTTON_PRESS_MASK)
                    #da.connect('event',self._on_color_clicked,colorName)
                    
                    if colorName == 'transparent':
                        da.connect("expose_event", self.expose_event)
                        da.connect("configure_event", self.configure_event)
                        self.currentColor = None
                    else:
                        da.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse(rgb2hex(colors[colorName])))
                    
                    da.show()
                    
                    littleFrame.add(da)
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
        
        def configure_event(self,widget, event):
            x, y, width, height = widget.get_allocation()
            self.pixmap = gtk.gdk.Pixmap(widget.window, width, height)
            white_gc = widget.get_style().white_gc
            self.pixmap.draw_rectangle(white_gc, True, 0, 0, width, height)
            return True
        
        def expose_event(self,widget, event):
            if not self.pixmap: return False
            
            x , y, w, h = event.area
            drawable_gc = widget.get_style().fg_gc[gtk.STATE_NORMAL]
            widget.window.draw_drawable(drawable_gc, self.pixmap, x, y, x, y, w, h)
            
            square_sz=20
            
            if not self.gc:
                self.gc = widget.window.new_gc()
                self.gc.set_rgb_fg_color(gtk.gdk.color_parse('red'))
            
            self.pixmap.draw_line(self.gc, 0,square_sz,square_sz,0)
            widget.queue_draw_area(0, 0, square_sz, square_sz)
                
            return False
    
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
        
        
        ### COMBOBOX Foreground/Background ###
        '''
        liststore = gtk.ListStore(gobject.TYPE_STRING,gobject.TYPE_INT)
        for key in (("Foreground",0),("Background",1)):
            liststore.append(key)
        combobox = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)
        
        combobox.show()
        vbox.pack_start(combobox,0,0,10)
        '''
        
        ### END COMBOBOX ###
        
        boxColorsAndStyle=gtk.VBox()
        
        ### COLORS ###
        
        self.frameBgColors=self.ColorsContainer('Background color',self.COLORNAMES)
        self.frameBgColors.connect('color-selected', lambda *args: self.emit('changed'))
        self.frameBgColors.show()
        
        self.frameFgColors=self.ColorsContainer('Foreground color',self.COLORNAMES)
        self.frameFgColors.connect('color-selected', lambda *args: self.emit('changed'))
        self.frameFgColors.show()
        
        
        ### END colors ###
        
        boxColorsAndStyle.pack_start(self.frameBgColors,0,0,2)
        boxColorsAndStyle.pack_start(self.frameFgColors,0,0,2)
        
        ### TABLE STYLES ###
        self.frameStyles=self.StylesContainer()
        self.frameStyles.connect('style-changed', lambda *args: self.emit('changed'))
        self.frameStyles.show()
        
        ### END TABLE STYLES ###
        
        boxColorsAndStyle.pack_start(self.frameStyles,0,0,2)
        
        boxColorsAndStyle.show()
        vbox.pack_start(boxColorsAndStyle,0,0,10)
        
        vbox.show()
        mainFrame.add(vbox)
        
        mainFrame.show()
        self.pack_start(mainFrame,1,1,0)
        
    def get_styling(self):
        return {
            'bgColor' : self.frameBgColors.get_color(),
            'fgColor' : self.frameFgColors.get_color(),
            'styles' : self.frameStyles.get_styles()
        }
    
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
        'keyword-clicked' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
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
        
        tableHelp=gtk.Table(len(helpDict),2)
        tableHelp.set_col_spacings(6)
        keys=commands.keys()
        keys.sort()
        
        row=0
        len_keys=len(keys)
        key_idx=0
        while key_idx < len_keys:
            for col in (0,1,2):
                key_idx=row*3+col
                if key_idx >= len_keys : break
                keyword=keys[key_idx]
                
                e=gtk.EventBox()
                e.add_events(gtk.gdk.BUTTON_PRESS_MASK)
                label=gtk.Label()
                label.set_markup('<span foreground="blue"><u>%s</u></span>' % keyword)
                label.set_tooltip_text(helpDict[keyword])
                label.show()
                e.add(label)
                e.text=keyword
                e.connect('button-press-event',lambda x,y: self.emit('keyword-clicked',x.text))
                e.connect('enter-notify-event',self.on_keyword_enter)
                e.connect('leave-notify-event',self.on_keyword_leave)
                e.show()
                
                tableHelp.attach(e,col,col+1,row,row+1)
            
            row+=1
        
        tableHelp.show()
        self.pack_start(tableHelp)
    
    def on_keyword_enter(self,widget,ev):
        widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
    
    def on_keyword_leave(self,widget,ev):
        widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.ARROW))
    

gobject.type_register(KeywordsBox)

class Window(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_size_request(500,600)
        self.set_border_width(5)
        self.connect('delete-event',self.on_delete_event)

        vbox=gtk.VBox()
        
        topHBox=gtk.HBox()
        
        stylingBox=Styling()
        stylingBox.connect('changed',self.on_style_changed)
        stylingBox.show()
        topHBox.pack_start(stylingBox,0,0,2)
        
        keywordsBox=KeywordsBox()
        keywordsBox.connect('keyword-clicked',self.on_shortcut_clicked)
        keywordsBox.show()
        topHBox.pack_start(keywordsBox,0,0,3)
        
        topHBox.show()
        vbox.pack_start(topHBox,0,0,2)
        
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
        term=shell.ShellWidget()
        term.loadColors(shell.getGnomeTerminalColors())
        term.set_size(term.get_column_count(),10)
        return term
    
    def on_shortcut_clicked(self,widget,key):
        self.textview.buffer.insert_at_cursor(key)
    
    def convert_to_bash_and_preview(self,*args):
        converted=self.convert_to_bash()
        self.preview(converted)
        self.code_preview(converted)
    
    def preview(self,prompt_format):
        self.term.set_prompt(prompt_format)
        self.term.clear()
    
    def code_preview(self,prompt_format):
        self.codePreview.set_text(prompt_format.strip(u'\x00'))
    
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