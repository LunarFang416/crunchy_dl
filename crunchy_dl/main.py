from __future__ import annotations
from __future__ import unicode_literals
import argparse
import pprint
import re
import yaml
import cfscrape
import requests
import os
import platform
import threading
import concurrent.futures
from threading import Thread
from sys import exit
from cerberus import Validator, DocumentError
from prettytable import PrettyTable
from .schema import CONFIG_SCHEMA
from contextlib import contextmanager
from itertools import cycle
from shutil import get_terminal_size
from time import sleep
from typing import Sequence
from typing import Optional
from typing import Tuple
from typing import List
from typing import Dict

try:
	import yt_dlp
except:
	print("Please ensure all required libraries specified in requirements.txt are available")
	exit()

__version__ = "0.1.0"

class Logger:
	def __init__(self, verbose: bool) -> None:
		self.verbose = verbose

	def debug(self, msg: str) -> None:
		if self.verbose: print(msg)		

	def info(self, msg: str) -> None:
		if self.verbose: print(msg)
		
	def warning(self, msg: str) -> None:
		if self.verbose: print(msg)

	def error(self, msg: str) -> None:
		print(msg)

class LoaderThread(Thread):
	def __init__(self, desc: str, end: str, timeout: float) -> None:
		Thread.__init__(self)
		self.desc = desc
		self.end = end
		self.timeout = timeout

	def run(self):
		self.active = True
		while self.active:
			steps = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
			for i in cycle(steps):
				if not self.active: break
				print(f"\r{self.desc} {i}", flush=True, end="")
				sleep(self.timeout)	
	
	def stop(self):
		self.active = False

@contextmanager
def loader(desc: str = "Downloading...", end: str = "Finished Downloading!", timeout: float = 0.1) -> None:
	_loader = LoaderThread(desc, end, timeout)
	_loader.start()
	try: yield _loader
	finally:
		_loader.stop()
		_loader.join()
		cols = get_terminal_size((80, 20)).columns
		print("\r" + " " * cols, end="", flush=True)
		print(f"\r{end}", flush=True)

class Downloader:
	def __init__(self, args: Dict[str, str]):
		self.args = args
		self.username = args["username"]	
		self.password = args["password"]
		self.config = {
			"postprocessors": [{"key": "FFmpegEmbedSubtitle"}],
			"ignoreerrors": True,
			"nooverwrites": True,
			"allsubtitles": True,
			"writesubtitles": True,
			"continuedl": True,
			"progress_hooks": [self._hook],
			"progress": True,
			"logger": Logger(self.args["verbosity"]),
			"username": self.args["username"],
			"password": self.args["password"],
			"ffmpeg_location": self.args["ffmpeg_location"],
			"paths": {"home": self.args["destination"]},
		}
		self.downloaded = 0
	def init_downloader(self, args: Optional[Dict[str, str]]):
		config = self.config.copy()
		for arg in args: config.update(arg)
		self.downloader = yt_dlp.YoutubeDL(config)
		return self.downloader
	
	def stdout(self, data: List[Dict[str, str]]):
		table = PrettyTable(["id", "Season", "Episode", "Title"], max_width = 100)
		output = []
		for entry in data:
			output.append([entry["id"], entry["season_number"], entry["episode_number"], entry["title"]])
		table.add_rows(output)
		print(table)

	def _hook(self, downloader: yt_dlp.YoutubeDL) -> None:
		if downloader["status"] == "finished":
			if yt_dlp.utils.determine_ext(downloader["filename"]) in yt_dlp.utils.KNOWN_EXTENSIONS:
				print("Finished downloading", os.path.basename(downloader["filename"]))
				self.downloaded += 1

	def download(self, url: str, args: Optional[Dict[str, str]]) -> None:
		dl = self.init_downloader(args)
		dl.params.update({"progress_hooks": [self._hook]})	
		dl.download([url])
		
class AnimeEpisode(Downloader):
	def extract_info(self, meta_data: Dict[str, str], args: Optional[Dict[str, str]]):
		self.extractor = yt_dlp.extractor.crunchyroll.CrunchyrollBetaIE(self.init_downloader(args))
		try:
			self.extractor._perform_login(self.username, self.password)
			raw_data = self.extractor._real_extract(meta_data["url"])
		except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as error:
			raise error
		raw_data["url"] = meta_data["url"]
		return ([raw_data], args)

