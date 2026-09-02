import os
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

try:
    import redis
except ImportError:
    redis = None

app = Flask(__name__)

db_host = os.environ.get("DB_HOST", "db")
db_user = os.environ.get("DB_USER", "root")
db_password = os.environ.get("DB_PASSWORD", "secret")
db_name = os.environ.get("DB_NAME", "students_db")
db_port = int(os.environ.get("DB_PORT", "3306"))
db_ssl = os.environ.get("DB_SSL", "false").lower() == "true"

redis_host = os.environ.get("REDIS_HOST")
redis_port = int(os.environ.get("REDIS_PORT", "6379"))

r = None

if redis and redis_host:
    try:
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        r.ping()
        print("Redis connected successfully.")
    except Exception as e:
        print(f"Redis connection unavailable: {e}")
        r = None


def get_db_connection():
    config = {
        "host": db_host,
        "port": db_port,
        "user": db_user,
        "password": db_password,
        "database": db_name
    }

    if db_ssl:
        config["ssl_disabled"] = False

    return mysql.connector.connect(**config)


def init_db():
    try:
        conn = get_db_connection()
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

        conn.commit()
        cursor.close()
        conn.close()

        print("Database initialized successfully.")

    except Exception as e:
        print(f"Database initialization error: {e}")


init_db()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll = request.form.get("roll", "").strip()
        phone = request.form.get("phone", "").strip()
        cgpa = request.form.get("cgpa", "").strip()
        degree = request.form.get("degree", "").strip()

        if not all([name, roll, phone, cgpa, degree]):
            return "All fields are required.", 400

        if r:
            try:
                queue_data = (
                    f"Name: {name}, "
                    f"Roll: {roll}, "
                    f"Phone: {phone}, "
                    f"CGPA: {cgpa}, "
                    f"Degree: {degree}"
                )

                r.lpush("student_queue", queue_data)

            except Exception as e:
                print(f"Redis queue error: {e}")

        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO students
                (name, roll, phone, cgpa, degree)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, roll, phone, cgpa, degree)
            )

            conn.commit()

        except Exception as e:
            print(f"Database insert error: {e}")
            return "Unable to save student data.", 500

        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

        return redirect(url_for("index"))

    return render_template("index.html")


@app.route("/results")
def results():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, roll, phone, cgpa, degree
            FROM students
            ORDER BY id DESC
        """)

        students = cursor.fetchall()

        return render_template(
            "results.html",
            students=students
        )

    except Exception as e:
        print(f"Results database error: {e}")

        return render_template(
            "results.html",
            students=[]
        )

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "80"))

    app.run(
        host="0.0.0.0",
        port=port
    )
