// MCWB Dashboard - Live Data Support with Cloudflare Tunnel
// This can connect to live data via Cloudflare Tunnel or run in demo mode

let autoRefreshEnabled = true;
let refreshInterval = null;
let isLiveMode = false;

// ============================================================================
// CONFIGURATION: Update this with your Cloudflare Tunnel URL
// ============================================================================
// After setting up Cloudflare Tunnel, replace the URL below with your tunnel URL
// Example: const TUNNEL_URL = 'https://mcwb-dashboard.yourdomain.com';
// 
// For the cPanel-hosted site at weather.example.com:
// Set this to your Cloudflare Tunnel URL that points to your bot at 192.168.1.100:5000
// Leave empty to run in demo mode only

const TUNNEL_URL = ''; // Set your Cloudflare Tunnel URL here (e.g., 'https://mcwb-dashboard.yourdomain.com')

// Alternative: Local network URL (if accessing from local network)
const LOCAL_URL = 'http://192.168.1.100:5000';

// ============================================================================

/**
 * Get the API URL to use for dashboard connections
 * Priority: Tunnel URL > Local URL > Demo Mode
 */
function getApiUrl() {
    // If tunnel URL is configured, use it
    if (TUNNEL_URL && TUNNEL_URL.trim() !== '') {
        return TUNNEL_URL;
    }
    
    // If we're on local network, try local URL
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || 
        hostname.startsWith('192.168.') || 
        hostname.startsWith('10.') ||
        hostname.startsWith('172.')) {
        return LOCAL_URL;
    }
    
    // No live URL configured - demo mode
    return null;
}

// Initialize dashboard - try live first, fallback to demo
document.addEventListener('DOMContentLoaded', function() {
    const apiUrl = getApiUrl();
    
    if (apiUrl) {
        console.log('Attempting to connect to live dashboard:', apiUrl);
        tryLiveConnection(apiUrl);
    } else {
        console.log('No live API URL configured - running in demo mode');
        showDemoMode();
    }
    
    setupAutoRefresh();
});
/**
 * Try to connect to live dashboard API
 */
async function tryLiveConnection(apiUrl) {
    try {
        // Test connection with a simple API call
        const response = await fetch(`${apiUrl}/api/status`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
            // Timeout after 5 seconds
            signal: AbortSignal.timeout(5000)
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✓ Connected to live dashboard:', data);
            isLiveMode = true;
            showLiveMode(apiUrl);
            loadLiveData(apiUrl);
            return;
        }
    } catch (error) {
        console.warn('Could not connect to live dashboard:', error.message);
    }
    
    // Fallback to demo mode
    console.log('Falling back to demo mode');
    showDemoMode();
}

/**
 * Show live mode indicator
 */
function showLiveMode(apiUrl) {
    const demoWarning = document.getElementById('demoModeWarning');
    
    if (demoWarning) {
        demoWarning.style.display = 'block';
        demoWarning.className = 'info-box success';
        demoWarning.innerHTML = `
            <h3><img src="img/emoji/2705.svg" alt="✅" class="emoji-icon"> Live Dashboard Connected</h3>
            <p>Successfully connected to your bot instance!</p>
            <p style="margin-top: 1rem;"><strong>API URL:</strong> <code>${apiUrl}</code></p>
            <p style="font-size: 0.9em; color: var(--text-muted); margin-top: 0.5rem;">
                Data updates automatically every 10 seconds.
            </p>
        `;
    }
}

/**
 * Load live data from the dashboard API
 */
async function loadLiveData(apiUrl) {
    try {
        // Fetch status
        const statusResponse = await fetch(`${apiUrl}/api/status`);
        if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            updateStatusDisplay(statusData);
        }
        
        // Fetch stats
        const statsResponse = await fetch(`${apiUrl}/api/stats`);
        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            updateStatsDisplay(statsData);
        }
        
        // Fetch channels
        const channelsResponse = await fetch(`${apiUrl}/api/channels`);
        if (channelsResponse.ok) {
            const channelsData = await channelsResponse.json();
            updateChannelsDisplay(channelsData);
        }
        
        // Fetch hourly stats for chart
        const hourlyResponse = await fetch(`${apiUrl}/api/stats/hourly`);
        if (hourlyResponse.ok) {
            const hourlyData = await hourlyResponse.json();
            updateChartDisplay(hourlyData);
        }
        
        // Fetch top locations
        const locationsResponse = await fetch(`${apiUrl}/api/stats/locations`);
        if (locationsResponse.ok) {
            const locationsData = await locationsResponse.json();
            updateLocationsDisplay(locationsData);
        }
        
        // Fetch bot logs
        const logsResponse = await fetch(`${apiUrl}/api/logs/bot`);
        if (logsResponse.ok) {
            const logsData = await logsResponse.json();
            updateLogsDisplay(logsData);
        }
        
    } catch (error) {
        console.error('Error loading live data:', error);
        // Don't fallback to demo mode immediately - might be temporary network issue
    }
}

