# Reads the user config file (config.json), generates patterns for
# text search and defines the constants used in other modules.

from aqt import mw
import csv
import os


# Redaing the user settings in config.json
class config_values:
    def __init__(self):
        config = mw.addonManager.getConfig(__name__)
        self.mybrowser_headers = {
            'User-Agent': config['0101-User-Agent']}

        self.display_pronunciation_button = (
            config['0201-Display \'Add Pronunciation\' button?'][0].lower() == 'y')
        self.display_1st_definition_button = (
            config['0202-Display \'Add 1st Definition\' button?'][0].lower() == 'y')
        self.display_all_definitions_button = (
            config['0203-Display \'Add All Definitions\' button?'][0].lower() == 'y')
        self.display_translation_button = (
            config['0204-Display \'Add Translation\' button?'][0].lower() == 'y')
        self.add_labels_to_play_buttons = (
            config['0205-Add labels to play buttons?'][0].lower() == 'y')

        self.pronunciation_field = (
            int(config['0301-Pronunciation field number'][0].strip()) - 1)
        self.pronunciation_field_us = (
            int(config['03011-Pronunciation US field number'][0].strip()) - 1)
        self.pronunciation_field_gb = (
            int(config['03012-Pronunciation GB field number'][0].strip()) - 1)
        self.add_US_pronunciation = (
            config['0302-Add US pronunciation?'][0].lower() == 'y')
        self.add_GB_pronunciation = (
            config['0303-Add GB pronunciation?'][0].lower() == 'y')
        self.US_pronunciation_first = (
            config['0304-US or GB pronunciation first?'][0].lower() == 'u')
        self.keep_pronunciation_duplicates = (
            config['0305-Keep pronunciation duplicates?'][0].lower() == 'y')

        self.not_overwrite_separator = config['0401-Not overwrite separator']
        self.not_overwrite_separator_color = config['0402-Not overwrite separator color'].strip(
        ).lower()
        self.titles_color = config['0403-Titles color'].strip().lower()
        self.synonyms_and_antonyms_separator = config['0404-Synonyms and antonyms separator']
        self.overwrite_1st_definition = (
            config['0405-Overwrite 1st Definition?'][0].lower() == 'y')
        self.overwrite_all_definitions = (
            config['0406-Overwrite All Definitions?'][0].lower() == 'y')

        self.first_definition_phonetic_field = int(
            config['0501-1st Definition phonetic field number'].strip())-1
        self.first_definition_phonetic_title = config['0502-1st Definition phonetic title']
        self.first_definition_phonetic_color = config['0503-1st Definition phonetic color'].strip(
        ).lower()

        self.first_definitions_pos_field = int(
            config['0511-1st Definition part of speech field number'].strip())-1
        self.first_definitions_pos_title = config['0512-1st Definition part of speech title']
        self.first_definitions_pos_color = config['0513-1st Definition part of speech color'].strip(
        ).lower()

        self.first_definition_definition_field = int(
            config['0521-1st Definition definition field number'].strip())-1
        self.first_definition_definition_title = config['0522-1st Definition definition title']
        self.first_definition_definition_color = config['0523-1st Definition definition color'].strip(
        ).lower()

        self.first_definition_example_field = int(
            config['0531-1st Definition example field number'].strip())-1
        self.first_definition_example_title = config['0532-1st Definition example title']
        self.first_definition_example_color = config['0533-1st Definition example color'].strip(
        ).lower()

        self.first_definition_synonyms_field = int(
            config['0541-1st Definition synonyms field number'].strip())-1
        self.first_definition_synonyms_title = config['0542-1st Definition synonyms title']
        self.first_definition_synonyms_color = config['0543-1st Definition synonyms color'].strip(
        ).lower()

        self.first_definition_antonyms_field = int(
            config['0551-1st Definition antonyms field number'].strip())-1
        self.first_definition_antonyms_title = config['0552-1st Definition antonyms title']
        self.first_definition_antonyms_color = config['0553-1st Definition antonyms color'].strip(
        ).lower()

        self.all_definitions_field = int(
            config['0601-All Definitions field number'])-1

        self.all_definitions_phonetic_field = int(
            config['0611-All Definitions phonetic field number'].strip())-1
        self.all_definitions_phonetic_title = config['0612-All Definitions phonetic title']
        self.all_definitions_phonetic_color = config['0613-All Definitions phonetic color'].strip(
        ).lower()

        self.all_definitions_pos_field = int(
            config['0621-All Definitions part of speech field number'].strip())-1
        self.all_definitions_pos_title = config['0622-All Definitions part of speech title']
        self.all_definitions_pos_color = config['0623-All Definitions part of speech color'].strip(
        ).lower()

        self.all_definitions_definition_field = int(
            config['0631-All Definitions definition field number'].strip())-1
        self.all_definitions_definition_title = config['0632-All Definitions definition title']
        self.all_definitions_definition_color = config['0633-All Definitions definition color'].strip(
        ).lower()

        self.all_definitions_example_field = int(
            config['0641-All Definitions example field number'].strip())-1
        self.all_definitions_example_title = config['0642-All Definitions example title']
        self.all_definitions_example_color = config['0643-All Definitions example color'].strip(
        ).lower()

        self.all_definitions_synonyms_field = int(
            config['0651-All Definitions synonyms field number'].strip())-1
        self.all_definitions_synonyms_title = config['0652-All Definitions synonyms title']
        self.all_definitions_synonyms_color = config['0653-All Definitions synonyms color'].strip(
        ).lower()

        self.all_definitions_antonyms_field = int(
            config['0661-All Definitions antonyms field number'].strip())-1
        self.all_definitions_antonyms_title = config['0662-All Definitions antonyms title']
        self.all_definitions_antonyms_color = config['0663-All Definitions antonyms color'].strip(
        ).lower()

        self.translation_field = (
            int(config['0701-Translation field number'])-1)
        self.translation_target_language = config['0702-Translation target language'].strip(
        ).lower()
        self.add_language_name = (
            config['0703-Add language name to translation title?'][0].lower() == 'y')
        self.translation_title = config['0704-Translation title']
        self.translation_color = config['0705-Translation color'].strip().lower()
        self.add_transliteration = (
            config['0706-Add transliteration to translation?'][0].lower() == 'y')
        self.transliteration_color = config['0707-Transliteration color'].strip(
        ).lower()
        self.overwrite_translation = (
            config['0708-Overwrite translation?'][0].lower() == 'y')


