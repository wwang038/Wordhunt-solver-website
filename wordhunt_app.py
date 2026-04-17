import json
import os
import random
from pathlib import Path

from flask import Flask, request, url_for, session, redirect
from flask import render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from backend.solver import *
import psycopg2
from psycopg2.extras import execute_values
from authlib.integrations.flask_client import OAuth
from pybloom_live import BloomFilter

_KEYS_PATH = Path(__file__).resolve().parent / "keys.json"
_keys = json.loads(_KEYS_PATH.read_text(encoding="utf-8"))
_web = _keys["web"]
_db  = _keys["database"]

VALID_WORD_LENGTHS = list(range(3, 17))


def score_for_length(word_length: int) -> int:
    if word_length == 3:
        return 100
    if 4 <= word_length < 6:
        return (word_length - 3) * 400
    return (word_length - 3) * 400 + 200


def get_db():
    return psycopg2.connect(
        host=_db["host"],
        database=_db["database"],
        user=_db["user"],
        password=_db["password"],
        port=_db["port"],
    )


app = Flask(__name__)
app.secret_key = _keys["app_session"]["secret_key"]
if os.environ.get("FLY_APP_NAME"):
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=_web["client_id"],
    client_secret=_web["client_secret"],
    server_metadata_url=_web.get(
        "server_metadata_url",
        "https://accounts.google.com/.well-known/openid-configuration",
    ),
    client_kwargs={'scope': 'openid email profile'},
)

# Bloom filter — capacity 10k users, 1% false-positive rate
_username_bloom = BloomFilter(capacity=10_000, error_rate=0.01)




def _init_bloom():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE username IS NOT NULL;")
        for (uname,) in cur.fetchall():
            _username_bloom.add(uname.lower())
        cur.close()
        conn.close()
    except Exception:
        pass



_init_bloom()



def current_user():
    """Return (user_id, username) from session, or (None, None)."""
    return session.get("user_id"), session.get("username")


@app.route('/authentication/google', methods=['GET'])
def authentication_google():
    redirect_uri = url_for('authentication_google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/authentication/google/callback', methods=['GET'])
def authentication_google_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get('userinfo') or {}
    google_id = userinfo.get('sub', '')
    email     = userinfo.get('email', '')

    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT id, username FROM users WHERE google_id = %s;", (google_id,))
    row = cur.fetchone()

    if row:
        user_id, username = row
    else:
        cur.execute(
            "INSERT INTO users (google_id, email) VALUES (%s, %s) RETURNING id;",
            (google_id, email),
        )
        user_id  = cur.fetchone()[0]
        username = None
        conn.commit()

    cur.close()
    conn.close()

    session['user_id']  = user_id
    session['username'] = username
    session['email']    = email

    if username:
        return redirect('/')
    return redirect('/setup-username')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------------------------------------------------------------------
# Username setup
# ---------------------------------------------------------------------------

@app.route('/setup-username', methods=['GET', 'POST'])
def setup_username():
    if 'user_id' not in session:
        return redirect('/authentication/google')

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()

        if not username or len(username) < 3 or len(username) > 20:
            error = "Username must be 3–20 characters."
        elif not all(c.isalnum() or c == '_' for c in username):
            error = "Only letters, numbers, and underscores are allowed."
        else:
            # Bloom filter: if it contains the name, verify in DB (may be false positive)
            if username.lower() in _username_bloom:
                conn = get_db()
                cur  = conn.cursor()
                cur.execute(
                    "SELECT 1 FROM users WHERE LOWER(username) = LOWER(%s);",
                    (username,),
                )
                taken = cur.fetchone() is not None
                cur.close()
                conn.close()
                if taken:
                    error = "That username is already taken."

            if not error:
                error = _claim_username(username)

        if not error:
            return redirect('/dashboard')

    return render_template('setup_username.html', error=error,
                           email=session.get('email'))


