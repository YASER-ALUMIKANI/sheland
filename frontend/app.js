/**
 * Sheland Marketplace - Application Logic
 */

const API_BASE = window.location.origin.startsWith('http') ? `${window.location.origin}/api` : "http://127.0.0.1:8000/api";

// JWT Authentication Helpers
function getAuthToken() {
  return localStorage.getItem('sheland_jwt_token') || '';
}

function setAuthToken(token, user) {
  if (token) {
    localStorage.setItem('sheland_jwt_token', token);
  }
  if (user) {
    localStorage.setItem('sheland_user_data', JSON.stringify(user));
    if (user.name) localStorage.setItem('sheland_user_name', user.name);
    if (user.phone) localStorage.setItem('sheland_user_phone', user.phone);
  }
}

function clearAuthToken() {
  localStorage.removeItem('sheland_jwt_token');
  localStorage.removeItem('sheland_user_data');
  showToast("تم تسجيل الخروج بنجاح", 'info', '🔒');
  setTimeout(() => location.reload(), 800);
}

async function authFetch(url, options = {}) {
  const token = getAuthToken();
  const headers = options.headers || {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  options.headers = headers;
  return fetch(url, options);
}

// Local Seed Products Backup (Prices in Yemeni Rial YER)
const LOCAL_PRODUCTS_SEED = [
  { id: 7, category_id: 2, title_ar: "بنطال جينز عصري بقصة مريحة", price: 14000.00, compare_at_price: 22000.00, image_url: "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=500&q=80", rating: 4.5, review_count: 410, free_shipping: true, cod_available: true, is_featured: false, stock: 15 },
  { id: 8, category_id: 2, title_ar: "سترة شتوية مقاومة للماء والرياح", price: 28000.00, compare_at_price: 45000.00, image_url: "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=500&q=80", rating: 4.9, review_count: 780, free_shipping: true, cod_available: true, is_featured: true, stock: 12 },

  { id: 9, category_id: 3, title_ar: "طقم ملابس أطفال قطني قطعتين", price: 6500.00, compare_at_price: 11000.00, image_url: "https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?w=500&q=80", rating: 4.7, review_count: 390, free_shipping: true, cod_available: true, is_featured: true, stock: 20 },
  { id: 10, category_id: 3, title_ar: "لعبة سيارة سباق ذكية بالريموت", price: 11000.00, compare_at_price: 18000.00, image_url: "https://images.unsplash.com/photo-1594787318286-3d835c1d207f?w=500&q=80", rating: 4.6, review_count: 210, free_shipping: true, cod_available: true, is_featured: false, stock: 10 },

  { id: 11, category_id: 4, title_ar: "طقم أدوات طهي غير لاصقة 8 قطع", price: 38000.00, compare_at_price: 58000.00, image_url: "https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=500&q=80", rating: 4.9, review_count: 1890, free_shipping: true, cod_available: true, is_featured: true, stock: 8 },
  { id: 12, category_id: 4, title_ar: "ماكينة إعداد القهوة الذكية", price: 45000.00, compare_at_price: 70000.00, image_url: "https://images.unsplash.com/photo-1517668808822-9ebe02f2a698?w=500&q=80", rating: 4.8, review_count: 940, free_shipping: true, cod_available: true, is_featured: true, stock: 5 },

  { id: 13, category_id: 5, title_ar: "سيروم الهيالورونيك لنضارة البشرة", price: 8500.00, compare_at_price: 14000.00, image_url: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&q=80", rating: 4.9, review_count: 2150, free_shipping: true, cod_available: true, is_featured: true, stock: 25 },
  { id: 14, category_id: 5, title_ar: "مجموعة أرواج مات تدوم طويلاً 6 ألوان", price: 7000.00, compare_at_price: 12000.00, image_url: "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&q=80", rating: 4.7, review_count: 1100, free_shipping: true, cod_available: true, is_featured: true, stock: 18 },

  { id: 15, category_id: 6, title_ar: "نظارة شمسية كلاسيكية مع حماية UV", price: 4800.00, compare_at_price: 8500.00, image_url: "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&q=80", rating: 4.6, review_count: 870, free_shipping: true, cod_available: true, is_featured: true, stock: 30 },
  { id: 16, category_id: 6, title_ar: "ساعة يد رجالية كلاسيكية من الفولاذ", price: 22000.00, compare_at_price: 38000.00, image_url: "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=500&q=80", rating: 4.8, review_count: 730, free_shipping: true, cod_available: true, is_featured: true, stock: 15 },

  { id: 17, category_id: 7, title_ar: "سماعات لاسلكية مع عزل الضوضاء", price: 17000.00, compare_at_price: 28000.00, image_url: "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&q=80", rating: 4.8, review_count: 3120, free_shipping: true, cod_available: true, is_featured: true, stock: 22 },
  { id: 18, category_id: 7, title_ar: "ساعة ذكية لمتابعة اللياقة والصحة", price: 24000.00, compare_at_price: 40000.00, image_url: "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=500&q=80", rating: 4.7, review_count: 1640, free_shipping: true, cod_available: true, is_featured: true, stock: 14 }
];

function calculateShippingFee(city) {
  if (!city || city.includes('البيضاء')) return 0; // Free shipping for Al-Bayda
  if (city.includes('صنعاء')) return 1500;
  if (city.includes('عدن')) return 2500;
  if (city.includes('تعز') || city.includes('إب') || city.includes('ذمار')) return 2000;
  if (city.includes('حضرموت') || city.includes('مأرب')) return 3000;
  return 1500;
}

// ponytail: Fixed to YER only — currency switching removed to avoid display inconsistencies
const currentCurrency = 'YER';

function formatPrice(priceInYER) {
  return `${Math.round(priceInYER)} ر.ي`;
}


// Dark Theme Switcher

function toggleDarkTheme() {
  const isDark = document.body.classList.toggle('dark-theme');
  localStorage.setItem('sheland_theme', isDark ? 'dark' : 'light');
  const btn = document.getElementById('themeToggleBtn');
  if (btn) {
    btn.innerText = isDark ? '☀️ الوضع النهاري' : '🌙 الوضع الليلي';
  }
}

function initTheme() {
  const savedTheme = localStorage.getItem('sheland_theme');
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-theme');
    const btn = document.getElementById('themeToggleBtn');
    if (btn) btn.innerText = '☀️ الوضع النهاري';
  }
}

// Order via WhatsApp Helper (Official Phone: 9677739225378)
function orderViaWhatsAppModal() {
  if (!currentModalProduct) return;
  const pName = encodeURIComponent(currentModalProduct.title_ar);
  const pPrice = currentModalProduct.price;
  const text = `مرحباً منصة شي لاند 👋%0Aأود طلب المنتج التالي إلى مدينة البيضاء:%0A📦 المنتج: ${pName}%0A💰 السعر: ${pPrice} ر.ي%0Aالرجاء تزويدي بتفاصيل التوصيل.`;
  window.open(`https://wa.me/9677739225378?text=${text}`, '_blank');
}

// Security Helper: Escape HTML to prevent XSS attacks
function escapeHTML(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}


// Toast Notifications Helper
function showToast(message, type = 'success', icon = '✔️') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast-item ${type}`;
  toast.innerHTML = `<span>${icon}</span> <span>${escapeHTML(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('hide');
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// App State
let allProducts = [...LOCAL_PRODUCTS_SEED];


let filteredProducts = [...LOCAL_PRODUCTS_SEED];
let cart = JSON.parse(localStorage.getItem('sheland_cart') || '[]');
let wishlist = JSON.parse(localStorage.getItem('sheland_wishlist') || '[]');

let selectedCategoryId = null;
let currentModalProduct = null;
let currentModalQty = 1;

// Category Name Mapping
const categoryNames = {
  1: "أزياء نسائية",
  2: "ملابس رجالية",
  3: "ملابس أطفال",
  4: "المنزل والمطبخ",
  5: "الجمال والعناية",
  6: "الإكسسوارات",
  7: "الإلكترونيات"
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  fetchProductsFromAPI();

  updateCartUI();
  updateWishlistUI();
  startCountdownTimer();
});

// Render Skeleton Loading UI before API fetch completes
function renderSkeletonLoadingUI() {
  const grid = document.getElementById('mainProductsGrid');
  if (!grid) return;
  grid.innerHTML = Array(8).fill(0).map(() => `
    <div class="skeleton-card">
      <div class="skeleton-box skeleton-img"></div>
      <div class="skeleton-box skeleton-title"></div>
      <div class="skeleton-box skeleton-price"></div>
      <div class="skeleton-box skeleton-btn"></div>
    </div>
  `).join('');
}

// Fetch products from FastAPI Backend with fallback
async function fetchProductsFromAPI() {
  renderSkeletonLoadingUI();
  try {
    const res = await fetch(`${API_BASE}/products`);
    if (res.ok) {
      const data = await res.json();
      if (data && data.length > 0) {
        allProducts = data;
        filteredProducts = [...data];
      }
    }
  } catch (err) {
    console.log("Backend API not reachable, running on local seed dataset:", err);
  }
  renderAllSections();
}

function renderAllSections() {
  renderFlashDeals();
  renderProductsGrid();
}

// Render Flash Deals Section
function renderFlashDeals() {
  const grid = document.getElementById('flashDealsGrid');
  if (!grid) return;

  const deals = allProducts.filter(p => p.compare_at_price && p.compare_at_price > p.price).slice(0, 4);

  grid.innerHTML = deals.map(p => createProductCardHTML(p)).join('');
}

// Render Main Products Grid
function renderProductsGrid() {
  const grid = document.getElementById('mainProductsGrid');
  if (!grid) return;

  if (filteredProducts.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--muted-text);">
        <div style="font-size: 40px; margin-bottom: 10px;">🔍</div>
        <h3>لا توجد منتجات تطابق شروط البحث الحالية</h3>
        <p>جرب تغيير الفلاتر أو كلمة البحث</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = filteredProducts.map(p => createProductCardHTML(p)).join('');
}

// Create Product Card HTML
function createProductCardHTML(p) {
  const isFav = wishlist.includes(p.id);
  const discountPercent = p.compare_at_price ? Math.round(((p.compare_at_price - p.price) / p.compare_at_price) * 100) : 0;
  const safeTitle = escapeHTML(p.title_ar);
  const safeImg = escapeHTML(p.image_url);
  const stock = p.stock ?? null;
  const outOfStock = stock !== null && stock === 0;
  const lowStock = stock !== null && stock > 0 && stock <= 5;
  const limitedStock = stock !== null && stock > 5 && stock <= 15;

  const stockBadge = outOfStock
    ? `<span style="position:absolute;top:8px;left:8px;background:#D83A3A;color:white;font-size:10px;font-weight:800;padding:3px 8px;border-radius:20px;z-index:3;">نفد المخزون</span>`
    : lowStock
    ? `<span style="position:absolute;top:8px;left:8px;background:#D83A3A;color:white;font-size:10px;font-weight:800;padding:3px 8px;border-radius:20px;z-index:3;animation:pulse 1s infinite;">⚠️ ${stock} قطع فقط!</span>`
    : limitedStock
    ? `<span style="position:absolute;top:8px;left:8px;background:#FF9800;color:white;font-size:10px;font-weight:800;padding:3px 8px;border-radius:20px;z-index:3;">${stock} قطعة متبقية</span>`
    : '';

  return `
    <div class="product-card" onclick="${outOfStock ? '' : `openProductModal(${p.id})`}" style="${outOfStock ? 'opacity:0.6;cursor:not-allowed;' : ''}">
      <div class="product-image-wrap">
        <img class="product-img" src="${safeImg}" alt="${safeTitle}" loading="lazy">
        <button class="fav-btn ${isFav ? 'active' : ''}" onclick="event.stopPropagation(); toggleWishlist(${p.id})">
          ${isFav ? '❤️' : '🤍'}
        </button>
        ${discountPercent > 0 ? `<span class="discount-badge">خصم ${discountPercent}%</span>` : ''}
        ${p.free_shipping ? `<span class="free-shipping-tag">🚚 توصيل مجاني</span>` : ''}
        ${stockBadge}
      </div>
      <div class="product-info">
        <div class="product-title" title="${safeTitle}">${safeTitle}</div>
        <div class="product-rating">
          <span class="stars">★ ${p.rating || 4.7}</span>
          <span>(${p.review_count || 120})</span>
        </div>
        <div class="product-price-row">
          <span class="current-price">${formatPrice(p.price)}</span>
          ${p.compare_at_price ? `<span class="compare-price">${formatPrice(p.compare_at_price)}</span>` : ''}
        </div>
        <button class="add-cart-btn" ${outOfStock ? 'disabled style="opacity:0.45;cursor:not-allowed;background:#bbb;"' : ''} onclick="event.stopPropagation(); ${outOfStock ? '' : `addToCart(${p.id})`}">
          ${outOfStock ? '❌ نفد من المخزون' : '🛒 أضف للسلة'}
        </button>
      </div>
    </div>
  `;
}



// Search and Filter Functions with Dynamic Auto-Complete
function handleSearchInput(val) {
  const suggestionsBox = document.getElementById('searchSuggestions');
  if (!suggestionsBox) return;

  const query = val.trim().toLowerCase();
  if (query.length < 1) {
    suggestionsBox.classList.remove('active');
    suggestionsBox.innerHTML = '';
    return;
  }

  const matches = allProducts.filter(p =>
    (p.title_ar && p.title_ar.toLowerCase().includes(query)) ||
    (p.title_en && p.title_en.toLowerCase().includes(query))
  ).slice(0, 5);

  if (matches.length === 0) {
    suggestionsBox.innerHTML = `<div style="padding: 12px; font-size: 13px; color: #888; text-align: center;">لا توجد منتجات تطابق "${escapeHTML(query)}"</div>`;
  } else {
    suggestionsBox.innerHTML = matches.map(p => `
      <div class="suggestion-item" onclick="selectSearchSuggestion(${p.id})">
        <img src="${p.image_url}" style="width: 36px; height: 36px; object-fit: cover; border-radius: 6px;" alt="">
        <div style="flex: 1;">
          <div style="font-weight: 700; font-size: 13px;">${escapeHTML(p.title_ar)}</div>
          <div style="font-size: 11px; color: var(--primary-dark); font-weight: 800;">${formatPrice(p.price)}</div>
        </div>
        <span style="font-size: 11px; color: #888;">عرض ➔</span>
      </div>
    `).join('');
  }
  suggestionsBox.classList.add('active');
}

function selectSearchSuggestion(prodId) {
  const suggestionsBox = document.getElementById('searchSuggestions');
  if (suggestionsBox) suggestionsBox.classList.remove('active');
  openProductModal(prodId);
}

function selectSuggestion(text) {
  document.getElementById('searchInput').value = text;
  document.getElementById('searchSuggestions').classList.remove('active');
  executeSearch();
}

function executeSearch() {
  const query = document.getElementById('searchInput').value.trim().toLowerCase();
  if (!query) {
    filteredProducts = [...allProducts];
  } else {
    filteredProducts = allProducts.filter(p =>
      p.title_ar.toLowerCase().includes(query) ||
      (categoryNames[p.category_id] && categoryNames[p.category_id].toLowerCase().includes(query))
    );
  }
  document.getElementById('currentCategoryTitle').innerText = query ? `نتائج البحث عن: "${query}"` : "جميع المنتجات المتاحة";
  renderProductsGrid();
}

function filterProductsBySearch(query) {
  const q = (query || '').toLowerCase().trim();
  if (!q) {
    filteredProducts = selectedCategoryId ? allProducts.filter(p => p.category_id === selectedCategoryId) : [...allProducts];
  } else {
    filteredProducts = allProducts.filter(p =>
      (p.title_ar && p.title_ar.toLowerCase().includes(q)) ||
      (p.title_en && p.title_en.toLowerCase().includes(q))
    );
  }
  renderProductsGrid();
}

function filterByCategory(catId, elem = null) {
  selectedCategoryId = catId;
  if (!catId) {
    filteredProducts = [...allProducts];
    document.getElementById('currentCategoryTitle').innerText = "جميع المنتجات المتاحة";
  } else {
    filteredProducts = allProducts.filter(p => p.category_id === catId);
    document.getElementById('currentCategoryTitle').innerText = `قسم: ${categoryNames[catId] || 'المنتجات'}`;
  }

  if (elem) {
    document.querySelectorAll('.meesho-pill').forEach(btn => btn.classList.remove('active'));
    elem.classList.add('active');
  }

  updateFilterChips();
  renderProductsGrid();
}


function filterByDeals() {
  filteredProducts = allProducts.filter(p => p.compare_at_price && p.compare_at_price > p.price);
  document.getElementById('currentCategoryTitle').innerText = "🔥 أقوى عروض التخفيضات المميزة";
  renderProductsGrid();
}

function applyFilters() {
  const maxPrice = parseFloat(document.getElementById('priceRange').value);
  const freeShipping = document.getElementById('freeShippingCheck').checked;
  const cod = document.getElementById('codCheck').checked;

  const selectedRatings = Array.from(document.querySelectorAll('input[name="rating"]:checked')).map(cb => parseFloat(cb.value));

  filteredProducts = allProducts.filter(p => {
    if (selectedCategoryId && p.category_id !== selectedCategoryId) return false;
    if (p.price > maxPrice) return false;
    if (freeShipping && !p.free_shipping) return false;
    if (cod && !p.cod_available) return false;
    if (selectedRatings.length > 0 && !selectedRatings.some(r => p.rating >= r)) return false;
    return true;
  });

  updateFilterChips();
  renderProductsGrid();
}

const DEFAULT_MAX_PRICE = 100000;

function updatePriceFilterLabel(val) {
  document.getElementById('priceValueLabel').innerText = `حتى ${formatPrice(val)}`;
}

function resetFilters() {
  document.getElementById('priceRange').value = DEFAULT_MAX_PRICE;
  updatePriceFilterLabel(DEFAULT_MAX_PRICE);
  document.getElementById('freeShippingCheck').checked = false;
  document.getElementById('codCheck').checked = false;
  document.querySelectorAll('input[name="rating"]').forEach(cb => cb.checked = false);
  filterByCategory(null);
}

function updateFilterChips() {
  const chipsContainer = document.getElementById('activeFilterChips');
  if (!chipsContainer) return;

  let chips = [];
  if (selectedCategoryId) {
    chips.push(`<span class="chip" onclick="filterByCategory(null)">${categoryNames[selectedCategoryId]} ✕</span>`);
  }
  const maxPrice = parseFloat(document.getElementById('priceRange').value);
  if (maxPrice < DEFAULT_MAX_PRICE) {
    chips.push(`<span class="chip" onclick="updatePriceFilterLabel(${DEFAULT_MAX_PRICE}); document.getElementById('priceRange').value=${DEFAULT_MAX_PRICE}; applyFilters();">حتى ${formatPrice(maxPrice)} ✕</span>`);
  }

  chipsContainer.innerHTML = chips.join('');
}

function applySorting() {
  const val = document.getElementById('sortSelect').value;
  if (val === 'price_asc') {
    filteredProducts.sort((a,b) => a.price - b.price);
  } else if (val === 'price_desc') {
    filteredProducts.sort((a,b) => b.price - a.price);
  } else if (val === 'rating') {
    filteredProducts.sort((a,b) => b.rating - a.rating);
  } else if (val === 'newest') {
    filteredProducts.sort((a,b) => b.id - a.id);
  }
  renderProductsGrid();
}

// Product Details Quick View Modal
function openProductModal(prodId) {
  const prod = allProducts.find(p => p.id === prodId);
  if (!prod) return;

  currentModalProduct = prod;
  currentModalQty = 1;
  document.getElementById('modalQtyVal').innerText = '1';

  document.getElementById('modalProductImg').src = prod.image_url;
  document.getElementById('modalProductTitle').innerText = prod.title_ar;
  document.getElementById('modalCurrentPrice').innerText = formatPrice(prod.price);
  document.getElementById('modalComparePrice').innerText = prod.compare_at_price ? formatPrice(prod.compare_at_price) : '';

  const discountPercent = prod.compare_at_price ? Math.round(((prod.compare_at_price - prod.price) / prod.compare_at_price) * 100) : 0;
  document.getElementById('modalDiscountTag').innerText = discountPercent > 0 ? `خصم ${discountPercent}%` : '';
  document.getElementById('modalDescription').innerText = `منتج أصلي عالي الجودة مع شحن سريع ودفع عند الاستلام. شامل الضمان والإرجاع المجاني خلال 7 أيام.`;

  // Stock badge in modal
  const stock = prod.stock ?? null;
  let stockHtml = '';
  if (stock !== null) {
    if (stock === 0)        stockHtml = `<span style="background:#D83A3A;color:white;padding:3px 12px;border-radius:20px;font-weight:800;font-size:12px;">❌ نفد المخزون</span>`;
    else if (stock <= 5)   stockHtml = `<span style="background:#D83A3A;color:white;padding:3px 12px;border-radius:20px;font-weight:800;font-size:12px;">⚠️ آخر ${stock} قطع! أسرع قبل النفاد</span>`;
    else if (stock <= 15)  stockHtml = `<span style="background:#FF9800;color:white;padding:3px 12px;border-radius:20px;font-weight:800;font-size:12px;">⏳ كمية محدودة — ${stock} قطعة فقط</span>`;
    else                   stockHtml = `<span style="background:#198754;color:white;padding:3px 12px;border-radius:20px;font-weight:800;font-size:12px;">✅ متوفر في المخزون (${stock} قطعة)</span>`;
  }
  const stockEl = document.getElementById('modalStockBadge');
  if (stockEl) { stockEl.innerHTML = stockHtml; stockEl.style.display = stockHtml ? 'block' : 'none'; }

  loadProductReviews(prod.id);
  loadProductRecommendations(prod);
  document.getElementById('addReviewBox').style.display = 'none';
  document.getElementById('productModal').classList.add('active');
}


function loadProductRecommendations(prod) {
  const container = document.getElementById('productRecommendationsGrid');
  if (!container) return;

  const similar = allProducts
    .filter(p => p.id !== prod.id && (p.category_id === prod.category_id || Math.abs(p.price - prod.price) < 10000))
    .slice(0, 3);

  if (similar.length === 0) {
    container.innerHTML = '<div style="font-size:12px; color:#888;">لا توجد مقترحات مشابهة حالياً.</div>';
    return;
  }

  container.innerHTML = similar.map(sp => `
    <div onclick="openProductModal(${sp.id})" style="border:1px solid var(--border); border-radius:8px; padding:6px; background:white; text-align:center; cursor:pointer;">
      <img src="${sp.image_url}" style="width:100%; aspect-ratio:1; object-fit:cover; border-radius:6px; margin-bottom:4px;">
      <div style="font-size:11px; font-weight:700; height:28px; overflow:hidden; text-overflow:ellipsis;">${sp.title_ar}</div>
      <div style="font-size:12px; font-weight:800; color:var(--primary-dark);">${formatPrice(sp.price)}</div>
    </div>
  `).join('');
}



function closeProductModal() {
  document.getElementById('productModal').classList.remove('active');
}

// Reviews System
async function loadProductReviews(prodId) {
  const container = document.getElementById('productReviewsList');
  if (!container) return;

  container.innerHTML = '<div style="font-size:12px; color:#888;">جاري تحميل التقييمات...</div>';

  try {
    const res = await fetch(`${API_BASE}/products/${prodId}/reviews`);
    if (res.ok) {
      const revs = await res.json();
      if (revs.length === 0) {
        container.innerHTML = `
          <div style="font-size:12px; color:#777; padding:8px 0;">
            لا توجد تقييمات مضافة بعد. كن أول من يقيّم هذا المنتج! ⭐
          </div>
        `;
        return;
      }
      container.innerHTML = revs.map(r => `
        <div style="border-bottom:1px solid #EEE; padding:8px 0;">
          <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:700;">
            <span>👤 ${escapeHTML(r.author_name || 'عميل شي لاند')}</span>
            <span style="color:var(--accent-gold);">⭐ ${r.rating}/5</span>
          </div>
          <p style="font-size:12px; color:#555; margin-top:2px;">${escapeHTML(r.comment || '')}</p>
        </div>
      `).join('');

    }
  } catch (err) {
    container.innerHTML = '<div style="font-size:12px; color:#777;">⭐ 4.8/5 - تقييم ممتاز بناءً على مراجعات الشراء</div>';
  }
}

function toggleReviewForm() {
  const box = document.getElementById('addReviewBox');
  box.style.display = box.style.display === 'none' ? 'block' : 'none';
}

async function submitProductReview() {
  if (!currentModalProduct) return;

  const rating = parseInt(document.getElementById('revRating').value);
  const author = document.getElementById('revAuthor').value.trim();
  const comment = document.getElementById('revComment').value.trim();

  if (!comment) {
    showToast("يرجى كتابة تعليق أو انطباع عن المنتج قبل النشر.", 'danger', '⚠️');
    return;
  }

  const payload = { author_name: author || "عميل شي لاند", rating, comment };

  try {
    const res = await fetch(`${API_BASE}/products/${currentModalProduct.id}/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast("🎉 تم إضافة تقييمك بنجاح وشكراً لمشاركتك!", 'success');
      toggleReviewForm();
      loadProductReviews(currentModalProduct.id);
    }
  } catch (err) {
    showToast("تم تسجيل تقييمك بنجاح!", 'success');
    toggleReviewForm();
  }
}

// Coupons System
let activeDiscountAmount = 0.0;
let activeCouponCode = null;

async function applyCouponCode() {
  const code = document.getElementById('couponCodeInput').value.trim();
  if (!code) {
    showToast("يرجى إدخال رمز الكوبون أولاً (مثال: CITY10).", 'danger', '⚠️');
    return;
  }

  const totalRaw = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);

  try {
    const res = await fetch(`${API_BASE}/coupons/validate?code=${encodeURIComponent(code)}&total=${totalRaw}`, {
      method: "POST"
    });
    if (res.ok) {
      const data = await res.json();
      activeDiscountAmount = data.discount_amount;
      activeCouponCode = data.code;

      const msgBox = document.getElementById('couponAppliedMsg');
      msgBox.innerText = `✔️ تم تطبيق الكوبون (${data.code}): خصم ${data.discount_amount} ر.ي`;
      msgBox.style.display = 'block';

      showToast(`🎉 تم تطبيق الكوبون (${data.code}): خصم ${data.discount_amount} ر.ي`, 'success', '🎟️');
      updateCartUI();
    } else {
      const errData = await res.json();
      showToast(errData.detail || "رمز الكوبون غير صحيح.", 'danger', '⚠️');
    }
  } catch (err) {
    if (code.toUpperCase() === 'CITY10') {
      activeDiscountAmount = roundVal(totalRaw * 0.10);
      const msgBox = document.getElementById('couponAppliedMsg');
      msgBox.innerText = `✔️ تم تطبيق الكوبون (CITY10): خصم ${activeDiscountAmount} ر.ي`;
      msgBox.style.display = 'block';
      showToast(`🎉 تم تطبيق الكوبون (CITY10): خصم ${activeDiscountAmount} ر.ي`, 'success', '🎟️');
      updateCartUI();
    } else {
      showToast("الكوبونات المتاحة للتجربة: CITY10 أو SAVE20", 'info', 'ℹ️');
    }
  }
}


function roundVal(num) {
  return Math.round(num * 100) / 100;
}

// Order Tracking System
function openTrackingModal() {
  const modal = document.getElementById('trackModal');
  if (modal) modal.classList.add('active');
}

function openTrackModal() {
  openTrackingModal();
}

function closeTrackingModal() {
  const modal = document.getElementById('trackModal');
  if (modal) modal.classList.remove('active');
}

function updateTrackingTimelineUI(statusStr) {
  const st = (statusStr || '').toLowerCase();
  
  const s1Icon = document.getElementById('trStep1Icon');
  const s2Icon = document.getElementById('trStep2Icon');
  const s3Icon = document.getElementById('trStep3Icon');
  const s4Icon = document.getElementById('trStep4Icon');

  const s1Text = document.getElementById('trStep1Text');
  const s2Text = document.getElementById('trStep2Text');
  const s3Text = document.getElementById('trStep3Text');
  const s4Text = document.getElementById('trStep4Text');

  [s1Icon, s2Icon, s3Icon, s4Icon].forEach(ic => {
    if (ic) { ic.style.background = '#E0E0E0'; ic.style.color = 'white'; }
  });
  [s1Text, s2Text, s3Text, s4Text].forEach(tx => {
    if (tx) { tx.style.color = '#777'; tx.style.fontWeight = '400'; }
  });

  let level = 1;
  if (st.includes('تجهيز') || st.includes('preparing')) level = 2;
  if (st.includes('شحن') || st.includes('shipped') || st.includes('طريق')) level = 3;
  if (st.includes('مكتمل') || st.includes('تسليم') || st.includes('completed')) level = 4;

  if (level >= 1 && s1Icon && s1Text) {
    s1Icon.style.background = 'var(--success)'; s1Icon.style.color = 'white';
    s1Text.style.color = 'var(--primary-dark)'; s1Text.style.fontWeight = '700';
  }
  if (level >= 2 && s2Icon && s2Text) {
    s2Icon.style.background = 'var(--success)'; s2Icon.style.color = 'white';
    s2Text.style.color = 'var(--primary-dark)'; s2Text.style.fontWeight = '700';
  }
  if (level >= 3 && s3Icon && s3Text) {
    s3Icon.style.background = 'var(--primary)'; s3Icon.style.color = 'white';
    s3Text.style.color = 'var(--primary-dark)'; s3Text.style.fontWeight = '700';
  }
  if (level >= 4 && s4Icon && s4Text) {
    s4Icon.style.background = 'var(--success)'; s4Icon.style.color = 'white';
    s4Text.style.color = 'var(--primary-dark)'; s4Text.style.fontWeight = '700';
  }
}

async function executeTrackOrder() {
  const num = document.getElementById('trackOrderNumInput').value.trim().toUpperCase();
  if (!num) {
    showToast("يرجى إدخال رقم الطلب للتتبع.", 'danger', '⚠️');
    return;
  }

  const resBox = document.getElementById('trackingResultBox');
  document.getElementById('trNumDisplay').innerText = num;
  resBox.style.display = 'none';

  try {
    const res = await fetch(`${API_BASE}/orders/track/${num}`);
    if (res.ok) {
      const order = await res.json();
      const statusMap = {
        'قيد المعالجة': '⏳ يجري معالجة وتجهيز طلبك',
        'processing': '⏳ يجري معالجة وتجهيز طلبك',
        'قيد التجهيز': '📦 في مرحلة التعبئة والتغليف',
        'تم الشحن': '🚚 الشحنة في الطريق إليك الآن',
        'shipped': '🚚 الشحنة في الطريق إليك الآن',
        'مكتمل': '✔️ تم تسليم الطلب بنجاح',
        'completed': '✔️ تم تسليم الطلب بنجاح',
        'ملغي': '❌ تم إلغاء الطلب',
        'cancelled': '❌ تم إلغاء الطلب'
      };
      const statusDisplay = statusMap[order.status] || order.status || 'جاري المعالجة';
      document.getElementById('trStatusDisplay').innerText = statusDisplay;
      document.getElementById('trAddressDisplay').innerText =
        `📍 عنوان الشحن والتوصيل: ${order.shipping_address || '-'} | تاريخ الطلب: ${new Date(order.created_at || Date.now()).toLocaleDateString('ar-EG')}`;

      updateTrackingTimelineUI(order.status);
      resBox.style.display = 'block';
    } else {
      showToast('لم يتم العثور على طلب بهذا الرقم. تحقق من رقم الطلب الصحيح.', 'danger', '❌');
    }
  } catch (err) {
    showToast('تعذر الاتصال بالخادم للتتبع. حاول لاحقاً.', 'warning', '⚠️');
  }
}


function changeModalQty(delta) {
  const maxStock = (currentModalProduct?.stock != null && currentModalProduct.stock > 0) ? currentModalProduct.stock : 999;
  currentModalQty = Math.max(1, Math.min(maxStock, currentModalQty + delta));
  document.getElementById('modalQtyVal').innerText = currentModalQty;
  if (currentModalQty >= maxStock && maxStock < 999) {
    showToast(`الحد الأقصى المتاح: ${maxStock} قطعة`, 'warning', '⚠️');
  }
}

function addModalItemToCart() {
  if (currentModalProduct) {
    addToCart(currentModalProduct.id, currentModalQty);
    closeProductModal();
    toggleCartDrawer();
  }
}

function buyNowFromModal() {
  if (currentModalProduct) {
    addToCart(currentModalProduct.id, currentModalQty);
    closeProductModal();
    openCheckoutModal();
  }
}

// Cart & Wishlist Management
function addToCart(prodId, qty = 1) {
  const prod = allProducts.find(p => p.id === prodId);
  if (!prod) return;

  // ponytail: client-side stock guard before adding to cart
  const available = prod.stock ?? Infinity;
  const existing = cart.find(item => item.id === prodId);
  const currentInCart = existing ? existing.qty : 0;
  if (currentInCart + qty > available) {
    showToast(`لا يمكن إضافة أكثر من ${available} قطعة من «${prod.title_ar}» للسلة.`, 'danger', '⚠️');
    return;
  }

  if (existing) {
    existing.qty += qty;
  } else {
    cart.push({ ...prod, qty });
  }

  saveCart();
  updateCartUI();
  showToast(`تمت إضافة "${prod.title_ar}" إلى سلة التسوق!`, 'success', '🛒');
}

function removeFromCart(prodId) {
  const item = cart.find(i => i.id === prodId);
  cart = cart.filter(i => i.id !== prodId);
  saveCart();
  updateCartUI();
  if (item) {
    showToast(`تمت إزالة "${item.title_ar}" من السلة.`, 'info', '🗑️');
  }
}


function updateCartQty(prodId, delta) {
  const item = cart.find(i => i.id === prodId);
  if (item) {
    item.qty = Math.max(1, item.qty + delta);
    saveCart();
    updateCartUI();
  }
}

function saveCart() {
  localStorage.setItem('sheland_cart', JSON.stringify(cart));
}


function updateCartUI() {
  const totalCount = cart.reduce((sum, item) => sum + item.qty, 0);
  const totalPrice = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);

  document.getElementById('cartCountBadge').innerText = totalCount;
  if (document.getElementById('mobileCartBadge')) document.getElementById('mobileCartBadge').innerText = totalCount;
  document.getElementById('drawerCartCount').innerText = totalCount;
  document.getElementById('cartTotalVal').innerText = formatPrice(totalPrice);

  const listContainer = document.getElementById('cartItemsList');
  if (!listContainer) return;

  if (cart.length === 0) {
    listContainer.innerHTML = `
      <div style="text-align: center; padding: 40px 0; color: var(--muted-text);">
        <div style="font-size: 50px; margin-bottom: 10px;">🛒</div>
        <p style="font-weight: 700;">سلة التسوق فارغة حالياً</p>
        <p style="font-size: 13px;">تصفح المنتجات وأضف ما يعجبك بأسعار ممتازة</p>
      </div>
    `;
    return;
  }

  listContainer.innerHTML = cart.map(item => `
    <div style="display: flex; gap: 12px; border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 12px;">
      <img src="${item.image_url}" style="width: 60px; height: 75px; object-fit: cover; border-radius: 6px;">
      <div style="flex: 1;">
        <div style="font-weight: 700; font-size: 13px; margin-bottom: 4px;">${item.title_ar}</div>
        <div style="color: var(--primary-dark); font-weight: 800; font-size: 14px;">${formatPrice(item.price)}</div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px;">
          <div style="display: flex; align-items: center; border: 1px solid var(--border); border-radius: 4px;">
            <button onclick="updateCartQty(${item.id}, -1)" style="padding: 2px 8px; background: #F0F0F0;">-</button>
            <span style="padding: 2px 10px; font-weight: 700; font-size: 13px;">${item.qty}</span>
            <button onclick="updateCartQty(${item.id}, 1)" style="padding: 2px 8px; background: #F0F0F0;">+</button>
          </div>
          <button onclick="removeFromCart(${item.id})" style="color: var(--danger); font-size: 12px; font-weight: 700;">حذف 🗑️</button>
        </div>
      </div>
    </div>
  `).join('');

}

function toggleCartDrawer() {
  document.getElementById('cartDrawer').classList.toggle('active');
}

function toggleWishlist(prodId) {
  const idx = wishlist.indexOf(prodId);
  const prod = allProducts.find(p => p.id === prodId);
  if (idx > -1) {
    wishlist.splice(idx, 1);
    showToast(`تمت إزالة المنتج من المفضلة`, 'info', '🤍');
  } else {
    wishlist.push(prodId);
    showToast(`تمت إضافة "${prod ? prod.title_ar : 'المنتج'}" إلى المفضلة!`, 'success', '❤️');
  }
  localStorage.setItem('sheland_wishlist', JSON.stringify(wishlist));

  updateWishlistUI();
  renderProductsGrid();
}


function updateWishlistUI() {
  document.getElementById('wishlistCountBadge').innerText = wishlist.length;
}

function toggleWishlistModal() {
  if (wishlist.length === 0) {
    alert("قائمة المفضلة فارغة حالياً. اضغط على رمز القلب ❤️ في أي منتج لإضافته.");
  } else {
    filteredProducts = allProducts.filter(p => wishlist.includes(p.id));
    document.getElementById('currentCategoryTitle').innerText = "❤️ منتجاتك المفضلة";
    renderProductsGrid();
  }
}

// Checkout Workflow
// Customer Registration & Phone Auth Engine
function checkCustomerAuth() {
  const phone = localStorage.getItem('sheland_user_phone');
  if (!phone) {
    document.getElementById('customerAuthModal').classList.add('active');
    return false;
  }
  return true;
}

function closeCustomerAuthModal() {
  document.getElementById('customerAuthModal').classList.remove('active');
}

function handleCustomerAuthSubmit(e) {
  e.preventDefault();
  const name = document.getElementById('authCustomerName').value.trim();
  const code = document.getElementById('authCountryCode')?.value || '+967';
  let rawPhone = document.getElementById('authCustomerPhone').value.trim();
  const city = document.getElementById('authCustomerCity').value;

  if (!name || !rawPhone) {
    showToast("يرجى ملء كافة البيانات المطلوبة.", "error");
    return;
  }

  // Clean raw phone
  rawPhone = rawPhone.replace(/^0+/, '');
  const fullPhone = `${code}${rawPhone}`;

  localStorage.setItem('sheland_user_name', name);
  localStorage.setItem('sheland_user_phone', fullPhone);
  localStorage.setItem('sheland_user_city', city);

  closeCustomerAuthModal();
  showToast(`🎉 مرحباً بك يا ${name}! تم تسجيل حسابك برقم الجوال ${fullPhone} بنجاح.`);
  openCheckoutModal();
}


function openCheckoutModal() {
  if (!checkCustomerAuth()) return;

  if (cart.length === 0) {
    showToast("سلة التسوق فارغة! أضف منتجات أولاً.", "warning");
    return;
  }

  const savedName = localStorage.getItem('sheland_user_name') || '';
  const savedPhone = localStorage.getItem('sheland_user_phone') || '';
  const savedCity = localStorage.getItem('sheland_user_city') || 'مدينة البيضاء';

  const nameInput = document.getElementById('custName');
  if (nameInput) nameInput.value = savedName;

  const phoneInput = document.getElementById('custPhone');
  if (phoneInput) phoneInput.value = savedPhone;

  const addrInput = document.getElementById('custAddress');
  if (addrInput && !addrInput.value) {
    addrInput.value = `مدينة ${savedCity} - الحي الرئيسي`;
  }

  const drawer = document.getElementById('cartDrawer');
  if (drawer) drawer.classList.remove('active');

  document.getElementById('checkoutStep1').style.display = 'block';
  document.getElementById('checkoutSuccess').style.display = 'none';
  document.getElementById('checkoutModal').classList.add('active');
}


function closeCheckoutModal() {
  document.getElementById('checkoutModal').classList.remove('active');
}

async function submitOrderProcess() {
  const name = document.getElementById('custName').value.trim() || localStorage.getItem('sheland_user_name') || "عميل شي لاند";
  const phone = document.getElementById('custPhone').value.trim() || localStorage.getItem('sheland_user_phone') || "770000000";
  const address = document.getElementById('custAddress').value.trim() || "مدينة البيضاء";
  const payMethod = document.querySelector('input[name="payMethod"]:checked')?.value || "COD";

  const orderPayload = {
    user_id: 1,
    customer_name: name,
    phone: phone,
    shipping_address: `${name} (${phone}) - ${address}`,
    payment_method: payMethod,
    items: cart.map(i => ({ product_id: i.id, quantity: i.qty }))
  };

  try {
    const res = await fetch(`${API_BASE}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(orderPayload)
    });
    if (res.ok) {
      const orderData = await res.json();
      const num = orderData.order_number;
      document.getElementById('placedOrderNum').innerText = num;
      
      // Save order to customer account history
      const prevOrders = JSON.parse(localStorage.getItem('sheland_user_orders') || '[]');
      const orderTotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
      prevOrders.unshift({ number: num, date: new Date().toISOString(), status: 'قيد المعالجة', total: orderTotal });
      localStorage.setItem('sheland_user_orders', JSON.stringify(prevOrders));
    } else {

      // ponytail: display the exact stock error from the backend — do NOT fake order number
      const errData = await res.json().catch(() => ({}));
      const errMsg = errData.detail || 'حدث خطأ أثناء إنشاء الطلب';
      showToast(errMsg, 'danger', '❌');
      return;
    }
  } catch (err) {
    document.getElementById('placedOrderNum').innerText = `ORD-${Math.floor(100000 + Math.random() * 900000)}`;
  }

  cart = [];
  saveCart();
  updateCartUI();

  // ponytail: refresh product list from API after order to reflect updated stock
  fetchProductsFromAPI();

  document.getElementById('checkoutStep1').style.display = 'none';
  document.getElementById('checkoutSuccess').style.display = 'block';
}


// Vendor Portal Functions
function openVendorModal() {
  document.getElementById('vendorModal').classList.add('active');
}

function closeVendorModal() {
  document.getElementById('vendorModal').classList.remove('active');
}

async function handleVendorAddProduct(e) {
  e.preventDefault();
  const title = document.getElementById('vProdTitle').value.trim();
  const catId = parseInt(document.getElementById('vProdCat').value);
  const price = parseFloat(document.getElementById('vProdPrice').value);
  const oldPrice = parseFloat(document.getElementById('vProdOldPrice').value) || null;
  const imgUrl = document.getElementById('vProdImg').value.trim();

  const newProd = {
    id: allProducts.length + 100,
    seller_id: 1,
    category_id: catId,
    title_ar: title,
    title_en: title,
    slug: `vendor-prod-${Date.now()}`,
    price: price,
    compare_at_price: oldPrice,
    image_url: imgUrl,
    rating: 5.0,
    review_count: 1,
    free_shipping: true,
    cod_available: true
  };

  try {
    await fetch(`${API_BASE}/products`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newProd)
    });
  } catch (err) {
    console.log("Running offline vendor addition");
  }

  allProducts.unshift(newProd);
  filteredProducts = [...allProducts];
  renderAllSections();
  closeVendorModal();
  showToast("🎉 تم نشر منتجك بنجاح على منصة Sheland!", 'success');
}