/**
 * Update status display with live data
 */
function updateStatusDisplay(data) {
    const statusEl = document.getElementById('botStatus');
    const lastUpdateEl = document.getElementById('lastUpdate');
    
    if (statusEl) {
        statusEl.textContent = data.status === 'running' ? 'Online' : 'Offline';
        statusEl.className = data.status === 'running' ? 'status online' : 'status offline';
    }
    
    if (lastUpdateEl && data.timestamp) {
        lastUpdateEl.textContent = data.timestamp;
    }
}

/**
 * Update stats display with live data
 */
function updateStatsDisplay(data) {
    const requestsTodayEl = document.getElementById('requestsToday');
    const uptimeEl = document.getElementById('uptime');
    
    if (requestsTodayEl) {
        requestsTodayEl.textContent = data.total_requests || 0;
    }
    
    if (uptimeEl && data.last_updated) {
        // Calculate uptime from last_updated timestamp
        const uptime = calculateUptime(data.last_updated);
        uptimeEl.textContent = uptime;
    }
}

/**
 * Update channels display with live data
 */
function updateChannelsDisplay(data) {
    const activeChannelsEl = document.getElementById('activeChannels');
    
    if (activeChannelsEl && data.channels) {
        activeChannelsEl.textContent = data.channels.length;
    }
}

/**
 * Update chart with live hourly data
 */
function updateChartDisplay(data) {
    if (!data || !data.hours) return;
    
    // Extract request counts from hourly data
    const values = data.hours.map(h => h.requests || 0);
    updateLineChart(values);
}

/**
 * Update locations chart with live data
 */
function updateLocationsDisplay(data) {
    if (!data || !data.locations) return;
    
    const locationsChart = document.getElementById('locationsChart');
    if (!locationsChart) return;
    
    // Clear existing chart
    locationsChart.innerHTML = '';
    
    // Get max value for scaling
    const maxCount = Math.max(...data.locations.map(l => l.count), 1);
    
    // Create bars for top locations
    data.locations.slice(0, 6).forEach(location => {
        const barContainer = document.createElement('div');
        barContainer.style.cssText = 'flex: 1; display: flex; flex-direction: column; align-items: center;';
        
        const bar = document.createElement('div');
        bar.className = 'bar';
        bar.style.height = `${(location.count / maxCount) * 100}%`;
        
        const value = document.createElement('span');
        value.className = 'bar-value';
        value.textContent = location.count;
        bar.appendChild(value);
        
        const label = document.createElement('div');
        label.className = 'bar-label';
        label.textContent = location.location;
        
        barContainer.appendChild(bar);
        barContainer.appendChild(label);
        locationsChart.appendChild(barContainer);
    });
}

/**
 * Update logs display with live data
 */
function updateLogsDisplay(data) {
    if (!data || !data.lines) return;
    
    const requestLog = document.getElementById('requestLog');
    const systemLog = document.getElementById('systemLog');
    
    if (requestLog) {
        requestLog.innerHTML = '';
        // Show last 10 log lines
        data.lines.slice(-10).reverse().forEach(line => {
            const entry = parseLogLine(line);
            if (entry) {
                addLogEntryToContainer(requestLog, entry);
            }
        });
    }
}

/**
 * Parse a log line into components
 */
function parseLogLine(line) {
    // Try to parse timestamp, level, and message
    const match = line.match(/\[([^\]]+)\]\s*(\w+)?\s*[-:]?\s*(.*)/);
    if (match) {
        return {
            timestamp: match[1],
            level: match[2] || 'INFO',
            message: match[3] || line
        };
    }
    return {
        timestamp: new Date().toLocaleTimeString(),
        level: 'INFO',
        message: line
    };
}

/**
 * Add a log entry to a container
 */