def _claim_username(username: str):
    """Write username to DB + bloom filter. Returns error string or None."""
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE users SET username = %s WHERE id = %s;",
            (username, session['user_id']),
        )
        conn.commit()
        cur.close()
        conn.close()
        session['username'] = username
        _username_bloom.add(username.lower())
        return None
    except Exception as exc:
        return f"Could not save username: {exc}"


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/authentication/google')

    user_id  = session['user_id']
    username = session.get('username')

    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT board, value
        FROM board_values
        WHERE user_id = %s
        ORDER BY value DESC
        LIMIT 10;
    """, (user_id,))
    boards = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM board_values WHERE user_id = %s;", (user_id,))
    total_boards = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        'dashboard.html',
        username=username,
        email=session.get('email'),
        boards=boards,
        total_boards=total_boards,
    )


# ---------------------------------------------------------------------------
# Public user profile
# ---------------------------------------------------------------------------

@app.route('/user/<username>')
def user_profile(username):
    conn = get_db()
    cur  = conn.cursor()

    cur.execute(
        "SELECT id FROM users WHERE LOWER(username) = LOWER(%s);",
        (username,),
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return render_template('profile.html', profile_username=username, not_found=True), 404

    profile_user_id = row[0]

    page_size   = 20
    page_number = max(request.args.get('page', 1, type=int), 1)
    offset      = (page_number - 1) * page_size

    cur.execute(
        "SELECT COUNT(*) FROM board_values WHERE user_id = %s;",
        (profile_user_id,),
    )
    total_records = cur.fetchone()[0]
    total_pages   = min((total_records + page_size - 1) // page_size, 10)

    cur.execute("""
        SELECT board, value
        FROM   board_values
        WHERE  user_id = %s
        ORDER  BY value DESC
        LIMIT  %s OFFSET %s;
    """, (profile_user_id, page_size, offset))
    boards = cur.fetchall()

    cur.close()
    conn.close()

    is_own_profile = session.get('user_id') == profile_user_id

    return render_template(
        'profile.html',
        profile_username=username,
        boards=boards,
        total_records=total_records,
        total_pages=total_pages,
        page_number=page_number,
        is_own_profile=is_own_profile,
        viewer_username=session.get('username'),
    )


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@app.route('/records', methods=['GET'])
def records():
    try:
        conn = get_db()
        page_size   = 20
        page_number = max(request.args.get('page', 1, type=int), 1)
        offset      = (page_number - 1) * page_size

        cur = conn.cursor()
        length_score_map  = {l: score_for_length(l) for l in VALID_WORD_LENGTHS}
        raw_length_params = request.args.getlist('length')
        selected_lengths  = []

        for raw in raw_length_params:
            try:
                p = int(raw)
            except (TypeError, ValueError):
                continue
            if p in VALID_WORD_LENGTHS:
                selected_lengths.append(p)
        selected_lengths = sorted(set(selected_lengths)) or VALID_WORD_LENGTHS.copy()
        selected_scores  = [length_score_map[l] for l in selected_lengths]

        cur.execute("""
            SELECT COUNT(DISTINCT bw.board)
            FROM board_words bw
            WHERE bw.value = ANY(%s);
        """, (selected_scores,))
        total_records = cur.fetchone()[0]
        total_pages   = min((total_records + page_size - 1) // page_size, 10)

        cur.execute("""
            SELECT bw.board,
                   SUM(bw.value)                   AS total_value,
                   COALESCE(u.username, 'guest')   AS username
            FROM   board_words  bw
            LEFT JOIN board_values bv ON bv.board = bw.board
            LEFT JOIN users        u  ON u.id     = bv.user_id
            WHERE  bw.value = ANY(%s)
            GROUP  BY bw.board, u.username
            ORDER  BY total_value DESC
            LIMIT %s OFFSET %s;
        """, (selected_scores, page_size, offset))
        board_records = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
            'records.html',
            records=board_records,
            page_number=page_number,
            total_pages=total_pages,
            total_records=total_records,
            valid_word_lengths=VALID_WORD_LENGTHS,
            selected_lengths=selected_lengths,
            length_score_map=length_score_map,
        )
    except Exception as exc:
        return render_template(
            'records.html',
            records=[],
            error=str(exc),
            valid_word_lengths=VALID_WORD_LENGTHS,
            selected_lengths=VALID_WORD_LENGTHS.copy(),
            length_score_map={l: score_for_length(l) for l in VALID_WORD_LENGTHS},
        )


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    user_id, username = current_user()

    if request.method == 'POST':
        conn = get_db()
        input_grid          = request.form['input_grid']
        results, total_score = web_solver(input_grid)
        cur                 = conn.cursor()
        better_than_me_percentage = 0

        if total_score != 0:
            cur.execute("""
                INSERT INTO board_values (board, value, user_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (board) DO NOTHING;
            """, (input_grid, total_score, user_id))

            cur.execute("SELECT COUNT(*) FROM board_values;")
            total_records = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM board_values WHERE value >= %s AND value != 0;",
                (total_score,),
            )
            better_than_me = cur.fetchone()[0]
            denominator    = max(total_records - 1, 1)
            better_than_me_percentage = round(
                ((total_records - better_than_me) / denominator) * 100, 2
            )

            result_rows = [(input_grid, word, score) for word, score in results]
            if result_rows:
                execute_values(cur, """
                    INSERT INTO board_words (board, word, value)
                    VALUES %s
                    ON CONFLICT (board, word) DO NOTHING;
                """, result_rows)

            conn.commit()

        cur.close()
        conn.close()

        return render_template(
            'index.html',
            results=results,
            total_score=total_score,
            submitted=True,
            better_than_me_percentage=better_than_me_percentage,
            username=username,
        )

    return render_template('index.html', results=[], submitted=False, username=username)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
