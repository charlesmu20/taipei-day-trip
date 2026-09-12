async function loadOrderData() {
  const params = new URLSearchParams(window.location.search);
  const orderNumber = params.get('number');
  // 沒有帶number參數，直接導回首頁
  if (!orderNumber) {
    location.href = '/';
    return;
  }
  document.getElementById('orderNumber').textContent = orderNumber;

  const token = localStorage.getItem('token');
  try {
    const res = await fetch(`/api/order/${orderNumber}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const result = await res.json();

    if (!result.data) {
      console.error('查無此訂單');
      return;
    }

    const data = result.data;

    if (data.status === 1) {
      // 付款成功：顯示訊息 + 完整行程資訊
      document.getElementById('thankyouMessage').textContent = '訂購成功，感謝您的預訂！';
      document.getElementById('orderDetail').style.display = 'flex';

      document.getElementById('orderImg').src = data.trip.attraction.image;
      document.getElementById('orderTitle').textContent = `台北一日遊：${data.trip.attraction.name}`;
      document.getElementById('orderDate').textContent = data.trip.date;
      const timeText = data.trip.time === 'morning' ? '早上9點到下午4點' : '下午4點到晚上11點';
      document.getElementById('orderTime').textContent = timeText;
      document.getElementById('orderPrice').textContent = `新台幣${data.price}元`;
      document.getElementById('orderAddress').textContent = data.trip.attraction.address;
    } else {
      // 付款失敗：只顯示訊息，藏起行程資訊
      document.getElementById('thankyouMessage').textContent = '很抱歉，付款未完成，請重新嘗試付款。';
      document.getElementById('orderDetail').style.display = 'none';
    }
  } catch (err) {
    console.error('取得訂單資料失敗', err);
  }
}

// 先確認登入狀態，沒登入就導回首頁
async function init() {
  const user = await authCheckPromise;
  if (!user) {
    location.href = '/';
    return;
  }
  loadOrderData();
}

init();