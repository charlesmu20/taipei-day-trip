//抓booking資料
async function loadBookingData(){
    const token = localStorage.getItem('token');
    try{
        const res = await fetch('/api/booking',{
            headers: { 'Authorization' : `Bearer ${token}` }
        });
        const result = await res.json();
        //如果後端抓沒有資料
        if (!result.data) {
            document.getElementById('bookingContent').style.display = 'none';
            document.getElementById('bookingEmpty').style.display = 'block';
            return;
        }

        document.getElementById('bookingContent').style.display = 'block';
        const data = result.data;
        document.getElementById('bookingImg').src = data.attraction.image;
        document.getElementById('bookingTitle').textContent = `台北一日遊：${data.attraction.name}`;
        document.getElementById('bookingDate').textContent = data.date;
        const timeText = data.time === 'morning' ? '早上9點到下午4點' : '下午4點到晚上11點';
        document.getElementById('bookingTime').textContent = timeText;
        document.getElementById('bookingPrice').textContent = `新台幣${data.price}元`;
        document.getElementById('bookingAddress').textContent = data.attraction.address;
        document.getElementById('confirmTotal').textContent = `總價：新台幣 ${data.price} 元`;
    } catch (err) {
        console.error('取得預約資料失敗', err);
    }
}
// 刪除按鈕
function setupDeleteBtn() {
  document.getElementById('deleteBtn').addEventListener('click', async () => {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch('/api/booking', {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await res.json();
      if (result.ok) {
        location.reload();
      } else {
        alert(result.message);
      }
    } catch (err) {
      console.error('刪除預約失敗', err);
    }
  });
}
async function init() {
  const user = await authCheckPromise;
  if (!user) {
    location.href = '/';
    return;
  }
  document.getElementById('headlineName').textContent = user.name;
  document.getElementById('contactName').value = user.name;
  document.getElementById('contactEmail').value = user.email;
  loadBookingData();
  setupDeleteBtn();
}
init();