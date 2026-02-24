// MCWB Dashboard - Live monitoring with custom charts

let autoRefreshEnabled = true;
let refreshInterval = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    updateDashboard();
    setupAutoRefresh();
    initializeLineChart();
});

// Update dashboard with demo data
function updateDashboard() {
    // Update stats with random demo data
    document.getElementById('requestsToday').textContent = Math.floor(Math.random() * 50) + 20;
    document.getElementById('activeChannels').textContent = Math.floor(Math.random() * 4) + 2;
    document.getElementById('uptime').textContent = (Math.random() * 48 + 12).toFixed(1);
    
    // Update last update time
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
    
    console.log('Dashboard updated at', now);
}

// Initialize line chart
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
    updateDashboard();
    updateCharts();
    
    // Visual feedback
    const btn = document.querySelector('.refresh-btn');
    const originalText = btn.textContent;
    btn.textContent = '✓ Refreshed';
    setTimeout(() => {
        btn.textContent = originalText;
    }, 1000);
}

// Update charts with new data
function updateCharts() {
    // Generate new data
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

// Simulate adding log entries (in real implementation, fetch from API)
function addLogEntry(timestamp, level, message) {
    const logContainer = document.getElementById('requestLog');
    if (!logContainer) return;
    
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `
        <span class="log-timestamp">[${timestamp}]</span>
        <span class="log-level-${level}">${level}</span>
        <span class="log-content">${message}</span>
    `;
    
    // Add to top
    logContainer.insertBefore(entry, logContainer.firstChild);
    
    // Keep only last 20 entries
    while (logContainer.children.length > 20) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

// Demo: Simulate log updates every 30 seconds
setInterval(function() {
    const now = new Date();
    const timestamp = now.toLocaleTimeString();
    const cities = ['London', 'Manchester', 'York', 'Leeds', 'Birmingham', 'Edinburgh', 'Glasgow', 'Bristol'];
    const city = cities[Math.floor(Math.random() * cities.length)];
    const users = ['User1', 'User2', 'User3', 'User4', 'User5'];
    const user = users[Math.floor(Math.random() * users.length)];
    
    addLogEntry(timestamp, 'INFO', `${user} requested weather for ${city}, GB`);
}, 30000);

