// MCWB Dashboard - Demo Mode Only
// This is a static demo for the Netlify website
// For live data, access the dashboard directly on your Raspberry Pi

let autoRefreshEnabled = true;
let refreshInterval = null;

// Initialize dashboard in demo mode only
document.addEventListener('DOMContentLoaded', function() {
    showDemoMode();
    setupAutoRefresh();
});

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

// Manual refresh
function refreshDashboard() {
    updateCharts();
    
    // Visual feedback
    const btn = document.querySelector('.refresh-btn');
    if (btn) {
        const originalText = btn.textContent;
        btn.textContent = '✓ Refreshed';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 1000);
    }
}

// Update charts with new data (called from auto-refresh in demo mode)
function updateCharts() {
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

