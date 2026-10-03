/* Network Monitor JavaScript */
let dashboardRefreshing = false;

async function autoRefreshDashboard() {
    const content = document.getElementById('dashboardContent');
    if (!content || dashboardRefreshing) return;
    dashboardRefreshing = true;
    const button = document.getElementById('refreshDashboard');
    const status = document.getElementById('refreshStatus');
    button.disabled = true;
    status.textContent = 'Refreshing saved readings…';
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
        const response = await fetch('/dashboard/fragment', {
            cache: 'no-store', signal: controller.signal
        });
        if (!response.ok) throw new Error('Dashboard request failed');
        const html = await response.text();
        // This fragment is rendered by our Jinja templates, with autoescaping enabled.
        content.innerHTML = html;
        status.className = 'text-muted';
        status.textContent = `Dashboard refreshed at ${new Date().toLocaleTimeString()}. Updates every 30 seconds.`;
    } catch (error) {
        status.className = 'text-danger';
        status.textContent = 'Cannot refresh dashboard. Showing previous readings; retrying automatically.';
    } finally {
        clearTimeout(timeout);
        dashboardRefreshing = false;
        button.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('dashboardContent')) return;
    document.getElementById('refreshDashboard').addEventListener('click', autoRefreshDashboard);
    setInterval(() => {
        if (!document.hidden) autoRefreshDashboard();
    }, 30000);
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) autoRefreshDashboard();
    });
});

// Format timestamps
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Export functionality
function exportEvents() {
    window.location.href = '/api/events/export';
}

// Search devices
function searchDevices(query) {
    if (!query) {
        return;
    }

    fetch(`/api/devices/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            console.log('Search results:', data);
        })
        .catch(error => console.error('Search error:', error));
}

// Status indicator helper
function getStatusBadge(status) {
    if (status === 'online') {
        return '<span class="badge bg-success">🟢 Online</span>';
    } else {
        return '<span class="badge bg-danger">🔴 Offline</span>';
    }
}
