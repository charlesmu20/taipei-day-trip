let images = [];
let currentIndex = 0;
// 預先載入所有圖片
function preloadImages(urls) {
  urls.forEach((url) => {
    const img = new Image();
    img.src = url;
  });
}
//從網頁抓景點id
function getAttractionId() {
  return window.location.pathname.split('/').pop();
}
//抓後端景點資料
async function loadAttraction(){
  const attractionId = getAttractionId();
  try {
    const res = await fetch(`/api/attraction/${attractionId}`);
    const result = await res.json();

    if (result.error) {
    console.error(result.message);
    return;
    }

    renderAttraction(result.data);
  } catch (err) {
    console.error('取得景點資料失敗', err);
}
}
//渲染畫面
function renderAttraction(attraction) {
  
  document.getElementById('profileTitle').textContent = attraction.name;
  document.getElementById('profileSubtitle').textContent = attraction.mrt? `${attraction.category} at ${attraction.mrt}`: attraction.category;

  images = attraction.images;
  preloadImages(images);
  currentIndex = 0;
  renderImage();                
  document.getElementById('currentImg').alt = attraction.name;
  renderIndicators(); 
  
  document.getElementById('attractionDesc').textContent = attraction.description;
  document.getElementById('infoAddress').textContent = attraction.address;
  document.getElementById('infoTransport').textContent = attraction.transport;
}
function setupTimeSelection() {
  const radios = document.querySelectorAll('input[name="timeSlot"]');
  radios.forEach((radio) => {
    radio.addEventListener('change', () => {
      updatePrice(radio.value);
    });
  });
}
function updatePrice(timeSlot) {
  const price = timeSlot === 'morning' ? 2000 : 2500;
  document.getElementById('priceValue').textContent = `新台幣 ${price} 元`;
}
//渲染圖片

// 顯示目前這張圖片
function renderImage() {
  document.getElementById('currentImg').src = images[currentIndex];
}
// 載入時建立indicator
function renderIndicators() {
  const bar = document.getElementById('indicatorBar');
  images.forEach((img, index) => {
    const span = document.createElement('span');
    span.className = 'indicator-segment' + (index === currentIndex ? ' active' : '');
    bar.appendChild(span);
  });
}
//切換active 樣式
function updateIndicators() {
  const segments = document.querySelectorAll('#indicatorBar .indicator-segment');
  segments.forEach((segment, index) => {
    segment.classList.toggle('active', index === currentIndex);
  });
}
// 左右箭頭事件
function setupArrows() {
  document.getElementById('prevBtn').addEventListener('click', () => {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    renderImage();
    updateIndicators();
  });

  document.getElementById('nextBtn').addEventListener('click', () => {
    currentIndex = (currentIndex + 1) % images.length;
    renderImage();
    updateIndicators();
  });
}
setupArrows();
setupTimeSelection();
loadAttraction();