// MCWB Dashboard - Live monitoring with custom charts

let autoRefreshEnabled = true;
let refreshInterval = null;
let apiEndpoint = null; // Will be set from localStorage or config
let usingRealData = false;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadApiEndpoint();
    updateDashboard();
    setupAutoRefresh();
    initializeLineChart();
    setupApiConfig();
});

// Update dashboard with demo data
function updateDashboard() {
    if (apiEndpoint && usingRealData) {
        updateDashboardFromAPI();
    } else {
        updateDashboardDemo();
    }
}

// Update dashboard with real API data
async function updateDashboardFromAPI() {
    try {
        // Fetch stats from the bot dashboard API
        const statsResponse = await fetch(`${apiEndpoint}/api/stats`);
        if (!statsResponse.ok) throw new Error('API not available');
        
        const statsData = await statsResponse.json();
        
        // Update stats display
        document.getElementById('requestsToday').textContent = statsData.total_requests || 0;
        document.getElementById('total-errors').textContent = statsData.total_errors || 0;
        
        // Calculate success rate
        const successRate = statsData.success_rate || 
            calculateSuccessRate(statsData.total_requests, statsData.total_errors);
        document.getElementById('success-rate-display').textContent = successRate + '%';
        
        // Update last update time
        if (statsData.last_updated) {
            const lastUpdate = new Date(statsData.last_updated);
            const now = new Date();
            const diffMs = now - lastUpdate;
            const diffMins = Math.floor(diffMs / 60000);
            
            let timeAgo;
            if (diffMins < 1) {
                timeAgo = 'Just now';
            } else if (diffMins < 60) {
                timeAgo = diffMins + 'm ago';
            } else {
                const diffHours = Math.floor(diffMins / 60);
                timeAgo = diffHours + 'h ago';
            }
            document.getElementById('lastUpdate').textContent = timeAgo;
        }
        
        // Fetch hourly data for chart
        const hourlyResponse = await fetch(`${apiEndpoint}/api/stats/hourly`);
        if (hourlyResponse.ok) {
            const hourlyData = await hourlyResponse.json();
            updateLineChartFromData(hourlyData);
        }
        
        // Fetch locations data for bar chart
        const locationsResponse = await fetch(`${apiEndpoint}/api/stats/locations`);
        if (locationsResponse.ok) {
            const locationsData = await locationsResponse.json();
            updateBarChartFromData(locationsData);
        }
        
        // Update status indicator
        document.getElementById('botStatus').textContent = 'Online (Live Data)';
        updateConnectionStatus(true);
        
        console.log('Dashboard updated with real API data at', new Date());
    } catch (error) {
        console.error('Failed to fetch from API, falling back to demo:', error);
        usingRealData = false;
        updateConnectionStatus(false);
        updateDashboardDemo();
    }
}

// Update dashboard with demo data
function updateDashboardDemo() {
    // Update stats with random demo data
    document.getElementById('requestsToday').textContent = Math.floor(Math.random() * 50) + 20;
    const activeChannelsEl = document.getElementById('activeChannels');
    if (activeChannelsEl) activeChannelsEl.textContent = Math.floor(Math.random() * 4) + 2;
    
    const uptimeEl = document.getElementById('uptime');
    if (uptimeEl) uptimeEl.textContent = (Math.random() * 48 + 12).toFixed(1);
    
    // Update last update time
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
    
    // Update status to indicate demo mode
    const statusEl = document.getElementById('botStatus');
    if (statusEl) {
        statusEl.textContent = 'Online (Demo Data)';
    }
    
    console.log('Dashboard updated with demo data at', now);
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

// Update line chart from API data
function updateLineChartFromData(hourlyData) {
    if (!hourlyData || hourlyData.length === 0) {
        return;
    }
    
    // Extract counts from API data
    const data = hourlyData.map(item => item.count);
    updateLineChart(data);
    
    // Update time labels
    const startTime = new Date(hourlyData[0].hour);
    const endTime = new Date(hourlyData[hourlyData.length - 1].hour);
    
    const startLabel = document.getElementById('chartStartTime');
    const endLabel = document.getElementById('chartEndTime');
    
    if (startLabel) startLabel.textContent = startTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
    if (endLabel) endLabel.textContent = endTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
}

// Update bar chart from API data
function updateBarChartFromData(locationsData) {
    const chartDiv = document.getElementById('locationsChart');
    if (!chartDiv || !locationsData || locationsData.length === 0) {
        return;
    }
    
    // Clear existing bars
    chartDiv.innerHTML = '';
    
    // Find max value for scaling
    const maxValue = Math.max(...locationsData.map(item => item.count));
    
    // Create bars for each location
    locationsData.forEach(item => {
        const barContainer = document.createElement('div');
        barContainer.style.cssText = 'flex: 1; display: flex; flex-direction: column; align-items: center;';
        
        const bar = document.createElement('div');
        bar.className = 'bar';
        const height = maxValue > 0 ? (item.count / maxValue) * 80 : 10;
        bar.style.height = height + '%';
        
        const value = document.createElement('span');
        value.className = 'bar-value';
        value.textContent = item.count;
        bar.appendChild(value);
        
        const label = document.createElement('div');
        label.className = 'bar-label';
        label.textContent = item.location;
        
        barContainer.appendChild(bar);
        barContainer.appendChild(label);
        chartDiv.appendChild(barContainer);
    });
}

function calculateSuccessRate(total, errors) {
    if (total === 0) return 100;
    return Math.round(((total - errors) / total) * 100);
}

// API endpoint configuration
function loadApiEndpoint() {
    // Try to load from localStorage
    const saved = localStorage.getItem('mcwb-api-endpoint');
    if (saved && saved !== '') {
        apiEndpoint = saved;
        usingRealData = true;
        console.log('Loaded API endpoint:', apiEndpoint);
    } else {
        console.log('No API endpoint configured, using demo data');
    }
}

function saveApiEndpoint(endpoint) {
    localStorage.setItem('mcwb-api-endpoint', endpoint);
    apiEndpoint = endpoint;
    usingRealData = endpoint && endpoint !== '';
    console.log('Saved API endpoint:', endpoint);
}

function setupApiConfig() {
    // Create config panel if it doesn't exist
    const configPanel = document.getElementById('api-config-panel');
    if (!configPanel) return;
    
    const input = document.getElementById('api-endpoint-input');
    const saveBtn = document.getElementById('save-api-endpoint');
    const clearBtn = document.getElementById('clear-api-endpoint');
    const testBtn = document.getElementById('test-api-endpoint');
    
    // Load saved endpoint into input
    if (apiEndpoint) {
        input.value = apiEndpoint;
    }
    
    // Save button
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            const endpoint = input.value.trim();
            if (endpoint) {
                // Remove trailing slash
                const cleaned = endpoint.replace(/\/$/, '');
                saveApiEndpoint(cleaned);
                showFeedback('API endpoint saved! Refreshing...', 'success');
                setTimeout(() => {
                    updateDashboard();
                }, 500);
            }
        });
    }
    
    // Clear button
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            saveApiEndpoint('');
            input.value = '';
            showFeedback('Switched to demo mode', 'info');
            updateDashboard();
        });
    }
    
    // Test button
    if (testBtn) {
        testBtn.addEventListener('click', async function() {
            const endpoint = input.value.trim().replace(/\/$/, '');
            if (!endpoint) {
                showFeedback('Please enter an API endpoint', 'error');
                return;
            }
            
            showFeedback('Testing connection...', 'info');
            
            try {
                const response = await fetch(`${endpoint}/api/stats`, {
                    method: 'GET',
                    mode: 'cors'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    showFeedback('✓ Connection successful! Found ' + data.total_requests + ' total requests', 'success');
                } else {
                    showFeedback('Connection failed: ' + response.status, 'error');
                }
            } catch (error) {
                showFeedback('Connection failed: ' + error.message, 'error');
            }
        });
    }
}

