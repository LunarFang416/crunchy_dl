# crunchy_dl

This python package utilizes the `yt_dlp` package to extend its ablilties to download multiple episodes and shows simultanrously with more user control and actions specified by the user.

The script utilizes threading to speed up download speeds and provides an easy to use interface with multiple ways to download desired anime episodes.

The CLI provides flexibility in wasy throughw hich users can download episodes and gives preview of the anime before commencing downloads.

## Quick Start

### Download through PyPI

You can download the package through pip: `pip install crunchy_dl`

### Cloning this repository

Clone this repository onto your local machine: `git clone https://github.com/LunarFang416/crunchy_dl`

Install requirements: `pip install -r requirements.txt`

Note: Make sure to have ffmpeg downloaded onto your machine, otherwise downloads will not go to completion. More information on how to download can be 
found [here](https://ffmpeg.org).

## Ways to download anime:

### Using YAML config file (recommended):


Using the template `yaml_template.yml` provided in the repository, you can configure all of your metadata easily and specify all the specifc shows and
anime episodes you want to download with their respective requirements. You can specify further [yt_dlp options](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L171) in the args section for each anime episdoe/show
you are downloading by adding a leading hyphen for each option.

To download using this method, the following cli command needs to be executed: `crunchy config [path_to_config_file]`

All config files will undergo a validation check; thus, and errors in the formatting or the schema of the yaml file will be notified to the user before
commencing download.

An exmaple YAML file configuration can be see as follows:
```yaml
username: [username]
password: [password]
ffmpeg_location: /Users/ffmpeg
destination: /Users/anime/
threads: 7
download:
 series:
  - url: https://beta.crunchyroll.com/series/GRMGQJ0ZR/the-idolmster-cinderella-girls-theater
    start: 22
    end: 24
  - url: https://beta.crunchyroll.com/series/G79H23V24/sabikui-bisco
    season: 1
    start: 1
    end: 10
  episodes:
   - url: https://beta.crunchyroll.com/watch/GWDU8KNNX/soar-on-king-trumpets
     args:
      - arg: -no_color
        value: True
   - url: https://beta.crunchyroll.com/watch/GYK5PJV7R/enter-naruto-uzumaki
```

### Using CLI arguments:

Using the cli arguments, you cannot download series and episodes together. Episodes are limited to one download per use. Series can be used to download
multiple episdoes, however this can only be from one series, support for multiple shows has not been configured yet.

You can also configure yt_dlp options when downloading episodes and series. You can use all [yt_dlp options](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L171) 
you are downloading by adding a leading hyphen for each option in the CLI command.

#### Download a single episode:
```console
usage: crunchy episode [-h] -u USERNAME -p PASSWORD -l URL [-t THREADS] [-d DESTINATION] [-v] -f FFMPEG

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Valid CrunchyRoll Username
  -p PASSWORD, --password PASSWORD
                        Valid CrunchyRoll Password
  -l URL, --url URL     Valid CrunchyRoll Series/Episode Link
  -t THREADS, --threads THREADS
                        Number of threads to utilize (1 - 10)
  -d DESTINATION, --destination DESTINATION
                        Destination of where to save downloads
  -v, --verbose         Verbosity of Downloader Output
  -f FFMPEG, --ffmpeg FFMPEG
                        Location of ffmpeg on machine
```

#### Download multiple episodes from a single anime series season:

```console
usage: crunchy series [-h] -u USERNAME -p PASSWORD -l URL [-t THREADS] [-d DESTINATION] [-v] -f FFMPEG [-r RANGE] [-s SEASON]

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Valid CrunchyRoll Username
  -p PASSWORD, --password PASSWORD
                        Valid CrunchyRoll Password
  -l URL, --url URL     Valid CrunchyRoll Series/Episode Link
  -t THREADS, --threads THREADS
                        Number of threads to utilize (1 - 10)
  -d DESTINATION, --destination DESTINATION
                        Destination of where to save downloads
  -v, --verbose         Verbosity of Downloader Output
  -f FFMPEG, --ffmpeg FFMPEG
                        Location of ffmpeg on machine
  -r RANGE, --range RANGE
                        Range of episodes to download from series
  -s SEASON, --season SEASON
                        Specify Season of Series
```

## Tests

```python
pytest
```

## LICENSE

See [LISENCE](https://github.com/LunarFang416/crunchy_dl/blob/master/LICENSE)
