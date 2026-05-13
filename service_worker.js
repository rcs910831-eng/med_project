// PHARMA-MOBILE Service Worker
// 오프라인 지원 및 캐싱 전략

const CACHE_VERSION = 'pharma-v2.0';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/service_worker.js'
];

// Service Worker 설치
self.addEventListener('install', event => {
  console.log('[SW] Installing Service Worker...');

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Service Worker 활성화
self.addEventListener('activate', event => {
  console.log('[SW] Activating Service Worker...');

  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE)
            .map(cacheName => {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// 네트워크 요청 처리
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // API 요청 (네트워크 우선)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // 성공 응답은 캐시에 저장
          if (response.status === 200) {
            const cache_response = response.clone();
            caches.open(DYNAMIC_CACHE).then(cache => {
              cache.put(request, cache_response);
            });
          }
          return response;
        })
        .catch(() => {
          // 네트워크 실패 시 캐시에서 조회
          return caches.match(request)
            .then(response => response || create_offline_response(request));
        })
    );
  }
  // 정적 자산 (캐시 우선)
  else {
    event.respondWith(
      caches.match(request)
        .then(response => response || fetch(request))
        .catch(() => create_offline_response(request))
    );
  }
});

// 오프라인 응답 생성
function create_offline_response(request) {
  if (request.destination === 'document') {
    return new Response(
      `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>오프라인</title>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
              display: flex;
              align-items: center;
              justify-content: center;
              height: 100vh;
              background: #f5f5f5;
              margin: 0;
            }
            .offline-message {
              text-align: center;
              padding: 40px;
              background: white;
              border-radius: 10px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #667eea; margin: 0 0 10px 0; }
            p { color: #666; margin: 10px 0; }
            .emoji { font-size: 60px; }
          </style>
        </head>
        <body>
          <div class="offline-message">
            <div class="emoji">📡</div>
            <h1>오프라인 상태</h1>
            <p>인터넷 연결을 확인하세요</p>
            <p style="font-size: 12px; color: #999;">캐시된 정보는 볼 수 있습니다</p>
          </div>
        </body>
      </html>
      `,
      {
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
      }
    );
  }

  return new Response('오프라인 상태입니다', {
    status: 503,
    statusText: 'Service Unavailable'
  });
}

// 백그라운드 동기화 (복약 알림)
self.addEventListener('sync', event => {
  if (event.tag === 'sync-medications') {
    event.waitUntil(
      fetch('/api/schedule/check')
        .then(response => {
          if (response.ok) {
            return response.json();
          }
        })
        .then(data => {
          // 푸시 알림 전송
          if (data && data.medications && data.medications.length > 0) {
            self.registration.showNotification('복약 알림', {
              body: `${data.medications[0]} 복용 시간입니다!`,
              icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect fill="%23667eea" width="192" height="192"/><text x="96" y="120" font-size="80" fill="white" text-anchor="middle" font-weight="bold">💊</text></svg>',
              badge: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect fill="%23667eea" width="192" height="192"/><text x="96" y="120" font-size="80" fill="white" text-anchor="middle" font-weight="bold">💊</text></svg>',
              tag: 'medication-reminder',
              requireInteraction: true
            });
          }
        })
        .catch(err => console.error('[SW] Sync failed:', err))
    );
  }
});

// 푸시 알림 처리
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};

  const notificationOptions = {
    body: data.body || '새로운 알림',
    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect fill="%23667eea" width="192" height="192"/><text x="96" y="120" font-size="80" fill="white" text-anchor="middle" font-weight="bold">💊</text></svg>',
    badge: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect fill="%23667eea" width="192" height="192"/><text x="96" y="120" font-size="80" fill="white" text-anchor="middle" font-weight="bold">💊</text></svg>',
    data: data.data || {},
    actions: [
      { action: 'open', title: '열기' },
      { action: 'close', title: '닫기' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'PHARMA-MOBILE', notificationOptions)
  );
});

// 알림 클릭 처리
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'open' || event.action === '') {
    event.waitUntil(
      clients.matchAll({ type: 'window' })
        .then(clientList => {
          // 이미 열려있는 창이 있으면 포커스
          for (let client of clientList) {
            if (client.url === '/' && 'focus' in client) {
              return client.focus();
            }
          }
          // 없으면 새 창 열기
          if (clients.openWindow) {
            return clients.openWindow('/');
          }
        })
    );
  }
});

console.log('[SW] Service Worker loaded');
