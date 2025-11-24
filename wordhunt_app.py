import random
from flask import Flask, request
from flask import render_template
from backend.solver import *
import psycopg2

host_string = "wordhunt-db.ch8ues0g2yx6.us-east-2.rds.amazonaws.com"
app = Flask(__name__)


@app.route('/records', methods = ['GET'])
def records():
    try:
        conn = psycopg2.connect(
            host=host_string,
            database="postgres",
            user="wwang038",
            password="Password0988",
            port=5432
        )
        page_size = 20

        page_number = request.args.get('page', 1, type=int)
        if page_number < 1:
            page_number = 1
        
        offset = (page_number - 1) * page_size
        

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM board_values;")
        total_records = cur.fetchone()[0]
        total_pages = (total_records + page_size - 1) // page_size  # Ceiling division
        
        # Get records for current page
        sql_query = "SELECT board, value FROM board_values ORDER BY value DESC LIMIT %s OFFSET %s;"
        cur.execute(sql_query, (page_size, offset))
        records = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('records.html', 
                            records=records, 
                            page_number=page_number,
                            total_pages=total_pages,
                            total_records=total_records)
    except Exception as e:
        return render_template('records.html', records=[], error=str(e))

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
        if total_score != 0:
            cur.execute('''
            INSERT INTO board_values (board, value) VALUES (%s, %s) ON CONFLICT (board) DO NOTHING
            ''', (input_grid, total_score))
            cur.execute('''
            SELECT COUNT(*) FROM board_values;
            ''')
            total_records = cur.fetchone()[0]
            cur.execute('''
            SELECT COUNT(*) FROM board_values WHERE value >= %s AND value != 0;
                        ''', (total_score,))
            better_than_me = cur.fetchone()[0]
            better_than_me_percentage = round(((total_records - better_than_me) / (total_records - 1)) * 100, 2)
            conn.commit()
            cur.close()
        else:
            better_than_me_percentage = 0

        conn.close()
        return render_template('index.html', results=results, total_score=total_score, submitted=True, better_than_me_percentage=better_than_me_percentage)
        
    else:
        
        return render_template('index.html', results = [], submitted=False)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)