class patterns:
    '''Generates regex or search patterns, accepting "word" as class argument.'''

    def __init__(self, word: str):
        self.word = word
        self.US_mp3_filename_pattern = f'{word}([a-zA-Z0-9._-]*)[_-]us[_-]([a-zA-Z0-9._-]*)\.mp3'
        self.GB_mp3_filename_pattern = f'{word}([a-zA-Z0-9._-]*)[_-]gb[_-]([a-zA-Z0-9._-]*)\.mp3'
        self.mp3_filename_pattern = f'{word}([a-zA-Z0-9._-]*)[_-](us|gb)[_-]([a-zA-Z0-9._-]*)\.mp3'
        self.google_pronounce_search_url = f'https://www.google.com/search?q=how+to+pronounce+{word}'
        self.google_define_search_url = f'https://www.google.com/search?q=define:{word}'


# Constant definitions
MP3_URL_BEGIN_STR = '//ssl.gstatic.com/dictionary/static/'
MP3_URL_END_STR = '.mp3'

# Loading ISO-639-1 codes / language name mapping into a python dict
_path = os.path.join(os.path.dirname(__file__), 'files/ISO-639-1_Codes.csv')
_iso_639_1_codes_file = open(_path, mode='r')
_iso_639_1_codes_dictreader = csv.DictReader(_iso_639_1_codes_file)

iso_639_1_codes_dict: dict = {}
for _row in _iso_639_1_codes_dictreader:
    iso_639_1_codes_dict[_row['ISO-639-1 Code']] = _row['Language']

_iso_639_1_codes_file.close()
