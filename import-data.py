import json
import mysql.connector
import os

with open('data/taipei-attractions.json', encoding='utf-8') as f:
    data = json.load(f)

password = os.environ.get('DB_PASSWORD')

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password=password,
    database='taipei_day_trip'
)

cursor = con.cursor()
img_host = data['img_host'] 
for item in data['list']:
    #存 attractions 資料
    id = item['_id']
    name = item['name']
    category = item['CAT']
    description = item['description']
    address = item['address']
    direction = item['direction']
    mrt = item['MRT']
    lat = float(item['latitude'])
    lng = float(item['longitude'])
    #cursor.execute("INSERT INTO attractions (id, name, category, description, address, transport, mrt, lat, lng) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (id, name, category, description, address, direction, mrt, lat, lng)  )
    #存 attraction_images 資料
    imgurl = item['imgurls']
    paths = imgurl.split('/imgs/')
    paths = paths[1:]
    full_urls = [img_host + '/imgs/' + p for p in paths]
    for url in full_urls:
        cursor.execute("INSERT INTO attraction_images (attraction_id, image_url) VALUES (%s, %s)", (id, url))
con.commit()
