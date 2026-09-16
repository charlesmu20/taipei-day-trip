//登出按鈕
document.getElementById('logoutBtn').addEventListener('click', signOut);

//load mcp token
async function loadToken(){
    const token = localStorage.getItem('token');
    try {
        const res = await fetch('/api/user/mcp-token',{
            headers:{'Authorization': `Bearer ${token}`}
        });
        const result = await res.json();
        renderToken(result.data.mcp_token);
    } catch (err) {
        console.error('取得mcp token失敗', err);
    }
}
//render mcp token
function renderToken(mcpToken){
    document.getElementById('tokenValue').textContent = mcpToken ;
}
// Create mcp token
function createToken(){
    document.getElementById('generateBtn').addEventListener('click',async ()=>{
        const token = localStorage.getItem('token');
        try {
            const res = await fetch('/api/user/mcp-token',{
                method:'POST',
                headers:{'Authorization': `Bearer ${token}`}
            });
            const result = await res.json();
            renderToken(result.data.mcp_token);
        }catch (err) {
            console.error('產生金鑰失敗', err);
            alert('產生金鑰時發生錯誤，請稍後再試');
        }
    })
}

async function init() {
    const user = await authCheckPromise;
    if (!user) {
    location.href = '/';
    return;
    }

    document.getElementById('headlineName').textContent = user.name;
    document.getElementById('hostUrl').textContent = location.origin + '/mcp/';

    loadToken();
    createToken();
}

init();