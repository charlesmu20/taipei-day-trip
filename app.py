from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
import mysql.connector
import os
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
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
# 註冊API收到的資料格式
class UserSignUpInput(BaseModel):
	name: str
	email: str
	password: str
# 登入API收到的資料格式
class UserSignInInput(BaseModel):
	email: str
	password: str
# --------------  Attraction -------------------
#/api/attractions
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
# --------------  Attraction Category -------------------
# 景點分類
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
# -------------- MRT Station -------------------
# 景點捷運站
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
# -------------- User -------------------
# 註冊會員
@app.post("/api/user")
async def sign_up(user: UserSignUpInput):
	try:
		con = get_connection()
		cursor = con.cursor()

		# 檢查email是否已存在
		cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
		existing = cursor.fetchone()
		if existing:
			cursor.close()
			con.close()
			return JSONResponse(status_code=400, content={"error": True, "message": "此Email已經被註冊"})
		#雜湊密碼
		hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')			
		#寫入資料庫
		cursor.execute(
			"INSERT INTO users (name,email,password) VALUES(%s,%s,%s)",
			(user.name, user.email, hashed_password)
		)
		con.commit()
		cursor.close()
		con.close()
		return {"ok": True}
	except Exception as e:
		print(e)
		return JSONResponse(status_code=500, content={"error": True, "message": "註冊時發生錯誤"})
# 登入會員
@app.put("/api/user/auth")
async def sign_in(user: UserSignInInput):
	try:
		con = get_connection()
		cursor = con.cursor()	
		# 用email查詢使用者資料
		cursor.execute("SELECT id, name, email, password FROM users WHERE email = %s", (user.email,))
		row = cursor.fetchone()
		cursor.close()
		con.close()

		# 沒有信箱資料代表帳號不存在
		if row is None:
			return JSONResponse(status_code=400, content={"error": True, "message": "帳號或密碼錯誤"})
		# 有資料 把查詢結果拆開存進對應的變數
		user_id, name, email, hashed_password = row

		#驗證密碼是否正確
		is_correct = bcrypt.checkpw(user.password.encode('utf-8'), hashed_password.encode('utf-8'))
		if not is_correct:
			return JSONResponse(status_code=400, content={"error": True, "message": "帳號或密碼錯誤"})

		# 密碼正確，產生JWT TOKEN，7天後過期
		payload = {
			"id": user_id,
			"name": name,
			"email": email,
			"exp": datetime.now(timezone.utc) + timedelta(days=7)
		}
		token = jwt.encode(payload, os.environ.get('JWT_SECRET'), algorithm="HS256")

		return{"token": token}
	
	except Exception as e:
		print(e)
		return JSONResponse(status_code=500, content={"error": True, "message": "登入時發生錯誤"})
# 取得目前登入的會員資訊
@app.get("/api/user/auth")
async def get_current_user(request: Request):
	# 讀取Authorization header
	auth_header = request.headers.get("Authorization")	
	#沒帶Token，表示未登入
	if auth_header is None:
		return {"data": None}
	
	try:	
		#拿掉前綴，取得 Token 字串
		token = auth_header.replace("Bearer ","")
		#解碼並驗證Token
		payload = jwt.decode(token, os.environ.get('JWT_SECRET'), algorithms=["HS256"])
		# 驗證成功，回傳使用者資訊
		return {"data": {
			"id": payload["id"],
			"name": payload["name"],
			"email": payload["email"]
		}}		
	except Exception as e:
		# TOKEN無效或過期，一律視為未登入
		print(e)
		return {"data": None}
# --------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
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