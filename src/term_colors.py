
import re

_hex_term_colors = [
    
    "#000000",   # 0 black
    "#ff0000",   # 1 red
    "#00ff00",   # 2 green (X11)
    "#a52a2a",   # 3 brown
    "#0000ff",   # 4 blue
    "#a020f0",   # 5 purple (X11)
    "#00ffff",   # 6 cyan
    "#aaaaaa",   # 7 gray (X11)
    
    "#a9a9a9",   # 8 dark gray
    "#ff5555",   # 9 light red (???)
    "#90ee90",   # 10 light green
    "#ffff00",   # 11 yellow
    "#add8e6",   # 12 light blue
    "#ff55ff",   # 13 light purple (???)
    "#e0ffff",   # 14 light cyan
    "#ffffff",   # 15 white
    
    "#000000",   # 16
    "#00005f",   # 17
    "#000087",   # 18
    "#0000af",   # 19
    "#0000d7",   # 20
    "#0000ff",   # 21
    "#005f00",   # 22
    "#005f5f",   # 23
    "#005f87",   # 24
    "#005faf",   # 25
    "#005fd7",   # 26
    "#005fff",   # 27
    "#008700",   # 28
    "#00875f",   # 29
    "#008787",   # 30
    "#0087af",   # 31
    "#0087d7",   # 32
    "#0087ff",   # 33
    "#00af00",   # 34
    "#00af5f",   # 35
    "#00af87",   # 36
    "#00afaf",   # 37
    "#00afd7",   # 38
    "#00afff",   # 39
    "#00d700",   # 40
    "#00d75f",   # 41
    "#00d787",   # 42
    "#00d7af",   # 43
    "#00d7d7",   # 44
    "#00d7ff",   # 45
    "#00ff00",   # 46
    "#00ff5f",   # 47
    "#00ff87",   # 48
    "#00ffaf",   # 49
    "#00ffd7",   # 50
    "#00ffff",   # 51
    "#5f0000",   # 52
    "#5f005f",   # 53
    "#5f0087",   # 54
    "#5f00af",   # 55
    "#5f00d7",   # 56
    "#5f00ff",   # 57
    "#5f5f00",   # 58
    "#5f5f5f",   # 59
    "#5f5f87",   # 60
    "#5f5faf",   # 61
    "#5f5fd7",   # 62
    "#5f5fff",   # 63
    "#5f8700",   # 64
    "#5f875f",   # 65
    "#5f8787",   # 66
    "#5f87af",   # 67
    "#5f87d7",   # 68
    "#5f87ff",   # 69
    "#5faf00",   # 70
    "#5faf5f",   # 71
    "#5faf87",   # 72
    "#5fafaf",   # 73
    "#5fafd7",   # 74
    "#5fafff",   # 75
    "#5fd700",   # 76
    "#5fd75f",   # 77
    "#5fd787",   # 78
    "#5fd7af",   # 79
    "#5fd7d7",   # 80
    "#5fd7ff",   # 81
    "#5fff00",   # 82
    "#5fff5f",   # 83
    "#5fff87",   # 84
    "#5fffaf",   # 85
    "#5fffd7",   # 86
    "#5fffff",   # 87
    "#870000",   # 88
    "#87005f",   # 89
    "#870087",   # 90
    "#8700af",   # 91
    "#8700d7",   # 92
    "#8700ff",   # 93
    "#875f00",   # 94
    "#875f5f",   # 95
    "#875f87",   # 96
    "#875faf",   # 97
    "#875fd7",   # 98
    "#875fff",   # 99
    "#878700",   # 100
    "#87875f",   # 101
    "#878787",   # 102
    "#8787af",   # 103
    "#8787d7",   # 104
    "#8787ff",   # 105
    "#87af00",   # 106
    "#87af5f",   # 107
    "#87af87",   # 108
    "#87afaf",   # 109
    "#87afd7",   # 110
    "#87afff",   # 111
    "#87d700",   # 112
    "#87d75f",   # 113
    "#87d787",   # 114
    "#87d7af",   # 115
    "#87d7d7",   # 116
    "#87d7ff",   # 117
    "#87ff00",   # 118
    "#87ff5f",   # 119
    "#87ff87",   # 120
    "#87ffaf",   # 121
    "#87ffd7",   # 122
    "#87ffff",   # 123
    "#af0000",   # 124
    "#af005f",   # 125
    "#af0087",   # 126
    "#af00af",   # 127
    "#af00d7",   # 128
    "#af00ff",   # 129
    "#af5f00",   # 130
    "#af5f5f",   # 131
    "#af5f87",   # 132
    "#af5faf",   # 133
    "#af5fd7",   # 134
    "#af5fff",   # 135
    "#af8700",   # 136
    "#af875f",   # 137
    "#af8787",   # 138
    "#af87af",   # 139
    "#af87d7",   # 140
    "#af87ff",   # 141
    "#afaf00",   # 142
    "#afaf5f",   # 143
    "#afaf87",   # 144
    "#afafaf",   # 145
    "#afafd7",   # 146
    "#afafff",   # 147
    "#afd700",   # 148
    "#afd75f",   # 149
    "#afd787",   # 150
    "#afd7af",   # 151
    "#afd7d7",   # 152
    "#afd7ff",   # 153
    "#afff00",   # 154
    "#afff5f",   # 155
    "#afff87",   # 156
    "#afffaf",   # 157
    "#afffd7",   # 158
    "#afffff",   # 159
    "#d70000",   # 160
    "#d7005f",   # 161
    "#d70087",   # 162
    "#d700af",   # 163
    "#d700d7",   # 164
    "#d700ff",   # 165
    "#d75f00",   # 166
    "#d75f5f",   # 167
    "#d75f87",   # 168
    "#d75faf",   # 169
    "#d75fd7",   # 170
    "#d75fff",   # 171
    "#d78700",   # 172
    "#d7875f",   # 173
    "#d78787",   # 174
    "#d787af",   # 175
    "#d787d7",   # 176
    "#d787ff",   # 177
    "#d7af00",   # 178
    "#d7af5f",   # 179
    "#d7af87",   # 180
    "#d7afaf",   # 181
    "#d7afd7",   # 182
    "#d7afff",   # 183
    "#d7d700",   # 184
    "#d7d75f",   # 185
    "#d7d787",   # 186
    "#d7d7af",   # 187
    "#d7d7d7",   # 188
    "#d7d7ff",   # 189
    "#d7ff00",   # 190
    "#d7ff5f",   # 191
    "#d7ff87",   # 192
    "#d7ffaf",   # 193
    "#d7ffd7",   # 194
    "#d7ffff",   # 195
    "#ff0000",   # 196
    "#ff005f",   # 197
    "#ff0087",   # 198
    "#ff00af",   # 199
    "#ff00d7",   # 200
    "#ff00ff",   # 201
    "#ff5f00",   # 202
    "#ff5f5f",   # 203
    "#ff5f87",   # 204
    "#ff5faf",   # 205
    "#ff5fd7",   # 206
    "#ff5fff",   # 207
    "#ff8700",   # 208
    "#ff875f",   # 209
    "#ff8787",   # 210
    "#ff87af",   # 211
    "#ff87d7",   # 212
    "#ff87ff",   # 213
    "#ffaf00",   # 214
    "#ffaf5f",   # 215
    "#ffaf87",   # 216
    "#ffafaf",   # 217
    "#ffafd7",   # 218
    "#ffafff",   # 219
    "#ffd700",   # 220
    "#ffd75f",   # 221
    "#ffd787",   # 222
    "#ffd7af",   # 223
    "#ffd7d7",   # 224
    "#ffd7ff",   # 225
    "#ffff00",   # 226
    "#ffff5f",   # 227
    "#ffff87",   # 228
    "#ffffaf",   # 229
    "#ffffd7",   # 230
    "#ffffff",   # 231
    "#080808",   # 232
    "#121212",   # 233
    "#1c1c1c",   # 234
    "#262626",   # 235
    "#303030",   # 236
    "#3a3a3a",   # 237
    "#444444",   # 238
    "#4e4e4e",   # 239
    "#585858",   # 240
    "#626262",   # 241
    "#6c6c6c",   # 242
    "#767676",   # 243
    "#808080",   # 244
    "#8a8a8a",   # 245
    "#949494",   # 246
    "#9e9e9e",   # 247
    "#a8a8a8",   # 248
    "#b2b2b2",   # 249
    "#bcbcbc",   # 250
    "#c6c6c6",   # 251
    "#d0d0d0",   # 252
    "#dadada",   # 253
    "#e4e4e4",   # 254
    "#eeeeee"    # 255
]

