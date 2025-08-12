// 离线图片上传功能

class OfflineImageUploader {
    constructor() {
        this.dbName = 'MoneyMindOfflineDB';
        this.dbVersion = 1;
        this.storeName = 'pendingUploads';
        this.db = null;
        this.maxRetries = 3;
        this.retryDelay = 5000; // 5秒
        
        this.init();
    }
    
    // 初始化IndexedDB
    async init() {
        try {
            this.db = await this.openDB();
            this.setupNetworkListeners();
            this.processPendingUploads();
        } catch (error) {
            console.error('初始化离线上传器失败:', error);
        }
    }
    
    // 打开IndexedDB数据库
    openDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // 创建存储待上传文件的对象存储
                if (!db.objectStoreNames.contains(this.storeName)) {
                    const store = db.createObjectStore(this.storeName, {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    
                    // 创建索引
                    store.createIndex('supplierId', 'supplierId', { unique: false });
                    store.createIndex('timestamp', 'timestamp', { unique: false });
                    store.createIndex('status', 'status', { unique: false });
                }
            };
        });
    }
    
    // 设置网络状态监听器
    setupNetworkListeners() {
        window.addEventListener('online', () => {
            console.log('网络已连接，开始处理待上传文件');
            this.processPendingUploads();
        });
        
        window.addEventListener('offline', () => {
            console.log('网络已断开，文件将保存到本地');
        });
    }
    
    // 检查网络状态
    isOnline() {
        return navigator.onLine;
    }
    
    // 获取网络连接质量
    getConnectionQuality() {
        if ('connection' in navigator) {
            const connection = navigator.connection;
            const effectiveType = connection.effectiveType;
            
            // 根据连接类型判断网络质量
            switch (effectiveType) {
                case 'slow-2g':
                case '2g':
                    return 'poor';
                case '3g':
                    return 'good';
                case '4g':
                    return 'excellent';
                default:
                    return 'unknown';
            }
        }
        return 'unknown';
    }
    
    // 上传图片（主要方法）
    async uploadImages(files, supplierId, options = {}) {
        const results = [];
        
        for (const file of files) {
            try {
                const result = await this.uploadSingleImage(file, supplierId, options);
                results.push(result);
            } catch (error) {
                console.error('上传图片失败:', error);
                results.push({ success: false, error: error.message, file: file.name });
            }
        }
        
        return results;
    }
    
    // 上传单个图片
    async uploadSingleImage(file, supplierId, options = {}) {
        // 检查文件大小和类型
        if (!this.validateFile(file)) {
            throw new Error('文件格式不支持或文件过大');
        }
        
        // 如果网络状况良好，直接上传
        if (this.isOnline() && this.getConnectionQuality() !== 'poor') {
            try {
                return await this.directUpload(file, supplierId, options);
            } catch (error) {
                console.warn('直接上传失败，保存到本地:', error);
                // 直接上传失败，保存到本地
                return await this.saveToLocal(file, supplierId, options);
            }
        } else {
            // 网络状况不佳或离线，保存到本地
            return await this.saveToLocal(file, supplierId, options);
        }
    }
    
    // 验证文件
    validateFile(file) {
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        const maxSize = 16 * 1024 * 1024; // 16MB
        
        return allowedTypes.includes(file.type) && file.size <= maxSize;
    }
    
    // 直接上传到服务器
    async directUpload(file, supplierId, options = {}) {
        const formData = new FormData();
        formData.append('images', file);
        
        const url = supplierId ? 
            `/api/supplier/${supplierId}/images` : 
            '/api/supplier/images';
        
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`上传失败: ${response.statusText}`);
        }
        
        const result = await response.json();
        return {
            success: true,
            uploaded: true,
            data: result,
            file: file.name
        };
    }
    
    // 保存到本地存储
    async saveToLocal(file, supplierId, options = {}) {
        try {
            // 将文件转换为ArrayBuffer
            const arrayBuffer = await file.arrayBuffer();
            
            const uploadData = {
                supplierId: supplierId,
                fileName: file.name,
                fileType: file.type,
                fileSize: file.size,
                fileData: arrayBuffer,
                timestamp: Date.now(),
                status: 'pending',
                retryCount: 0,
                options: options
            };
            
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const request = store.add(uploadData);
            
            return new Promise((resolve, reject) => {
                request.onsuccess = () => {
                    console.log('文件已保存到本地存储:', file.name);
                    resolve({
                        success: true,
                        uploaded: false,
                        saved: true,
                        id: request.result,
                        file: file.name,
                        message: '文件已保存到本地，将在网络恢复后自动上传'
                    });
                };
                
                request.onerror = () => {
                    reject(new Error('保存到本地存储失败'));
                };
            });
        } catch (error) {
            throw new Error(`保存到本地失败: ${error.message}`);
        }
    }
    
    // 处理待上传的文件
    async processPendingUploads() {
        if (!this.isOnline()) {
            console.log('网络未连接，跳过处理待上传文件');
            return;
        }
        
        try {
            const pendingFiles = await this.getPendingUploads();
            console.log(`发现 ${pendingFiles.length} 个待上传文件`);
            
            for (const fileData of pendingFiles) {
                await this.retryUpload(fileData);
            }
        } catch (error) {
            console.error('处理待上传文件时出错:', error);
        }
    }
    
    // 获取待上传的文件
    async getPendingUploads() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readonly');
            const store = transaction.objectStore(this.storeName);
            const index = store.index('status');
            const request = index.getAll('pending');
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
    
    // 重试上传
    async retryUpload(fileData) {
        try {
            // 重新创建File对象
            const file = new File([fileData.fileData], fileData.fileName, {
                type: fileData.fileType
            });
            
            // 尝试上传
            const result = await this.directUpload(file, fileData.supplierId, fileData.options);
            
            // 上传成功，从本地存储中删除
            await this.removeFromLocal(fileData.id);
            
            console.log('文件上传成功:', fileData.fileName);
            
            // 触发上传成功事件
            this.dispatchUploadEvent('success', {
                fileName: fileData.fileName,
                supplierId: fileData.supplierId,
                result: result
            });
            
        } catch (error) {
            console.error('重试上传失败:', fileData.fileName, error);
            
            // 增加重试次数
            fileData.retryCount = (fileData.retryCount || 0) + 1;
            
            if (fileData.retryCount >= this.maxRetries) {
                // 达到最大重试次数，标记为失败
                await this.updateUploadStatus(fileData.id, 'failed');
                
                this.dispatchUploadEvent('failed', {
                    fileName: fileData.fileName,
                    supplierId: fileData.supplierId,
                    error: error.message
                });
            } else {
                // 更新重试次数
                await this.updateRetryCount(fileData.id, fileData.retryCount);
                
                // 延迟后重试
                setTimeout(() => {
                    this.retryUpload(fileData);
                }, this.retryDelay);
            }
        }
    }
    
    // 从本地存储中删除文件
    async removeFromLocal(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const request = store.delete(id);
            
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }
    
    // 更新上传状态
    async updateUploadStatus(id, status) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const getRequest = store.get(id);
            
            getRequest.onsuccess = () => {
                const data = getRequest.result;
                if (data) {
                    data.status = status;
                    const putRequest = store.put(data);
                    putRequest.onsuccess = () => resolve();
                    putRequest.onerror = () => reject(putRequest.error);
                } else {
                    reject(new Error('记录不存在'));
                }
            };
            
            getRequest.onerror = () => reject(getRequest.error);
        });
    }
    
    // 更新重试次数
    async updateRetryCount(id, retryCount) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const getRequest = store.get(id);
            
            getRequest.onsuccess = () => {
                const data = getRequest.result;
                if (data) {
                    data.retryCount = retryCount;
                    const putRequest = store.put(data);
                    putRequest.onsuccess = () => resolve();
                    putRequest.onerror = () => reject(putRequest.error);
                } else {
                    reject(new Error('记录不存在'));
                }
            };
            
            getRequest.onerror = () => reject(getRequest.error);
        });
    }
    
    // 触发自定义事件
    dispatchUploadEvent(type, detail) {
        const event = new CustomEvent(`offlineUpload${type.charAt(0).toUpperCase() + type.slice(1)}`, {
            detail: detail
        });
        window.dispatchEvent(event);
    }
    
    // 获取待上传文件统计
    async getUploadStats() {
        try {
            const transaction = this.db.transaction([this.storeName], 'readonly');
            const store = transaction.objectStore(this.storeName);
            const request = store.getAll();
            
            return new Promise((resolve, reject) => {
                request.onsuccess = () => {
                    const files = request.result;
                    const stats = {
                        total: files.length,
                        pending: files.filter(f => f.status === 'pending').length,
                        failed: files.filter(f => f.status === 'failed').length,
                        totalSize: files.reduce((sum, f) => sum + f.fileSize, 0)
                    };
                    resolve(stats);
                };
                
                request.onerror = () => reject(request.error);
            });
        } catch (error) {
            console.error('获取上传统计失败:', error);
            return { total: 0, pending: 0, failed: 0, totalSize: 0 };
        }
    }
    
    // 清理失败的上传记录
    async clearFailedUploads() {
        try {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const index = store.index('status');
            const request = index.getAll('failed');
            
            request.onsuccess = () => {
                const failedFiles = request.result;
                const deletePromises = failedFiles.map(file => {
                    return new Promise((resolve, reject) => {
                        const deleteRequest = store.delete(file.id);
                        deleteRequest.onsuccess = () => resolve();
                        deleteRequest.onerror = () => reject(deleteRequest.error);
                    });
                });
                
                Promise.all(deletePromises).then(() => {
                    console.log(`已清理 ${failedFiles.length} 个失败的上传记录`);
                });
            };
        } catch (error) {
            console.error('清理失败上传记录时出错:', error);
        }
    }
}

