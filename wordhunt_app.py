import random
from flask import Flask, request
from flask import render_template
from backend.solver import *
import psycopg2

host_string = "wordhunt-db.ch8ues0g2yx6.us-east-2.rds.amazonaws.com"
app = Flask(__name__)


@app.route('/records', methods = ['GET'])
def records():
    conn = psycopg2.connect(
    host=host_string,
    database="postgres",
    user="wwang038",
    password="Password0988",
    port=5432
)
    cur = conn.cursor()
    cur.execute('''
    SELECT * FROM board_values ORDER BY value DESC LIMIT 20
    ''')
    records = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('records.html', records=records)

@app.route('/', methods = ['GET', 'POST'])
def index():
    conn = psycopg2.connect(
    host=host_string,
    database="postgres",
    user="wwang038",
    password="Password0988",
    port=5432
)

    
    if request.method == 'POST':
        input_grid = request.form['input_grid']
        results, total_score = web_solver(input_grid)
        cur = conn.cursor()

        cur.execute('''
        INSERT INTO board_values (board, value) VALUES (%s, %s) ON CONFLICT (board) DO NOTHING
        ''', (input_grid, total_score))
        conn.commit()
        cur.close()

        conn.close()
        return render_template('index.html', results=results, total_score=total_score, submitted=True)
    else:
        
        return render_template('index.html', results = [], submitted=False)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)