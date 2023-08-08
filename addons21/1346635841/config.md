* Color values can be either HTML Hex Codes (e.g. "#00FF00") or Color Names (e.g. "green"). There are some websites and online tools for reference, such as:
    - [Wikipedia - Web colors](https://en.wikipedia.org/wiki/Web_colors)
	- [W3Schools - Colors Tutorial](https://www.w3schools.com/colors/default.asp)


* **0101-User-Agent**: There is a default value, but it is **highly recommended** that you paste your own user agent here. You can find it by:
    - Googling "my user agent"
    - Using websites like [whatismybrowser.com](https://www.whatismybrowser.com/detect/what-is-my-user-agent) or [whatsmyua.info](https://www.whatsmyua.info/)


* **0201-Display 'Add Pronunciation' button?**: "Yes" if you want to see the "Add Pronunciation" button, "No" otherwise
* **0202-Display 'Add 1st Definition' button?**: "Yes" if you want to see the "Add 1st Definition" button, "No" otherwise
* **0203-Display 'Add All Definitions' button?**: "Yes" if you want to see the "Add All Definitions" button, "No" otherwise
* **0204-Display 'Add Translation' button?**: "Yes" if you want to see the "Add Translation" button, "No" otherwise
* **0205-Add labels to play buttons?**: "Yes" if you want the US or GB labels to appear on the respective media play buttons, "No" otherwise


* **0301-Pronunciation field number**: Field number that you want the pronunciations to be added to; typically "1" if you want to add it to the entry (word)
* **0302-Add US pronunciation?**: "Yes" if you want to add US (American) pronunciation, "No" otherwise
* **0303-Add GB pronunciation?**: "Yes" if you want to add GB (British) pronunciation, "No" otherwise
* **0304-US or GB pronunciation first?**: "GB" if you want the sequence of pronunciation files to be 1-GB 2-US, "US" if vice versa
* **0305-Keep pronunciation duplicates?**: "No" if you do not want to add the pronunciation if it already exists, "Yes" otherwise


* **0401-Not overwrite separator**: The separator with the previous contents of a field if "Overwrite 1st Definition" and/or "Overwrite All Definitions" are set to "No"; &lt;br&gt; means a line break (like pressing the Enter button on the keyboard while typing)
* **0402-Not overwrite separator color**: "Not overwrite separator" color
* **0403-Titles color**: The titles color; applies to all titles in the 1st Definition and All Definitions.
* **0404-Synonyms and antonyms separator**: The separator between the synonyms and the antonyms words
* **0405-Overwrite 1st Definition**: "Yes" if you want the definition elements to replace the previous contents of the specified fields, "No" if you want the elements to be added to them; applies to all the specified fields.
* **0406-Overwrite All Definitions**: "Yes" if you want the definitions to replace the previous contents of the specified field, "No" if you want the elements to be added to it


* **0501-1st Definition phonetic field number**: The field number to add to or replace its contents with the phonetic. Set to "0" if you want the phonetic not to appear in any field.
* **0502-1st Definition phonetic title"**: The title to add before the 1st Definition phonetic
* **0503-1st Definition phonetic color**: The 1st Definition phonetic color

* **0511-1st Definition part of speech field number**: The field number to add to or replace its contents with the part of speech. Set to "0" if you want the part of speech not to appear in any field.
* **0512-1st Definition part of speech title**: The title to add before the 1st Definition part of speech
* **0513-1st Definition part of speech color**: The 1st Definition part of speech color

* **0521-1st Definition definition field number**: The field number to add to or replace its contents with the definition. Set to "0" if you want the definition not to appear in any field.
* **0522-1st Definition definition title**: The title to add before the 1st Definition definition
* **0523-1st Definition definition color**: The 1st Definition definition color

* **0531-1st Definition example field number**: The field number to add to or replace its contents with the example. Set to "0" if you want the example not to appear in any field.
* **0532-1st Definition example title**: The title to add before the 1st Definition example
* **0533-1st Definition example color**: The 1st Definition example color

* **0541-1st Definition synonyms field number**: The field number to add to or replace its contents with the synonyms. Set to "0" if you want the synonyms not to appear in any field.
* **0542-1st Definition synonyms title**: The title to add before the 1st Definition synonyms
* **0543-1st Definition synonyms color**: The 1st Definition synonyms color. Applies to both synonyms and their separator ("Synonyms and antonyms separator").

* **0551-1st Definition antonyms field number**: The field number to add to or replace its contents with the antonyms. Set to "0" if you want the antonyms not to appear in any field.
* **0552-1st Definition antonyms title**: The title to add before the 1st Definition antonyms
* **0553-1st Definition antonyms color**: The 1st Definition antonyms color. Applies to both antonyms and their separator ("Synonyms and antonyms separator").


* **0601-All Definitions field number**: The field number to add to or replace its contents with the definitions. It overrides all the defined elements field numbers, except those who are set to "0" which means they will not appear in the definitions.

* **0611-All Definitions phonetic field number**: Phonetic will not appear if this is set to "0". Values other than "0" are overridden by "All Definitions field number".
* **0612-All Definitions phonetic title**: The title to add before the All Definitions phonetic
* **0613-All Definitions phonetic color**: All Definitions phonetic color

* **0621-All Definitions part of speech field number**: Part of speech will not appear if this is set to "0". Values other than "0" are overridden by "All Definitions field number".
* **0622-All Definitions part of speech title**: The title to add before the All Definitions part of speech
* **0623-All Definitions part of speech color**: All Definitions part of speech color

* **0631-All Definitions definition field number**: Definition will not appear if this is set to "0". Values other than "0" are overridden by "All Definitions field number".
* **0632-All Definitions definition title**: The title to add before the All Definitions definitions
* **0633-All Definitions definition color**: All Definitions definition color

* **0641-All Definitions example field number**: Example will not appear if this is set to "0". Values other than "0" are overridden by "All Definitions field number".
* **0642-All Definitions example title**: The title to add before the All Definitions example
* **0643-All Definitions example color**: All Definitions example color

* **0651-All Definitions synonyms field number**: Synonyms will not appear if this is set to "0". Values other than "0" are overridden by "All Definitions field number".
* **0652-All Definitions synonyms title**: The title to add before the All Definitions synonyms
* **0653-All Definitions synonyms color**: All Definitions synonyms color. Applies to both synonyms and their separator ("Synonyms and antonyms separator").

* **0661-All Definitions antonyms field number**: Antonyms will not appear if this is set to "0". Values other than "0" are overridden by "All Definitions field number".
* **0662-All Definitions antonyms title**: The title to add before the All Definitions antonyms
* **0663-All Definitions antonyms color**: All Definitions antonyms color. Applies to both antonyms and their separator ("Synonyms and antonyms separator").


* **0701-Translation field number**: The field number to add to or replace its contents with the translation.
* **0702-Translation target language**: Choose a target language ISO-639-1 two-letter code. You can find the code in [Google documentation](https://cloud.google.com/translate/docs/languages) or [Wikipedia](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). Source language is always English.
* **0703-Add language name to translation title?**: Set "Yes" if you want to add the language name before the specified "Translation title". For example if "Translation target language" is set to "fr" and "Translation title" is set to " translation: " and "Add language name to translation title?" is set to "Yes", the final title shown would be "French translation: ".
* **0704-Translation title**: The title to add before the translation. It can precede by the target language name if "Add language name to translation title?" is set to "Yes". Leaving a blank value ("") will make "Add language name to translation title?" ineffective and no title will be shown.
* **0705-Translation color**: The translation color
* **0706-Add transliteration to translation?**: "Yes" if you want the transliteration (in the target language) to appear alongside the translation. Transliteration is the translation written in the Latin alphabet; for example, if the English word entry is "night", Russian translation is "ночь" and transliteration is "noch'", that helps to know how the translation is pronounced in the target language.
* **0707-Transliteration color**: The transliteration color
* **0708-Overwrite translation?**: "Yes" if you want the translation to replace the previous contents of the specified field, "No" if you want the translation to be added to it