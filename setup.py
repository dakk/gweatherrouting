# -*- coding: utf-8 -*-
# Copyright (C) 2017 Davide Gessa
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
from regattasim import config

setup(name='regattasim',
	version=0.1,
	description='',
	author=['Riccardo Apolloni', 'Davide Gessa'],
	setup_requires='setuptools',
	author_email=['riccardo.apolloni@gmail.com', 'gessadavide@gmail.com'],
	packages=['regattasim', 'regattasim.ui', 'regattasim.core', 'regattasim.core.routers'],
	package_data={'regattasim': ['data/*', 'data/boats/*', 'data/boats/*/*']},
	entry_points={
		'console_scripts': [
			'regattasim=regattasim.main:startUI',
			'regattasim_cli=regattasim.main:startCli'
		],
	},
	install_requires=open ('requirements.txt', 'r').read ().split ('\n')
)
