#!/usr/bin/env python
# encoding: utf-8
# setup.py

from distutils.core import setup
import py2exe
options = {"py2exe": {  
		"dll_excludes": ["MSVCP90.dll"],  
		"compressed": 1,  
		"optimize": 2, 
		"bundle_files": 1 
	}
}
setup(
	version = "0.1.0",
	description = u"NCString",
	name = "NCString",
	options = options,
	zipfile = None,
	data_files = [('config', ['config/config.yaml']),
				('templates', [u'templates/海德汉.txt', u'templates/西门子.txt']),
				('logs', [u'logs/trace.log']),
				('help', [u'help/readme.html']),
			],
	windows=[{'script':'NCString.py',"icon_resources":[(1, 'NCString.ico')]}]
)
