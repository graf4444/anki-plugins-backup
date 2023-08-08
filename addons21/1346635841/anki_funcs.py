# Functions interacting with Anki and its display.


from multiprocessing.connection import wait
from PyQt5.QtWidgets import QMenu
from anki import notes
from . import settings, scrape
from aqt import browser, mw
from anki.cards import Card
import re
import requests
from bs4 import BeautifulSoup
import aqt.utils
from typing import Any, List, Dict
from aqt import editor, webview, mw
import sys
import os
import urllib
import html
from anki.httpclient import HttpClient
import time
import random
from .ru_audio import datasource
import copy


# Add external_libs directory to module search path
parent_dir = os.path.abspath(os.path.dirname(__file__))
external_libs_dir = os.path.join(parent_dir, 'external_libs')
sys.path.append(external_libs_dir)
from googletrans import Translator


def _get_word(note: notes.Note) -> str:
    '''
    Extracts and cleans the word (the question) from the note.

    Arguments:
        A note

    Returns:
        A word
    '''

    field0 = note.fields[0]

    field0 = str(field0).replace('&nbsp;', ' ')
    word_and_av_filenames = re.split('[\[\]]|sound:', field0)

    # Removing blank list items
    word_and_av_filenames = list(filter(None, word_and_av_filenames))

    word = word_and_av_filenames[0].strip().lower()

    # Replacing multi-space with single-space in multi-word terms
    word = re.sub('\s+', ' ', word)

    # For debugging
    # aqt.utils.showText("editor.note.fields[0]:\n" + editor.note.fields[0] + "\n\n_field0:\n" +
    #                    field0 + "\n\nword_and_av_filenames:\n" + str(word_and_av_filenames) + "\n\nword:\n" + word)

    return word

def _get_translated_word(note: notes.Note) -> str:
    '''
    Extracts and cleans the word (the question) from the note.

    Arguments:
        A note

    Returns:
        A word
    '''

    field0 = note.fields[1]

    field0 = str(field0).replace('&nbsp;', ' ')
    word_and_av_filenames = re.split('[\[\]]|sound:', field0)

    # Removing blank list items
    word_and_av_filenames = list(filter(None, word_and_av_filenames))

    word = word_and_av_filenames[0].strip().lower()

    # Replacing multi-space with single-space in multi-word terms
    word = re.sub('\s+', ' ', word)

    # For debugging
    # aqt.utils.showText("editor.note.fields[0]:\n" + editor.note.fields[0] + "\n\n_field0:\n" +
    #                    field0 + "\n\nword_and_av_filenames:\n" + str(word_and_av_filenames) + "\n\nword:\n" + word)

    return word


def _get_av_filenames(note: notes.Note) -> List[str]:
    '''
    Extracts and cleans the audio filenames from the note.

    Arguments:
        A note

    Returns:
        A list of filenames
    '''

    pronunciation_field_contents = str(
        note.fields[settings.config_values().pronunciation_field]).replace('&nbsp;', ' ')
    word_and_av_filenames = re.split(
        '[\[\]]|sound:', pronunciation_field_contents)

    # Removing blank list items
    word_and_av_filenames = list(filter(None, word_and_av_filenames))

    av_filenames: List[str] = []
    for word_and_av_filename in word_and_av_filenames:
        if re.match('.*\.mp3', word_and_av_filename):
            av_filenames.append(word_and_av_filename)

    # For debugging
    # aqt.utils.showText("note.fields[settings.config_values().pronunciation_field]:\n" + note.fields[settings.config_values().pronunciation_field] + "\n\nfield0:\n" +
    #                    pronunciation_field_contents + "\n\nword_and_av_filenames:\n" + str(word_and_av_filenames) + "\n\nav_filenames:\n" + str(av_filenames))

    return av_filenames


def add_context_menu(browser: browser.Browser, context_menu: QMenu):
    '''
    Adds the menu "Google Dictionary" to the context menu (right click menu)
    in the browser, adds actions (submenu items) to the menu and assigns functions
    to the actions.

    By clicking the respective button one of the below happens:
    1- _add_pronunciation_mp3s_batch is triggered and pronunciations will be added to the entries.
    2- _add_1st_definition_batch is triggered and only the first meaning will be added to the entries.
    3- _add_all_definitions_batch is triggered and all meanings will be added to the entries.
    4- _add_translation_batch is triggered and translation in the specified target language
       will be added to the entries.

    '''
    _qmenu = context_menu.addMenu("Google Dictionary")

    _batch_add_pronunciation_action = _qmenu.addAction(
        "Add Pronunciation")
    _batch_add_1st_definition_action = _qmenu.addAction("Add 1st Definition")
    _batch_add_all_definitions_action = _qmenu.addAction("Add All Definitions")
    _batch_add_translation_action = _qmenu.addAction("Add Translation")
    _qmenu.addActions((_batch_add_pronunciation_action, _batch_add_1st_definition_action,
                      _batch_add_all_definitions_action, _batch_add_translation_action))

    _batch_add_pronunciation_action.triggered.connect(
        lambda _, b=browser: _add_pronunciation_mp3s_batch(b))
    _batch_add_1st_definition_action.triggered.connect(
        lambda _, b=browser: _add_1st_definition_batch(b))
    _batch_add_all_definitions_action.triggered.connect(
        lambda _, b=browser: _add_all_definitions_batch(b))
    _batch_add_translation_action.triggered.connect(
        lambda _, b=browser: _add_translation_batch(b))

    return


