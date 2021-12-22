# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''

from setuptools import find_packages
from setuptools import setup

buildOptions = {}
executables = {}
W32 = False

if W32:
	from cx_Freeze import setup, Executable

	buildOptions = {
		"build_exe": {
			"packages": ["gi"], 
			"include_files":[]
		}
	}
	executables = [
		Executable("main.py") #  icon="evm_bg_KYa_icon.ico")
	]


setup(name='gweatherrouting',
	version=0.1,
	description='',
	author='Davide Gessa',
	setup_requires='setuptools',
	author_email='gessadavide@gmail.com',
	packages=['gweatherrouting', 'gweatherrouting.conn', 
		'gweatherrouting.ui.common',
		'gweatherrouting.ui', 'gweatherrouting.ui.gtk', 'gweatherrouting.ui.gtk.maplayers', 
		'gweatherrouting.ui.gtk.settings', 'gweatherrouting.ui.gtk.widgets',
		'gweatherrouting.ui.gtk.charts', 'gweatherrouting.ui.gtk.charts.vectordrawer', 
		'gweatherrouting.core'],
	package_data={
		'gweatherrouting': [
			'data/*', 'data/boats/*', 'data/polars/*', 
			'ui/gtk/*.glade', 'ui/gtk/settings/*.glade', 'ui/gtk/widgets/*.glade'
		]
	},
	entry_points={
		'console_scripts': [
			'gweatherrouting=gweatherrouting.main:startUIGtk',
			# 'gweatherrouting_cli=gweatherrouting.main:startCli'
		],
	},
	options=buildOptions,
	executables=executables,
	install_requires=open ('requirements.txt', 'r').read ().split ('\n')
)
