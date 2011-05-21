# -*- coding: utf-8 -*-

CURRENT_LANG = 'en'

AVAILABLE_LANGUAGES = ('en','it')

def _(string_key):
    try:
        return STRINGS[string_key][CURRENT_LANG]
    except KeyError,e:
        try:
            return STRINGS[string_key]['en']
        except KeyError,e:
            return strings_key


STRINGS = {
    'HELP_TEXT' : {
        'en' : 'Choose a keyword from the list or write what you want\n'+
               'Remember that a bold word on a terminal will have a lighter color, a faint word will be darker\n',
        'it' : 'Scegli una parola chiave dall\'elenco qui sotto o scrivi quello che preferisci\n'+
               'Ricorda che su un terminale una parola in \'grassetto\' avrà un colore più brillante, una in \'pallido\' più scuro\n'
    },
    'CLICK_TO_USE_COLORS_FOR_BACKGROUND_FOREGROUND': {
        'en' : 'use colors to change background and text color of this area',
        'it' : "usa i colori per modificare sfondo e colore del testo di quest'area"
    },
    'SAVE_MESSAGE' : {
        'en' : 'Code inserted in ~/.bashrc, try it opening a new terminal or using "source ~/.bashrc"',
        'it' : 'Aggiunto il codice in ~/.bashrc, per provarlo apri un nuovo terminale o usa "source ~/.bashrc"'
    },
    'GENERATED_CODE' : {
        'en' : '<b>Generated code</b>',
        'it' : '<b>Codice generato</b>'
    },
    'RESET' : {
        'en' : 'reset',
        'it' : 'ripristina'
    },
    'IMPORT' : {
        'en' : 'import ...',
        'it' : 'importa ...'
    },
    'BACKGROUND_COLOR' : {
        'en' : 'Background color',
        'it' : 'Colore di sfondo'
    },
    'FOREGROUND_COLOR' : {
        'en' : 'Foreground color',
        'it' : 'Colore del testo'
    },
    'SAVE' : {
        'en' : 'Save',
        'it' : 'Salva'
    },
    'ENTER_BASH_PROMPT_CODE' : {
        'en' : 'Please enter your bash prompt code:',
        'it' : 'Inserisci il codice del tuo bash prompt:'
    },
    'OPTIONS' : {
        'en' : 'Options',
        'it' : 'Opzioni'
    },
    'UNDERLINE' : {
        'en' : 'underline',
        'it' : 'sottolineato:'
    },
    'STRIKETHROUGH' : {
        'en' : 'strikethrough',
        'it' : 'linea in mezzo'
    },
    'INVERT' : {
        'en' : 'invert',
        'it' : 'inverti'
    },
    'TEXT_NORMAL' : {
        'en' : 'normal',
        'it' : 'normale'
    },
    'TEXT_BOLD' : {
        'en' : 'bold',
        'it' : 'grassetto'
    },
    'TEXT_FAINT' : {
        'en' : 'faint',
        'it' : 'pallido'
    },
    'CMD_DATELONG' : {
        'en' : 'data in format %d/%b/%Y',
        'it' : 'data nel formato %d/%b/%Y'
    },
    'CMD_DATESHORT' : {
        'en' : 'date in format %d/%m/%y',
        'it' : 'data nel formato %d/%m/%y'
    },
    'CMD_TIMELONG' : {
        'en' : 'time in format %H:%M:%S',
        'it' : 'tempo nel formato %H:%M:%S'
    },
    'CMD_TIMESHORT' : {
        'en' : 'time in format %H:%M',
        'it' : 'tempo nel formato %H:%M'
    },
    'CMD_HOST' : {
        'en' : 'the host name',
        'it' : 'il nome dell\'host'
    },
    'CMD_USERNAME' : {
        'en' : 'the username of the current user',
        'it' : 'il nome-utente dell\'utente corrente'
    },
    'CMD_NEWLINE' : {
        'en' : 'newline character',
        'it' : 'carattere di nuova linea'
    },
    'CMD_SHELL' : {
        'en' : 'the name of the shell',
        'it' : 'nome della shell'
    },
    'CMD_VERSION' : {
        'en' : 'the version of bash',
        'it' : 'versione di bash'
    },
    'CMD_RELEASE' : {
        'en' : 'the release of bash, version + patch level',
        'it' : 'release di bash (versione + numero di patch)'
    },
    'CMD_ABS_PWD' : {
        'en' : 'the current working directory, with $HOME abbreviated with a tilde ',
        'it' : 'la directory di lavoro corrente con HOME abbreviato con una tilde'
    },
    'CMD_BASE_PWD' : {
        'en' : 'the basename of the current working directory, with $HOME abbreviated with a tilde ',
        'it' : 'il basename della directory di lavoro corrente, con HOME abbreviato con una tilde'
    },
    'CMD_HISTORY' : {
        'en' : 'the history number of this command ',
        'it' : 'il numero nella cronologia del comando attuale'
    },
    'CMD_COMMAND_NUMBER' : {
        'en' : 'the command number of this command ',
        'it' : 'il numero di comando del comando attuale'
    },
    'CMD_PROMPT' : {
        'en' : '<b>#</b> if root, else <b>$</b>',
        'it' : '<b>#</b> se root, <b>$</b> altrimenti'
    },
    'CMD_BACKSLASH' : {
        'en' : 'backslash character \\',
        'it' : 'carattere di backslash \\'
    },
}
