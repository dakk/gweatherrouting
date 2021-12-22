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

from setuptools import setup

setup(name='gweatherrouting',
	version=0.1,
	description='',
	author='Davide Gessa',
	setup_requires='setuptools',
	author_email='gessadavide@gmail.com',
	packages=['gweatherrouting', 'gweatherrouting.core',
		'gweatherrouting.ui.kivy', 'gweatherrouting.ui.kivy.maplayers',
		'gweatherrouting.ui.common',
		'gweatherrouting.ui'],
	package_data={
		'gweatherrouting': [
			'data/*', 'data/boats/*', 'data/polars/*', 
			'ui/kivy/*.kv'
		]
	},
	entry_points={
		'console_scripts': [
			'gweatherrouting-kivy=gweatherrouting.main:startUIKivy'
		],
	},
	options={},
	executables={},
	install_requires=open ('requirements.kivy.txt', 'r').read ().split ('\n')
)
