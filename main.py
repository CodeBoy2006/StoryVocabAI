import logging
from typing import Callable, Any

from app import app
import openai
import os
from dotenv import load_dotenv
from backend import openai_ops

teststr = '''People do acquire a
little brief author-
ity by equipping
themselves with
jargon: they can
ponticate and air a
supercial expertise.
But what we should
ask of educated
mathematicians is
not what they can
speechify about,
nor even what they
know about the
existing corpus
of mathematical
knowledge, but
rather what can
they now do with
their learning and
whether they can
actually solve math-
ematical problems
arising in practice.
In short, we look for
deeds not words.'''


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = "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"


if __name__ == '__main__':
    # print(openai_ops.get_word_and_translation(teststr, ''))
    app.run(debug=True)

