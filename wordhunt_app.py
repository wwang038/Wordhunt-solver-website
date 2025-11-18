from flask import Flask, request
from flask import render_template
from backend.solver import *

app = Flask(__name__)

@app.route('/', methods = ['GET', 'POST'])
def index():
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