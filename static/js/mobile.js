// 移动端优化脚本

document.addEventListener('DOMContentLoaded', function() {
    // 移动端导航功能现在完全由base.html中的脚本处理
    // 这里只保留其他移动端优化功能
    
    // 移动端表单优化
    const formInputs = document.querySelectorAll('input, select, textarea');
    formInputs.forEach(input => {
        // 防止iOS缩放
        if (input.type === 'text' || input.type === 'number' || input.type === 'email' || 
            input.type === 'password' || input.type === 'date' || input.type === 'tel') {
            input.style.fontSize = '16px';
        }
        
        // 添加触摸反馈
        input.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.98)';
        });
        
        input.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // 移动端按钮优化
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        // 添加触摸反馈
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.95)';
        });
        
        button.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // 移动端表格优化
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        // 添加横向滚动提示
        if (table.scrollWidth > table.clientWidth) {
            const scrollHint = document.createElement('div');
            scrollHint.className = 'text-muted small text-center mt-2';
            scrollHint.innerHTML = '<i class="fas fa-arrows-alt-h me-1"></i>左右滑动查看更多';
            table.parentNode.appendChild(scrollHint);
        }
    });
    
    // 移动端分页优化
    const pagination = document.querySelector('.pagination');
    if (pagination && window.innerWidth < 768) {
        // 简化分页显示
        const pageItems = pagination.querySelectorAll('.page-item');
        pageItems.forEach((item, index) => {
            if (index > 2 && index < pageItems.length - 3) {
                item.style.display = 'none';
            }
        });
    }
    
    // 移动端搜索优化
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="搜索"]');
    searchInputs.forEach(input => {
        input.addEventListener('focus', function() {
            // 延迟滚动到输入框
            setTimeout(() => {
                this.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
        });
    });
    
    // 移动端长按优化
    let longPressTimer;
    const longPressElements = document.querySelectorAll('.btn, .nav-link');
    
    longPressElements.forEach(element => {
        element.addEventListener('touchstart', function(e) {
            longPressTimer = setTimeout(() => {
                // 长按反馈
                this.style.backgroundColor = '#e9ecef';
                this.style.transform = 'scale(0.9)';
            }, 500);
        });
        
        element.addEventListener('touchend', function(e) {
            clearTimeout(longPressTimer);
            this.style.backgroundColor = '';
            this.style.transform = '';
        });
        
        element.addEventListener('touchmove', function(e) {
            clearTimeout(longPressTimer);
        });
    });
    
    // 移动端性能优化
    let scrollTimer;
    window.addEventListener('scroll', function() {
        if (scrollTimer) {
            clearTimeout(scrollTimer);
        }
        scrollTimer = setTimeout(() => {
            // 滚动停止后的处理
            document.body.classList.add('scrolled');
        }, 150);
    });
    
    // 移动端键盘优化
    window.addEventListener('resize', function() {
        if (window.innerHeight < window.outerHeight) {
            // 键盘弹出时的处理
            document.body.classList.add('keyboard-open');
        } else {
            document.body.classList.remove('keyboard-open');
        }
    });
    
    // 移动端手势优化
    let startX, startY;
    document.addEventListener('touchstart', function(e) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    });
    
    document.addEventListener('touchend', function(e) {
        if (!startX || !startY) return;
        
        const endX = e.changedTouches[0].clientX;
        const endY = e.changedTouches[0].clientY;
        
        const diffX = startX - endX;
        const diffY = startY - endY;
        
        // 检测滑动手势
        if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
            if (diffX > 0) {
                // 向左滑动
                console.log('向左滑动');
            } else {
                // 向右滑动
                console.log('向右滑动');
            }
        }
        
        startX = startY = null;
    });
    
    // 移动端网络状态检测
    if ('connection' in navigator) {
        navigator.connection.addEventListener('change', function() {
            const connection = navigator.connection;
            if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
                // 慢速网络优化
                document.body.classList.add('slow-connection');
            } else {
                document.body.classList.remove('slow-connection');
            }
        });
    }
    
    // 移动端电池状态检测
    if ('getBattery' in navigator) {
        navigator.getBattery().then(function(battery) {
            battery.addEventListener('levelchange', function() {
                if (battery.level < 0.2) {
                    // 低电量优化
                    document.body.classList.add('low-battery');
                } else {
                    document.body.classList.remove('low-battery');
                }
            });
        });
    }
});

// 移动端工具函数
const MobileUtils = {
    // 检测是否为移动设备
    isMobile: function() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    // 检测是否为触摸设备
    isTouchDevice: function() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    },
    
    // 检测屏幕方向
    getOrientation: function() {
        return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
    },
    
    // 滚动到元素中心
    scrollToCenter: function(element) {
        if (element) {
            const rect = element.getBoundingClientRect();
            const windowHeight = window.innerHeight;
            const scrollTo = window.pageYOffset + rect.top - (windowHeight / 2) + (rect.height / 2);
            
            window.scrollTo({
                top: scrollTo,
                behavior: 'smooth'
            });
        }
    },
    
    // 显示移动端提示
    showMobileHint: function(message, duration = 3000) {
        const hint = document.createElement('div');
        hint.className = 'mobile-hint';
        hint.textContent = message;
        hint.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            z-index: 9999;
            font-size: 14px;
        `;
        
        document.body.appendChild(hint);
        
        setTimeout(() => {
            hint.remove();
        }, duration);
    }
};

// 导出工具函数
window.MobileUtils = MobileUtils;