# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from setuptools import find_packages
from setuptools import setup
from regattasim import config

setup(name='regattasim',
	version=0.1,
	description='',
	author=['Riccardo Apolloni', 'Davide Gessa'],
	setup_requires='setuptools',
	author_email=['riccardo.apolloni@gmail.com', 'gessadavide@gmail.com'],
	packages=['regattasim'],
	entry_points={
		'console_scripts': [
			'regattasim=regattasim.main:main'
		],
	},
	install_requires=open ('requirements.txt', 'r').read ().split ('\n')
)