def _add_pronunciation_mp3s_batch(browser: browser.Browser) -> None:
    '''
    Finds and adds US and/or GB pronunciations after right clicking in
    the add-on menu (batch use) to the specified field(s) in the config file.

    Arguments:
        browser, from which the user selected notes will be used.

    Returns:
        None. Adds the found [sound:filename.mp3] tags to the entries
        and the related audio files in the collection.media folder (in a typical
        Windows installation in:
        C:\_Users\_your_name\AppData\Roaming\Anki2\_your_name\collection.media').
        No change will be done if a pronunciation is not found.
    '''

    # Works in sequence as (for all the selected notes in a for loop):
    # 1- Gets the word from the note
    #
    # 2- Searches Google for pronunciation
    #
    # 3- If one pronunciation is found (usually the US is found first), it makes
    #    the other (usually GB) url by replacing "us" with "gb" in the url
    #    filename part (or vice versa if GB is found first).
    #
    # 4- Checks the existing audio/video filenames to find whether
    #    pronunciation files are already there.
    #
    # 5- Tries to add the US and/or GB pronunciations based on config file flag
    #    values.

    note_ids = browser.selectedNotes()

    for note_id in note_ids:
        note = mw.col.getNote(note_id)

        # 1
        word = _get_word(note)

        # 2
        mp3_urls_and_filenames = scrape.search_google(word)
        if len(mp3_urls_and_filenames) == 0:
            break
        else:
            # Only the first url is used.
            # The rest (if any) are reserved for possible future use.
            (mp3_url, mp3_filename) = mp3_urls_and_filenames[0]

        # Wait times are added for scraping safety
        _FIXED_DELAY = 1
        _RND_DELAY_COEF = 1
        time.sleep(_FIXED_DELAY+_RND_DELAY_COEF*random.random())

        # Some "hyphenated compound words" like "add-on" appear with underscore
        # in the mp3 filename and mp3 url, but should be searched with hyphen.
        # This change is to address this special case.
        word_hyphen_to_underscore = re.sub('-', '_', word)

        # 3
        if re.match(settings.patterns(word_hyphen_to_underscore).GB_mp3_filename_pattern, mp3_filename):
            mp3_url_gb = mp3_url
            us_or_gb_sub_string = re.search(
                '[_-]gb[_-]', mp3_filename).group(0)
            mp3_url_us = re.sub(
                '[_-]gb[_-]', us_or_gb_sub_string.replace('gb', 'us'), mp3_url)
        elif re.match(settings.patterns(word_hyphen_to_underscore).US_mp3_filename_pattern, mp3_filename):
            mp3_url_us = mp3_url
            us_or_gb_sub_string = re.search(
                '[_-]us[_-]', mp3_filename).group(0)
            mp3_url_gb = re.sub(
                '[_-]us[_-]', us_or_gb_sub_string.replace('us', 'gb'), mp3_url)

        # 4
        GB_pronunciation_exists = US_pronunciation_exists = False
        av_filenames = _get_av_filenames(note)
        for av_filename in av_filenames:
            if re.match(settings.patterns(word_hyphen_to_underscore).GB_mp3_filename_pattern, av_filename):
                GB_pronunciation_exists = True
            if re.match(settings.patterns(word_hyphen_to_underscore).US_mp3_filename_pattern, av_filename):
                US_pronunciation_exists = True

        try_adding_GB_pronunciation = try_adding_US_pronunciation = False
        if settings.config_values().add_GB_pronunciation and (not(GB_pronunciation_exists) or settings.config_values().keep_pronunciation_duplicates):
            try_adding_GB_pronunciation = True
        if settings.config_values().add_US_pronunciation and (not(US_pronunciation_exists) or settings.config_values().keep_pronunciation_duplicates):
            try_adding_US_pronunciation = True

        note.fields[settings.config_values().pronunciation_field] += "</br></br></br>"
        # 5
        if settings.config_values().US_pronunciation_first:
            if (requests.head(mp3_url_us).status_code == 200) and try_adding_US_pronunciation:
                mp3_filename = os.path.basename(
                    urllib.parse.unquote(mp3_url_us))
                filecontents = HttpClient().get(mp3_url_us).content
                newfilename = mw.col.media.write_data(
                    mp3_filename, filecontents)
                note.fields[settings.config_values(
                ).pronunciation_field] += f"US [sound:{html.escape(newfilename, quote=False)}]"

            if (requests.head(mp3_url_gb).status_code == 200) and try_adding_GB_pronunciation:
                mp3_filename = os.path.basename(
                    urllib.parse.unquote(mp3_url_gb))
                filecontents = HttpClient().get(mp3_url_gb).content
                newfilename = mw.col.media.write_data(
                    mp3_filename, filecontents)
                note.fields[settings.config_values(
                ).pronunciation_field] += f"GB [sound:{html.escape(newfilename, quote=False)}]"

        else:
            if (requests.head(mp3_url_gb).status_code == 200) and try_adding_GB_pronunciation:
                mp3_filename = os.path.basename(
                    urllib.parse.unquote(mp3_url_gb))
                filecontents = HttpClient().get(mp3_url_gb).content
                newfilename = mw.col.media.write_data(
                    mp3_filename, filecontents)
                note.fields[settings.config_values(
                ).pronunciation_field] += f"GB [sound:{html.escape(newfilename, quote=False)}]"

            if (requests.head(mp3_url_us).status_code == 200) and try_adding_US_pronunciation:
                mp3_filename = os.path.basename(
                    urllib.parse.unquote(mp3_url_us))
                filecontents = HttpClient().get(mp3_url_us).content
                newfilename = mw.col.media.write_data(
                    mp3_filename, filecontents)
                note.fields[settings.config_values(
                ).pronunciation_field] += f"US [sound:{html.escape(newfilename, quote=False)}]"

        # Applies the new content.
        note.flush()
        
    return


