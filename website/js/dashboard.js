// MCWB Dashboard - Live monitoring with custom charts

let autoRefreshEnabled = true;
let refreshInterval = null;
let dashboardUrl = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadCustomApiUrlFromStorage();
    detectDashboardUrl();
    setupAutoRefresh();
});

// Load custom API URL from localStorage or URL parameter
function loadCustomApiUrlFromStorage() {
    // Check URL parameter first
    const urlParams = new URLSearchParams(window.location.search);
    const apiUrlParam = urlParams.get('apiUrl');
    if (apiUrlParam) {
        localStorage.setItem('customDashboardApiUrl', apiUrlParam);
        const input = document.getElementById('customApiUrl');
        if (input) input.value = apiUrlParam;
    }
    
    // Load from localStorage
    const savedUrl = localStorage.getItem('customDashboardApiUrl');
    if (savedUrl) {
        const input = document.getElementById('customApiUrl');
        if (input) input.value = savedUrl;
    }
}

// Set custom API URL
function setCustomApiUrl() {
    const input = document.getElementById('customApiUrl');
    if (!input) return;
    
    let url = input.value.trim();
    if (!url) {
        alert('Please enter a valid URL');
        return;
    }
    
    // Validate and normalize URL
    // Note: Default to http:// for local network access (Raspberry Pi typically doesn't have SSL)
    // Users can explicitly specify https:// if they have SSL configured
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'http://' + url;
    }
    
    // Remove trailing slash
    url = url.replace(/\/$/, '');
    
    // Save to localStorage
    localStorage.setItem('customDashboardApiUrl', url);
    input.value = url;
    
    // Try to connect
    dashboardUrl = null; // Reset to force re-detection
    detectDashboardUrl();
}

// Clear custom API URL
function clearCustomApiUrl() {
    localStorage.removeItem('customDashboardApiUrl');
    const input = document.getElementById('customApiUrl');
    if (input) input.value = '';
    
    // Reset to default detection
    dashboardUrl = null;
    detectDashboardUrl();
}

// Detect dashboard URL
async function detectDashboardUrl() {
    // Build list of URLs to try
    const urls = [];
    
    // 1. Try custom URL from localStorage first
    const customUrl = localStorage.getItem('customDashboardApiUrl');
    if (customUrl) {
        urls.push(customUrl);
    }
    
    // 2. Try common local URLs
    urls.push('http://localhost:5000');
    urls.push('http://127.0.0.1:5000');
    
    // 3. Try current hostname (useful when accessing via network)
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        urls.push(`${window.location.protocol}//${window.location.hostname}:5000`);
    }
    
    for (const url of urls) {
        try {
            const response = await fetch(`${url}/api/stats`, { 
                method: 'GET',
                mode: 'cors',
                signal: AbortSignal.timeout(2000) // 2 second timeout
            });
            if (response.ok) {
                dashboardUrl = url;
                console.log('Dashboard found at:', url);
                showLiveDataInfo(url);
                await updateDashboard();
                return;
            }
        } catch (error) {
            // Try next URL
            continue;
        }
    }
    
    // No dashboard found, show demo mode
    console.warn('Dashboard API not found. Showing demo mode.');
    showDemoMode();
}

// Show live data info banner
function showLiveDataInfo(url) {
    const demoWarning = document.getElementById('demoModeWarning');
    const liveInfo = document.getElementById('liveDataInfo');
    const connectedUrl = document.getElementById('connectedUrl');
    
    if (demoWarning) {
        demoWarning.style.display = 'none';
    }
    if (liveInfo) {
        liveInfo.style.display = 'block';
    }
    if (connectedUrl) {
        connectedUrl.textContent = url;
    }
}