// 创建全局实例
window.offlineUploader = new OfflineImageUploader();

// 导出类
window.OfflineImageUploader = OfflineImageUploader;

// 为现有的上传功能提供增强
function enhanceExistingUpload() {
    // 监听文件选择事件
    document.addEventListener('change', function(event) {
        if (event.target.type === 'file' && event.target.accept && event.target.accept.includes('image')) {
            const files = Array.from(event.target.files);
            if (files.length > 0) {
                // 显示网络状态提示
                showNetworkStatus();
            }
        }
    });
    
    // 监听上传事件
    window.addEventListener('offlineUploadSuccess', function(event) {
        const { fileName, supplierId } = event.detail;
        console.log(`文件 ${fileName} 已成功上传到供应商 ${supplierId}`);
        
        // 可以在这里刷新页面或更新UI
        if (typeof loadExistingImages === 'function') {
            loadExistingImages(supplierId);
        }
    });
    
    window.addEventListener('offlineUploadFailed', function(event) {
        const { fileName, error } = event.detail;
        console.error(`文件 ${fileName} 上传失败:`, error);
        
        // 显示错误提示
        if (typeof showNotification === 'function') {
            showNotification(`文件 ${fileName} 上传失败: ${error}`, 'error');
        }
    });
}

// 显示网络状态
function showNetworkStatus() {
    const isOnline = navigator.onLine;
    const connectionQuality = window.offlineUploader.getConnectionQuality();
    
    let message = '';
    let type = 'info';
    
    if (!isOnline) {
        message = '当前离线，图片将保存到本地，网络恢复后自动上传';
        type = 'warning';
    } else if (connectionQuality === 'poor') {
        message = '网络连接较慢，图片将保存到本地，稍后自动上传';
        type = 'warning';
    } else {
        message = '网络连接良好，图片将直接上传';
        type = 'success';
    }
    
    // 显示临时提示
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
    
    // 3秒后自动移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

// 页面加载完成后增强现有功能
document.addEventListener('DOMContentLoaded', enhanceExistingUpload);

// 添加上传状态指示器
function createUploadStatusIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'uploadStatusIndicator';
    indicator.className = 'position-fixed';
    indicator.style.cssText = `
        bottom: 20px;
        right: 20px;
        z-index: 9998;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 10px 15px;
        border-radius: 25px;
        font-size: 14px;
        display: none;
        align-items: center;
        gap: 10px;
    `;
    
    document.body.appendChild(indicator);
    
    // 定期更新状态
    setInterval(async () => {
        if (window.offlineUploader && window.offlineUploader.db) {
            const stats = await window.offlineUploader.getUploadStats();
            
            if (stats.pending > 0) {
                indicator.innerHTML = `
                    <i class="fas fa-cloud-upload-alt"></i>
                    待上传: ${stats.pending} 个文件
                `;
                indicator.style.display = 'flex';
            } else {
                indicator.style.display = 'none';
            }
        }
    }, 5000); // 每5秒检查一次
}

// 创建状态指示器
document.addEventListener('DOMContentLoaded', createUploadStatusIndicator);