def _add_1st_definition_batch(browser: browser.Browser) -> None:
    '''Adds only the first definition elements given by api.dictionaryapi.dev
    after right clicking in the add-on menu (batch use) to the specified
    field(s) in the config file.'''
    # Same as _add_all_definitions_batch, just breaking the loop after the first definition.

    note_ids = browser.selectedNotes()

    for note_id in note_ids:
        note = mw.col.getNote(note_id)

        word = _get_word(note)

        # Gets the word from api.dictionaryapi.dev (than returns a list of length 1).
        try:
            api_json = requests.get(
                "https://api.dictionaryapi.dev/api/v2/entries/en/" + word).json()[0]
        except:
            break

        # _answer will be constructed and used to fill the "Back" box.
        _defsectname_defsectvalue: Dict[str, str] = {}
        _defsectname_fieldnum: Dict[str, int] = {}

        try:
            if settings.config_values().first_definition_phonetic_field:
                if settings.config_values().first_definition_phonetic_title:
                    _defsectname_defsectvalue['phonetic'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definition_phonetic_title}</font>'
                else:
                    _defsectname_defsectvalue['phonetic'] = ''

                _defsectname_defsectvalue['phonetic'] += f"<font color={settings.config_values().first_definition_phonetic_color}>{api_json['phonetic']}<br><br>"
                _defsectname_fieldnum['phonetic'] = settings.config_values(
                ).first_definition_phonetic_field
        except:
            pass

        # Loop to add all the meanings, plus formatting.
        for meaning in api_json['meanings']:
            try:
                if settings.config_values().first_definitions_pos_title:
                    _defsectname_defsectvalue[
                        'partOfSpeech'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definitions_pos_title}</font>'
                else:
                    _defsectname_defsectvalue['partOfSpeech'] = ''

                _defsectname_defsectvalue[
                    'partOfSpeech'] += f"<b><font color={settings.config_values().first_definitions_pos_color}>{meaning['partOfSpeech']}</font></b><br>"
                _defsectname_fieldnum['partOfSpeech'] = settings.config_values(
                ).first_definitions_pos_field
            except:
                pass

            for definition in meaning['definitions']:
                try:
                    if settings.config_values().first_definition_definition_title:
                        _defsectname_defsectvalue[
                            'definition'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definition_definition_title}</font>'
                    else:
                        _defsectname_defsectvalue['definition'] = ''

                    _defsectname_defsectvalue[
                        'definition'] += f"<font color={settings.config_values().first_definition_definition_color}>{definition['definition']}</font><br>"
                    _defsectname_fieldnum['definition'] = settings.config_values(
                    ).first_definition_definition_field
                except:
                    pass

                try:
                    if definition['example']:
                        if settings.config_values().first_definition_example_title:
                            _defsectname_defsectvalue[
                                'example'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definition_example_title}</font>'
                        else:
                            _defsectname_defsectvalue['example'] = ''

                        _defsectname_defsectvalue[
                            'example'] += f"<font color={settings.config_values().first_definition_example_color}>{definition['example']}</font><br>"
                        _defsectname_fieldnum['example'] = settings.config_values(
                        ).first_definition_example_field
                except:
                    pass

                try:
                    if definition['synonyms']:
                        if settings.config_values().first_definition_synonyms_title:
                            _defsectname_defsectvalue[
                                'synonyms'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definition_synonyms_title}</font>'
                        else:
                            _defsectname_defsectvalue['synonyms'] = ''

                        _defsectname_defsectvalue['synonyms'] += f"<font color={settings.config_values().first_definition_synonyms_color}>{settings.config_values().synonyms_and_antonyms_separator.join(definition['synonyms'])}</font><br>"
                        _defsectname_fieldnum['synonyms'] = settings.config_values(
                        ).first_definition_synonyms_field
                except:
                    pass

                try:
                    if definition['antonyms']:
                        if settings.config_values().first_definition_antonyms_title:
                            _defsectname_defsectvalue[
                                'antonyms'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definition_antonyms_title}</font>'
                        else:
                            _defsectname_defsectvalue['antonyms'] = ''

                        _defsectname_defsectvalue['antonyms'] += f"<font color={settings.config_values().first_definition_antonyms_color}>{settings.config_values().synonyms_and_antonyms_separator.join(definition['antonyms'])}</font><br>"
                        _defsectname_fieldnum['antonyms'] = settings.config_values(
                        ).first_definition_antonyms_field
                except:
                    pass

                break
            break

        _separator = f'<font color={settings.config_values().not_overwrite_separator_color}>{settings.config_values().not_overwrite_separator}</font>'

        # For debugging
        # aqt.utils.showText(str(_defsectname_defsectvalue))
        # aqt.utils.showText(str(_defsectname_fieldnum))

        _note_fields_temp: Dict[int, str] = {}

        for _fieldnum in _defsectname_fieldnum.values():
            _note_fields_temp[_fieldnum] = ''

        for _defsectname, _fieldnum in _defsectname_fieldnum.items():
            _note_fields_temp[_fieldnum] += _defsectname_defsectvalue[_defsectname]

        # Removes duplicates from _defsectname_fieldnum.values()
        _fieldnums = list(dict.fromkeys(list(_defsectname_fieldnum.values())))

        for _fieldnum in _fieldnums:
            if not(settings.config_values().overwrite_1st_definition) and note.fields[_fieldnum]:
                _note_fields_temp[_fieldnum] = note.fields[_fieldnum] + \
                    _separator + _note_fields_temp[_fieldnum]

        # For debugging
        # aqt.utils.showText(str(_note_fields_temp))

        # Removes any of the line breaks added in the above loop at the beginning
        # or end of _answer.
        # Can be replaced by removesuffix and removeprefix in the later Anki versions
        # for better readability.
        for _fieldnum in _note_fields_temp.keys():
            while _note_fields_temp[_fieldnum][:4] == '<br>':
                _note_fields_temp[_fieldnum] = _note_fields_temp[_fieldnum][4:]

            while _note_fields_temp[_fieldnum][-4:] == '<br>':
                _note_fields_temp[_fieldnum] = _note_fields_temp[_fieldnum][:-4]

            if _fieldnum != -1:
                note.fields[_fieldnum] = _note_fields_temp[_fieldnum]

        # For debugging
        # aqt.utils.showText(str(note.fields[1]))

        # Applies the new content.
        note.flush()

    return


