// Sheland Network-First Service Worker with Web Push Notifications
const CACHE_NAME = 'sheland-v3';

self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(keys.map(key => caches.delete(key)));
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});

// Handle Web Push Notifications
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {
    title: 'منصة شي لاند 🛍️',
    body: 'عروض جديدة وأسعار منخفضة جداً! تسوق الآن.',
    url: '/'
  };

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/manifest.json',
      badge: '/manifest.json',
      data: { url: data.url || '/' }
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});

