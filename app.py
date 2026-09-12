from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
import mysql.connector
import os
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
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
# booking 收到的資聊格式
class BookingInput(BaseModel):
	attractionId: int
	date: str
	time: str
	price: int
# region orders收到的巢狀資料格式
class OrderAttractionInput(BaseModel):
    id: int
    name: str
    address: str
    image: str

class OrderTripInput(BaseModel):
    attraction: OrderAttractionInput
    date: str
    time: str

class OrderContactInput(BaseModel):
    name: str
    email: str
    phone: str

class OrderDetailInput(BaseModel):
    price: int
    trip: OrderTripInput
    contact: OrderContactInput

class CreateOrderInput(BaseModel):
    prime: str
    order: OrderDetailInput
# endregion

# region Attractions
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
#endregion

# region 會員
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
# endregion

# region Booking
# 從Authorization header解析JWT token，回傳user_id；驗證失敗或未登入則回傳None
def get_user_id_from_token(request: Request):
	auth_header = request.headers.get("Authorization")
	if not auth_header:
		return None
	token = auth_header.replace("Bearer ", "")
	try:
		payload = jwt.decode(token, os.environ.get('JWT_SECRET'), algorithms=["HS256"])
		return payload["id"]
	except Exception:
		return None
# POST /api/booking
@app.post("/api/booking")
async def create_booking(request:Request, booking: BookingInput):
	#檢查登入狀態
	user_id = get_user_id_from_token(request)
	if user_id is None:
		return JSONResponse(status_code=403, content={"error": True, "message": "請先登入"})
	if not booking.date:
		return JSONResponse(status_code=400, content={"error": True, "message": "請選擇日期"})
	#確認時間格式是否正確
	if booking.time not in ("morning", "afternoon"):
		return JSONResponse(status_code=400, content={"error": True, "message": "時間格式不正確"})
	# 價格由後端根據time計算，
	price = 2000 if booking.time == "morning" else 2500

	try:
		con = get_connection()
		cursor = con.cursor()
		# 確認景點編號是否存在
		cursor.execute("SELECT id FROM attractions WHERE id = %s", (booking.attractionId,))
		row = cursor.fetchone()
		if row is None:
			cursor.close()
			con.close()
			return JSONResponse(status_code=400, content={"error": True, "message": "景點編號不正確"})
		# 先刪除使用者原本有的預約
		cursor.execute("DELETE FROM bookings WHERE user_id = %s", (user_id,))
		# 新增這筆預約
		cursor.execute(
			"INSERT INTO bookings (user_id, attraction_id, date, time, price) VALUES (%s, %s, %s, %s, %s)",
			(user_id, booking.attractionId, booking.date, booking.time, price)
		)
		con.commit()
		cursor.close()
		con.close()
		return {"ok": True}
	except Exception as e:
		print(e)
		return JSONResponse(status_code=500, content={"error": True, "message": "建立預約時發生錯誤"}) 
# GET /api/booking
@app.get("/api/booking")
async def get_booking(request: Request):
	# 檢查登入狀態
	user_id = get_user_id_from_token(request)
	if user_id is None:
		return JSONResponse(status_code=403, content={"error": True, "message": "請先登入"})
	try:
		con = get_connection()
		cursor = con.cursor()
		# 一次拿景點資料＋預約資訊
		cursor.execute(
			"""
			SELECT attractions.id, attractions.name, attractions.address, attraction_images.image_url,
				bookings.date, bookings.time, bookings.price
			FROM bookings
			JOIN attractions ON bookings.attraction_id = attractions.id
			LEFT JOIN attraction_images ON attraction_images.attraction_id = attractions.id
			WHERE bookings.user_id = %s
			LIMIT 1
			""",
			(user_id,)
		)
		row = cursor.fetchone()
		cursor.close()
		con.close()

		if row is None:
			return {"data": None}

		booking_data = {
			"attraction": {
				"id": row[0],
				"name": row[1],
				"address": row[2],
				"image": row[3]
			},
			"date": str(row[4]),
			"time": row[5],
			"price": row[6]
		}
		return {"data": booking_data}
	except Exception as e:
		print(e)
		return JSONResponse(status_code=500, content={"error": True, "message": "取得預約資料時發生錯誤"})
# DELETE /api/booking
@app.delete("/api/booking")
async def delete_booking(request: Request):
	# 檢查登入狀態
	user_id = get_user_id_from_token(request)
	if user_id is None:
		return JSONResponse(status_code=403, content={"error": True, "message": "請先登入"})

	try:
		con = get_connection()
		cursor = con.cursor()
		cursor.execute("DELETE FROM bookings WHERE user_id = %s", (user_id,))
		con.commit()
		cursor.close()
		con.close()
		return {"ok": True}
	except Exception as e:
		print(e)
		return JSONResponse(status_code=500, content={"error": True, "message": "刪除預約時發生錯誤"})	
