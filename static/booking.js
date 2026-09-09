let currentBooking = null; 
//抓booking資料 渲染畫面
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
        currentBooking = data; //將資料存到全域變數
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
// 刪除功能與按鈕
async function deleteBooking() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/booking', {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return res.json();
}

function setupDeleteBtn() {
  document.getElementById('deleteBtn').addEventListener('click', async () => {
    const token = localStorage.getItem('token');
    try {
      const result = await deleteBooking();
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
// 初始化TapPay SDK
const confirmBtn = document.getElementById('confirmBtn');
function setupTapPay() {
  TPDirect.setupSDK(171024, 'app_ew7tKGjncDIPzWWFExOvln50j2hNrMzmC6yfMCbGN4UEJ1Us3D13tTJrQMxC', 'sandbox');
  //setup
  TPDirect.card.setup({
    fields: {
      number: { element: '#cardNumber', placeholder: '**** **** **** ****' },
      expirationDate: { element: '#cardExpiry', placeholder: 'MM / YY' },
      ccv: { element: '#cardCvv', placeholder: 'CVV' }
    },
    styles: {
      'input': { 'font-size': '16px', 'color': '#000000' }
    }
  });
  //onUpdate 控制付款按鈕能不能按
  TPDirect.card.onUpdate(function (update) {
    confirmBtn.disabled = !update.canGetPrime;
  });
}
// 按下確認訂購並付款，取得TapPay Prime
function setupConfirmBtn() {
  confirmBtn.addEventListener('click', () => {
    //檢查聯絡資訊
    const contactName = document.getElementById('contactName').value.trim();
    const contactEmail = document.getElementById('contactEmail').value.trim();
    const contactPhone = document.getElementById('contactPhone').value.trim();
    if (!contactName || !contactEmail || !contactPhone) {
      alert('請填寫完整的聯絡資訊');
      return;
    }
    //檢查信用卡資訊
    const tappayStatus = TPDirect.card.getTappayFieldsStatus();
    if (!tappayStatus.canGetPrime) {
      alert('請確認信用卡資訊填寫正確');
      return;
    }
    TPDirect.card.getPrime(async(result) => {
      if (result.status !== 0) {
        alert('取得Prime失敗: ' + result.msg);
        return;
      }
      const prime = result.card.prime;
      
      const orderData = {
        prime: prime,
        order: {
          price: currentBooking.price,
          trip: {
            attraction: {
              id: currentBooking.attraction.id,
              name: currentBooking.attraction.name,
              address: currentBooking.attraction.address,
              image: currentBooking.attraction.image
            },
            date: currentBooking.date,
            time: currentBooking.time
          },
          contact: {
            name: contactName,
            email: contactEmail,
            phone: contactPhone
          }
        }
      };

      try {
        const res = await fetch('/api/orders',{
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(orderData)
          
        });
        const orderResult = await res.json();
        // 如果訂單建立失敗，顯示錯誤訊息
        if (orderResult.error) {
          alert(orderResult.message);
          return;
        }
        // 付款成功後，清除預定行程
        if (orderResult.data.payment.status === 0) {
          try {
            await deleteBooking();
          } catch (err) {
            console.error('清除預定行程失敗', err);
          }
        }
        // 導向感謝頁面，並帶上訂單編號
        location.href = `/thankyou?number=${orderResult.data.number}`;
      } catch (err) {
        console.error('建立訂單失敗', err);
      }
    });
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
setupTapPay();
setupConfirmBtn();