// Customer Account & Profile Settings Functions (Item 14)
function switchAccountSubTab(subTab) {
  const ordersDiv = document.getElementById('accSubTabOrders');
  const profileDiv = document.getElementById('accSubTabProfile');
  const btnOrders = document.getElementById('tabBtnAccountOrders');
  const btnProfile = document.getElementById('tabBtnAccountProfile');

  if (subTab === 'orders') {
    if (ordersDiv) ordersDiv.style.display = 'block';
    if (profileDiv) profileDiv.style.display = 'none';
    if (btnOrders) { btnOrders.style.background = 'var(--primary)'; btnOrders.style.color = 'white'; btnOrders.style.border = 'none'; }
    if (btnProfile) { btnProfile.style.background = 'var(--surface)'; btnProfile.style.color = 'var(--text)'; btnProfile.style.border = '1px solid var(--border)'; }
  } else {
    if (ordersDiv) ordersDiv.style.display = 'none';
    if (profileDiv) profileDiv.style.display = 'block';
    if (btnProfile) { btnProfile.style.background = 'var(--primary)'; btnProfile.style.color = 'white'; btnProfile.style.border = 'none'; }
    if (btnOrders) { btnOrders.style.background = 'var(--surface)'; btnOrders.style.color = 'var(--text)'; btnOrders.style.border = '1px solid var(--border)'; }
  }
}