def _add_all_definitions_batch(browser: browser.Browser) -> None:
    '''Adds all meanings given by api.dictionaryapi.dev after right clicking
    in the add-on menu (batch use) to the specified field in the config file.'''

    note_ids = browser.selectedNotes()

    for note_id in note_ids:
        note = mw.col.getNote(note_id)

        word = _get_word(note)

        # Gets the word from api.dictionaryapi.dev (that returns a list of length 1).
        try:
            api_json = requests.get(
                "https://api.dictionaryapi.dev/api/v2/entries/en/" + word).json()[0]
        except:
            break

        # _answer will be constructed and used to fill the "Back" box.
        _answer: str = ''

        try:
            if settings.config_values().all_definitions_phonetic_field != -1:
                if settings.config_values().all_definitions_phonetic_title:
                    _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_phonetic_title}</font>'
                _answer += f'<font color={settings.config_values().all_definitions_phonetic_color}>{api_json["phonetic"]}</font>' + '<br><br>'
        except:
            pass

        # Loop to add all the meanings, plus formatting.
        for meaning in api_json['meanings']:
            try:
                if settings.config_values().all_definitions_pos_field != -1:
                    if settings.config_values().all_definitions_pos_title:
                        _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_pos_title}</font>'
                    _answer += f"<font color={settings.config_values().all_definitions_pos_color}><b>{meaning['partOfSpeech']}</b><br></font>"
            except:
                pass

            for definition in meaning['definitions']:
                if settings.config_values().all_definitions_definition_field != -1:
                    if settings.config_values().all_definitions_definition_title:
                        _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_definition_title}</font>'
                    try:
                        _answer += (
                            f"<font color={settings.config_values().all_definitions_definition_color}>{definition['definition']}</font>" + '<br>')
                    except:
                        pass

                if settings.config_values().all_definitions_example_field != -1:
                    try:
                        if definition['example']:
                            if settings.config_values().all_definitions_example_title:
                                _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_example_title}</font>'
                            _answer += (f'<font color={settings.config_values().all_definitions_example_color}>' + '"' +
                                        definition['example'] + '"' + '</font>' + '<br>')
                    except:
                        pass

                if settings.config_values().all_definitions_synonyms_field != -1:
                    try:
                        if definition['synonyms']:
                            if settings.config_values().all_definitions_synonyms_title:
                                _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_synonyms_title}</font>'
                            _answer += f"<font color={settings.config_values().all_definitions_synonyms_color}>{settings.config_values().synonyms_and_antonyms_separator.join(definition['synonyms'])}</font><br>"
                    except:
                        pass

                if settings.config_values().all_definitions_antonyms_field != -1:
                    try:
                        if definition['antonyms']:
                            if settings.config_values().all_definitions_antonyms_title:
                                _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_antonyms_title}</font>'
                            _answer += f"<font color={settings.config_values().all_definitions_antonyms_color}>{settings.config_values().synonyms_and_antonyms_separator.join(definition['antonyms'])}</font><br>"
                    except:
                        pass

                _answer += '<br>'
            _answer += '<br>'

        # Removes any of the line breaks added in the above loop at the beginning
        # or end of _answer.
        # Can be replaced by removesuffix and removeprefix in the later Anki versions
        # for better readability.
        while _answer[:4] == '<br>':
            _answer = _answer[4:]

        while _answer[-4:] == '<br>':
            _answer = _answer[:-4]

        # For debugging
        # aqt.utils.showText(str(note.fields[settings.config_values().all_definitions_field]))

        # If overwrite is disabled, separates the new and old contents with the specified separator
        # in the config file.
        if settings.config_values().overwrite_all_definitions or not(note.fields[settings.config_values().all_definitions_field]):
            note.fields[settings.config_values(
            ).all_definitions_field] = _answer
        else:
            note.fields[settings.config_values().all_definitions_field] += (
                f'<font color={settings.config_values().not_overwrite_separator_color}>{settings.config_values().not_overwrite_separator}</font>' + _answer)

        # For debugging
        # aqt.utils.showText(str(note.fields[1]))

        # Applies the new content.
        note.flush()

    return


def _add_translation_batch(browser: browser.Browser) -> None:
    '''Adds translation given by googletrans (https://pypi.org/project/googletrans/)
    after right clicking in the add-on menu (batch use) to the specified field(s)
    in the config file.'''

    note_ids = browser.selectedNotes()

    for note_id in note_ids:
        note = mw.col.getNote(note_id)

        word = _get_word(note)

        if not(settings.config_values().translation_field):
            return

        # Initiating Translator
        _translator = Translator(
            user_agent=settings.config_values().mybrowser_headers['User-Agent'])

        # Gets the translation
        try:
            _translated = _translator.translate(
                word, src='en', dest=settings.config_values().translation_target_language)
        except:
            break

        # _answer will be constructed and used to fill the "Back" box.
        _answer: str = ''

        if settings.config_values().add_language_name:
            try:
                _answer += settings.iso_639_1_codes_dict[settings.config_values(
                ).translation_target_language]
            except:
                pass

        if settings.config_values().translation_title:
            _answer = (f'<font color="{settings.config_values().titles_color}">' +
                       _answer + settings.config_values().translation_title + '</font>')

        else:
            _answer = ''

        try:
            _answer += (f'<font color="{settings.config_values().translation_color}">' +
                        _translated.text + '</font>')
        except:
            pass

        try:
            if settings.config_values().add_transliteration:
                _answer += (f'<font color="{settings.config_values().transliteration_color}">' + ' (' +
                            _translated.pronunciation + ')' + '</font>')
        except:
            pass

        # If overwrite is disabled, separates the new and old contents with the specified separator
        # in the config file.
        _separator = f'<font color={settings.config_values().not_overwrite_separator_color}>{settings.config_values().not_overwrite_separator}</font>'

        if settings.config_values().overwrite_translation or not(note.fields[settings.config_values().translation_field]):
            note.fields[settings.config_values(
            ).translation_field] = _answer
        else:
            note.fields[settings.config_values().translation_field] += (
                _separator + _answer)

        # For debugging
        # aqt.utils.showText(str(editor.note.fields[1]))

        # Applies the new content.
        note.flush()

    return