# endregion

# region Order
# POST /api/orders
@app.post("/api/orders")
async def create_order(request: Request, body: CreateOrderInput):
    user_id = get_user_id_from_token(request)
	# 檢查登入狀態
    if user_id is None:
        return JSONResponse(status_code=403, content={"error": True, "message": "請先登入"})

    # 檢查聯絡資訊是否完整
    if not body.order.contact.name or not body.order.contact.email or not body.order.contact.phone:
        return JSONResponse(status_code=400, content={"error": True, "message": "聯絡資訊填寫不完整"})

    con = get_connection()
    cursor = con.cursor()

    # 檢查景點是否存在
    cursor.execute("SELECT id FROM attractions WHERE id = %s", (body.order.trip.attraction.id,))
    attraction = cursor.fetchone()
    if attraction is None:
        return JSONResponse(status_code=400, content={"error": True, "message": "景點不存在"})

    try:
        # 產生訂單編號
        order_number = datetime.now().strftime('%Y%m%d%H%M%S')

        # 建立訂單記錄，狀態先設為UNPAID
        cursor.execute(
            """
            INSERT INTO orders (order_number, user_id, attraction_id, date, time, price, contact_name, contact_email, contact_phone, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                order_number,
                user_id,
                body.order.trip.attraction.id,
                body.order.trip.date,
                body.order.trip.time,
                body.order.price,
                body.order.contact.name,
                body.order.contact.email,
                body.order.contact.phone,
                "UNPAID"
            )
        )
        con.commit()

		# 取得剛剛新增那筆訂單的id，等一下要用它來關聯order_payments
        order_id = cursor.lastrowid
        # 呼叫TapPay Pay By Prime API進行信用卡付款
        tappay_res = requests.post(
            "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime",
            headers={
                "Content-Type": "application/json",
                "x-api-key": os.environ.get("TAPPAY_PARTNER_KEY")
            },
            json={
                "prime": body.prime,
                "partner_key": os.environ.get("TAPPAY_PARTNER_KEY"),
                "merchant_id": os.environ.get("TAPPAY_MERCHANT_ID"),
                "details": "台北一日遊行程",
                "amount": body.order.price,
                "cardholder": {
                    "phone_number": body.order.contact.phone,
                    "name": body.order.contact.name,
                    "email": body.order.contact.email
                }
            }
        )
        tappay_result = tappay_res.json()
        payment_status = tappay_result.get("status")
        payment_message = tappay_result.get("msg")
        # 將付款結果寫入payments資料表
        cursor.execute(
            "INSERT INTO order_payments (order_id, status, message) VALUES (%s, %s, %s)",
            (order_id, payment_status, payment_message)
        )
		# 如果付款成功，更新訂單狀態為PAID
        if payment_status == 0:
            cursor.execute(
                "UPDATE orders SET status = %s WHERE id = %s",
                ("PAID", order_id)
            )
        con.commit()
		# 結果回傳給前端
        return {
            "data": {
                "number": order_number,
                "payment": {
                    "status": payment_status,
                    "message": payment_message
                }
            }
        }
    except Exception as err:
        print("建立訂單失敗", err)
        return JSONResponse(status_code=500, content={"error": True, "message": "伺服器內部錯誤"})
# GET /api/order/{orderNumber}
@app.get("/api/order/{orderNumber}")
async def get_order(request: Request, orderNumber: str):
	# 檢查登入狀態
	user_id = get_user_id_from_token(request)
	if user_id is None:
		return JSONResponse(status_code=403, content={"error": True, "message": "請先登入"})

	con = get_connection()
	cursor = con.cursor(dictionary=True)
	cursor.execute(
		"""
		SELECT orders.*, attractions.name AS attraction_name,
	           attractions.address AS attraction_address,
	           attraction_images.image_url AS attraction_image
		FROM orders 
		JOIN attractions ON orders.attraction_id = attractions.id
		LEFT JOIN attraction_images ON attraction_images.attraction_id = attractions.id
		WHERE orders.order_number = %s
		LIMIT 1
		""" ,
		(orderNumber,)
	)
	order = cursor.fetchone()

	# 查無訂單，回傳null
	if order is None:
		return {"data": None}
	# 付款狀態轉換為0或1
	order_status = 1 if order["status"] == "PAID" else 0

	return {		    
		"data": {
			"number": order["order_number"],
			"price": order["price"],
			"trip": {
				"attraction": {
					"id": order["attraction_id"],
					"name": order["attraction_name"],
					"address": order["attraction_address"],
					"image": order["attraction_image"]
				},
				"date": order["date"],
				"time": order["time"]
			},
			"contact": {
				"name": order["contact_name"],
				"email": order["contact_email"],
				"phone": order["contact_phone"]
			},
			"status": order_status
		}
	}
# endregion
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