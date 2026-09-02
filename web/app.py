import os
from flask import Flask, render_template, request, redirect, url_for
import redis
import mysql.connector

app = Flask(__name__)

redis_host = os.environ.get('REDIS_HOST', 'redis')
db_host = os.environ.get('DB_HOST', 'db')
db_user = os.environ.get('DB_USER', 'root')
db_password = os.environ.get('DB_PASSWORD', 'secret')
db_name = os.environ.get('DB_NAME', 'students_db')

r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

def init_db():
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.close()
        conn.close()
        
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                roll VARCHAR(50),
                phone VARCHAR(50),
                cgpa VARCHAR(10),
                degree VARCHAR(100)
            )
        """)
        cursor.close()
        conn.close()
    except Exception as e:
        print("Database initialization error:", e)

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']
        phone = request.form['phone']
        cgpa = request.form['cgpa']
        degree = request.form['degree']

        # Push data to Redis queue for the worker to process
        r.lpush('student_queue', f"Name: {name}, Roll: {roll}, Phone: {phone}, CGPA: {cgpa}, Degree: {degree}")

        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (name, roll, phone, cgpa, degree) VALUES (%s, %s, %s, %s, %s)",
            (name, roll, phone, cgpa, degree)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/results')
def results():
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception:
        students = []
    return render_template('results.html', students=students)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