def _add_pronunciation_mp3s_single(editor: editor.Editor) -> None:
    '''
    Finds and adds US and/or GB pronunciations after clicking the add-on
    button to the specified field(s) in the config file.

    Arguments:
        editor

    Returns:
        None. If successful, adds the [sound:filename.mp3] tags to the entries
        and the related audio files in the collection.media folder (in a typical
        Windows installation in:
        C:\_Users\_your_name\AppData\Roaming\Anki2\_your_name\collection.media').
        If unsuccessful, quits without any change.
    '''

    # Works in sequence as:
    # 1- Gets the word from the editor
    #
    # 2- Searches Google for pronunciation
    #
    # 3- If one pronunciation is found (usually the US is found first), it makes
    #    the other (usually GB) url by replacing "us" with "gb" in the url
    #    filename part (or vice versa if GB is found first).
    #
    # 4- Checks the existing audio/video filenames in the editor to find whether
    #    pronunciation files are already there.
    #
    # 5- Tries to add the US and/or GB pronunciations based on config file flag
    #    values.

    # 1
    word = _get_word(editor.note)

    # 2
    if len(scrape.search_google(word)) == 0:
        return

    # Only the first url is used.
    # The rest (if any) are reserved for possible future use.
    (mp3_url, mp3_filename) = scrape.search_google(word)[0]

    # Some "hyphenated compound words" like "add-on" appear with underscore
    # in the mp3 filename and mp3 url, but should be searched with hyphen.
    # This change is to address this special case.
    word_hyphen_to_underscore = re.sub('-', '_', word)

    # 3
    if re.match(settings.patterns(word_hyphen_to_underscore).GB_mp3_filename_pattern, mp3_filename):
        mp3_url_gb = mp3_url
        us_or_gb_sub_string = re.search('[_-]gb[_-]', mp3_filename).group(0)
        mp3_url_us = re.sub(
            '[_-]gb[_-]', us_or_gb_sub_string.replace('gb', 'us'), mp3_url)
    elif re.match(settings.patterns(word_hyphen_to_underscore).US_mp3_filename_pattern, mp3_filename):
        mp3_url_us = mp3_url
        us_or_gb_sub_string = re.search('[_-]us[_-]', mp3_filename).group(0)
        mp3_url_gb = re.sub(
            '[_-]us[_-]', us_or_gb_sub_string.replace('us', 'gb'), mp3_url)

    # 4
    GB_pronunciation_exists = US_pronunciation_exists = False
    av_filenames = _get_av_filenames(editor.note)
    for av_filename in av_filenames:
        if re.match(settings.patterns(word_hyphen_to_underscore).GB_mp3_filename_pattern, av_filename):
            GB_pronunciation_exists = True
        if re.match(settings.patterns(word_hyphen_to_underscore).US_mp3_filename_pattern, av_filename):
            US_pronunciation_exists = True

    # 5
    try_adding_GB_pronunciation = try_adding_US_pronunciation = False
    if settings.config_values().add_GB_pronunciation and (not(GB_pronunciation_exists) or settings.config_values().keep_pronunciation_duplicates):
        try_adding_GB_pronunciation = True
    if settings.config_values().add_US_pronunciation and (not(US_pronunciation_exists) or settings.config_values().keep_pronunciation_duplicates):
        try_adding_US_pronunciation = True

    if settings.config_values().US_pronunciation_first:
        if (requests.head(mp3_url_us).status_code == 200) and try_adding_US_pronunciation:
            file_path_us = editor.urlToFile(mp3_url_us)

            # This extra line was added after Anki upgraded to to 2.1.5x (specifically 2.1.54 Qt5 and Qt6)
            # The old versions didn't need the complete media file path to be passed to _addMedia
            file_path_us = os.path.join(mw.col.media.dir(), file_path_us)

            editor.note.fields[settings.config_values(
            ).pronunciation_field_us] +=  editor._addMedia(file_path_us)

        if (requests.head(mp3_url_gb).status_code == 200) and try_adding_GB_pronunciation:
            file_path_gb = editor.urlToFile(mp3_url_gb)

            # This extra line was added after Anki upgraded to to 2.1.5x (specifically 2.1.54 Qt5 and Qt6)
            # The old versions didn't need the complete media file path to be passed to _addMedia
            file_path_gb = os.path.join(mw.col.media.dir(), file_path_gb)

            editor.note.fields[settings.config_values(
            ).pronunciation_field_gb] += editor._addMedia(file_path_gb)

    else:
        if (requests.head(mp3_url_gb).status_code == 200) and try_adding_GB_pronunciation:
            file_path_gb = editor.urlToFile(mp3_url_gb)

            # This extra line was added after Anki upgraded to to 2.1.5x (specifically 2.1.54 Qt5 and Qt6)
            # The old versions didn't need the complete media file path to be passed to _addMedia
            file_path_gb = os.path.join(mw.col.media.dir(), file_path_gb)

            editor.note.fields[settings.config_values(
            ).pronunciation_field_gb] += editor._addMedia(file_path_gb)

        if (requests.head(mp3_url_us).status_code == 200) and try_adding_US_pronunciation:
            file_path_us = editor.urlToFile(mp3_url_us)

            # This extra line was added after Anki upgraded to to 2.1.5x (specifically 2.1.54 Qt5 and Qt6)
            # The old versions didn't need the complete media file path to be passed to _addMedia
            file_path_us = os.path.join(mw.col.media.dir(), file_path_us)

            editor.note.fields[settings.config_values(
            ).pronunciation_field_us] += editor._addMedia(file_path_us)

    # Applies the new content.
    editor.loadNote()