// Update dashboard with real data from API
async function updateDashboard() {
    if (!dashboardUrl) {
        showDemoMode();
        return;
    }
    
    try {
        // Fetch stats data
        const [statsRes, hourlyRes, locationsRes] = await Promise.all([
            fetch(`${dashboardUrl}/api/stats`),
            fetch(`${dashboardUrl}/api/stats/hourly`),
            fetch(`${dashboardUrl}/api/stats/locations`)
        ]);
        
        if (!statsRes.ok || !hourlyRes.ok || !locationsRes.ok) {
            throw new Error('Failed to fetch dashboard data');
        }
        
        const stats = await statsRes.json();
        const hourly = await hourlyRes.json();
        const locations = await locationsRes.json();
        
        // Update status indicator
        const statusSpan = document.querySelector('#botStatus');
        if (statusSpan) {
            statusSpan.textContent = stats.total_requests > 0 ? 'Online' : 'Idle';
        }
        
        // Calculate today's requests from hourly data
        const today = new Date().toISOString().split('T')[0];
        const todayRequests = hourly
            .filter(item => item.hour.startsWith(today))
            .reduce((sum, item) => sum + item.count, 0);
        
        // Update stat displays
        document.getElementById('requestsToday').textContent = todayRequests;
        
        // Calculate active channels (estimate from top locations)
        const activeChannels = Math.min(locations.length, 6); // Reasonable estimate
        document.getElementById('activeChannels').textContent = activeChannels;
        
        // Calculate uptime based on last update
        if (stats.last_updated) {
            const lastUpdate = new Date(stats.last_updated);
            const now = new Date();
            const MILLISECONDS_PER_HOUR = 3600000;
            const diffHours = Math.abs(now - lastUpdate) / MILLISECONDS_PER_HOUR;
            document.getElementById('uptime').textContent = diffHours.toFixed(1);
        } else {
            document.getElementById('uptime').textContent = '--';
        }
        
        // Update last update time
        const now = new Date();
        document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
        
        // Update charts
        updateUsageChart(hourly);
        updateLocationsChart(locations);
        
        console.log('Dashboard updated at', now);
    } catch (error) {
        console.error('Error updating dashboard:', error);
        showDemoMode();
    }
}

// Show demo mode with fake data
function showDemoMode() {
    // Show demo warning, hide live info
    const demoWarning = document.getElementById('demoModeWarning');
    const liveInfo = document.getElementById('liveDataInfo');
    if (demoWarning) {
        demoWarning.style.display = 'block';
    }
    if (liveInfo) {
        liveInfo.style.display = 'none';
    }
    
    // Update stats with random demo data
    document.getElementById('requestsToday').textContent = Math.floor(Math.random() * 50) + 20;
    document.getElementById('activeChannels').textContent = Math.floor(Math.random() * 4) + 2;
    document.getElementById('uptime').textContent = (Math.random() * 48 + 12).toFixed(1);
    
    // Update last update time
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
    
    // Show demo charts
    initializeLineChart();
    
    console.log('Dashboard in demo mode at', now);
}

// Update usage chart with real hourly data
function updateUsageChart(hourlyData) {
    if (!hourlyData || hourlyData.length === 0) {
        initializeLineChart(); // Fallback to demo
        return;
    }
    
    // Take last 12 hours of data
    const last12Hours = hourlyData.slice(-12);
    const data = last12Hours.map(item => item.count);
    
    updateLineChart(data);
}

// Update locations bar chart with real data
function updateLocationsChart(locationsData) {
    const locationsChart = document.getElementById('locationsChart');
    if (!locationsChart) return;
    
    if (!locationsData || locationsData.length === 0) {
        return; // Keep demo bars
    }
    
    // Take top 6 locations
    const topLocations = locationsData.slice(0, 6);
    
    // Find max count for scaling
    const maxCount = Math.max(...topLocations.map(loc => loc.count));
    
    // Clear chart safely
    while (locationsChart.firstChild) {
        locationsChart.removeChild(locationsChart.firstChild);
    }
    
    topLocations.forEach(location => {
        const container = document.createElement('div');
        container.style.flex = '1';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.alignItems = 'center';
        
        const bar = document.createElement('div');
        bar.className = 'bar';
        const height = (location.count / maxCount) * 80; // Scale to 80% max
        bar.style.height = height + '%';
        
        const value = document.createElement('span');
        value.className = 'bar-value';
        value.textContent = location.count;
        bar.appendChild(value);
        
        const label = document.createElement('div');
        label.className = 'bar-label';
        label.textContent = location.location;
        
        container.appendChild(bar);
        container.appendChild(label);
        locationsChart.appendChild(container);
    });
}

// Initialize line chart with demo data
function initializeLineChart() {
    const svg = document.querySelector('#usageChart svg');
    if (!svg) return;
    
    // Generate demo data points
    const dataPoints = [];
    for (let i = 0; i < 12; i++) {
        dataPoints.push(Math.floor(Math.random() * 8) + 1);
    }
    
    updateLineChart(dataPoints);
}

// Update line chart
function updateLineChart(data) {
    const width = 600;
    const height = 200;
    const padding = 20;
    const maxValue = Math.max(...data, 10);
    
    // Calculate points for line
    const linePoints = data.map((value, index) => {
        const x = padding + (index * (width - 2 * padding) / (data.length - 1));
        const y = height - padding - ((value / maxValue) * (height - 2 * padding));
        return `${x},${y}`;
    }).join(' ');
    
    // Calculate points for area (add bottom points)
    const areaPoints = linePoints + ` ${width - padding},${height - padding} ${padding},${height - padding}`;
    
    // Update SVG
    const line = document.getElementById('usageLine');
    const area = document.getElementById('usageArea');
    
    if (line) line.setAttribute('points', linePoints);
    if (area) area.setAttribute('points', areaPoints);
}