_hex_grayscale = _hex_term_colors[232:] # dark to bright, missing black (0) and white (15)

_hex_ansi_colors = _hex_term_colors[0:16]


def rgb2hex(colorTuple):
    esa = ['#']
    for col in colorTuple:
        ascii=str(hex(col))
        esa.append(len(ascii)==4 and ascii[-2:] or ('0'+ascii[-1:]))
    return ''.join(esa)

def _normalizeHexColor(hexColor):
    if hexColor[0] == '#': hexColor = hexColor[1:]
    elif hexColor[0:2].lower() == '0x': hexColor = hexColor[2:]
    
    if len(hexColor) == 3:
        hexColor = ''.join(val for val in hexColor for i in range(2))
    elif len(hexColor) == 12:
        hexColor = hexColor[0]*2+hexColor[4]*2+hexColor[8]*2
    
    return hexColor

def hex2rgb(hexColor):
    hexColor = _normalizeHexColor(hexColor)
    return int(hexColor[0:2], 16), int(hexColor[2:4], 16), int(hexColor[4:6], 16)

from colorsys import rgb_to_hsv, hsv_to_rgb
def lighter_rgb(colorTuple):
    hsv = rgb_to_hsv(*(x/255. for x in colorTuple))
    return tuple(int(round(x*255)) for x in hsv_to_rgb(hsv[0],min(1,hsv[1]*1.10),min(1,hsv[2]*1.25)))

