import os
import mysql.connector

def get_connection():
    password = os.environ.get('DB_PASSWORD')
    con = mysql.connector.connect(
        host='localhost',
        user='root',
        password=password,
        database='taipei_day_trip'
    )
    return con

def get_user_id_by_mcp_token(token):
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("SELECT id FROM users WHERE mcp_token = %s", (token,))
    row = cursor.fetchone()
    cursor.close()
    con.close()
    if row is None:
        return None
    return row[0]
# 建立訂單
def create_booking(user_id, attraction_id, date, time, price):
    con = get_connection()
    cursor = con.cursor()

    cursor.execute("SELECT id FROM attractions WHERE id = %s", (attraction_id,))
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        con.close()
        return False

    cursor.execute("DELETE FROM bookings WHERE user_id = %s", (user_id,))
    cursor.execute(
        "INSERT INTO bookings (user_id, attraction_id, date, time, price) VALUES (%s, %s, %s, %s, %s)",
        (user_id, attraction_id, date, time, price)
    )
    con.commit()
    cursor.close()
    con.close()
    return True