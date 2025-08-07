// Camera Monitoring System - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips and popovers
    initializeTooltips();
    
    // Initialize sidebar toggle for mobile
    initializeSidebarToggle();
    
    // Initialize auto-refresh functionality
    initializeAutoRefresh();
    
    // Initialize notification system
    initializeNotifications();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize sidebar toggle for mobile devices
 */
function initializeSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }
}

/**
 * Initialize auto-refresh functionality
 */
function initializeAutoRefresh() {
    // Auto-refresh camera feeds every 30 seconds
    if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
        setInterval(refreshCameraFeeds, 30000);
    }
    
    // Auto-refresh camera status on camera management page
    if (window.location.pathname === '/cameras') {
        setInterval(refreshCameraStatus, 15000);
    }
}

/**
 * Refresh camera feeds
 */
function refreshCameraFeeds() {
    const cameraFeeds = document.querySelectorAll('.camera-feed');
    
    cameraFeeds.forEach(feed => {
        // Add a subtle animation to indicate refresh
        feed.classList.add('pulse');
        setTimeout(() => {
            feed.classList.remove('pulse');
        }, 1000);
    });
}

/**
 * Refresh camera status via API
 */
function refreshCameraStatus() {
    fetch('/api/camera-status')
        .then(response => response.json())
        .then(data => {
            updateCameraStatus(data);
        })
        .catch(error => {
            console.error('Error fetching camera status:', error);
        });
}

/**
 * Update camera status in the UI
 */
function updateCameraStatus(cameras) {
    cameras.forEach(camera => {
        const cameraElements = document.querySelectorAll(`[data-camera-id="${camera.id}"]`);
        
        cameraElements.forEach(element => {
            const statusBadge = element.querySelector('.status-badge');
            if (statusBadge) {
                // Update status badge
                statusBadge.className = `status-badge status-${camera.status}`;
                statusBadge.innerHTML = `<i class="fas fa-circle"></i> ${camera.status.charAt(0).toUpperCase() + camera.status.slice(1)}`;
            }
            
            // Update feed content based on status
            const feedContent = element.querySelector('.feed-content');
            if (feedContent) {
                updateFeedContent(feedContent, camera);
            }
            
            // Update last seen time
            const lastSeenElement = element.querySelector('.last-seen');
            if (lastSeenElement && camera.last_seen) {
                lastSeenElement.textContent = `Last seen: ${formatRelativeTime(camera.last_seen)}`;
            }
        });
    });
}

/**
 * Update feed content based on camera status
 */
function updateFeedContent(feedContent, camera) {
    if (camera.status === 'online') {
        feedContent.innerHTML = `
            <div class="mock-feed">
                <i class="fas fa-video feed-icon"></i>
                <div class="feed-overlay">
                    <div class="timestamp">${new Date().toLocaleTimeString()}</div>
                </div>
            </div>
        `;
    } else {
        feedContent.innerHTML = `
            <div class="feed-offline">
                <i class="fas fa-video-slash"></i>
                <p>Camera ${camera.status.charAt(0).toUpperCase() + camera.status.slice(1)}</p>
            </div>
        `;
    }
}

/**
 * Initialize notification system
 */
function initializeNotifications() {
    // Check for browser notification support
    if ('Notification' in window) {
        // Request permission if not already granted
        if (Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
}

/**
 * Show desktop notification
 */
function showNotification(title, message, type = 'info') {
    // Show in-app notification
    showInAppNotification(message, type);
    
    // Show desktop notification if permission granted
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: message,
            icon: '/static/images/camera-icon.png',
            tag: 'camera-monitoring'
        });
        
        notification.onclick = function() {
            window.focus();
            notification.close();
        };
        
        // Auto-close after 5 seconds
        setTimeout(() => notification.close(), 5000);
    }
}

/**
 * Show in-app notification
 */