def _add_1st_definition_single(editor: editor.Editor) -> None:
    '''Adds only the first definition elements given by api.dictionaryapi.dev
    after clicking the add-on button to the specified field(s) in the config file.'''
    # Same as _add_all_definitions_single, just breaking the loop after the first definition.

    word = _get_word(editor.note)

    # Gets the word from api.dictionaryapi.dev (than returns a list of length 1).
    try:
        api_json = requests.get(
            "https://api.dictionaryapi.dev/api/v2/entries/en/" + word).json()[0]
    except:
        return

    # _answer will be constructed and used to fill the "Back" box.
    _defsectname_defsectvalue: Dict[str, str] = {}
    _defsectname_fieldnum: Dict[str, int] = {}

    try:
        if settings.config_values().first_definition_phonetic_field:
            if settings.config_values().first_definition_phonetic_title:
                _defsectname_defsectvalue['phonetic'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definition_phonetic_title}</font>'
            else:
                _defsectname_defsectvalue['phonetic'] = ''

            _defsectname_defsectvalue['phonetic'] += f"<font color={settings.config_values().first_definition_phonetic_color}>{api_json['phonetic']}<br><br>"
            _defsectname_fieldnum['phonetic'] = settings.config_values(
            ).first_definition_phonetic_field
    except:
        pass

    # Loop to add all the meanings, plus formatting.
    for meaning in api_json['meanings']:
        try:
            if settings.config_values().first_definitions_pos_title:
                _defsectname_defsectvalue['partOfSpeech'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definitions_pos_title}</font>'
            else:
                _defsectname_defsectvalue['partOfSpeech'] = ''

            _defsectname_defsectvalue['partOfSpeech'] += f"<b><font color={settings.config_values().first_definitions_pos_color}>{meaning['partOfSpeech']}</font></b><br>"
            _defsectname_fieldnum['partOfSpeech'] = settings.config_values(
            ).first_definitions_pos_field
        except:
            pass

        for definition in meaning['definitions']:
            try:
                if settings.config_values().first_definition_definition_title:
                    _defsectname_defsectvalue['definition'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definition_definition_title}</font>'
                else:
                    _defsectname_defsectvalue['definition'] = ''

                _defsectname_defsectvalue['definition'] += f"<font color={settings.config_values().first_definition_definition_color}>{definition['definition']}</font><br>"
                _defsectname_fieldnum['definition'] = settings.config_values(
                ).first_definition_definition_field
            except:
                pass

            try:
                if definition['example']:
                    if settings.config_values().first_definition_example_title:
                        _defsectname_defsectvalue[
                            'example'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definition_example_title}</font>'
                    else:
                        _defsectname_defsectvalue['example'] = ''

                    _defsectname_defsectvalue[
                        'example'] += f"<font color={settings.config_values().first_definition_example_color}>{definition['example']}</font><br>"
                    _defsectname_fieldnum['example'] = settings.config_values(
                    ).first_definition_example_field
            except:
                pass

            try:
                if definition['synonyms']:
                    if settings.config_values().first_definition_synonyms_title:
                        _defsectname_defsectvalue[
                            'synonyms'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definition_synonyms_title}</font>'
                    else:
                        _defsectname_defsectvalue['synonyms'] = ''

                    _defsectname_defsectvalue['synonyms'] += f"<font color={settings.config_values().first_definition_synonyms_color}>{settings.config_values().synonyms_and_antonyms_separator.join(definition['synonyms'])}</font><br>"
                    _defsectname_fieldnum['synonyms'] = settings.config_values(
                    ).first_definition_synonyms_field
            except:
                pass

            try:
                if definition['antonyms']:
                    if settings.config_values().first_definition_antonyms_title:
                        _defsectname_defsectvalue[
                            'antonyms'] = f'<font color={settings.config_values().titles_color}>{settings.config_values().first_definition_antonyms_title}</font>'
                    else:
                        _defsectname_defsectvalue['antonyms'] = ''

                    _defsectname_defsectvalue['antonyms'] += f"<font color={settings.config_values().first_definition_antonyms_color}>{settings.config_values().synonyms_and_antonyms_separator.join(definition['antonyms'])}</font><br>"
                    _defsectname_fieldnum['antonyms'] = settings.config_values(
                    ).first_definition_antonyms_field
            except:
                pass

            break
        break

    _separator = f'<font color={settings.config_values().not_overwrite_separator_color}>{settings.config_values().not_overwrite_separator}</font>'

    # For debugging
    # aqt.utils.showText(str(_defsectname_defsectvalue))
    # aqt.utils.showText(str(_defsectname_fieldnum))

    _note_fields_temp: Dict[int, str] = {}

    for _fieldnum in _defsectname_fieldnum.values():
        _note_fields_temp[_fieldnum] = ''

    for _defsectname, _fieldnum in _defsectname_fieldnum.items():
        _note_fields_temp[_fieldnum] += _defsectname_defsectvalue[_defsectname]

    # Removes duplicates from _defsectname_fieldnum.values()
    _fieldnums = list(dict.fromkeys(list(_defsectname_fieldnum.values())))

    for _fieldnum in _fieldnums:
        if not(settings.config_values().overwrite_1st_definition) and editor.note.fields[_fieldnum]:
            _note_fields_temp[_fieldnum] = editor.note.fields[_fieldnum] + \
                _separator + _note_fields_temp[_fieldnum]

    # For debugging
    # aqt.utils.showText(str(_note_fields_temp))

    # Removes any of the line breaks added in the above loop at the beginning
    # or end of _answer.
    # Can be replaced by removesuffix and removeprefix in the later Anki versions
    # for better readability.
    for _fieldnum in _note_fields_temp.keys():
        while _note_fields_temp[_fieldnum][:4] == '<br>':
            _note_fields_temp[_fieldnum] = _note_fields_temp[_fieldnum][4:]

        while _note_fields_temp[_fieldnum][-4:] == '<br>':
            _note_fields_temp[_fieldnum] = _note_fields_temp[_fieldnum][:-4]

        if _fieldnum != -1:
            editor.note.fields[_fieldnum] = _note_fields_temp[_fieldnum]

    # For debugging
    # aqt.utils.showText(str(editor.note.fields[1]))

    # Applies the new content.
    editor.loadNote()

    return