def darker_rgb(colorTuple):
    hsv = rgb_to_hsv(*(x/255. for x in colorTuple))
    return tuple(int(round(x*255)) for x in hsv_to_rgb(hsv[0],min(1,hsv[1]*0.90),min(1,hsv[2]*0.75)))

class BashColor:
    def __init__(self,hexcolor,bashIndex):
        self.hexcolor = '#'+_normalizeHexColor(hexcolor)
        self.index = bashIndex
        self.rgb = hex2rgb(self.hexcolor)
    
    def getEscapeCode(self,isBackground=False):
        colorCode = self.index
        styleCode = ''
        
        if isBackground:
            styleCode = '48;5;'
        else:
            styleCode = '38;5;'
        
        return '%s%d' % (styleCode,colorCode)
    
    def __str__(self):
        return self.__unicode__().encode('utf-8')
    
    def __unicode__(self):
        return u'%s-idx(%d)' % (self.hexcolor,self.index)
    
    def __eq__(self,obj):
        if isinstance(obj,BashColor):
            return obj.hexcolor==self.hexcolor
        else:
            return False
        
    def __hash__(self):
        return hash('%s idx(%d)' % (self.hexcolor,self.index))
    
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,str(self))
    
    @staticmethod
    def getAllColors():
        return BASH_TERM_COLORS
    

class ANSIColor(BashColor):
    def getEscapeCode(self,isBackground=False):        
        colorCode = self.index
        styleCode = ''
        
        if isBackground:
            if colorCode > 8:
                colorCode -= 8
            
            colorCode += 40
            
        else:
            if colorCode > 8:
                # it's a light version
                styleCode = '1;'
                colorCode -= 8
            
            colorCode += 30
        
        return '%s%d' % (styleCode,colorCode)
    
    @staticmethod
    def getAllColors():
        return BASH_ANSI_COLORS