function showFeedback(message, type) {
    const feedbackEl = document.getElementById('api-feedback');
    if (!feedbackEl) return;
    
    feedbackEl.textContent = message;
    feedbackEl.className = 'feedback-message ' + type;
    feedbackEl.style.display = 'block';
    
    setTimeout(() => {
        feedbackEl.style.display = 'none';
    }, 3000);
}

function updateConnectionStatus(isConnected) {
    const indicator = document.querySelector('.status.online');
    const statusEl = document.getElementById('botStatus');
    
    if (indicator) {
        if (isConnected) {
            indicator.style.background = '#4ade80';
        } else {
            indicator.style.background = '#fbbf24';
        }
    }
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

// Update line chart from API data
function updateLineChartFromData(hourlyData) {
    if (!hourlyData || hourlyData.length === 0) {
        return;
    }
    
    // Extract counts from API data
    const data = hourlyData.map(item => item.count);
    updateLineChart(data);
    
    // Update time labels
    const startTime = new Date(hourlyData[0].hour);
    const endTime = new Date(hourlyData[hourlyData.length - 1].hour);
    
    const startLabel = document.getElementById('chartStartTime');
    const endLabel = document.getElementById('chartEndTime');
    
    if (startLabel) startLabel.textContent = startTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
    if (endLabel) endLabel.textContent = endTime.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
}

// Update bar chart from API data
function updateBarChartFromData(locationsData) {
    const chartDiv = document.getElementById('locationsChart');
    if (!chartDiv || !locationsData || locationsData.length === 0) {
        return;
    }
    
    // Clear existing bars
    chartDiv.innerHTML = '';
    
    // Find max value for scaling
    const maxValue = Math.max(...locationsData.map(item => item.count));
    
    // Create bars for each location
    locationsData.forEach(item => {
        const barContainer = document.createElement('div');
        barContainer.style.cssText = 'flex: 1; display: flex; flex-direction: column; align-items: center;';
        
        const bar = document.createElement('div');
        bar.className = 'bar';
        const height = maxValue > 0 ? (item.count / maxValue) * 80 : 10;
        bar.style.height = height + '%';
        
        const value = document.createElement('span');
        value.className = 'bar-value';
        value.textContent = item.count;
        bar.appendChild(value);
        
        const label = document.createElement('div');
        label.className = 'bar-label';
        label.textContent = item.location;
        
        barContainer.appendChild(bar);
        barContainer.appendChild(label);
        chartDiv.appendChild(barContainer);
    });
}

function calculateSuccessRate(total, errors) {
    if (total === 0) return 100;
    return Math.round(((total - errors) / total) * 100);
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
    if (apiEndpoint && usingRealData) {
        // Real data updates are handled by updateDashboardFromAPI
        return;
    }
    
    // Generate new data for demo mode
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

// Demo: Simulate log updates every 30 seconds (only in demo mode)
setInterval(function() {
    if (!usingRealData) {
        const now = new Date();
        const timestamp = now.toLocaleTimeString();
        const cities = ['London', 'Manchester', 'York', 'Leeds', 'Birmingham', 'Edinburgh', 'Glasgow', 'Bristol'];
        const city = cities[Math.floor(Math.random() * cities.length)];
        const users = ['User1', 'User2', 'User3', 'User4', 'User5'];
        const user = users[Math.floor(Math.random() * users.length)];
        
        addLogEntry(timestamp, 'INFO', `${user} requested weather for ${city}, GB`);
    }
}, 30000);