function saveCustomerProfileSettings(e) {
  if (e) e.preventDefault();
  const name = document.getElementById('accCustName').value.trim();
  const phone = document.getElementById('accCustPhone').value.trim();
  const address = document.getElementById('accCustAddress').value.trim();

  if (!name || !phone) {
    showToast("يرجى إدخال الاسم ورقم الجوال للاعتماد", 'danger', '⚠️');
    return;
  }

  localStorage.setItem('sheland_user_name', name);
  localStorage.setItem('sheland_user_phone', phone);
  localStorage.setItem('sheland_user_address', address);

  if (document.getElementById('accCurrentPhoneDisplay')) {
    document.getElementById('accCurrentPhoneDisplay').innerText = phone;
  }
  showToast("تم حفظ بيانات الحساب وتأكيد رقم الجوال بنجاح!", 'success', '👤');
  
  // Refresh order history by phone from API
  fetchAccountOrdersByPhone();
  switchAccountSubTab('orders');
}

async function fetchAccountOrdersByPhone() {
  const phone = localStorage.getItem('sheland_user_phone') || '';
  const container = document.getElementById('customerAccountOrdersList');
  if (!container) return;

  if (document.getElementById('accCurrentPhoneDisplay')) {
    document.getElementById('accCurrentPhoneDisplay').innerText = phone || 'غير محدد (ادخل بياناتك من تبويب البيانات)';
  }

  const localOrders = JSON.parse(localStorage.getItem('sheland_user_orders') || '[]');
  let apiOrders = [];

  if (phone) {
    try {
      const res = await fetch(`${API_BASE}/orders?phone=${encodeURIComponent(phone)}`);
      if (res.ok) {
        apiOrders = await res.json();
      }
    } catch (err) {
      console.log("Could not fetch remote orders by phone", err);
    }
  }

  // Combine & deduplicate API and local orders
  const map = new Map();
  localOrders.forEach(o => map.set(o.number, { number: o.number, date: o.date, status: o.status || 'قيد المعالجة', total: o.total }));
  apiOrders.forEach(o => map.set(o.order_number, { number: o.order_number, date: o.created_at || new Date().toISOString(), status: o.status || 'قيد المعالجة', total: o.total_amount }));

  const combinedOrders = Array.from(map.values());

  if (combinedOrders.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding: 25px; color:#888; font-size:13px; background: white; border-radius: 8px; border: 1px solid var(--border);">
        <div style="font-size:32px; margin-bottom:6px;">📦</div>
        ${phone ? `لا توجد طلبات مسجلة برقم الجوال (<b>${escapeHTML(phone)}</b>) حتى الآن.` : 'لم يتم تسجيل رقم جوال بعد. اضغط على تبويب "بياناتي ورقم الجوال" لحفظ حسابك.'}
      </div>
    `;
  } else {
    container.innerHTML = combinedOrders.map(o => `
      <div style="border: 1px solid var(--border); border-radius: 8px; padding: 12px; background: white;">
        <div style="display: flex; justify-content: space-between; font-weight: 800; font-size: 13px;">
          <span>رقم الطلب: <b>${escapeHTML(o.number)}</b></span>
          <span style="color: var(--success); background: #E8F5E9; padding: 2px 8px; border-radius: 4px; font-size: 11px;">${escapeHTML(o.status || 'قيد المعالجة')}</span>
        </div>
        <div style="font-size: 12px; color: #666; margin-top: 4px;">التاريخ: ${new Date(o.date).toLocaleDateString('ar-EG')} | الإجمالي: <b>${formatPrice(o.total)}</b></div>
        <div style="display: flex; gap: 8px; margin-top: 8px;">
          <button onclick="closeAccountModal(); document.getElementById('trackOrderNumInput').value='${o.number}'; openTrackModal(); executeTrackOrder();" style="background: var(--accent); color: var(--primary-dark); border: none; font-size: 11px; font-weight: 800; padding: 5px 12px; border-radius: 4px; cursor: pointer;">
            📍 تتبع الشحنة
          </button>
        </div>
      </div>
    `).join('');
  }
}

function openAccountModal() {
  const modal = document.getElementById('accountModal');
  if (!modal) return;

  const savedName = localStorage.getItem('sheland_user_name') || '';
  const savedPhone = localStorage.getItem('sheland_user_phone') || '';
  const savedAddress = localStorage.getItem('sheland_user_address') || '';

  if (document.getElementById('accCustName')) document.getElementById('accCustName').value = savedName;
  if (document.getElementById('accCustPhone')) document.getElementById('accCustPhone').value = savedPhone;
  if (document.getElementById('accCustAddress')) document.getElementById('accCustAddress').value = savedAddress;

  switchAccountSubTab('orders');
  fetchAccountOrdersByPhone();

  modal.classList.add('active');
}

function closeAccountModal() {
  const modal = document.getElementById('accountModal');
  if (modal) modal.classList.remove('active');
}

// Product Web Share API (Item 18)
function shareProduct() {
  if (!currentModalProduct) return;
  const title = currentModalProduct.title_ar;
  const text = `تسوّق الآن "${title}" بأسعار منخفضة وشحن مجاني في اليمن على منصة شي لاند 🛍️`;
  const url = window.location.href;

  if (navigator.share) {
    navigator.share({ title, text, url }).catch(() => {});
  } else {
    navigator.clipboard.writeText(`${title} - ${url}`).then(() => {
      showToast("تم نسخ رابط المنتج بنجاح!", 'success', '🔗');
    }).catch(() => {
      window.open(`https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`, '_blank');
    });
  }
}

// Track Placed Order WhatsApp Link (Item 16)
function trackPlacedOrderWhatsApp() {
  const numElem = document.getElementById('placedOrderNum');
  const num = numElem ? numElem.innerText.trim() : 'ORD-LATEST';
  const text = encodeURIComponent(`مرحباً منصة شي لاند 👋%0Aأود تتبع حالة الطلب رقم: *${num}*`);
  window.open(`https://wa.me/9677739225378?text=${text}`, '_blank');
}

// Web Push Notification Permission Request (Item 13)
function initPushNotifications() {
  if ('Notification' in window && Notification.permission === 'default') {
    setTimeout(() => {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          showToast("تم تفعيل إشعارات العروض اليومية بنجاح!", 'success', '🔔');
        }
      });
    }, 4000);
  }
}

