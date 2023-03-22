import random
import sqlite3

import requests
from flask import Flask, render_template, request

from backend.export import export_CSV
from backend.openai_ops import *
from backend.utils import *

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        sentence = request.form['sentence']
        known_words = {*[x['word'] for x in get_words_from_database()],
                       *[x['word_normal'] for x in get_words_from_database()]}  # exclude known words
        exist_known_words = known_words & tokenize_text(sentence)
        # print(exist_known_words)
        data = get_word_and_translation(sentence, exist_known_words).word_sample
        add_word_to_database(data.word,
                             data.word_normal,
                             data.word_meaning,
                             data.pronunciation,
                             highlight_words(data.orig_text, [data.word, data.word_normal]),  # highlight the key word
                             data.translated_text,
                             data.part_of_speech)
    words = get_words_from_database()
    return render_template('index.html', words=words)


@app.route('/delete_word', methods=['POST'])
def deleteWord():
    data = request.get_json()
    print(data["target"])
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()
    try:
        # print('DELETE FROM words WHERE id=', data['target'])
        cursor.execute(
            'UPDATE words SET is_mastered = 1 WHERE id=' + str(data['target']))  # mark as known word in the DB
    except:
        return 'server fault', 500
    connection.commit()
    connection.close()
    return 'deleted successfully', 200


# Export words and its details to CSV form
@app.route('/export', methods=['POST'])
def export():
    file = export_CSV()
    return {'file': file}


@app.route('/add_single_word', methods=['POST'])
def add_single_word():
    data = request.get_json()
    print(data['word'])
    dataraw = requests.get('https://dict.youdao.com/jsonapi?q=' + data['word'])
    winfo = dataraw.json()
    meaning = ""
    for i in winfo["syno"]["synos"]:
        meaning += i["syno"]["pos"] + ' ' + i["syno"]["tran"] + '<br>'
    # print(json.dumps(data["syno"]["synos"], indent=4))
    print(meaning)
    add_word_to_database(data["word"].lower(), data["word"].lower(), meaning,
                         '/' + winfo["ec"]["word"][0]["ukphone"] + '/', "Not Available",
                         "手动添加暂时不支持例句", "None")
    # try:
    #
    # except:
    #     return "Failed to get the meaning of the word", 500
    return winfo["syno"]["synos"], 200


@app.route('/story', methods=['POST'])
def write_story():
    connection = sqlite3.connect('words.db')
    connection.row_factory = dict_factory
    cursor = connection.cursor()
    cursor.execute(
        'SELECT * FROM words WHERE is_mastered = 0 ORDER BY id DESC;')  # choose the words which are not mastered
    words = cursor.fetchall()
    random.shuffle(words)
    # print(words)
    chosen = []
    for i in range(0, min(len(words), 5)):  # choose 5 words randomly
        chosen.append(words[i])
    connection.close()
    story = get_story(chosen, LiveStoryInfo())
    print({*[x['word'] for x in chosen],
           *[x['word_normal'] for x in chosen]})

    temp = highlight_words(story, {*[x['word'] for x in chosen],
                                   *[x['word_normal'] for x in chosen]})
    highlighted_story = highlight_story_text(temp)
    return {"story": highlighted_story, "words": chosen}


# Add a word to SQLite database
def add_word_to_database(word, word_normal, meaning, pronunciation, orig_text, orig_translation, part_of_speech):
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()
    cursor.execute('''INSERT INTO words
                   (word, word_normal, meaning, pronunciation, orig_text, orig_translation, part_of_speech, add_date) VALUES
                   (?, ?, ?, ?, ?, ?, ?, DateTime('now', 'localtime'))''',
                   (word, word_normal, meaning, pronunciation, orig_text, orig_translation, part_of_speech))
    connection.commit()
    connection.close()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# Query words from database
def get_words_from_database() -> list[Any]:
    connection = sqlite3.connect('words.db')
    connection.row_factory = dict_factory
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM words ORDER BY id DESC')
    words = cursor.fetchall()
    connection.close()
    return words
