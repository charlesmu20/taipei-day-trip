let nextPage = 0;
let isLoading = false;
let currentKeyword = '';
// 取得景點資料
async function loadAttractions(page,category,keyword) {
  if (isLoading || page === null) return;
  isLoading = true;
  try {
    const params = new URLSearchParams();
    params.set('page', page);
    if (category) params.set('category', category);
    if (keyword) params.set('keyword', keyword);
    
    const res = await fetch(`/api/attractions?${params.toString()}`);
    const result = await res.json();
    renderAttractions(result.data);
    nextPage = result.nextPage;
  } catch (err) {
    console.error('取得景點資料失敗', err);
  } finally {
    isLoading = false;
  }
}
// 
function renderAttractions(attractions) {
  const container = document.getElementById('attractionsGroup');

  attractions.forEach((item) => {
    const card = document.createElement('a');
    card.className = 'attraction';
    card.href = `/attraction/${item.id}`;

    const attractionContainer = document.createElement('div');
    attractionContainer.className = 'attraction-container';

    const img = document.createElement('img');
    img.className = 'attraction-img';
    img.src = item.images[0];
    img.alt = item.name;

    const overlay = document.createElement('div');
    overlay.className = 'attraction-overlay';

    const title = document.createElement('span');
    title.className = 'attraction-title';
    title.textContent = item.name;

    overlay.appendChild(title);
    attractionContainer.appendChild(img);
    attractionContainer.appendChild(overlay);

    const details = document.createElement('div');
    details.className = 'details';

    const info = document.createElement('div');
    info.className = 'info';

    const mrt = document.createElement('span');
    mrt.className = 'attraction-mrt';
    mrt.textContent = item.mrt ?? '';

    const category = document.createElement('span');
    category.className = 'attraction-category';
    category.textContent = item.category;

    info.appendChild(mrt);
    info.appendChild(category);
    details.appendChild(info);

    card.appendChild(attractionContainer);
    card.appendChild(details);

    container.appendChild(card);
  });
}
// 分類選單
let selectedCategory = null;

async function loadCategoryMenu() {
  const menu = document.getElementById('categoryMenu');
  try {
    const res = await fetch('/api/categories');
    const result = await res.json();
    const categories = result.data;

    const allItem = document.createElement('button');
    allItem.className = 'category-item';
    allItem.type = 'button';
    allItem.textContent = '全部分類';
    allItem.addEventListener('click', () => selectCategory(null, '全部分類'));
    menu.appendChild(allItem);

    categories.forEach((category) => {
      const item = document.createElement('button');
      item.className = 'category-item';
      item.type = 'button';
      item.textContent = category;
      item.addEventListener('click', () => selectCategory(category, category));
      menu.appendChild(item);
    });
  } catch (err) {
    console.error('取得分類資料失敗', err);
  }
}

function selectCategory(category, label) {
  selectedCategory = category;
  document.getElementById('categoryLabel').textContent = label + ' ▼';
  document.getElementById('categoryMenu').hidden = true;
}
// 監聽分類按鈕點擊事件
const categoryBtn = document.getElementById('categoryBtn');
const categoryMenu = document.getElementById('categoryMenu');
categoryBtn.addEventListener('click', () => {
  categoryMenu.hidden = !categoryMenu.hidden;
});
// 監聽搜尋按鈕點擊事件
function searchAttractions() {
  currentKeyword = document.querySelector('.search-input').value;
  document.getElementById('attractionsGroup').replaceChildren();
  nextPage = 0;
  loadAttractions(0, selectedCategory, currentKeyword);
}
document.querySelector('.search-btn').addEventListener('click', searchAttractions);
// 監聽滾動事件
const scrollSentinel = document.getElementById('scrollSentinel');
const scrollObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting && nextPage !== null) {
      loadAttractions(nextPage, selectedCategory, currentKeyword);
    }
  });
});
// List列表
async function loadMrtTabs() {
  const container = document.getElementById('mrtList');
  try {
    const res = await fetch('/api/mrts');
    const result = await res.json();
    const mrts = result.data;

    container.replaceChildren();
    mrts.forEach((mrt) => {
      const btn = document.createElement('button');
      btn.className = 'list-item';
      btn.type = 'button';
      btn.textContent = mrt;
        btn.addEventListener('click', () => {
        document.querySelector('.search-input').value = mrt;
        searchAttractions();
      });
      container.appendChild(btn);
    });
  } catch (err) {
    console.error('取得捷運站資料失敗', err);
  }
}
//按鈕捲動list-bar
const listContainer = document.querySelector('.container');
const arrowLeft = document.querySelector('.arrow-left');
const arrowRight = document.querySelector('.arrow-right');

arrowLeft.addEventListener('click', () => {
  listContainer.scrollBy({ left: -listContainer.clientWidth * 0.8, behavior: 'smooth' });
});

arrowRight.addEventListener('click', () => {
  listContainer.scrollBy({ left: listContainer.clientWidth * 0.8, behavior: 'smooth' });
});

scrollObserver.observe(scrollSentinel);
loadAttractions(0);
loadCategoryMenu();
loadMrtTabs();