// Setup auto-refresh
function setupAutoRefresh() {
    const toggle = document.getElementById('autoRefreshToggle');
    const statusText = document.getElementById('refreshStatus');
    
    if (toggle) {
        toggle.addEventListener('click', function() {
            autoRefreshEnabled = !autoRefreshEnabled;
            toggle.classList.toggle('active');
            
            if (autoRefreshEnabled) {
                statusText.textContent = 'Enabled (10s)';
                startAutoRefresh();
            } else {
                statusText.textContent = 'Disabled';
                stopAutoRefresh();
            }
        });
    }
    
    startAutoRefresh();
}

// Start auto-refresh
function startAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    refreshInterval = setInterval(function() {
        if (autoRefreshEnabled) {
            updateDashboard();
            updateCharts();
        }
    }, 10000); // 10 seconds
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Manual refresh
function refreshDashboard() {
    if (dashboardUrl) {
        updateDashboard();
    } else {
        detectDashboardUrl();
    }
    
    // Visual feedback
    const btn = document.querySelector('.refresh-btn');
    const originalText = btn.textContent;
    btn.textContent = '✓ Refreshed';
    setTimeout(() => {
        btn.textContent = originalText;
    }, 1000);
}

// Update charts with new data (called from auto-refresh in demo mode)
function updateCharts() {
    if (dashboardUrl) {
        updateDashboard(); // Fetch real data
    } else {
        // Generate new demo data
        const newData = [];
        for (let i = 0; i < 12; i++) {
            newData.push(Math.floor(Math.random() * 8) + 1);
        }
        updateLineChart(newData);
        
        // Update bar chart heights randomly for demo
        const bars = document.querySelectorAll('.bar');
        bars.forEach((bar, index) => {
            const newHeight = Math.floor(Math.random() * 30) + 20;
            const newValue = Math.floor(newHeight / 5);
            bar.style.height = newHeight + '%';
            const valueSpan = bar.querySelector('.bar-value');
            if (valueSpan) {
                valueSpan.textContent = newValue;
            }
        });
    }
}

// Simulate adding log entries (demo mode only)
// Convert @username mentions to clickable links for MeshCore app
function convertUserMentionsToLinks(text) {
    // Escape HTML first to prevent XSS
    const escapeHtml = (str) => {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    };
    
    const escaped = escapeHtml(text);
    
    // Convert @username patterns to meshcore:// links
    // Username can contain alphanumeric, underscore, hyphen, and dot
    return escaped.replace(/@([a-zA-Z0-9_.-]+)/g, '<a href="meshcore://user/$1" class="user-mention">@$1</a>');
}

function addLogEntry(timestamp, level, message) {
    const logContainer = document.getElementById('requestLog');
    if (!logContainer) return;
    
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    
    // Create child elements safely
    const timestampSpan = document.createElement('span');
    timestampSpan.className = 'log-timestamp';
    timestampSpan.textContent = `[${timestamp}]`;
    
    const levelSpan = document.createElement('span');
    levelSpan.className = `log-level-${level}`;
    levelSpan.textContent = level;
    
    const contentSpan = document.createElement('span');
    contentSpan.className = 'log-content';
    // Convert @mentions to clickable links while maintaining security
    contentSpan.innerHTML = convertUserMentionsToLinks(message);
    
    entry.appendChild(timestampSpan);
    entry.appendChild(document.createTextNode(' '));
    entry.appendChild(levelSpan);
    entry.appendChild(document.createTextNode(' '));
    entry.appendChild(contentSpan);
    
    // Add to top
    logContainer.insertBefore(entry, logContainer.firstChild);
    
    // Keep only last 20 entries
    while (logContainer.children.length > 20) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

// Demo: Simulate log updates every 30 seconds (only in demo mode)
setInterval(function() {
    if (!dashboardUrl) {  // Only in demo mode
        const now = new Date();
        const timestamp = now.toLocaleTimeString();
        const cities = ['London', 'Manchester', 'York', 'Leeds', 'Birmingham', 'Edinburgh', 'Glasgow', 'Bristol'];
        const city = cities[Math.floor(Math.random() * cities.length)];
        const users = ['User1', 'User2', 'User3', 'User4', 'User5'];
        const user = users[Math.floor(Math.random() * users.length)];
        
        addLogEntry(timestamp, 'INFO', `${user} requested weather for ${city}, GB`);
    }
}, 30000);

