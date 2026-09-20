from fastmcp import FastMCP
from db import get_connection, get_user_id_by_mcp_token, create_booking
from fastmcp.server.dependencies import get_http_headers, get_http_request

mcp_server = FastMCP(name="台北一日遊")
mcp_app = mcp_server.http_app(path="/")
#搜尋景點
@mcp_server.tool(
    name="搜尋台北市景點",
    description="透過關鍵字和捷運站名搜尋台北市一日旅遊的景點"
)
async def search_taipei_attractions(keyword: str) -> dict:
    """
    Args:
        keyword: 景點名稱或捷運站名稱的關鍵字
    """
    try:
        con = get_connection()
        cursor = con.cursor(dictionary=True)
        fuzzy_keyword = '%'+ keyword + '%'
        cursor.execute(
            """
            SELECT id, name, description FROM attractions
            WHERE mrt = %s OR name LIKE %s
            """,
            (keyword, fuzzy_keyword)
        )
        attractions = cursor.fetchall()
        cursor.close()
        con.close()

        return {"data": attractions}
    except Exception as e:
        print(e)
        return {"error": True}
#建立預約資訊
@mcp_server.tool(
    name="預定景點導覽行程",
    description="根據景點編號、日期、時間、價格，預定一個景點導覽行程"
)
async def book_attraction(attraction_id: int, date: str, time: str, price: int) -> dict:
    """
    Args:
        attraction_id: 景點編號
        date: 預定日期，格式為YYYY-MM-DD
        time: 上半天 或 下半天
        price: 預定價格，上半天為2000元，下半天為2500元
    """
    try:
        #從request header拿bearer token，反查對應的使用者
        headers = get_http_headers(include={"authorization"})
        auth_header = headers.get("authorization")
        if not auth_header:
            return {"error":True}
        token = auth_header.replace("Bearer ","")

        user_id = get_user_id_by_mcp_token(token)
        if user_id is None:
            return {"error": True}
        # 驗證time、換算price
        if time == "上半天":
            internal_time = "morning"
            expected_price = 2000
        elif time == "下半天":
            internal_time = "afternoon"
            expected_price = 2500
        else:
            return {"error": True}

        if price != expected_price:
            return {"error": True}

        if not date:
            return {"error": True}
        # 呼叫函式建立預約
        success = create_booking(user_id, attraction_id, date, internal_time, expected_price)
        if not success:
            return {"error": True}
        # 算出目前網址
        request = get_http_request()
        booking_page_url = f"{request.base_url}booking"

        return {
            "ok": True,
            "message": f"台北導覽行程，預定成功，請到 {booking_page_url} 完成付款。"
        }
    except Exception as e:
        print(e)
        return {"error": True}