/**
 * PhishAwareLab - Real-Time Dashboard Controller
 * Handles live polling, metric updates, Chart.js rendering, and simulation controls.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const metricSent = document.getElementById('metricSent');
    const metricOpened = document.getElementById('metricOpened');
    const metricClicked = document.getElementById('metricClicked');
    const metricSubmitted = document.getElementById('metricSubmitted');

    const metricOpenRate = document.getElementById('metricOpenRate');
    const metricClickRate = document.getElementById('metricClickRate');
    const metricSubmitRate = document.getElementById('metricSubmitRate');

    const funnelSent = document.getElementById('funnelSent');
    const funnelOpened = document.getElementById('funnelOpened');
    const funnelClicked = document.getElementById('funnelClicked');
    const funnelSubmitted = document.getElementById('funnelSubmitted');

    const activityFeed = document.getElementById('activityFeed');
    const statusLabel = document.getElementById('statusLabel');
    const btnStartDemo = document.getElementById('btnStartDemo');
    const btnResetDemo = document.getElementById('btnResetDemo');

    // Controlled Event Testing buttons
    const btnEventSent = document.getElementById('btnEventSent');
    const btnEventOpened = document.getElementById('btnEventOpened');
    const btnEventClicked = document.getElementById('btnEventClicked');
    const btnEventCompleted = document.getElementById('btnEventCompleted');

    const currentTime = document.getElementById('currentTime');
    const currentDate = document.getElementById('currentDate');

    // Chart.js instance variable
    let funnelChart = null;

    // Cache of activity IDs to prevent redundant re-renders
    let renderedActivityHash = '';

    // =========================================================================
    // 1. Live Clock & Calendar
    // =========================================================================
    function updateClock() {
        const now = new Date();

        // Format time: HH:MM:SS AM/PM
        const timeStr = now.toLocaleTimeString('en-US', {
            hour12: true,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        // Format date: Day, Month DD, YYYY
        const dateStr = now.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });

        if (currentTime) currentTime.textContent = timeStr;
        if (currentDate) currentDate.textContent = dateStr;
    }

    updateClock();
    setInterval(updateClock, 1000);

    // =========================================================================
    // 2. Chart.js Initialization
    // =========================================================================
    function initFunnelChart() {
        const ctx = document.getElementById('funnelChart').getContext('2d');

        // Stage colors
        const colors = {
            sent: '#38bdf8',
            opened: '#10b981',
            clicked: '#f59e0b',
            submitted: '#a855f7'
        };

        const bgGradients = [
            'rgba(56, 189, 248, 0.75)',
            'rgba(16, 185, 129, 0.75)',
            'rgba(245, 158, 11, 0.75)',
            'rgba(168, 85, 247, 0.75)'
        ];

        const borderColors = [
            '#38bdf8',
            '#10b981',
            '#f59e0b',
            '#a855f7'
        ];

        funnelChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Invitations Sent', 'Opens (Demo/Measured)', 'Training Link Clicks', 'Training Completed'],
                datasets: [{
                    label: 'Participants',
                    data: [30, 22, 14, 8],
                    backgroundColor: bgGradients,
                    borderColor: borderColors,
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    barPercentage: 0.6,
                    categoryPercentage: 0.8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 500,
                    easing: 'easeOutQuart'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleColor: '#f8fafc',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(255, 255, 255, 0.15)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                const val = context.raw;
                                const sentVal = context.chart.data.datasets[0].data[0] || 1;
                                const pct = ((val / sentVal) * 100).toFixed(1);
                                return `${context.label}: ${val} (${pct}% of sent)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                family: "'Inter', sans-serif",
                                size: 12,
                                weight: '500'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#64748b',
                            stepSize: 5,
                            font: {
                                family: "'JetBrains Mono', monospace",
                                size: 11
                            }
                        }
                    }
                }
            }
        });
    }

    // =========================================================================
    // 3. UI Helpers & Icons
    // =========================================================================
    function getEventIcon(type) {
        switch (type) {
            case 'sent':
                return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>`;
            case 'opened':
                return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
            case 'clicked':
                return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>`;
            case 'submitted':
                return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`;
            case 'completed':
                return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
            default:
                return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
        }
    }

    function showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span>${message}</span>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 300);
        }, 3200);
    }

    // =========================================================================
    // 4. Data Polling & UI Synchronization
    // =========================================================================
    async function fetchStats() {
        try {
            const response = await fetch('/api/stats');
            if (!response.ok) throw new Error('Network response failed');
            const data = await response.json();

            // 1. Update Metric Cards
            const stats = data.stats || {};
            metricSent.textContent = stats.sent ?? 0;
            metricOpened.textContent = stats.opened ?? 0;
            metricClicked.textContent = stats.clicked ?? 0;
            metricSubmitted.textContent = stats.submitted ?? stats.completed ?? 0;

            metricOpenRate.textContent = `${stats.open_rate ?? 0}%`;
            metricClickRate.textContent = `${stats.click_rate ?? 0}%`;
            metricSubmitRate.textContent = `${stats.submit_rate ?? 0}%`;

            // 2. Update Funnel Summary Numbers
            funnelSent.textContent = stats.sent ?? 0;
            funnelOpened.textContent = stats.opened ?? 0;
            funnelClicked.textContent = stats.clicked ?? 0;
            funnelSubmitted.textContent = stats.submitted ?? stats.completed ?? 0;

            // 3. Update Status Indicator
            if (data.is_running) {
                statusLabel.textContent = 'Demo In Progress...';
                btnStartDemo.disabled = true;
                btnStartDemo.classList.add('loading');
            } else {
                statusLabel.textContent = data.status || 'Simulation Active';
                btnStartDemo.disabled = false;
                btnStartDemo.classList.remove('loading');
            }

            // 4. Update Chart.js if initialized
            if (funnelChart) {
                const chartData = [
                    stats.sent ?? 0,
                    stats.opened ?? 0,
                    stats.clicked ?? 0,
                    stats.submitted ?? 0
                ];

                // Update data and max scale smoothly
                funnelChart.data.datasets[0].data = chartData;
                const maxVal = Math.max(...chartData, 10);
                funnelChart.options.scales.y.suggestedMax = Math.ceil((maxVal + 5) / 5) * 5;
                funnelChart.update();
            }

            // 5. Update Recent Activity Feed
            const activities = data.recent_activity || [];
            const newHash = JSON.stringify(activities.map(a => a.id + a.timestamp));

            if (newHash !== renderedActivityHash) {
                renderedActivityHash = newHash;
                renderActivityList(activities);
            }

        } catch (err) {
            console.warn('Live poll error:', err);
        }
    }

    function renderActivityList(activities) {
        if (!activities || activities.length === 0) {
            activityFeed.innerHTML = '<div class="feed-placeholder">No activity recorded yet.</div>';
            return;
        }

        const itemsHtml = activities.map(item => {
            const type = item.type || 'system';
            const iconSvg = getEventIcon(type);

            return `
                <div class="activity-item type-${type}">
                    <div class="activity-badge-icon">
                        ${iconSvg}
                    </div>
                    <div class="activity-content">
                        <div class="activity-top">
                            <span class="activity-user">${item.user || 'System'}</span>
                            <span class="activity-time">${item.timestamp || ''}</span>
                        </div>
                        <div class="activity-action">${item.action || 'Simulation Event'}</div>
                        <div class="activity-desc">${item.details || ''}</div>
                    </div>
                </div>
            `;
        }).join('');

        activityFeed.innerHTML = itemsHtml;
    }

    // =========================================================================
    // 5. Simulation Action Controls (Start / Reset)
    // =========================================================================
    btnStartDemo.addEventListener('click', async () => {
        try {
            btnStartDemo.disabled = true;
            const res = await fetch('/api/start-demo', { method: 'POST' });
            const result = await res.json();

            showToast(result.message || 'Synthetic demo started!', 'success');
            // Fetch immediately to capture any early updates
            fetchStats();
        } catch (err) {
            showToast('Failed to start demo', 'warning');
            btnStartDemo.disabled = false;
        }
    });

    btnResetDemo.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/reset-demo', { method: 'POST' });
            const result = await res.json();

            showToast(result.message || 'Demo statistics reset.', 'info');
            btnStartDemo.disabled = false;
            fetchStats();
        } catch (err) {
            showToast('Failed to reset demo', 'warning');
        }
    });

    // =========================================================================
    // 5b. Controlled Event Testing Handlers
    // =========================================================================
    async function triggerSyntheticEvent(eventType, btn) {
        if (!btn) return;
        btn.disabled = true;

        try {
            const res = await fetch(`/api/event/${eventType}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: eventType })
            });
            const result = await res.json();

            if (res.ok && result.success) {
                showToast(result.message || `Recorded ${eventType} event.`, 'success');
                // Refresh metrics, chart, and activity stream immediately
                await fetchStats();
            } else {
                showToast(result.message || 'Error recording event', 'warning');
            }
        } catch (err) {
            showToast('Unable to connect to simulation server.', 'warning');
        } finally {
            btn.disabled = false;
        }
    }

    if (btnEventSent) {
        btnEventSent.addEventListener('click', () => triggerSyntheticEvent('sent', btnEventSent));
    }
    if (btnEventOpened) {
        btnEventOpened.addEventListener('click', () => triggerSyntheticEvent('opened', btnEventOpened));
    }
    if (btnEventClicked) {
        btnEventClicked.addEventListener('click', () => triggerSyntheticEvent('clicked', btnEventClicked));
    }
    if (btnEventCompleted) {
        btnEventCompleted.addEventListener('click', () => triggerSyntheticEvent('completed', btnEventCompleted));
    }

    // =========================================================================
    // 6. Launch App & Setup 2-Second Polling
    // =========================================================================
    initFunnelChart();
    fetchStats(); // Initial load
    setInterval(fetchStats, 2000); // 2-second live refresh
});
