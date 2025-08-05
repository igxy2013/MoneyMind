// PWA 功能脚本

document.addEventListener('DOMContentLoaded', function() {
    let deferredPrompt;
    const pwaInstallPrompt = document.getElementById('pwaInstallPrompt');
    const pwaInstallBtn = document.getElementById('pwaInstallBtn');
    const pwaCloseBtn = document.getElementById('pwaCloseBtn');
    
    // 监听 beforeinstallprompt 事件
    window.addEventListener('beforeinstallprompt', function(e) {
        e.preventDefault();
        deferredPrompt = e;
        
        // 显示安装提示
        if (pwaInstallPrompt) {
            setTimeout(() => {
                pwaInstallPrompt.classList.add('show');
            }, 3000);
        }
    });
    
    // 安装按钮点击事件
    if (pwaInstallBtn) {
        pwaInstallBtn.addEventListener('click', function() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then(function(choiceResult) {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('用户接受了PWA安装');
                        showNotification('七彩果坊已成功安装到主屏幕！', 'success');
                    } else {
                        console.log('用户拒绝了PWA安装');
                        showNotification('您可以稍后在浏览器菜单中安装应用', 'info');
                    }
                    deferredPrompt = null;
                    pwaInstallPrompt.classList.remove('show');
                });
            }
        });
    }
    
    // 关闭按钮点击事件
    if (pwaCloseBtn) {
        pwaCloseBtn.addEventListener('click', function() {
            pwaInstallPrompt.classList.remove('show');
        });
    }
    
    // 监听 appinstalled 事件
    window.addEventListener('appinstalled', function() {
        console.log('PWA已安装');
        if (pwaInstallPrompt) {
            pwaInstallPrompt.classList.remove('show');
        }
        showNotification('七彩果坊已成功安装！', 'success');
    });
    
    // 显示通知
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 300px;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // 自动移除通知
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    // 检查是否已安装PWA
    function checkIfInstalled() {
        if (window.matchMedia('(display-mode: standalone)').matches) {
            console.log('应用已在独立窗口中运行');
            // 隐藏安装提示
            if (pwaInstallPrompt) {
                pwaInstallPrompt.style.display = 'none';
            }
        }
    }
    
    // 页面加载时检查
    checkIfInstalled();
    
    // 监听显示模式变化
    window.matchMedia('(display-mode: standalone)').addEventListener('change', function(e) {
        if (e.matches) {
            console.log('应用切换到独立窗口模式');
            checkIfInstalled();
        }
    });
});

// Service Worker 注册
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js')
            .then(function(registration) {
                console.log('Service Worker 注册成功:', registration.scope);
            })
            .catch(function(error) {
                console.log('Service Worker 注册失败:', error);
            });
    });
}

// PWA 工具函数
const PWAUtils = {
    // 检查是否为PWA模式
    isPWA: function() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    },
    
    // 检查是否支持PWA
    isPWASupported: function() {
        return 'serviceWorker' in navigator && 'PushManager' in window;
    },
    
    // 请求通知权限
    requestNotificationPermission: function() {
        if ('Notification' in window) {
            return Notification.requestPermission();
        }
        return Promise.resolve('denied');
    },
    
    // 显示通知
    showNotification: function(title, options = {}) {
        if ('Notification' in window && Notification.permission === 'granted') {
            return new Notification(title, {
                icon: '/static/logo.png',
                badge: '/static/logo.png',
                ...options
            });
        }
    },
    
    // 检查网络状态
    isOnline: function() {
        return navigator.onLine;
    },
    
    // 监听网络状态变化
    onNetworkChange: function(callback) {
        window.addEventListener('online', () => callback(true));
        window.addEventListener('offline', () => callback(false));
    }
};

// 导出工具函数
window.PWAUtils = PWAUtils; 