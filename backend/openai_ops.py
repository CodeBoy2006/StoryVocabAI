import logging
from typing import Any, Callable, Dict, List, Optional, Set

import openai

from backend.exceptions import OpenAIServiceError
from backend.models import TranslationResult, WordSample, LiveStoryInfo

logger = logging.getLogger()

# Param: content
StreamHandler = Callable[[str], Any]


def get_word_and_translation(
        text: str, known_words: Set[str]  # , live_info: LiveTranslationInfo
) -> TranslationResult:
    """Get the most uncommon word in the given text, the result also include other
    information such as meaning of the word and etc.

    :param text: The text which needs to be translated
    :param known_words: Words already known
    :param live_info: The info object which will be updated in the midway
    :return: a `WordSample` object
    :raise VocBuilderError: when unable to finish the API call or reply is malformed
    """

    _received = ''

    # def handle_stream_content(text: str):
    #     """Extract "translated" and updated the live_info object"""
    #     nonlocal _received
    #     _received += text
    #     translated = TranslationReplyParser().extract_translated(_received)
    #     live_info.translated_text = translated

    try:
        reply = query_openai(text, known_words)  # , stream_handler=handle_stream_content)
    except Exception as e:
        raise OpenAIServiceError('Error querying OpenAI API: %s' % e)
    finally:
        pass
        # Mark current info object as finished
        # live_info.is_finished = True
    try:
        return TranslationReplyParser().parse(reply, text)
    except ValueError as e:
        raise OpenAIServiceError(e)


class TranslationReplyParser:
    """Parser for the reply for translation request"""

    def parse(self, reply_text: str, orig_text: str) -> TranslationResult:
        """Parse the OpenAI reply

        :param text: Formatted text
        :param orig_text: The original text which needs translation
        :return: TranslationResult object
        :raise: ValueError when the given reply text can not be parsed
        """
        fields = self.parse_to_dict(reply_text)

        required_fields = {
            'word',
            'word_normal',
            'word_meaning',
            'pronunciation',
            'translated_text',
            'part_of_speech',
        }
        # All fields must be provided
        if set(fields.keys()) != required_fields:
            raise ValueError('Reply text "%s" is invalid' % reply_text)

        # The word was surrounded by {} sometimes, remove
        fields['word'] = fields['word'].strip('{}').lower()
        # Preserve case for normal form
        fields['word_normal'] = fields['word_normal'].strip('{}')
        return TranslationResult(
            word_sample=WordSample(
                word=fields['word'],
                word_normal=fields['word_normal'],
                word_meaning=fields['word_meaning'],
                pronunciation=fields['pronunciation'],
                translated_text=fields['translated_text'],
                orig_text=orig_text,
                part_of_speech=fields['part_of_speech'],
            ),
        )

    def extract_translated(self, reply_text: str) -> str:
        """Extract the translated paragraph from a reply text which is not complete yet

        :return: The translated text, might be an empty string
        """
        fields = self.parse_to_dict(reply_text)
        return fields.get('translated_text', '')

    def parse_to_dict(self, text: str) -> Dict:
        """Turn reply text to a result dict"""
        # Get the key value pairs from text first
        kv_pairs: Dict[str, str] = {}
        for line in text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                kv_pairs[key.strip(' -').lower()] = value.strip()

        # The reply may use non-standard keys sometimes, define a list of possible keys to handle
        # these situations.
        #   {field_name}: {list_of_possible_keys}
        possible_field_index: Dict[str, List[str]] = {
            'word': ['word', 'unknown-word', 'unknown word'],
            'word_normal': ['normal_form'],
            'word_meaning': ['meaning'],
            'pronunciation': ['pronunciation'],
            'translated_text': ['translated'],
            'part_of_speech': ['part of speech', 'the part of speech', 'the_part_of_speech'],
        }

        # Build a fields dict for making the WordSample object
        fields: Dict[str, str] = {}
        for field, keys in possible_field_index.items():
            for k in keys:
                field_value = kv_pairs.get(k)
                if field_value:
                    fields[field] = field_value
                    break
        return fields


# The prompt being used to make word
prompt_main_system = """\
You are a translation assistant, \
I will give you a paragraph of english and a list of words called "known-words" which is divided by ",", \
please find out the top 1 most rarely used word in the paragraph(the word must not in "known-words"). \
Get the normal form, the simplified Chinese meaning, \
the part of speech of the word in this specific sentence (e.g. noun./adj./adv.) and the pronunciation of that word, \
then translate the whole paragraph into simplified Chinese.

Your answer should be separated into 5 different lines, each line's content is as below:

translated: {{translated_paragraph}}
word: {{word}}
normal_form: {{normal_form_of_word}}
pronunciation: {{pronunciation}}
meaning: {{chinese_meaning_of_word}}
the_part_of_speech: {{the_part_of_speech}}

The answer should only include 1 word and have no extra content.
"""  # noqa: E501

prompt_main_user_tmpl = """\
known-words: {known_words}

The paragraph is:

{text}
"""


def query_openai(
        text: str, known_words: Set[str], stream_handler: Optional[StreamHandler] = None
) -> str:
    """Query OpenAI to get the translation results.

    :param stream_handler: A callback function to handle partial replies.
    :return: Well formatted string contains word and meaning.
    """
    user_content = prompt_main_user_tmpl.format(text=text, known_words=','.join(known_words))
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        stream=True,
        messages=[
            {"role": "system", "content": prompt_main_system},
            {"role": "user", "content": user_content},
            # Use a single "user" message at this moment because "system" role doesn't perform better
            # {"role": "user", "content": prompt_main_system + '\n' + user_content},
        ],
    )
    content = ''
    for part in completion:
        logger.debug('Completion API returns: %s', part)
        delta = part.choices[0].delta
        delta_content = delta.get('content')
        if delta_content:
            # Callback handler function if given
            if stream_handler:
                stream_handler(delta_content)
            content += delta_content
    # Return the content at once
    return content.strip()


# The prompt being used to generate story from words
prompt_write_story_user_tmpl = """\
Please write a short story which is less than 200 words, the story should use simple words and these special words must be included: {words}. Also surround every special word with a single "$" character at the beginning and the end.
"""


def get_story(words: List[dict], live_info: LiveStoryInfo) -> str:
    """Query OpenAI to get a story.

    :param live_info: The info object which represents the writing procedure
    :return: The story text
    :raise: OpenAIServiceError
    """
    _received = ''

    def handle_stream_content(text: str):
        nonlocal _received
        _received += text
        live_info.story_text = _received

    # Try to use the normal form of each word
    str_words = [w["word_normal"] or w["word"] for w in words]
    try:
        return query_story(str_words, stream_handler=handle_stream_content)
    except Exception as e:
        raise OpenAIServiceError('Error querying OpenAI API: %s' % e)
    finally:
        # Ends the live procedure
        live_info.is_finished = True


def query_story(words: List[str], stream_handler: Optional[StreamHandler] = None) -> str:
    """Query OpenAI API to get a story.

    :param stream_handler: A callback function to handle partial replies.
    :return: The story text
    """
    content = ''

    # Try to use the normal form of each word
    words_str = ','.join(words)
    user_content = prompt_write_story_user_tmpl.format(words=words_str)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        stream=True,
        messages=[
            # Use a single "user" message at this moment because "system" role doesn't perform better
            {"role": "user", "content": user_content},
        ],
    )
    for part in completion:
        logger.debug('Completion API returns: %s', part)
        delta = part.choices[0].delta
        delta_content = delta.get('content')
        if delta_content:
            if stream_handler:
                stream_handler(delta_content)
            content += delta_content
    return content
