import sqlite3
from datetime import datetime

from xlsxwriter.workbook import Workbook


def export_CSV():
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()
    op = cursor.execute('SELECT * FROM words ORDER BY id DESC')
    filename = str(int(datetime.now().timestamp())) + '.xlsx'
    workbook = Workbook("static/export/" + filename)
    worksheet = workbook.add_worksheet("words")
    for i, row in enumerate(op):
        for j, value in enumerate(row):
            worksheet.write(i, j, value)
    workbook.close()
    connection.close()
    return filename