class TextStyle(object):
    INCONSISTENT = -1
    
    WEIGHT_NORMAL = 'normal'
    WEIGHT_BOLD = 'bold'
    WEIGHT_FAINT = 'faint'
    
    WEIGHT = 'weight'
    STRIKETHROUGH = 'strikethrough'
    UNDERLINE = 'underline'
    INVERT = 'invert'
    
    BACKGROUND = 'background'
    FOREGROUND = 'foreground'
    
    def __init__(self):
        self._weight = None
        self._invert = False
        self._underline = False
        self._strikethrough = False
        self._background = None
        self._foreground = None
    
    @property
    def background(self):
        # check for True to include INCONSINSTENT too
        return self._background if not self._invert==True else self._foreground
    
    @background.setter
    def background(self,value):
        if value != None and value != TextStyle.INCONSISTENT and not isinstance(value,BashColor):
            raise TypeError("Not a valid background")
        
        if self._invert==True: # check for True to include INCONSINSTENT too
            self._foreground = value
        else:
            self._background = value
    
    @property
    def foreground(self):
        # check for True to include INCONSINSTENT too
        return self._foreground if not self._invert==True else self._background
    
    @foreground.setter
    def foreground(self,value):
        if value != None and value != TextStyle.INCONSISTENT and not isinstance(value,BashColor):
            raise TypeError("Not a valid foreground")
        
        if self._invert==True: # check for True to include INCONSINSTENT too
            self._background = value
        else:
            self._foreground = value
    
    @property
    def underline(self):
        return self._underline
    
    @underline.setter
    def underline(self,value):
        self._underline = TextStyle._getBoolOrInconsistent(value)
    
    @property
    def strikethrough(self):
        return self._strikethrough
    
    @strikethrough.setter
    def strikethrough(self,value):
        self._strikethrough = TextStyle._getBoolOrInconsistent(value)
    
    @property
    def invert(self):
        return self._invert
    
    @invert.setter
    def invert(self,value):
        invert = TextStyle._getBoolOrInconsistent(value)
        if invert!=self._invert and invert!=TextStyle.INCONSISTENT:
            self._background,self._foreground = self._foreground, self._background
        
        self._invert = invert
    
    @property
    def weight(self):
        return self._weight
    
    @weight.setter
    def weight(self,value):
        if value not in (None,
                         TextStyle.INCONSISTENT,
                         TextStyle.WEIGHT_NORMAL,
                         TextStyle.WEIGHT_BOLD,
                         TextStyle.WEIGHT_FAINT):
            raise TypeError("Not a valid weight")
        
        self._weight = value
        
    def __str__(self):
        return self.__unicode__().encode('utf-8')
    
    def __unicode__(self):
        map = {}
        if self.background:
            if self.is_inconsistent('background'):
                map['background'] = TextStyle.INCONSISTENT
            else:
                map['background'] = self.background.hexcolor
        
        if self.foreground:
            if self.is_inconsistent('foreground'):
                map['foreground'] = TextStyle.INCONSISTENT
            else:
                map['foreground'] = self.foreground.hexcolor
        
        for attrName in ('underline','strikethrough','weight','invert'):
            if getattr(self,attrName):
                map[attrName] = getattr(self,attrName)
        
        return u'<'+self.__class__.__name__+' '+u' '.join(('%s="%s"' % (key,value)) for key,value in map.iteritems())+u'>'
    
    def __repr__(self):
        return str(self)
    
    def calculate_background(self):
        return self._foreground if self.invert else self._background
    
    def calculate_foreground(self):
        return self._background if self.invert else self._foreground
    
    def set_inconsistent(self,attrName):
        setattr(self,attrName,TextStyle.INCONSISTENT)
    
    def is_inconsistent(self,attrName):
        return getattr(self,attrName) == TextStyle.INCONSISTENT
    
    def is_set(self,attrName):
        return attrName and not self.is_inconsistent(attrName)
    
    @staticmethod
    def _getBoolOrInconsistent(value):
        return TextStyle.INCONSISTENT if TextStyle.INCONSISTENT==value else bool(value)
    
    @staticmethod
    def _merge_styles_attr(st1,st2,attrName,fill_empty_properties):
        attr1 = getattr(st1,attrName)
        attr2 = getattr(st2,attrName)
        
        if attr1 == attr2:
            return attr1
        
        # with fill_empty_properties if a properties is set and the
        # other unset it doesn't become INCONSISTENT
        if fill_empty_properties and not (attr1 and attr2):
            return attr1 or attr2
        else:
            return TextStyle.INCONSISTENT
    
    @classmethod
    def merge_styles(cls,text_styles,fill_empty_properties=False):
        if not len(text_styles): return cls()
        
        tstyle = text_styles[0]
        
        for ts in text_styles[1:]:
            
            for attrName in ('_underline','_strikethrough','_background','_foreground','_weight'):
                
                setattr(tstyle,attrName,
                        TextStyle._merge_styles_attr(tstyle,ts,attrName,fill_empty_properties))
            
            if ts.invert and not tstyle.is_inconsistent('invert'):
                tstyle.invert = True
        
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
            codes.append(tstyle.background.getEscapeCode(isBackground=True))
        elif tstyle.background==None:
            codes.append(49)
        
        if tstyle.foreground and not tstyle.is_inconsistent('foreground'):
            codes.append(tstyle.foreground.getEscapeCode())
        elif tstyle.foreground==None:
            codes.append(39)
        
        if len(codes):
            return r'\e[%sm' % ';'.join(str(x) for x in codes)
        else:
            return ''
    

