import os
import time
import redis
import mysql.connector

redis_host = os.environ.get('REDIS_HOST', 'redis')
db_host = os.environ.get('DB_HOST', 'db')
db_user = os.environ.get('DB_USER', 'root')
db_password = os.environ.get('DB_PASSWORD', 'secret')
db_name = os.environ.get('DB_NAME', 'students_db')

print("Connecting to Redis...")
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

print("Worker started, watching student queue...")

while True:
    try:
        # Pop data from Redis queue
        item = r.brpop('student_queue', timeout=5)
        if item:
            queue_name, data = item
            print(f"Processed student data from queue: {data}")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(1)
