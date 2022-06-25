from typing import Dict
from cerberus import DocumentError
import re
import os

def required_type(required: bool, data_type: str) -> Dict[str, str]:
	return {'required': required, 'type': data_type}

def validate_episode_url_schema(field, value, error) -> bool:
	valid_url = r'https?://beta\.crunchyroll\.com/((?:\w{1,2}/)?)watch/(\w+)/([\w\-]*)/?(?:\?|$)'
	validity = re.match(valid_url, value)
	if not validity:
		raise DocumentError("Episode URL is invalid")
		error(field, "Episode URL is invalid")
	return True

def validate_series_url_schema(field, value, error) -> bool:
	valid_url = r'https?://beta\.crunchyroll\.com/((?:\w{1,2}/)?)series/(\w+)/([\w\-]*)/?(?:\?|$)'
	validity = re.match(valid_url, value)
	if not validity:
		raise DocumentError("Series URL is invalid")
		error(field, "Series URL is invalid")
	return True

def valid_thread_input(field, value, error) -> bool:
	try:
		threads = int(value)
	except:
		raise DocumentError(f"Expected int, received {value}")
		error(field, f"Expected int, received {value}")
	if threads < 1 or threads > 10:
		raise DocumentError(f"Valid range for number of threads is (1 - 10), received {threads}")
		error(field, f"Valid range for number of threads is (1 - 10), received {threads}")
	return True

def validate_destination_path(field, value, error) -> bool:
	if not os.path.exists(value):
		raise DocumentError("This path does not exist. Enter a vlid path")
		error(field, "This path does not exist. Enter a vlid path")
	return True


YT_DLP_ARG_SCHEMA = {
	'type': 'dict',
	'required': True,
	'schema': {
		'arg': required_type(True, 'string'),
		'value': required_type(True, 'string')
	}
}

EPISODE_SCHEMA = {
	'url': {
		'required': True,
		'type': 'string',
		'check_with': validate_episode_url_schema,
	},
	'args': {
		'type': 'list',
		'required': False,
		'schema': YT_DLP_ARG_SCHEMA,
		'default': []
	}
}

SERIES_SCHEMA = {
	'url': {
		'required': True,
		'type': 'string',
		'check_with': validate_series_url_schema
	},
	'season': { 'type': 'integer', 'default': 1 },
	'start': { 'type': 'integer', 'default': 1 }, 
	'end': { 'type': 'integer', 'default': 1 },	
	'args': {
        'type': 'list',
        'required': False, 
		'schema': YT_DLP_ARG_SCHEMA,
		'default': []
    }
}

CONFIG_SCHEMA = {
	'username': required_type(True, 'string'),
	'password': required_type(True, 'string'),
	'destination':{ 
		'type': 'string', 
		'default': os.getcwd(),
		'check_with': validate_destination_path	
	},
	'ffmpeg_location': required_type(True, 'string'),
	'verbosity': { 'type': 'boolean', 'default': False },
	'threads': {
		'required': False,
		'type': "integer",
		'check_with': valid_thread_input,
	},
	'download': {
		'required': True,
		'type': 'dict',
		'schema':{ 
			'series':{
				'type': 'list',
				'schema': {
					'type':'dict',
					'schema': SERIES_SCHEMA
				},
			},
			'episodes': {
				'type':'list',
				'schema': {
					'type': 'dict',
					'schema': EPISODE_SCHEMA
				}
			}
		},
	},
	'history':{
		'required': False,
		'type': 'list',
		'schema': {
			'type': 'dict',
			'schema': {
				'date': required_type(True, "date"),
				'completed': required_type(True, "boolean"),
				'queue':{
					'type': 'list',
					'required': True,
					'anyof_schema': [SERIES_SCHEMA, EPISODE_SCHEMA],
				}	
			}
		},

	}
}