def _add_all_definitions_single(editor: editor.Editor) -> None:
    '''Adds all meanings given by api.dictionaryapi.dev after clicking the add-on
    button to the specified field in the config file.'''

    word = _get_word(editor.note)

    # Gets the word from api.dictionaryapi.dev (that returns a list of length 1).
    try:
        api_json = requests.get(
            "https://api.dictionaryapi.dev/api/v2/entries/en/" + word).json()[0]
    except:
        return

    # _answer will be constructed and used to fill the "Back" box.
    _answer: str = ''

    try:
        if settings.config_values().all_definitions_phonetic_field != -1:
            if settings.config_values().all_definitions_phonetic_title:
                _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_phonetic_title}</font>'
            _answer += f'<font color={settings.config_values().all_definitions_phonetic_color}>{api_json["phonetic"]}</font>' + '<br><br>'
    except:
        pass

    # Loop to add all the meanings, plus formatting.
    for meaning in api_json['meanings']:
        try:
            if settings.config_values().all_definitions_pos_field != -1:
                if settings.config_values().all_definitions_pos_title:
                    _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_pos_title}</font>'
                _answer += f"<font color={settings.config_values().all_definitions_pos_color}><b>{meaning['partOfSpeech']}</b><br></font>"
        except:
            pass

        for definition in meaning['definitions']:
            if settings.config_values().all_definitions_definition_field != -1:
                if settings.config_values().all_definitions_definition_title:
                    _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_definition_title}</font>'
                try:
                    _answer += (
                        f"<font color={settings.config_values().all_definitions_definition_color}>{definition['definition']}</font>" + '<br>')
                except:
                    pass

            if settings.config_values().all_definitions_example_field != -1:
                try:
                    if definition['example']:
                        if settings.config_values().all_definitions_example_title:
                            _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_example_title}</font>'
                        _answer += (f'<font color={settings.config_values().all_definitions_example_color}>' + '"' +
                                    definition['example'] + '"' + '</font>' + '<br>')
                except:
                    pass

            if settings.config_values().all_definitions_synonyms_field != -1:
                try:
                    if definition['synonyms']:
                        if settings.config_values().all_definitions_synonyms_title:
                            _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_synonyms_title}</font>'
                        _answer += f"<font color={settings.config_values().all_definitions_synonyms_color}>{settings.config_values().synonyms_and_antonyms_separator.join(definition['synonyms'])}</font><br>"
                except:
                    pass

            if settings.config_values().all_definitions_antonyms_field != -1:
                try:
                    if definition['antonyms']:
                        if settings.config_values().all_definitions_antonyms_title:
                            _answer += f'<font color={settings.config_values().titles_color}>{settings.config_values().all_definitions_antonyms_title}</font>'
                        _answer += f"<font color={settings.config_values().all_definitions_antonyms_color}>{settings.config_values().synonyms_and_antonyms_separator.join(definition['antonyms'])}</font><br>"
                except:
                    pass

            _answer += '<br>'
        _answer += '<br>'

    # Removes any of the line breaks added in the above loop at the beginning
    # or end of _answer.
    # Can be replaced by removesuffix and removeprefix in the later Anki versions
    # for better readability.
    while _answer[:4] == '<br>':
        _answer = _answer[4:]

    while _answer[-4:] == '<br>':
        _answer = _answer[:-4]

    # For debugging
    # aqt.utils.showText(str(editor.note.fields[settings.config_values().all_definitions_field]))

    # If overwrite is disabled, separates the new and old contents with the specified separator
    # in the config file.
    if settings.config_values().overwrite_all_definitions or not(editor.note.fields[settings.config_values().all_definitions_field]):
        editor.note.fields[settings.config_values(
        ).all_definitions_field] = _answer
    else:
        editor.note.fields[settings.config_values().all_definitions_field] += (
            f'<font color={settings.config_values().not_overwrite_separator_color}>{settings.config_values().not_overwrite_separator}</font>' + _answer)

    # For debugging
    # aqt.utils.showText(str(editor.note.fields[1]))

    # Applies the new content.
    editor.loadNote()

    return


def _add_translation_single(editor: editor.Editor) -> None:
    '''Adds translation given by googletrans (https://pypi.org/project/googletrans/)
    after clicking the add-on button to the specified field(s) in the config file.'''

    if not(settings.config_values().translation_field):
        return

    word = _get_word(editor.note)
    # Initiating Translator
    _translator = Translator(
        user_agent=settings.config_values().mybrowser_headers['User-Agent'])

    # Gets the translation
    try:
        _translated = _translator.translate(
            word, src='en', dest=settings.config_values().translation_target_language)
    except:
        return

    # _answer will be constructed and used to fill the "Back" box.
    _answer: str = ''

    if settings.config_values().add_language_name:
        try:
            _answer += settings.iso_639_1_codes_dict[settings.config_values(
            ).translation_target_language]
        except:
            pass

    if settings.config_values().translation_title:
        _answer = (f'<font color="{settings.config_values().titles_color}">' +
                   _answer + settings.config_values().translation_title + '</font>')

    else:
        _answer = ''

    try:
        _answer += (f'<font color="{settings.config_values().translation_color}">' +
                    _translated.text + '</font>')
    except:
        pass

    try:
        if settings.config_values().add_transliteration:
            _answer += (f'<font color="{settings.config_values().transliteration_color}">' + ' (' +
                        _translated.pronunciation + ')' + '</font>')
    except:
        pass

    # If overwrite is disabled, separates the new and old contents with the specified separator
    # in the config file.
    _separator = f'<font color={settings.config_values().not_overwrite_separator_color}>{settings.config_values().not_overwrite_separator}</font>'

    if settings.config_values().overwrite_translation or not(editor.note.fields[settings.config_values().translation_field]):
        editor.note.fields[settings.config_values(
        ).translation_field] = _answer
    else:
        editor.note.fields[settings.config_values().translation_field] += (
            _separator + _answer)

    # For debugging
    # aqt.utils.showText(str(editor.note.fields[1]))

    # Applies the new content.
    editor.loadNote()

    return


def add_buttons(buttons, editor: editor.Editor) -> List[str]:
    '''
    Adds the new buttons to the editor, and assigns image, function, tip and shortcut key to them.
    By clicking the respective button one of the below happens:
    1- _add_pronunciation_mp3s_single is triggered and pronunciations will be added to the entry.
    2- _add_1st_definition_single is triggered and only the first meaning will be added to the entry.
    3- _add_all_definitions_single is triggered and all meanings will be added to the entry.
    4- _add_translation_single is triggered and translation in the specified target language
       will be added to the entry.
    5- _my_custom_add_all.
    '''

    _buttons = buttons

    if settings.config_values().display_pronunciation_button:
        _buttons += [editor.addButton(icon=os.path.join(os.path.dirname(__file__), 'images',
                                                        'sil.svg'), func=_add_pronunciation_mp3s_single, cmd='click_pronunciation_button', tip='Add Pronunciation\n(Alt+P)', keys='Alt+P')]
    if settings.config_values().display_1st_definition_button:
        _buttons += [editor.addButton(icon=os.path.join(os.path.dirname(
            __file__), 'images', '1st.svg'), func=_add_1st_definition_single, cmd='click_1st_definition_button', tip='Add 1st Definition\n(Alt+1)', keys='Alt+1')]
    if settings.config_values().display_all_definitions_button:
        _buttons += [editor.addButton(icon=os.path.join(os.path.dirname(
            __file__), 'images', 'All.svg'), func=_add_all_definitions_single, cmd='click_all_definitions_button', tip='Add All Definitions\n(Alt+A)', keys='Alt+A')]
    if settings.config_values().display_translation_button:
        _buttons += [editor.addButton(icon=os.path.join(os.path.dirname(
            __file__), 'images', 'T.svg'), func=_add_translation_single, cmd='click_translation_button', tip='Add Translation\n(Alt+T)', keys='Alt+T')]
    if settings.config_values().display_translation_button:
        _buttons += [editor.addButton(icon=os.path.join(os.path.dirname(
            __file__), 'images', 'cube.svg'), func=_my_custom_add_all, cmd='click_translation_button', tip='Add Translation\n(Alt+C)', keys='Alt+C')]

    return _buttons


