/**
 * Gotinha - Service Worker para cache offline básico
 * Cacheia assets estáticos e última conversa
 */

const CACHE_NAME = 'gotinha-v3';
const STATIC_ASSETS = [
  '/',
  '/static/style.css?v=3',
  '/static/app.js',
  // Fontes IBM Plex (CDN)
  'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap'
];

// Install - cacheia assets estáticos
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS.map(url => new Request(url, { credentials: 'same-origin' })));
    }).then(() => self.skipWaiting())
  );
});

// Activate - limpa caches antigos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch - strategy: network first para API, cache first para static
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Não intercepte requests não-GET
  if (event.request.method !== 'GET') return;
  
  // API requests - network first, fallback para cache
  if (url.pathname.startsWith('/health') || url.pathname.startsWith('/ready')) {
    event.respondWith(networkFirst(event.request));
    return;
  }
  
  // Static assets - cache first
  if (url.pathname.startsWith('/static/') || STATIC_ASSETS.includes(url.href)) {
    event.respondWith(cacheFirst(event.request));
    return;
  }
  
  // HTML pages - network first com fallback offline
  if (event.request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirst(event.request));
    return;
  }
  
  // Default - network first
  event.respondWith(networkFirst(event.request));
});

async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  
  if (cached) {
    // Atualiza cache em background
    fetch(request).then(response => {
      if (response.ok) cache.put(request, response.clone());
    }).catch(() => {});
    return cached;
  }
  
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (error) {
    return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
  }
}

async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    
    // Fallback para página offline
    if (request.headers.get('accept')?.includes('text/html')) {
      return cache.match('/');
    }
    return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
  }
}

// Background sync para enviar perguntas quando voltar online
self.addEventListener('sync', (event) => {
  if (event.tag === 'send-message') {
    event.waitUntil(sendQueuedMessages());
  }
});

async function sendQueuedMessages() {
  // Implementar se necessário: ler de IndexedDB e reenviar
  console.log('Background sync: send-message');
}
