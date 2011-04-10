#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__='Riccardo Attilio Galli <riccardo@sideralis.org>'
__organization__='Sideralis'
__version__='1.1.0'

import gtk,pango,gobject
import shell
import output, re
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
colors['yellow']=(255,255,0)
colors['blue']=(0,0,255)
colors['purple']=(204,0,204)
colors['fucsia']=(255,0,255)
colors['black']=(0,0,0)
colors['white']=(255,255,255)
colors['red']=(255,0,0)
colors['brown']=(204,204,0)
colors['turquoise']=(0,255,255)
colors['darkred']=(204,0,0)
colors['gray']=(170,170,170)
colors['darkgreen']=(0,204,0)
colors['darkgray']=(51,51,51)
colors['darkblue']=(0,0,204)
colors['green']=(0,255,0)
colors['teal']=(0,204,204)

colors['bg_black']=colors['black']
colors['bg_blue']=colors['darkblue']
colors['bg_green']=colors['darkgreen']
colors['bg_teal']=colors['teal']
colors['bg_red']=colors['darkred']
colors['bg_purple']=colors['purple']
colors['bg_brown']=colors['brown']
colors['bg_gray']=colors['gray']

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

class ColorBox(gtk.HBox):
    __gsignals__ = {
         'color-selected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                (gobject.TYPE_PYOBJECT,))
    }

    
    def __init__(self,*args):
        gobject.GObject.__init__(self)
        
        for title in ('caratteri','sfondo'):
            frame=gtk.Frame(title)
            frame.set_border_width(1)
            table=gtk.Table(rows=2,columns=8,homogeneous=True)
            table.set_row_spacings(1)
            table.set_col_spacings(1)
            
            if title=='sfondo':
                colorNames=['bg_black', 'bg_blue','bg_red', 'bg_purple', 'bg_green', 'bg_brown', 'bg_teal', 'bg_gray']
            else:
                colorNames=[
                    'black', 'darkblue','darkred', 'purple', 'green', 'brown', 'teal', 'gray',
                    'darkgray','blue','red','fucsia','green','yellow','turquoise', 'white'
                ]
            
            for row in (0,1):
                for column,name in enumerate(colorNames[row*8:(row*8+8)]):
                    littleframe=gtk.Frame()
                    littleframe.set_border_width(2)
                    da=gtk.DrawingArea()
                    da.set_size_request(20,20)
                    da.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse(rgb2hex(colors[name])))
                    da.set_events(gtk.gdk.BUTTON_PRESS_MASK)
                    da.connect('event',self.on_color_clicked,name)
                    da.show()
                    littleframe.add(da)
                    littleframe.show()
                    table.attach(littleframe,column,column+1,row,row+1)

            table.show()
            frame.add(table)
            frame.show()
            self.pack_start(frame,0,0,3)

    def on_color_clicked(self,drawingArea,event,colorName):
        if event.type!=gtk.gdk.BUTTON_PRESS: return
        self.emit('color-selected',colorName)
    
gobject.type_register(ColorBox)

class promptTextView(gtk.TextView):
    def __init__(self,*args):
        gtk.TextView.__init__(self,*args)
        self.modify_font(pango.FontDescription('Courier 14'))
        self.set_property('left-margin',2) 
        self.modify_base(gtk.STATE_NORMAL,gtk.gdk.color_parse('#000000'))
        self.modify_text(gtk.STATE_NORMAL,gtk.gdk.color_parse('#FFFFFF'))
        self.buffer=self.get_buffer()
        
        table=self.buffer.get_tag_table()
        
        for name in colors:
            tag=gtk.TextTag(name)
            if name.startswith('bg_'):
                tag.set_property('background',rgb2hex(colors[name]))
            else:
                tag.set_property('foreground',rgb2hex(colors[name]))
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
        
        keywordsBox=KeywordsBox()
        keywordsBox.connect('keyword-clicked',self.on_shortcut_clicked)
        keywordsBox.show()
        vbox.pack_start(keywordsBox,0,0,3)

        colorBox=ColorBox()
        colorBox.connect('color-selected',self.on_table_color_selected)
        colorBox.show()
        vbox.pack_start(colorBox,0,0,2)
        
        self.checkBtn=gtk.CheckButton('usa i colori per modificare sfondo e colore del testo di EasyPrompt')
        self.checkBtn.show()
        vbox.pack_start(self.checkBtn,0,0,2)
        
        self.textview=promptTextView()
        self.textview.show()
        vbox.pack_start(self.textview,1,1,2)
        
        self.term=self.create_terminal()
        self.term.show()
        vbox.pack_start(self.term,0,0,2)
        
        btn=gtk.Button('Preview')
        btn.connect('clicked',self.convert_to_bash_and_preview)
        btn.show()
        vbox.pack_start(btn,0,0,2)
        
        vbox.show()
        self.add(vbox)

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
    
    def preview(self,prompt_format):
        self.term.set_prompt(prompt_format)
        self.term.clear()
    
    def convert_to_bash(self):
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
                #print 'DENTRO'
                text.append('\[%s\]' % codes['reset'])
                for name in last_tags:
                     text.append('\[%s\]' % codes[name])
                mustReset=False

            if not tags and last_tags:
                #print 'INSIDE'
                text.append('\[%s\]' % codes['reset'])
                last_tags=[]
            text.append(iter1.get_char())
            #print 'PING'
            if not iter1.forward_char(): break
        if last_tags: text.append('\[%s\]' % codes['reset'])
        
        #now convert every \x1b char with the octal equivalen \033
        line=''.join(text).replace('\x1b','\\'+str(oct(ord('\x1b'))))
        for elem in commands: #convert commands in bash equivalent -> BAD use of strings. ro re-write
            line=line.replace(elem,commands[elem])
        
        #line=line.replace('"','\\"')
        
        for module in re.findall('plug_(.+\.py)',line):
            line=line.replace('plug_%s' % module,'\\$(python %s/%s)' % (PLUGINS_PATH,module))
        
        return line

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
        
    
    def apply_tag_to_template(self,textview,tagName):
        
        buffer=self.textview.buffer
        settingBgColor=tagName.startswith('bg_')
        
        try:
            selectionStart,selectionEnd=buffer.get_selection_bounds()
            iter1=selectionStart.copy()
            
            while not iter1.is_end() and iter1.get_offset() < selectionEnd.get_offset():
                
                iter2=iter1.copy()
                iter2.forward_char()
                
                for tag in iter1.get_tags():
                    
                    isTagBgColor=tag.get_property('name').startswith('bg_')
                    
                    if not (isTagBgColor^settingBgColor): # (isTagBgColor and settingBgColor) or (not isTagBgColor and not settingBgColor)):
                        buffer.remove_tag(tag,iter1,iter2)
                
                iter1=iter2
            
            
            buffer.apply_tag_by_name(tagName,selectionStart,selectionEnd)
            buffer.select_range(selectionEnd,selectionEnd)
            
        except ValueError: pass #nothing selected
    
    
    def on_delete_event(self,*args):
        gtk.main_quit()
        
    
    def run(self):
        gtk.main()

if __name__=='__main__':
    win=Window()
    win.run()