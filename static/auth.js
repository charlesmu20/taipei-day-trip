const dialogOverlay = document.getElementById('dialogOverlay')
const authTrigger = document.getElementById('authTrigger');
const signinForm = document.getElementById('signinForm');
const signupForm = document.getElementById('signupForm');
// 開啟登入視窗（顯示登入表單）
function openSigninDialog() {
  signinForm.style.display = 'flex';
  signupForm.style.display = 'none';
  dialogOverlay.style.display = 'flex';
}
// 預定行程 按鈕
function setupBookingTrigger() {
  document.getElementById('bookingTrigger').addEventListener('click', () => {
    if (isLoggedIn) {
      location.href = '/booking';
    } else {
      openSigninDialog();
    }
  });
}
// 綁定登入/登出按鈕開關事件
function setupDialogToggle(){
    authTrigger.addEventListener('click',function(){
        if (isLoggedIn) {
            signOut();
        } else {
            openSigninDialog()
        }
    });
    document.getElementById('dialogClose').addEventListener('click',function(){
        dialogOverlay.style.display = 'none';
    });
}
// 切換登入/註冊表單
function setupFormSwitch() {
  document.getElementById('switchToSignup').addEventListener('click', () => {
    signinForm.style.display = 'none';
    signupForm.style.display = 'flex';
});
  document.getElementById('switchToSignin').addEventListener('click', () => {
    signupForm.style.display = 'none';
    signinForm.style.display = 'flex';
});
}
// 檢查登入狀態
let isLoggedIn = false;
async function checkAuthStatus() {
    const token = localStorage.getItem('token');
    try {
        const res = await fetch('/api/user/auth',{
            headers: token ? {'Authorization':`Bearer ${token}`} : {}
        });
        const result = await res.json();
        renderAuthStatus(result.data);
        return result.data; //把使用者資料回傳出去
    } catch (err) {
        console.error('取得登入狀態失敗', err);
    }
}
// 根據登入狀態，更新右上角文字
function renderAuthStatus(user) {
  if (user) {
    isLoggedIn = true;
    authTrigger.textContent = '登出系統';
  } else {
    isLoggedIn = false;
    authTrigger.textContent = '登入/註冊';
  }
}
// 登出
function signOut() {
  localStorage.removeItem('token');
  location.reload();
}
// 註冊帳號
function setupSignUp() {
  document.getElementById('signupBtn').addEventListener('click', async() => {
    const name = document.getElementById('signupName').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPassword').value;
    const signupError = document.getElementById('signupError'); 
    // 檢查欄位
    if (!name || !email || !password) {
        signupError.style.display = 'block';
        signupError.style.color = '#E74C3C';
        signupError.textContent = '請填寫所有欄位';
        return;  
    }
    //檢查密碼是否包含空白
    if (/\s/.test(password)) {
        signupError.style.display = 'block';
        signupError.style.color = '#E74C3C';
        signupError.textContent = '密碼不可包含空白';
        return;
    }

    try{
        const res = await fetch('/api/user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json'},
            body: JSON.stringify({name, email, password})
        });
        const result = await res.json();

        signupError.style.display = 'block';

        if (result.ok) {
            signupError.style.color = '#448899';
            signupError.textContent = '註冊成功！請登入';
            document.getElementById('signupName').value = '';
            document.getElementById('signupEmail').value = '';
            document.getElementById('signupPassword').value = '';
        } else {
            signupError.style.color = '#E74C3C';
            signupError.textContent = result.message;
        }
    } catch (err) {
        console.error('註冊失敗', err);
    }
  });
}
// 登入帳碼
function setupSignIn() {
    document.getElementById('signinBtn').addEventListener('click', async() => {
        const email = document.getElementById('signinEmail').value.trim();
        const password = document.getElementById('signinPassword').value;
        const signinError = document.getElementById('signinError');

        if (!email || !password) {
            signinError.style.display = 'block';
            signinError.style.color = '#E74C3C';
            signinError.textContent = '請填寫所有欄位';
            return;  
        }
        try{
            const res = await fetch ('/api/user/auth',{
                method : 'PUT',
                headers: { 'Content-Type': 'application/json'},
                body: JSON.stringify({email, password})
            });
            const result = await res.json();

            if (result.token){
                localStorage.setItem('token', result.token);
                location.reload();
            } else {
                signinError.style.display = 'block';
                signinError.style.color = '#E74C3C';
                signinError.textContent = result.message;
            }
        } catch (err) {
            console.error('登入失敗', err);
        }
    });
}
setupDialogToggle();
setupFormSwitch();
let authCheckPromise = checkAuthStatus();  
setupSignUp();
setupSignIn();
setupBookingTrigger();