function showInAppNotification(message, type = 'info') {
    const alertClass = type === 'error' ? 'danger' : type;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${alertClass} alert-dismissible fade show notification-toast`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Style the notification toast
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1060;
        min-width: 300px;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

/**
 * Initialize real-time updates
 */
function initializeRealTimeUpdates() {
    // Update live timestamps every second
    setInterval(updateLiveTimestamps, 1000);
    
    // Simulate random camera status changes for demo
    if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
        setInterval(simulateStatusChanges, 60000); // Every minute
    }
}

/**
 * Update live timestamps
 */
function updateLiveTimestamps() {
    const timestampElements = document.querySelectorAll('.timestamp, .timestamp-large, #liveTimestamp');
    const now = new Date();
    
    timestampElements.forEach(element => {
        element.textContent = now.toLocaleTimeString();
    });
}

/**
 * Simulate camera status changes for demo purposes
 */
function simulateStatusChanges() {
    // Only simulate if we have camera feeds
    const cameraFeeds = document.querySelectorAll('.camera-feed');
    
    if (cameraFeeds.length > 0 && Math.random() < 0.2) { // 20% chance
        const randomFeed = cameraFeeds[Math.floor(Math.random() * cameraFeeds.length)];
        const statusBadge = randomFeed.querySelector('.status-badge');
        
        if (statusBadge) {
            const currentStatus = statusBadge.className.includes('status-online') ? 'online' : 
                                statusBadge.className.includes('status-offline') ? 'offline' : 'error';
            
            const possibleStatuses = ['online', 'offline', 'error'];
            const newStatus = possibleStatuses[Math.floor(Math.random() * possibleStatuses.length)];
            
            if (newStatus !== currentStatus) {
                // Update status badge
                statusBadge.className = `status-badge status-${newStatus}`;
                statusBadge.innerHTML = `<i class="fas fa-circle"></i> ${newStatus.charAt(0).toUpperCase() + newStatus.slice(1)}`;
                
                // Update feed content
                const feedContent = randomFeed.querySelector('.feed-content');
                if (feedContent) {
                    updateFeedContent(feedContent, { status: newStatus });
                }
                
                // Show notification for status change
                const cameraName = randomFeed.querySelector('.camera-name')?.textContent || 'Camera';
                showNotification(
                    'Camera Status Change',
                    `${cameraName} is now ${newStatus}`,
                    newStatus === 'error' ? 'error' : newStatus === 'offline' ? 'warning' : 'success'
                );
            }
        }
    }
}

/**
 * Format relative time (e.g., "2 minutes ago")
 */
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return 'Just now';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days} day${days !== 1 ? 's' : ''} ago`;
    }
}

/**
 * Utility function to show loading state
 */
function showLoadingState(element, message = 'Loading...') {
    const originalContent = element.innerHTML;
    element.innerHTML = `
        <div class="d-flex justify-content-center align-items-center p-3">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            ${message}
        </div>
    `;
    
    return originalContent;
}

/**
 * Utility function to hide loading state
 */
function hideLoadingState(element, originalContent) {
    element.innerHTML = originalContent;
}

/**
 * Confirm deletion with modal
 */
function confirmDelete(itemName, deleteUrl, itemType = 'item') {
    const modalHtml = `
        <div class="modal fade" id="confirmDeleteModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title text-danger">
                            <i class="fas fa-exclamation-triangle"></i> Confirm Deletion
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to delete ${itemType} "<strong>${itemName}</strong>"?</p>
                        <p class="text-muted">This action cannot be undone.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <form method="POST" action="${deleteUrl}" class="d-inline">
                            <button type="submit" class="btn btn-danger">
                                <i class="fas fa-trash"></i> Delete ${itemType}
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('confirmDeleteModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add new modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
    modal.show();
    
    // Remove modal from DOM when hidden
    document.getElementById('confirmDeleteModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

/**
 * Handle form validation
 */
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showInAppNotification('Copied to clipboard!', 'success');
    }, function() {
        showInAppNotification('Failed to copy to clipboard', 'error');
    });
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Debounce function for search inputs
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    showInAppNotification('An error occurred. Please refresh the page if problems persist.', 'error');
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showInAppNotification('An error occurred while processing your request.', 'error');
});

// Export functions for use in other scripts
window.CameraMonitoring = {
    showNotification,
    showInAppNotification,
    confirmDelete,
    validateForm,
    copyToClipboard,
    formatFileSize,
    debounce,
    formatRelativeTime,
    showLoadingState,
    hideLoadingState
};
