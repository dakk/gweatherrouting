# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
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

from colorlog import ColoredFormatter
import logging


formatter = ColoredFormatter(
	'%(log_color)s[%(asctime)-8s] %(module)s: %(message_log_color)s%(message)s',
	datefmt=None,
	reset=True,
	log_colors = {
		'DEBUG':	'blue',
		'PLUGINFO': 'purple',
		'INFO':	 'green',
		'WARNING':  'yellow',
		'ERROR':	'red',
		'CRITICAL': 'red',
	},
	secondary_log_colors={
		'message': {
			'DEBUG':	'purple',
			'PLUGINFO': 'blue',
			'INFO':	 'yellow',
			'WARNING':  'green',
			'ERROR':	'yellow',
			'CRITICAL': 'red',
		}
	},
	style = '%'
)

stream = logging.StreamHandler ()
stream.setFormatter (formatter)

logger = logging.getLogger ('gweatherrouting')
logger.addHandler (stream)
logger.setLevel (10)

