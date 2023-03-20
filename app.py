import backend as backend
from flask import Flask, render_template, request
import sqlite3
from backend.openai_ops and backend.utils import *

app = Flask(__name__)


# 路由和视图函数
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        sentence = request.form['sentence']
        data = get_word_and_translation(sentence, '').word_sample
        add_word_to_database(data.word,
                             data.word_normal,
                             data.word_meaning,
                             data.pronunciation,
                             data.orig_text,
                             data.translated_text,
                             data.part_of_speech)
    words = get_words_from_database()
    return render_template('index.html', words=words)


# 将单词添加到SQLite数据库
def add_word_to_database(word, word_normal, meaning, pronunciation, orig_text, orig_translation, part_of_speech):
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO words (word, word_normal, meaning, pronunciation, orig_text, orig_translation, part_of_speech) VALUES'
                   '(?, ?, ?, ?, ?, ?, ?)', (word, word_normal, meaning, pronunciation, orig_text, orig_translation, part_of_speech))
    connection.commit()
    connection.close()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# 从SQLite数据库中获取单词
def get_words_from_database():
    connection = sqlite3.connect('words.db')
    connection.row_factory = dict_factory
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM words ORDER BY id DESC')
    words = cursor.fetchall()
    connection.close()
    return words