TERM_COLORS = [BashColor(hexcolor,idx) for idx,hexcolor in enumerate(_hex_term_colors)]
ANSI_COLORS = [ANSIColor(hexcolor,idx) for idx,hexcolor in enumerate(_hex_ansi_colors)]

BLACK = TERM_COLORS[0]
WHITE = TERM_COLORS[15]

GRAYSCALE = [BLACK]+[BashColor(hexcolor,idx) for idx,hexcolor in enumerate(_hex_grayscale)]+[WHITE]


def parse_bash_code(bash_code,commands=None,styleClass=TextStyle):
    
    # XXX temporary clumsy fix for terminal with title set
    bash_code = re.sub(r'\\\[\\\e]0;.*?\\\]','',bash_code)
    
    bash_code  = re.sub(r'(\\\[|\\\])','',bash_code) # strip \[ and \]
    
    if commands==None:
        commands = []
    
    ### this is incredibly inefficient ###
    for command in commands:
        bash_code = bash_code.replace(command.toBash(),command.keyword)
    ### ###
    
    pattern = re.compile(r'(?:\\033|\\e)\[((?:\d*[;m])*)')
    
    tstyles = []
    for groupMatch in pattern.findall(bash_code):
        
        groupMatch = groupMatch[:-1]
        
        if groupMatch == '':
            tstyles.append(styleClass())
        else:
            tstyles.append(__from_bash_code_values((int(x) for x in groupMatch.split(';')),styleClass))
    
    parts = pattern.split(bash_code) # having groups, splitting contains the splitting part too at even indexes
    
    if not parts:
        return []
    
    res = []
    for i in range(1,len(parts)-1,2):
        tstyle = tstyles[(i-1)/2]
        res.append((tstyle,parts[i+1]))
    
    return [(styleClass(),parts[0])] + res

def __from_bash_code_values(values,styleClass):
    tstyle = styleClass()
    
    values = list(values)
    
    def get_highcolor(values,isBackground):
        colIndex = None
        startVal = 48 if isBackground else 38
        try:
            highColorsIdx = values.index(startVal)
            if values[highColorsIdx+1] == 5:
                colIndex = values[highColorsIdx+2]
                values = values[:highColorsIdx]+values[highColorsIdx+3:]
        except (ValueError,IndexError) as e:
            pass
        
        return [values,colIndex]
    
    values,fgIndex = get_highcolor(values,False)
    if fgIndex != None:
        tstyle.foreground = TERM_COLORS[fgIndex]
    
    values,bgIndex = get_highcolor(values,False)
    if bgIndex != None:
        tstyle.background = TERM_COLORS[bgIndex]
    
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
            tstyle.foreground = ANSI_COLORS[val-30]
        elif 40 <= val <= 47:
            tstyle.background = ANSI_COLORS[val-40+8]
        
    
    return tstyle