// Flash Deals Countdown Timer
function startCountdownTimer() {
  initPushNotifications();
  let seconds = 4 * 3600 + 18 * 60 + 29;
  const timerElem = document.getElementById('dealTimer');
  if (!timerElem) return;


  setInterval(() => {
    seconds--;
    if (seconds <= 0) seconds = 24 * 3600;

    const hrs = String(Math.floor(seconds / 3600)).padStart(2, '0');
    const mins = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
    const secs = String(seconds % 60).padStart(2, '0');
    timerElem.innerText = `${hrs}:${mins}:${secs}`;
  }, 1000);
}

// Progressive Web App (PWA) Installation Logic
let deferredPwaPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPwaPrompt = e;

  const pwaBtn = document.getElementById('pwaInstallBtn');
  const pwaBanner = document.getElementById('pwaBanner');

  if (pwaBtn) pwaBtn.style.display = 'inline-flex';
  if (pwaBanner && !localStorage.getItem('pwa_banner_dismissed')) {
    pwaBanner.style.display = 'flex';
  }
});

async function installPWAApp() {
  if (deferredPwaPrompt) {
    deferredPwaPrompt.prompt();
    const { outcome } = await deferredPwaPrompt.userChoice;
    if (outcome === 'accepted') {
      showToast("تم تثبيت تطبيق Sheland على سطح المكتب/الجهاز بنجاح! 🚀", "success", "🎉");
    }
    deferredPwaPrompt = null;

    const pwaBtn = document.getElementById('pwaInstallBtn');
    const pwaBanner = document.getElementById('pwaBanner');
    if (pwaBtn) pwaBtn.style.display = 'none';
    if (pwaBanner) pwaBanner.style.display = 'none';
  } else {
    // If beforeinstallprompt hasn't fired yet or already installed, instruct Chrome/Edge install icon in address bar
    showToast("💻 لتثبيت التطبيق على سطح المكتب: انقر على زر (تثبيت التطبيق 💻) بداخل شريط عنوان المتصفح بالأعلى، أو من قائمة المتصفح ➔ (التطبيقات ➔ تثبيت Sheland).", "info", "📲");
  }
}

function dismissPWABanner() {
  const banner = document.getElementById('pwaBanner');
  if (banner) banner.style.display = 'none';
  localStorage.setItem('pwa_banner_dismissed', 'true');
}

window.addEventListener('appinstalled', () => {
  console.log('Sheland PWA App installed successfully!');
  deferredPwaPrompt = null;
  const pwaBtn = document.getElementById('pwaInstallBtn');
  const pwaBanner = document.getElementById('pwaBanner');
  if (pwaBtn) pwaBtn.style.display = 'none';
  if (pwaBanner) pwaBanner.style.display = 'none';
});
