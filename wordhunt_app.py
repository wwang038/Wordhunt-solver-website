import random
from flask import Flask, request
from flask import render_template
from backend.solver import *
import psycopg2
from psycopg2.extras import execute_values

VALID_WORD_LENGTHS = list(range(3, 17))


def score_for_length(word_length: int) -> int:
    if word_length == 3:
        return 100
    if 4 <= word_length < 6:
        return (word_length - 3) * 400
    return (word_length - 3) * 400 + 200

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

        length_score_map = {length: score_for_length(length) for length in VALID_WORD_LENGTHS}
        raw_length_params = request.args.getlist('length')
        selected_lengths = []
        if raw_length_params:
            for raw_length in raw_length_params:
                try:
                    parsed_length = int(raw_length)
                except (TypeError, ValueError):
                    continue
                if parsed_length in VALID_WORD_LENGTHS:
                    selected_lengths.append(parsed_length)
            selected_lengths = sorted(set(selected_lengths))
        if not selected_lengths:

            selected_lengths = VALID_WORD_LENGTHS.copy()
        selected_scores = [length_score_map[length] for length in selected_lengths]

        cur.execute("""
            SELECT COUNT(DISTINCT board)
            FROM board_words
            WHERE value = ANY(%s);
        """, (selected_scores,))
        total_records = cur.fetchone()[0]
        total_pages = min((total_records + page_size - 1) // page_size, 10)

        cur.execute("""
            SELECT board, SUM(value) AS total_value
            FROM board_words
            WHERE value = ANY(%s)
            GROUP BY board
            ORDER BY total_value DESC
            LIMIT %s OFFSET %s;
        """, (selected_scores, page_size, offset))
        board_records = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('records.html', 
                            records=board_records,
                            page_number=page_number,
                            total_pages=total_pages,
                            total_records=total_records,
                            valid_word_lengths=VALID_WORD_LENGTHS,
                            selected_lengths=selected_lengths,
                            length_score_map=length_score_map)
    except Exception as e:
        return render_template('records.html', 
                               records=[], 
                               error=str(e),
                               valid_word_lengths=VALID_WORD_LENGTHS,
                               selected_lengths=VALID_WORD_LENGTHS.copy(),
                               length_score_map={length: score_for_length(length) for length in VALID_WORD_LENGTHS})

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
        better_than_me_percentage = 0
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
            denominator = max(total_records - 1, 1)
            better_than_me_percentage = round(((total_records - better_than_me) / denominator) * 100, 2)
            result_rows = [(input_grid, word, score) for word, score in results]
            if result_rows:
                execute_values(cur, '''
                INSERT INTO board_words (board, word, value) 
                VALUES %s ON CONFLICT (board, word) DO NOTHING
                ''', result_rows)
            conn.commit()
        cur.close()
        conn.close()
        return render_template('index.html', results=results, total_score=total_score, submitted=True, better_than_me_percentage=better_than_me_percentage)
        
    else:
        
        return render_template('index.html', results = [], submitted=False)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)