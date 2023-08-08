# The scraping module that reads mp3 urls and filenames
# from Google.

from . import settings
from typing import List, Tuple
import requests
import re


def _scrape(url: str, word: str) -> List[Tuple[str, str]]:
    '''
    Finds the mp3 urls and their related filenames in a web page.

    Arguments:
        url: Typically a google search url like:
        https://www.google.com/search?q=how+to+pronounce+water or
        https://www.google.com/search?q=define:water.

        word: The word we are searching its pronunciation. It is
        "water" in the above example.

    Returns:
        A list of (url, filename) tuple(s) sorted in ascending
        order of the length of the urls.
    '''
    _html = requests.get(
        url, headers=settings.config_values().mybrowser_headers)

    # Some "hyphenated compound words" like "add-on" appear with underscore
    # in the mp3 filename and mp3 url, but should be searched with hyphen.
    # This change is to address this special case.
    _word_hyphen_to_underscore = re.sub('-', '_', word)

    try:
        # 80 and 30 are the assumed maximum possible number of characters in
        # each mp3 url between its beginning, middle and end patterns.
        mp3_urls = re.findall('%s.{0,80}%s.{0,30}%s' %
                              (settings.MP3_URL_BEGIN_STR, _word_hyphen_to_underscore, settings.MP3_URL_END_STR), _html.text)
    except:
        return ()

    # To remove duplicates in the list
    mp3_urls = list(dict.fromkeys(mp3_urls))

    mp3_urls.sort(key=len)
    mp3_urls = ['http:' + mp3_url for mp3_url in mp3_urls]

    mp3_filenames = []
    # To extract filenames from the mp3 urls
    for _mp3_url in mp3_urls:
        mp3_filenames.append(re.search(settings.patterns(
            _word_hyphen_to_underscore).mp3_filename_pattern, _mp3_url).group(0))

    # For debugging
    # aqt.utils.showText("url:\n" + url + "\n\nword:\n" + word + "\n\nmp3_urls:\n" +
    #                    str(mp3_urls) + "\n\nmp3_filenames:\n" + str(mp3_filenames))

    return tuple(zip(mp3_urls, mp3_filenames))


def search_google(word: str) -> List[Tuple[str, str]]:
    '''
    Searches Google for pronunciation, first using "how to pronounce word",
    and if not found then by "define:word".

    Arguments:
        word

    Returns:
        A list of (url, filename) tuple(s) sorted in ascending
        order of the length of the urls.
    '''

    mp3_urls_and_filenames = _scrape(
        settings.patterns(word).google_pronounce_search_url, word)
    if len(mp3_urls_and_filenames) == 0:
        mp3_urls_and_filenames = _scrape(
            settings.patterns(word).google_define_search_url, word)

    return mp3_urls_and_filenames
