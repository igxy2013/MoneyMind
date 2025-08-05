// Service Worker for MoneyMind PWA

const CACHE_NAME = 'moneymind-v1.0.0';
const urlsToCache = [
    '/',
    '/static/css/bootstrap.min.css',
    '/static/css/all.min.css',
    '/static/css/mobile.css',
    '/static/js/bootstrap.bundle.min.js',
    '/static/js/mobile.js',
    '/static/js/pwa.js',
    '/static/js/plotly-latest.min.js',
    '/static/logo.png',
    '/static/favicon.ico',
    '/static/site.webmanifest'
];

// 安装事件
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('缓存已打开');
                return cache.addAll(urlsToCache);
            })
            .then(function() {
                console.log('所有资源已缓存');
                return self.skipWaiting();
            })
    );
});

// 激活事件
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        console.log('删除旧缓存:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(function() {
            console.log('Service Worker 已激活');
            return self.clients.claim();
        })
    );
});

// 获取事件
self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // 如果找到缓存的响应，则返回缓存
                if (response) {
                    return response;
                }
                
                // 否则尝试从网络获取
                return fetch(event.request).then(function(response) {
                    // 检查是否收到有效响应
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }
                    
                    // 克隆响应
                    const responseToCache = response.clone();
                    
                    // 缓存新的响应
                    caches.open(CACHE_NAME)
                        .then(function(cache) {
                            cache.put(event.request, responseToCache);
                        });
                    
                    return response;
                });
            })
            .catch(function() {
                // 如果网络请求失败，尝试返回缓存的离线页面
                if (event.request.mode === 'navigate') {
                    return caches.match('/');
                }
            })
    );
});

// 推送事件
self.addEventListener('push', function(event) {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: '/static/logo.png',
            badge: '/static/logo.png',
            vibrate: [100, 50, 100],
            data: {
                dateOfArrival: Date.now(),
                primaryKey: 1
            },
            actions: [
                {
                    action: 'explore',
                    title: '查看详情',
                    icon: '/static/logo.png'
                },
                {
                    action: 'close',
                    title: '关闭',
                    icon: '/static/logo.png'
                }
            ]
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// 通知点击事件
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    } else if (event.action === 'close') {
        // 关闭通知，不做任何操作
    } else {
        // 默认点击行为
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// 后台同步事件
self.addEventListener('sync', function(event) {
    if (event.tag === 'background-sync') {
        event.waitUntil(
            // 执行后台同步任务
            syncData()
        );
    }
});

// 后台同步函数
function syncData() {
    // 这里可以实现数据同步逻辑
    console.log('执行后台数据同步');
    return Promise.resolve();
}

// 消息事件
self.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
});

// 错误处理
self.addEventListener('error', function(event) {
    console.error('Service Worker 错误:', event.error);
});

// 未处理的Promise拒绝
self.addEventListener('unhandledrejection', function(event) {
    console.error('Service Worker 未处理的Promise拒绝:', event.reason);
}); 