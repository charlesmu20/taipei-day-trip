from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
import mysql.connector
import os
def get_connection():
    password = os.environ.get('DB_PASSWORD')
    con = mysql.connector.connect(
        host='localhost',
        user='root',
        password=password,
        database='taipei_day_trip'
    )
    return con

app=FastAPI()
#attractions
@app.get("/api/attractions")
async def get_attractions(page: int,category: str = None,keyword: str = None):
	try:
		offset = page * 8
		con = get_connection()
		cursor = con.cursor()

		if category and keyword:
			hotel_keyword = '%'+ keyword +'%'
			cursor.execute("SELECT * FROM attractions WHERE category = %s AND (mrt=%s OR name LIKE %s) LIMIT 8 OFFSET %s",(category,keyword,hotel_keyword,offset))
		elif category:
			cursor.execute("SELECT * FROM attractions WHERE category = %s LIMIT 8 OFFSET %s", (category, offset))
		elif keyword:
			hotel_keyword = '%'+ keyword +'%'
			cursor.execute("SELECT * FROM attractions WHERE (mrt=%s OR name LIKE %s) LIMIT 8 OFFSET %s",(keyword,hotel_keyword,offset))
		else:
			cursor.execute("SELECT * FROM attractions LIMIT 8 OFFSET %s", (offset,))
		rows = cursor.fetchall()
		
		attractions = []
		for row in rows:
			id = row[0]
			cursor.execute("SELECT image_url FROM attraction_images WHERE attraction_id = %s", (id,))
			image_rows = cursor.fetchall()
			images = [img_row[0] for img_row in image_rows]
			attraction = {
				"id": row[0],
				"name": row[1],
				"category": row[2],
				"description": row[3],
				"address": row[4],
				"transport": row[5],
				"mrt": row[6],
				"lat": row[7],
				"lng": row[8],
				"images": images
			}
			attractions.append(attraction)
		cursor.close()
		con.close()

		if len(rows) < 8:
			next_page = None
		else:
			next_page = page + 1
		return {"nextPage": next_page,"data": attractions}
	
	except Exception as e:
		print(e)
		return JSONResponse(status_code=500, content={"error":True, "message":"取得景點資料時發生錯誤"})
	
#attraction/{attractionId}
@app.get("/api/attraction/{attractionId}")
async def get_attraction(attractionId: int):
	try:
		con = get_connection()
		cursor = con.cursor()
		cursor.execute("SELECT * FROM attractions WHERE id = %s", (attractionId,))
		row = cursor.fetchone()
		if row is None:
			return JSONResponse(status_code=400, content={"error":True, "message":"景點編號不正確"})
		
		cursor.execute("SELECT image_url FROM attraction_images WHERE attraction_id = %s", (attractionId,))
		image_rows = cursor.fetchall()
		images = [img_row[0] for img_row in image_rows]
		attraction = {
			"id": row[0],
			"name": row[1],
			"category": row[2],
			"description": row[3],
			"address": row[4],
			"transport": row[5],
			"mrt": row[6],
			"lat": row[7],
			"lng": row[8],
			"images": images
		}
		cursor.close()
		con.close()
		return {"data":attraction}
	except Exception as e:
		print(e)
		return JSONResponse(status_code=500, content={"error": True, "message": "取得景點資料時發生錯誤"})

#categories
@app.get("/api/categories")
async def get_categories():
	try:
		con = get_connection()
		cursor = con.cursor()
		cursor.execute("SELECT DISTINCT category FROM attractions")
		rows = cursor.fetchall()
		cursor.close()
		con.close()
		categories = [row[0] for row in rows]
		return {"data": categories}
	except Exception as e:
		print(e)
		return JSONResponse(status_code=500, content={"error":True, "message":"取得分類資料時發生錯誤"})
#mrt
@app.get("/api/mrts")
async def get_mrts():
	try:
		con = get_connection()
		cursor = con.cursor()
		cursor.execute("SELECT mrt, COUNT(*) as count FROM attractions WHERE mrt IS NOT NULL AND mrt != '' GROUP BY mrt ORDER by count DESC")
		rows = cursor.fetchall()
		cursor.close()
		con.close()
		mrts = [row[0] for row in rows]
		return {"data": mrts}
	except Exception as e:
		print(e)
		return JSONResponse(status_code=500, content={"error":True, "message":"取得捷運資料時發生錯誤"})
# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")