from flask import Flask, render_template, request
from db import get_db_connection, get_db_cursor

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    min_age = request.form.get('min_age', type=int)
    max_age = request.form.get('max_age', type=int)
    gender = request.form.get('gender', default='не указано')

    conn = get_db_connection()
    cursor = get_db_cursor(conn)

    query = 'SELECT * FROM profiles WHERE age BETWEEN ? AND ? AND (gender = ? OR gender = "не указано")'
    cursor.execute(query, (min_age, max_age, gender))
    profiles = cursor.fetchall()

    conn.close()

    print("DEBUG: Profiles to render:", profiles)  # Отладочный вывод

    return render_template('search_results.html', profiles=profiles)
    return render_template('search.html', profiles=profiles)


if __name__ == '__main__':
    app.run(debug=True)
