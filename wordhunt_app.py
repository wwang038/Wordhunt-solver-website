import random
from flask import Flask, request
from flask import render_template
from backend.solver import *
import psycopg2

host_string = "wordhunt-db.ch8ues0g2yx6.us-east-2.rds.amazonaws.com"
app = Flask(__name__)







def random_string():
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    random_string = ''
    for i in range(16):
        random_string += random.choice(alphabet)
    return random_string



@app.route('/', methods = ['GET', 'POST'])
def index():

    
    conn = psycopg2.connect(
    host=host_string,
    database="postgres",
    user="wwang038",
    password="Password0988",
    port=5432
)

    cur = conn.cursor()
    random_board = random_string()
    cur.execute('''
    INSERT INTO test_table (board, board_value) VALUES (%s, %s) ON CONFLICT (board) DO NOTHING
    ''', (random_board, 50))
    conn.commit()
    cur.close()
    
    conn.close()
    if request.method == 'POST':
        input_grid = request.form['input_grid']
        results = web_solver(input_grid)
        return render_template('index.html', results=results)
    else:
        return render_template('index.html')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)