function addLogEntryToContainer(container, entry) {
    const entryEl = document.createElement('div');
    entryEl.className = 'log-entry';
    
    const timestampSpan = document.createElement('span');
    timestampSpan.className = 'log-timestamp';
    timestampSpan.textContent = `[${entry.timestamp}]`;
    
    const levelSpan = document.createElement('span');
    levelSpan.className = `log-level-${entry.level}`;
    levelSpan.textContent = entry.level;
    
    const contentSpan = document.createElement('span');
    contentSpan.className = 'log-content';
    contentSpan.innerHTML = convertUserMentionsToLinks(entry.message);
    
    entryEl.appendChild(timestampSpan);
    entryEl.appendChild(document.createTextNode(' '));
    entryEl.appendChild(levelSpan);
    entryEl.appendChild(document.createTextNode(' '));
    entryEl.appendChild(contentSpan);
    
    container.appendChild(entryEl);
}

/**
 * Calculate uptime from timestamp
 */
function calculateUptime(lastUpdated) {
    try {
        const now = new Date();
        const updated = new Date(lastUpdated);
        const diffMs = now - updated;
        const hours = Math.floor(diffMs / (1000 * 60 * 60));
        return hours > 0 ? `${hours}h` : '< 1h';
    } catch (e) {
        return '--';
    }
}

// Show demo mode with fake data
function showDemoMode() {
    // Show demo warning, hide live info
    const demoWarning = document.getElementById('demoModeWarning');
    const liveInfo = document.getElementById('liveDataInfo');
    const connectionError = document.getElementById('connectionError');
    
    if (demoWarning) {
        demoWarning.style.display = 'block';
    }
    if (liveInfo) {
        liveInfo.style.display = 'none';
    }
    if (connectionError) {
        connectionError.style.display = 'none';
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
    // Get container width for responsive sizing
    const container = document.querySelector('.line-chart');
    const containerWidth = container ? container.offsetWidth : 600;
    const width = Math.min(600, containerWidth);
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
    const svg = document.querySelector('.line-chart svg');
    const line = document.getElementById('usageLine');
    const area = document.getElementById('usageArea');
    
    if (svg) {
        svg.setAttribute('width', width);
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    }
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

// Manual refresh of demo data
function refreshDashboard() {
    if (isLiveMode) {
        const apiUrl = getApiUrl();
        if (apiUrl) {
            loadLiveData(apiUrl);
        }
    } else {
        updateCharts();
    }
    
    // Visual feedback
    const btn = document.querySelector('.refresh-btn');
    if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = '<img src="img/emoji/2705.svg" alt="✓" class="emoji-icon"> Refreshed';
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 1000);
    }
}

// Update charts with new data (called from auto-refresh in demo mode)
function updateCharts() {
    if (isLiveMode) {
        // In live mode, refresh all data
        const apiUrl = getApiUrl();
        if (apiUrl) {
            loadLiveData(apiUrl);
        }
    } else {
        // In demo mode, generate random data
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
    
    // First, convert markdown-style mention links: [@username](meshcore://user/username)
    // This handles bot responses that already include the markdown link format
    // Use placeholders to protect converted links from further processing
    const markdownLinks = [];
    let result = escaped.replace(/\[@([a-zA-Z0-9_.-]+)\]\(meshcore:\/\/user\/([a-zA-Z0-9_.-]+)\)/g, 
                                  (match, displayName, urlName) => {
                                      // Security: Validate that display name matches URL username
                                      // to prevent spoofing attacks like [@alice](meshcore://user/bob)
                                      if (displayName !== urlName) {
                                          // Replace @ with a placeholder to prevent it from being converted
                                          return match.replace('@', '\u0000PROTECTED_AT\u0000');
                                      }
                                      const link = `<a href="meshcore://user/${urlName}" class="user-mention">@${displayName}</a>`;
                                      const placeholder = `__MDLINK_${markdownLinks.length}__`;
                                      markdownLinks.push(link);
                                      return placeholder;
                                  });
    
    // Then convert any remaining plain @username patterns to meshcore:// links
    // This maintains backward compatibility with messages that don't use markdown format
    result = result.replace(/@([a-zA-Z0-9_.-]+)/g, '<a href="meshcore://user/$1" class="user-mention">@$1</a>');
    
    // Restore protected @ symbols from mismatched markdown links
    result = result.replace(/\u0000PROTECTED_AT\u0000/g, '@');
    
    // Restore converted markdown links from placeholders
    markdownLinks.forEach((link, index) => {
        result = result.replace(`__MDLINK_${index}__`, link);
    });
    
    return result;
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