class AnimeShow(Downloader):
	def extract_info(self, meta_data: Dict[str, str], args: Optional[Dict[str, str]]):
		self.extractor = yt_dlp.extractor.crunchyroll.CrunchyrollBetaShowIE(self.init_downloader(args))	
		try:
			self.extractor._perform_login(self.username, self.password)
			raw_data = self.extractor._real_extract(meta_data["url"])
		except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as error:
			raise error
		eps_collection = set()
		data = []
		for entry in raw_data["entries"]:
			if (entry["season_number"] == meta_data["season"] and 
				meta_data["start"] <= entry["episode_number"] <= meta_data["end"] and
				(entry["season_number"], entry["episode_number"]) not in eps_collection):
				data.append(entry)
				eps_collection.add((entry["season_number"], entry["episode_number"]))
		return (data, args)
		
def session(config):
	episode_ie = AnimeEpisode(config)
	show_ie = AnimeShow(config)
	video_data = []
	urls = []
	with concurrent.futures.ThreadPoolExecutor(max_workers = config["threads"]) as executor:
		threads = []
		if "series" in config["download"]:
			for series in config["download"]["series"]:
				thread = executor.submit(show_ie.extract_info, series, series["args"])
				threads.append(thread)
		if "episodes" in config["download"]:
			for episode in config["download"]["episodes"]:
				thread = executor.submit(episode_ie.extract_info, episode, episode["args"])
				threads.append(thread)
		
		for thread in concurrent.futures.as_completed(threads):
			result = thread.result()
			video_data.extend(result[0])
			for entries in result[0]:
				urls.append((entries["url"], result[1]))
	dl = Downloader(config)
	
	dl.stdout(video_data)
	proceed = input("Do you want to proceed with your download (y/n)")
	if proceed.lower() == "y":
		with loader():
			with concurrent.futures.ThreadPoolExecutor(max_workers = config["threads"]) as executor:		
				threads = []
				for url, args in urls:
					thread = executor.submit(dl.download, url, args)
					threads.append(thread)	
	else:
		print(f"[EXITED]")

def series_episode_range_type(s: str) -> Tuple[int, int]:
	ep_range = re.match(r"\(?(\d+)\s*?[-|,]?\s*?((\d+))?\)?$", s)
	if not ep_range:
		raise argparse.ArgumentTypeError("'" + s + "' is not a range of number. Expected forms like '0-5' or '2'.")
	print(ep_range)
	start = ep_range.group(1)
	end = ep_range.group(2) or start 
	if int(start) > int(end): end = start
	if int(start) == 0 or int(end) == 0:
		raise argparse.ArgumentTypeError("Please enter a valid range")
	return (int(start), int(end))

def positive_int_type(season: str) -> int:
	try:
		season = int(season)
	except:
		raise argparse.ArgumentTypeError(f"Expected positive integer, received {season}")
	
	if season <= 0:
		raise argparse.ArgumentTypeError(f"Expected positive integer, received {season}")

	return season

def validate_user_metadata(config_data: str) -> Dict[str, ...]:
	config_data = yaml.load(config_data, Loader=yaml.FullLoader)
	config_validator = Validator(CONFIG_SCHEMA)
	is_valid = config_validator.validate(config_data, CONFIG_SCHEMA)
	if not is_valid:
		raise DocumentError(config_validator.errors)
	
	return (True, config_validator.normalized(config_data))
	
def get_user_agent() -> str:
	"""
	Determines the user agent string for the current platform.
  	:returns: str -- User agent string
	"""
	chrome_version = 'Chrome/59.0.3071.115'
	base = 'Mozilla/5.0 '
	base += '%PL% '
	base += 'AppleWebKit/537.36 (KHTML, like Gecko) '
	base += '%CH_VER% Safari/537.36'.replace('%CH_VER%', chrome_version)
	system = platform.system()
	if system == 'Darwin':
		return base.replace('%PL%', '(Macintosh; Intel Mac OS X 10_10_1)')
	if system == 'Windows':
		return base.replace('%PL%', '(Windows NT 6.1; WOW64)')
	if platform.machine().startswith('arm'):
		return base.replace('%PL%', '(X11; CrOS armv7l 7647.78.0)')
	return base.replace('%PL%', '(X11; Linux x86_64)')


def validate_user_credentials(username: str, password: str) -> bool:
	headers = {
		'User-Agent': get_user_agent(),	
		'Connection':'keep-alive'
	}
	session = cfscrape.create_scraper()
	page_fetch = session.get('http://www.crunchyroll.com/login', headers=headers)
	print(page_fetch)
	if page_fetch.status_code == 200:
		token_search = re.search('name="login_form\\[_token\\]" value="([^"]*)"', page_fetch.text)
		if not token_search:
			print("[ERROR] CrunchyRoll login token not found, Try again later")
			return False
		
		token = s.group(1)
		payload = {
			'login_form[redirect_url]': '/',
			'login_form[name]': username,
			'login_form[password]': password,
			'login_form[_token]': token
		}
		
		login = session.post('https://www.crunchyroll.com/login', data=payload, headers=headers, allow_redirects = False)
		if login.status_code == 200:
			return True		
		else:
			print("[ERROR] Invalid Credentials")
			return False
	else:
		print("[ERROR] Login Failed, Try again later")
		return False

