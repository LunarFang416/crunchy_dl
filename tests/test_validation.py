from __future__ import unicode_literals
from ..crunchy_dl.main import (
    validate_series_url,
    validate_episode_url,
    validate_user_credentials,
    validate_user_metadata,
	positive_int_type,
	series_episode_range_type
)
from ..crunchy_dl.schema import (
	valid_thread_input,
	validate_destination_path
)
from cerberus import Validator, DocumentError, errors
from argparse import ArgumentTypeError
import pytest

def test_validate_episode_url():
	assert validate_episode_url("https://beta.crunchyroll.com/") == False
	assert validate_episode_url("https://beta.crunchyroll.com/series/GYQ4MKDZ6/gintama") == False
	assert validate_episode_url("https://beta.crunchyroll.com/watch/GRWEXZWJR/you-guys-do-you-even-have-a-gintama-part-1") == True
	assert validate_episode_url("https://beta.crunchyroll.com/watch/GR3VGV0W6/nobody-knows-your-face") == True
	assert validate_episode_url("https://beta.crunchyroll.com/watch") == False
	assert validate_episode_url("https://beta.crunchyroll.com/watch/GK9U353KM/the-great-dodgeball-plan") == True

def test_validate_series_url():
	assert validate_series_url("https://beta.crunchyroll.com/") == False
	assert validate_series_url("https://beta.crunchyroll.com/watch/GYGG70ZDY/untitled") == False
	assert validate_series_url("https://beta.crunchyroll.com/series/GJ0H7QX0Z/tomodachi-game") == True
	assert validate_series_url("https://beta.crunchyroll.com/series/G6NVG970Y/welcome-to-demon-school-iruma-kun") == True
	assert validate_series_url("https://beta.crunchyroll.com/watch/GK9U353KM/the-great-dodgeball-plan") == False
	assert validate_series_url("https://beta.crunchyroll.com/series/GR75253JY/psycho-pass") == True

def test_valid_thread_input():
	with pytest.raises(DocumentError):
		valid_thread_input("threads", 11, Validator())
		valid_thread_input("threads", -1, Validator())
		valid_thread_input("threads", 0, Validator())
		valid_thread_input("threads", "3", Validator())
		valid_thread_input("threads", "", Validator())
	assert valid_thread_input("threads", 1, Validator()) == True
	assert valid_thread_input("threads", 10, Validator()) == True

def test_valid_destination_path():
	with pytest.raises(DocumentError):
		validate_destination_path("destination", "", Validator())
		validate_destination_path("destination", "mmmmm", Validator())
		validate_destination_path("destination", "////", Validator())
		validate_destination_path("destination", "----", Validator())
	assert validate_destination_path("destination", "/", Validator()) == True
	assert validate_destination_path("destination", "/Users", Validator()) == True
	assert validate_destination_path("destination", "/Users/", Validator()) == True

@pytest.mark.parametrize(
	('_input', 'expected'),
	(('5', 5), ('10', 10), ('100000', 100000), ('1', 1),),
)
def test_positive_int_type(_input, expected):
	assert positive_int_type(_input) == expected


@pytest.mark.parametrize(
	('_input'),
	["-1", "0", "kjhfkj", "orange", "who", "<>", "", " ", "ter8934", "834DFD"] 
)
def test_positive_int_type_error(_input):
	with pytest.raises(ArgumentTypeError):
		positive_int_type(_input)

@pytest.mark.parametrize(
	('_input', 'expected'),
	(('5-4', (5, 5)),('1-1', (1, 1)), ('(5-4)', (5, 5)), 
	 ('6-8', (6, 8)), ('(6-8)', (6, 8)), ('10-1', (10, 10)),
	 ('5-', (5, 5)), ('10', (10, 10)), ('(10, 10)', (10, 10))
))
def test_series_episode_range_type(_input, expected):
	assert series_episode_range_type(_input) == expected

@pytest.mark.parametrize(
	('_input'),
	(('5--4'), ('-1-1'), ('(5-4)))'), ('68)))'), ('10-----1'),
	 ('444j44'), ('rrrrr'), (''), ('0'), ('10-pp')
))
def test_series_episode_range_type_error(_input):
	with pytest.raises(ArgumentTypeError):
		series_episode_range_type(_input)

def test_validate_user_metadata():
	with pytest.raises(DocumentError):
		validate_user_metadata("")
		validate_user_metadata(
            """
            dummy: dummy
            username: jjjj
			"""
		)
		validate_user_metadata(
			"""
			username: s
			password: 3333
			"""
		)				
		validate_user_metadata(
            """
            username: username
            password: password
            ffmpeg_location: location
            destination: destination
            download:
             series:
               - url: url
             episodes:
               - url: url            
            """
		)
		validate_user_metadata(
            """
            username: username
            password: password
            ffmpeg_location: location
            destination: destination
            threads: 11
            download:
             series:
               - url: url
             episodes:
               - url: url            
            """
		)
		validate_user_metadata(
            """
            username: username
            password: password
            ffmpeg_location: location
            destination: destination
            threads: lksdajhf
            download:
             series:
               - url: url
             episodes:
               - url: url
            """
		)

	assert validate_user_metadata(
            """
            username: username
            password: password
            ffmpeg_location: location
            destination: /
            threads: 5
            download:
             series:
               - url: https://beta.crunchyroll.com/series/GJ0H7QX0Z/tomodachi-game
             episodes:
               - url: https://beta.crunchyroll.com/watch/GRWEXZWJR/you-guys-do-you-even-have-a-gintama-part-1
            """
        )[0] == True
	
	assert validate_user_metadata(
            """
            username: username
            password: password
            ffmpeg_location: location
            destination: /
            threads: 5
            download:
             series:
               - url: https://beta.crunchyroll.com/series/GJ0H7QX0Z/tomodachi-game
                 season: 1
                 start: 1
                 end: 10                 
                 """
        )[0] == True

	assert validate_user_metadata(
            """
            username: username
            password: password
            ffmpeg_location: location
            destination: /
            threads: 5
            download:
             series:
               - url: https://beta.crunchyroll.com/series/GJ0H7QX0Z/tomodachi-game
                 season: 1
                 start: 1
                 end: 10                 
                 args:
                  - arg: --username
                    value: test    
             """
        )[0] == True