def new_play_button_css(web_content: webview.WebContent, context: Any) -> None:
    '''
    Appends a css to modify the shape of an existing button
    or define the shape of a new audio play button.

    In our case, only a text element is added to the
    Anki defined "replay-button svg" by "add_label_to_button.css" file.
    '''

    if not(settings.config_values().add_labels_to_play_buttons):
        return

    # Below codes/explanations belong to Anki "webview_will_set_content" hook in genhooks_gui.py
    # that are kept for possible future use.

    # if not isinstance(context, aqt.reviewer.Reviewer):
    #     # not reviewer, do not modify content
    #     return

    # reviewer, perform changes to content

    # context: aqt.reviewer.Reviewer
    # mw.addonManager.setWebExports(__name__, r"web/.*(css|js)")

    addon_package = mw.addonManager.addonFromModule(__name__)
    web_content.css.append(
        f'/_addons/{addon_package}/web/add_label_to_button.css')

    # web_content.js.append(
    # f"/_addons/{addon_package}/web/my-addon.js")

    # web_content.head += "<script>console.log('my-addon')</script>"
    # web_content.body += "<div id='my-addon'></div>"


def add_play_button_labels(text: str, card: Card, kind: str) -> BeautifulSoup.prettify:
    '''
    Adds US/GB labels to the respective pronunciation play buttons.
    This function is used by the card_will_show hook in the __init__.py
    to modify the card appearance before display.

    Arguments:
    text: The window html, passed to the function by Anki.
    card: The card, passed to the function by Anki.
    kind: The window kind, passed to the function by Anki.
    Values 'reviewQuestion', 'reviewAnswer', 'previewQuestion',
    'previewAnswer' are considered to be processed by this function.

    Returns:
    The original or modified text (html input), decided based on kind value
    and audio/video filenames in the card.
    '''

    if not(settings.config_values().add_labels_to_play_buttons):
        return

    # Function works in below steps:
    # 1- Checks the kind, it should be in either reviewer or previewer
    #    question or answer.
    #
    #    Update: This condition is removed along with adding card.answer_av_tags()
    #    to be labeled. This change is to show labels in answers and also card views as well as
    #    question views.
    #
    # 2- Extracts the word and audio/video filenames from the card.
    #
    # 3- Considers "USsettings.config_values().synonyms_and_antonyms_separatorGB" or "none" labels to each audio/video file.
    #    Purpose of this step is to distinguish between the audio/video
    #    files added by this add-on (labeled "US" or "GB") and other
    #    possible existing ones (labeled "none").
    #
    # 4- Adds the label text and format of the new buttons.

    # For debugging
    # aqt.utils.showText("text\n" + text + "\n\ncard\n" +
    #                    str(card) + "\n\nkind\n" + kind)

    # 1
    # if kind not in ('reviewQuestion', 'reviewAnswer', 'previewQuestion', 'previewAnswer'):
    #     return text

    # 2
    q_text = (card.render_output().question_text).replace('&nbsp;', ' ')
    word = (re.split('[\[\]]', q_text))[0].strip().lower()
    word = re.sub('\s+', ' ', word)

    # Some "hyphenated compound words" like "add-on" appear with underscore
    # in the mp3 filename and mp3 url, but should be searched with hyphen.
    # This change is to address this special case.
    word = re.sub('-', '_', word)

    av_filenames = [av_tags.filename for av_tags in (
        card.question_av_tags() + card.answer_av_tags())]

    # For debugging
    # aqt.utils.showText("word\n" + word +
    #                    "\n\nav_filenames\n" + str(av_filenames))

    # 3
    labels = []
    for av_filename in av_filenames:
        if re.match(settings.patterns(word).US_mp3_filename_pattern, av_filename):
            labels.append('US')
        elif re.match(settings.patterns(word).mp3_filename_pattern, av_filename):
            labels.append('GB')
        else:
            labels.append('none')

    # For debugging
    # aqt.utils.showText("av_filenames\n" +
    #                    str(av_filenames) + "\n\nlabels\n" + str(labels))

    # 4
    text_soup = BeautifulSoup(text, 'html.parser')
    svg_tags = text_soup.find_all('svg')

    for (svg_tag, label) in zip(svg_tags, labels):
        if label != 'none':
            # The next line of code is needed only if a new button is going to
            # be defined from scratch by a css.
            #
            # "replay-button-new" should be defined similar to "replay-button"
            # in the original Anki reviewer.css file.
            #
            # In this add-on the css (add_label_to_button.css) only adds the
            # text color (white) to the Anki default button ("replay-button").

            # svg_tag.parent['class'] = 'replay-button-new soundLink'

            style = text_soup.new_tag('style')
            style.string = '.button_font { font: 75% arial; }'
            svg_tag.insert(1, style)

            text_tag = text_soup.new_tag('text')
            text_tag.string = label
            text_tag['x'] = '50%'
            text_tag['y'] = '50%'
            text_tag['alignment-baseline'] = 'middle'
            text_tag['text-anchor'] = 'middle'
            text_tag['class'] = 'button_font'
            svg_tag.path.insert_after(text_tag)

    # For debugging
    # aqt.utils.showText("original text:\n" + BeautifulSoup(text, 'html.parser').prettify() +
    #                    "\n\n\nmodified text:\n" + text_soup.prettify() + "\n\nkind is:\n" + kind)

    return text_soup.prettify()

def get_config():
    config = mw.addonManager.getConfig(__name__)
    if 'profiles' not in config:
        config['profiles'] = {}
    if mw.pm.name not in config['profiles']:
        original = copy.deepcopy(config)
        del original['profiles']
        config['profiles'][mw.pm.name] = original
    return config


def _my_custom_add_all(editor: editor.Editor) -> None:
    _add_translation_single(editor)
    _add_pronunciation_mp3s_single(editor)
    _add_all_definitions_single(editor)
