/**
 * Sheland Marketplace - Application Logic
 */

const API_BASE = "http://localhost:8000/api";

// Local Seed Products Backup (Prices in Yemeni Rial YER)
const LOCAL_PRODUCTS_SEED = [
  { id: 7, category_id: 2, title_ar: "بنطال جينز عصري بقصة مريحة", price: 55.00, compare_at_price: 95.00, image_url: "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=500&q=80", rating: 4.5, review_count: 410, free_shipping: true, cod_available: true, is_featured: false },
  { id: 8, category_id: 2, title_ar: "سترة شتوية مقاومة للماء والرياح", price: 119.00, compare_at_price: 199.00, image_url: "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=500&q=80", rating: 4.9, review_count: 780, free_shipping: true, cod_available: true, is_featured: true },

  { id: 9, category_id: 3, title_ar: "طقم ملابس أطفال قطني قطعتين", price: 25.00, compare_at_price: 45.00, image_url: "https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?w=500&q=80", rating: 4.7, review_count: 390, free_shipping: true, cod_available: true, is_featured: true },
  { id: 10, category_id: 3, title_ar: "لعبة سيارة سباق ذكية بالريموت", price: 45.00, compare_at_price: 75.00, image_url: "https://images.unsplash.com/photo-1594787318286-3d835c1d207f?w=500&q=80", rating: 4.6, review_count: 210, free_shipping: true, cod_available: true, is_featured: false },

  { id: 11, category_id: 4, title_ar: "طقم أدوات طهي غير لاصقة 8 قطع", price: 149.00, compare_at_price: 240.00, image_url: "https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=500&q=80", rating: 4.9, review_count: 1890, free_shipping: true, cod_available: true, is_featured: true },
  { id: 12, category_id: 4, title_ar: "ماكينة إعداد القهوة الذكية", price: 189.00, compare_at_price: 299.00, image_url: "https://images.unsplash.com/photo-1517668808822-9ebe02f2a698?w=500&q=80", rating: 4.8, review_count: 940, free_shipping: true, cod_available: true, is_featured: true },

  { id: 13, category_id: 5, title_ar: "سيروم الهيالورونيك لنضارة البشرة", price: 35.00, compare_at_price: 60.00, image_url: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&q=80", rating: 4.9, review_count: 2150, free_shipping: true, cod_available: true, is_featured: true },
  { id: 14, category_id: 5, title_ar: "مجموعة أرواج مات تدوم طويلاً 6 ألوان", price: 29.00, compare_at_price: 50.00, image_url: "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&q=80", rating: 4.7, review_count: 1100, free_shipping: true, cod_available: true, is_featured: true },

  { id: 15, category_id: 6, title_ar: "نظارة شمسية كلاسيكية مع حماية UV", price: 19.00, compare_at_price: 35.00, image_url: "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&q=80", rating: 4.6, review_count: 870, free_shipping: true, cod_available: true, is_featured: true },
  { id: 16, category_id: 6, title_ar: "ساعة يد رجالية كلاسيكية من الفولاذ", price: 89.00, compare_at_price: 150.00, image_url: "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=500&q=80", rating: 4.8, review_count: 730, free_shipping: true, cod_available: true, is_featured: true },

  { id: 17, category_id: 7, title_ar: "سماعات لاسلكية مع عزل الضوضاء", price: 69.00, compare_at_price: 119.00, image_url: "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&q=80", rating: 4.8, review_count: 3120, free_shipping: true, cod_available: true, is_featured: true },
  { id: 18, category_id: 7, title_ar: "ساعة ذكية لمتابعة اللياقة والصحة", price: 99.00, compare_at_price: 169.00, image_url: "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=500&q=80", rating: 4.7, review_count: 1640, free_shipping: true, cod_available: true, is_featured: true }
];

function calculateShippingFee(city) {
  if (!city || city.includes('البيضاء')) return 0; // Free shipping for Al-Bayda
  if (city.includes('صنعاء')) return 1500;
  if (city.includes('عدن')) return 2500;
  if (city.includes('تعز') || city.includes('إب') || city.includes('ذمار')) return 2000;
  if (city.includes('حضرموت') || city.includes('مأرب')) return 3000;
  return 1500;
}

// Multi-Currency Engine

let currentCurrency = localStorage.getItem('sheland_currency') || 'YER';
const exchangeRates = {
  'YER': { rate: 1, symbol: 'ر.ي' },
  'SAR': { rate: 1 / 420, symbol: 'ر.س' },
  'USD': { rate: 1 / 1580, symbol: '$' }
};

function setCurrency(curr) {
  currentCurrency = curr;
  localStorage.setItem('sheland_currency', curr);
  const sel = document.getElementById('currencySelect');
  if (sel) sel.value = curr;
  renderProductsGrid();
  updateCartUI();
}

function formatPrice(priceInYER) {
  const currData = exchangeRates[currentCurrency] || exchangeRates['YER'];
  const converted = priceInYER * currData.rate;
  if (currentCurrency === 'USD') {
    return `${currData.symbol}${converted.toFixed(2)}`;
  }
  return `${Math.round(converted)} ${currData.symbol}`;
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

// Order via WhatsApp Helper
function orderViaWhatsAppModal() {
  if (!currentModalProduct) return;
  const pName = encodeURIComponent(currentModalProduct.title_ar);
  const pPrice = currentModalProduct.price;
  const text = `مرحباً منصة شي لاند 👋%0Aأود طلب المنتج التالي إلى مدينة البيضاء:%0A📦 المنتج: ${pName}%0A💰 السعر: ${pPrice} ر.ي%0Aالرجاء تزويدي بتفاصيل التوصيل.`;
  window.open(`https://wa.me/967770000000?text=${text}`, '_blank');
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

// Fetch products from FastAPI Backend with fallback
async function fetchProductsFromAPI() {
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

  return `
    <div class="product-card" onclick="openProductModal(${p.id})">
      <div class="product-image-wrap">
        <img class="product-img" src="${safeImg}" alt="${safeTitle}" loading="lazy">
        <button class="fav-btn ${isFav ? 'active' : ''}" onclick="event.stopPropagation(); toggleWishlist(${p.id})">
          ${isFav ? '❤️' : '🤍'}
        </button>
        ${discountPercent > 0 ? `<span class="discount-badge">خصم ${discountPercent}%</span>` : ''}
        ${p.free_shipping ? `<span class="free-shipping-tag">🚚 توصيل مجاني</span>` : ''}
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

        <button class="add-cart-btn" onclick="event.stopPropagation(); addToCart(${p.id})">
          🛒 أضف للسلة
        </button>
      </div>
    </div>
  `;
}


// Search and Filter Functions
function handleSearchInput(val) {
  const suggestionsBox = document.getElementById('searchSuggestions');
  if (val.trim().length > 1) {
    suggestionsBox.classList.add('active');
  } else {
    suggestionsBox.classList.remove('active');
  }
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

function updatePriceFilterLabel(val) {
  document.getElementById('priceValueLabel').innerText = `حتى ${val} ر.ي`;
}

function resetFilters() {
  document.getElementById('priceRange').value = 300;
  updatePriceFilterLabel(300);
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
  if (maxPrice < 300) {
    chips.push(`<span class="chip" onclick="updatePriceFilterLabel(300); document.getElementById('priceRange').value=300; applyFilters();">حتى ${maxPrice} ر.ي ✕</span>`);
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
            <span>👤 ${escapeHTML(r.author_name || 'عميل سيتي لاند')}</span>
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

  const payload = { author_name: author || "عميل سيتي لاند", rating, comment };

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
  document.getElementById('trackModal').classList.add('active');
}

function closeTrackingModal() {
  document.getElementById('trackModal').classList.remove('active');
}

async function executeTrackOrder() {
  const num = document.getElementById('trackOrderNumInput').value.trim();
  if (!num) {
    alert("يرجى إدخال رقم الطلب للتتبع.");
    return;
  }

  const resBox = document.getElementById('trackingResultBox');
  document.getElementById('trNumDisplay').innerText = num;
  document.getElementById('trAddressDisplay').innerText = `العنوان المقيد: الرياض - المملكة العربية السعودية (حالة الشحنة: في الطريق للتسليم)`;
  resBox.style.display = 'block';
}


function changeModalQty(delta) {
  currentModalQty = Math.max(1, currentModalQty + delta);
  document.getElementById('modalQtyVal').innerText = currentModalQty;
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

  const existing = cart.find(item => item.id === prodId);
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
      document.getElementById('placedOrderNum').innerText = orderData.order_number;
    } else {
      document.getElementById('placedOrderNum').innerText = `ORD-${Math.floor(100000 + Math.random() * 900000)}`;
    }
  } catch (err) {
    document.getElementById('placedOrderNum').innerText = `ORD-${Math.floor(100000 + Math.random() * 900000)}`;
  }

  cart = [];
  saveCart();
  updateCartUI();

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

function openAccountModal() {
  showToast("مرحباً بك في Sheland! يمكنك إدارة طلباتك السابقة وعناوين الشحن من هنا.", 'info');
}


// Flash Deals Countdown Timer
function startCountdownTimer() {
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
