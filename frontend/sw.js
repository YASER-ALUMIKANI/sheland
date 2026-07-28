// Sheland Network-First Service Worker
const CACHE_NAME = 'sheland-v2';

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
  // Always fetch fresh from network for API and pages
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
