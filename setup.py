#!/usr/bin/env python

import sys

try: assert sys.version_info[:3]>(2,3,0)
except (AttributeError, AssertionError):
    print 'Python >=2.3.0 is required'
    sys.exit(-1)

from distutils.core import setup
import os

DEST_DIR=''

if sys.argv[1]=='install':
    DEST_DIR='/usr/local/share/EasyPrompt'
    if not os.path.exists('/usr/portage'):  #to avoid a message error in gentoo
        try: os.symlink(os.path.join(DEST_DIR,'easyprompt.py'),'/usr/bin/easyprompt')
        except OSError: pass

DEST_DIR='/usr/local/share/EasyPrompt'

setup(
     name="easyprompt",
     version="1.1.0",
     description="EasyPrompt, GUI for creating bash prompt",
     author="Riccardo Attilio Galli",
     author_email="riccardo@sideralis.net",
     url="http://www.sideralis.net",
     license='GPL',
     platforms=['GNU\\Linux'],
     data_files=[(DEST_DIR, ['src/easyprompt.py','src/output.py','src/acpi.py'])],
     long_description="""EasyPrompt, GUI for creating bash prompt"""
    )

if sys.argv[1]=='install': print 'Installation successful'