def validate_series_url(url: str) -> bool:
	valid_url = r'https?://beta\.crunchyroll\.com/((?:\w{1,2}/)?)series/(\w+)/([\w\-]*)/?(?:\?|$)'
	validity = re.match(valid_url, url)
	if not validity:
		return False
	return True

def validate_episode_url(url: str) -> bool:
	valid_url = r'https?://beta\.crunchyroll\.com/((?:\w{1,2}/)?)watch/(\w+)/([\w\-]*)/?(?:\?|$)'
	validity = re.match(valid_url, url)
	if not validity:	
		return False
	return True

def thread_input_type(threads: str) -> int:
	try:
		threads = int(threads)
	except:
		raise argparse.ArgumentTypeError(f"Expected Positive integer, received {threads}")
	
	if threads < 1 or threads > 10:
		raise argparse.ArgumentTypeError(f"Expected integer between (1 - 10), receievd {threads}")
	
	return threads

def destination_path_type(destination: str) -> str:
	if not os.path.exists(destination):
		raise argparse.ArgumentTypeError("This path does not exist, please enter valid path")
	return destination

def argument_parsing(argv: Optional[Sequence[str]]) -> Tuple[argparse.Namespace, List[str, ...]]:
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--version", help="crunchy_dl version", action="store_true")
	sub_parsers = parser.add_subparsers(dest="action")
	print(parser.parse_known_args(argv)[0])
	if parser.parse_known_args(argv)[0].version:
		return parser.parse_known_args(argv)	
	
	sub_parsers.required = True
	
	episode_parser = sub_parsers.add_parser('episode', help="Download Single Anime Episode")
	series_parser = sub_parsers.add_parser('series', help="Download Anime Series")
	config_parser = sub_parsers.add_parser('config', help="Specify MetaData in separate config file")

	for sub_parser in (episode_parser, series_parser):
		sub_parser.add_argument('-u', '--username', help="Valid CrunchyRoll Username", required=True)
		sub_parser.add_argument('-p', '--password', help="Valid CrunchyRoll Password", required=True)
		sub_parser.add_argument('-l', '--url', help="Valid CrunchyRoll Series/Episode Link", required=True)
		sub_parser.add_argument(
			'-t', '--threads', type=thread_input_type, default = 5,
			help="Number of threads to utilize (1 - 10)"
		)		
		sub_parser.add_argument(
			'-d', '--destination', type=destination_path_type, default = os.getcwd(), 
			help="Destination of where to save downloads"
		)	
		sub_parser.add_argument('-v', '--verbose', action='store_true', help="Verbosity of Downloader Output")		
		sub_parser.add_argument('-f', '--ffmpeg', help="Location of ffmpeg on machine", required=True)

	series_parser.add_argument(
		'-r', "--range",
		type=series_episode_range_type, default=(1, 1),
		help="Range of episodes to download from series"
	)

	series_parser.add_argument('-s', "--season", type=positive_int_type, default=1, help="Specify Season of Series")
	config_parser.add_argument("config_file", help="Path to config file containing metadata")
	
	return parser.parse_known_args(argv)

def main(argv: Optional[Sequence[str]] = None) -> int:
	args, yt_dlp_args  = argument_parsing(argv)

	if args.version:
		print(__version__)
		return 0
	
	if args.action == "config":
		with open(args.config_file) as f:
			config_data = validate_user_metadata(f.read())[1]
	else:
		config_data = {}
		config_data["username"] = args.username
		config_data["password"] = args.password
		config_data["ffmpeg_location"] = args.ffmpeg
		config_data["destination"] = args.destination
		config_data["threads"] = args.threads or 5
		config_data["verbosity"] = args.verbosity
		if args.action == "series":
			config_data["download"] = {
				'series': [{ 	
					"url": args.url,
					"season": args.season,
					"start": args.range[0],
					"end": args.range[1],
					"args": yt_dlp_args
				}]
			}
		else:
			config_data["download"] = {
				"episodes": [{
					"url": args.url,
					"args": yt_dlp_args
				}]
			}			
		
	session(config_data)
	return 0

if __name__ == "__main__":
	raise SystemExit(main())
