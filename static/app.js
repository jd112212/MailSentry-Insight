document.addEventListener('DOMContentLoaded', () => {
    // 1. STATE INITIALIZATION
    const state = {
        activeTab: 'dashboard',
        isConfigured: false,
        emails: [],
        entities: [],
        analytics: {},
        charts: {
            category: null,
            volume: null,
            senders: null
        }
    };

    // 2. DOM ELEMENTS
    const navItems = document.querySelectorAll('.nav-item');
    const tabSections = document.querySelectorAll('.tab-section');
    const pageTitle = document.getElementById('pageTitle');
    const pageDescription = document.getElementById('pageDescription');
    const syncBtn = document.getElementById('syncBtn');
    const syncIcon = document.getElementById('syncIcon');
    const alertContainer = document.getElementById('alertContainer');
    
    // Status indicators
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    // Tables elements
    const emailsTableBody = document.getElementById('emailsTableBody');
    const entitiesTableBody = document.getElementById('entitiesTableBody');
    const emailSearch = document.getElementById('emailSearch');
    const emailCategoryFilter = document.getElementById('emailCategoryFilter');
    const entitySearch = document.getElementById('entitySearch');

    // Settings elements
    const settingsForm = document.getElementById('settingsForm');
    const gmailUsername = document.getElementById('gmailUsername');
    const gmailAppPassword = document.getElementById('gmailAppPassword');
    const fetchLimit = document.getElementById('fetchLimit');
    const appendMode = document.getElementById('appendMode');

    // KPI Elements
    const kpiTotal = document.getElementById('kpiTotal');
    const kpiLeads = document.getElementById('kpiLeads');
    const kpiInvoices = document.getElementById('kpiInvoices');
    const kpiRate = document.getElementById('kpiRate');

    // 3. TAB ROUTING SYSTEM
    const tabMetaData = {
        dashboard: {
            title: 'Analytics Dashboard',
            desc: 'Visual overview of email intelligence metrics'
        },
        emails: {
            title: 'Processed Emails',
            desc: 'Classification results and message body content logs'
        },
        entities: {
            title: 'Extracted Entities',
            desc: 'Structured variables retrieved from message parsing'
        },
        settings: {
            title: 'Connection Settings',
            desc: 'Configure credentials and sync parameters'
        }
    };

    function switchTab(tabId) {
        state.activeTab = tabId;
        
        // Toggle Nav item active classes
        navItems.forEach(item => {
            if (item.getAttribute('data-tab') === tabId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Toggle Tab section active classes
        tabSections.forEach(section => {
            if (section.id === `tab-${tabId}`) {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });

        // Update titles
        const meta = tabMetaData[tabId] || { title: 'Workspace', desc: '' };
        pageTitle.textContent = meta.title;
        pageDescription.textContent = meta.desc;

        // Force resize canvas on tab switch to redraw charts correctly
        if (tabId === 'dashboard') {
            updateCharts();
        }
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            switchTab(item.getAttribute('data-tab'));
        });
    });

    // 4. NOTIFICATION / ALERT ENGINE
    function showAlert(message, type = 'info', duration = 5000) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        
        let iconName = 'info';
        if (type === 'success') iconName = 'check-circle';
        if (type === 'error') iconName = 'alert-triangle';

        alert.innerHTML = `
            <div style="display:flex; align-items:center; gap:10px;">
                <i data-lucide="${iconName}"></i>
                <span>${message}</span>
            </div>
            <button class="alert-close">&times;</button>
        `;
        
        alertContainer.appendChild(alert);
        lucide.createIcons();

        // Close button click
        alert.querySelector('.alert-close').addEventListener('click', () => {
            alert.remove();
        });

        // Auto close after duration
        if (duration > 0) {
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.classList.add('fade-out');
                    setTimeout(() => alert.remove(), 300);
                }
            }, duration);
        }
    }

    // 5. API CLIENT OPERATIONS

    // A. Check config status
    async function checkConfigStatus() {
        try {
            const response = await fetch('/api/config/status');
            const data = await response.json();
            
            state.isConfigured = data.configured;

            if (data.configured) {
                statusDot.className = 'status-indicator-dot online';
                statusText.textContent = 'Configured';
                // Fill inputs if currently empty
                if (!gmailUsername.value) gmailUsername.value = data.username;
                fetchLimit.value = data.fetch_limit;
                appendMode.value = String(data.append_mode);
            } else {
                statusDot.className = 'status-indicator-dot offline';
                statusText.textContent = 'Not Setup';
            }
        } catch (error) {
            console.error('Error getting config status:', error);
            statusDot.className = 'status-indicator-dot offline';
            statusText.textContent = 'API Error';
        }
    }

    // B. Save settings configuration
    settingsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            username: gmailUsername.value.trim(),
            app_password: gmailAppPassword.value.trim(),
            fetch_limit: parseInt(fetchLimit.value),
            append_mode: appendMode.value === 'true'
        };

        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (response.ok) {
                showAlert('Gmail credentials updated successfully!', 'success');
                gmailAppPassword.value = ''; // clear password input field for safety
                await checkConfigStatus();
            } else {
                showAlert(data.detail || 'Failed to update credentials.', 'error');
            }
        } catch (error) {
            showAlert('Network error: Could not contact backend.', 'error');
        }
    });

    // C. Trigger Inbox synchronization
    syncBtn.addEventListener('click', async () => {
        if (!state.isConfigured) {
            showAlert('Gmail is not configured. Please go to Connection Settings first.', 'error');
            switchTab('settings');
            return;
        }

        // Set Loading States
        syncBtn.disabled = true;
        syncIcon.classList.add('spinning');
        showAlert('Connecting to Gmail IMAP server and retrieving messages. Please wait...', 'info', 0);

        try {
            const response = await fetch('/api/fetch', { method: 'POST' });
            // Clear the informational alert
            alertContainer.innerHTML = '';

            const data = await response.json();
            
            if (response.ok) {
                showAlert(data.message, 'success');
                // Refresh all dashboard metrics & tables
                await loadAllData();
            } else {
                showAlert(data.detail || 'Inbox sync process encountered an error.', 'error');
            }
        } catch (error) {
            alertContainer.innerHTML = '';
            showAlert('Network request failed. Is the FastAPI server running?', 'error');
        } finally {
            // Restore States
            syncBtn.disabled = false;
            syncIcon.classList.remove('spinning');
        }
    });

    // D. Fetch data tables lists
    async function loadAllData() {
        try {
            const emailsResponse = await fetch('/api/emails');
            state.emails = await emailsResponse.json();

            const entitiesResponse = await fetch('/api/entities');
            state.entities = await entitiesResponse.json();

            const analyticsResponse = await fetch('/api/analytics');
            state.analytics = await analyticsResponse.json();

            // Populate dashboard components
            renderEmailsTable();
            renderEntitiesTable();
            updateKPIs();
            updateCharts();
        } catch (error) {
            console.error('Failed to load table datasets:', error);
            showAlert('Could not read processed CSV datasets from backend.', 'error');
        }
    }

    // 6. RENDER TABLES

    // Emails Table Render with Search and Filtering
    function renderEmailsTable() {
        const filterCat = emailCategoryFilter.value;
        const query = emailSearch.value.toLowerCase().trim();

        const filtered = state.emails.filter(email => {
            const matchesCat = (filterCat === 'ALL' || email.category === filterCat);
            const matchesQuery = (
                email.sender.toLowerCase().includes(query) ||
                email.subject.toLowerCase().includes(query) ||
                email.body_preview.toLowerCase().includes(query) ||
                email.email_id.toString().includes(query)
            );
            return matchesCat && matchesQuery;
        });

        if (filtered.length === 0) {
            emailsTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="table-empty">No matching records found.</td>
                </tr>
            `;
            return;
        }

        emailsTableBody.innerHTML = filtered.map(email => {
            let badgeClass = 'badge-internal';
            if (email.category === 'Sales Lead') badgeClass = 'badge-lead';
            if (email.category === 'Support') badgeClass = 'badge-support';
            if (email.category === 'Invoice') badgeClass = 'badge-invoice';
            if (email.category === 'HR') badgeClass = 'badge-hr';
            if (email.category === 'Spam') badgeClass = 'badge-spam';

            return `
                <tr>
                    <td><span class="log-value code">${email.email_id}</span></td>
                    <td title="${email.sender}">${email.sender}</td>
                    <td title="${email.subject}">${email.subject}</td>
                    <td>${email.date}</td>
                    <td><span class="badge ${badgeClass}">${email.category}</span></td>
                    <td title="${email.body_preview}">${email.body_preview}</td>
                </tr>
            `;
        }).join('');
    }

    // Entities Table Render with Search
    function renderEntitiesTable() {
        const query = entitySearch.value.toLowerCase().trim();

        const filtered = state.entities.filter(item => {
            return (
                item.email_id.toString().includes(query) ||
                item.phone_number.toLowerCase().includes(query) ||
                item.invoice_id.toLowerCase().includes(query) ||
                item.ticket_id.toLowerCase().includes(query) ||
                item.amount.toLowerCase().includes(query) ||
                item.order_id.toLowerCase().includes(query)
            );
        });

        if (filtered.length === 0) {
            entitiesTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="table-empty">No matching records found.</td>
                </tr>
            `;
            return;
        }

        entitiesTableBody.innerHTML = filtered.map(item => {
            const hasPhone = item.phone_number !== 'N/A';
            const hasInv = item.invoice_id !== 'N/A';
            const hasTck = item.ticket_id !== 'N/A';
            const hasAmt = item.amount !== 'N/A';
            const hasOrd = item.order_id !== 'N/A';

            return `
                <tr>
                    <td><span class="log-value code">${item.email_id}</span></td>
                    <td><span class="${hasPhone ? 'text-primary font-semibold' : 'text-muted'}">${item.phone_number}</span></td>
                    <td><span class="${hasInv ? 'log-value code text-orange' : 'text-muted'}">${item.invoice_id}</span></td>
                    <td><span class="${hasTck ? 'log-value code text-blue' : 'text-muted'}">${item.ticket_id}</span></td>
                    <td><span class="${hasAmt ? 'text-primary font-semibold' : 'text-muted'}">${item.amount}</span></td>
                    <td><span class="${hasOrd ? 'log-value code text-purple' : 'text-muted'}">${item.order_id}</span></td>
                </tr>
            `;
        }).join('');
    }

    // Hook search/filter input events
    emailSearch.addEventListener('input', renderEmailsTable);
    emailCategoryFilter.addEventListener('change', renderEmailsTable);
    entitySearch.addEventListener('input', renderEntitiesTable);

    // 7. DASHBOARD KPIS
    function updateKPIs() {
        if (!state.analytics || Object.keys(state.analytics).length === 0) return;

        kpiTotal.textContent = state.analytics.total_emails || 0;
        kpiLeads.textContent = state.analytics.lead_count || 0;
        kpiInvoices.textContent = state.analytics.invoice_count || 0;

        // Calculate parsing rate: % of emails with at least one extracted entity
        if (state.entities.length > 0) {
            const successfulExtractions = state.entities.filter(item => {
                return (
                    item.phone_number !== 'N/A' ||
                    item.invoice_id !== 'N/A' ||
                    item.ticket_id !== 'N/A' ||
                    item.amount !== 'N/A' ||
                    item.order_id !== 'N/A'
                );
            }).length;
            const rate = Math.round((successfulExtractions / state.entities.length) * 100);
            kpiRate.textContent = `${rate}%`;
        } else {
            kpiRate.textContent = '0%';
        }
    }

    // 8. INTERACTIVE CHARTS (CHART.JS)
    function updateCharts() {
        if (!state.analytics || Object.keys(state.analytics).length === 0) return;

        // Set global Chart.js configs for premium dark mode aesthetics
        Chart.defaults.color = '#9ca3af';
        Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";

        // A. Category Distribution Pie Chart
        const catCanvas = document.getElementById('categoryChart');
        if (state.charts.category) state.charts.category.destroy();

        const catData = state.analytics.category_distribution || {};
        const catLabels = Object.keys(catData);
        const catValues = Object.values(catData);

        state.charts.category = new Chart(catCanvas, {
            type: 'doughnut',
            data: {
                labels: catLabels,
                datasets: [{
                    data: catValues,
                    backgroundColor: [
                        '#3b82f6', // Blue (Support)
                        '#10b981', // Green (Leads)
                        '#f59e0b', // Orange (Invoice)
                        '#8b5cf6', // Purple (HR)
                        '#6b7280', // Grey (Internal)
                        '#ef4444'  // Red (Spam)
                    ],
                    borderWidth: 2,
                    borderColor: '#121826'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { boxWidth: 12, padding: 15 }
                    }
                },
                cutout: '70%'
            }
        });

        // B. Daily Volume Line Chart
        const volCanvas = document.getElementById('volumeChart');
        if (state.charts.volume) state.charts.volume.destroy();

        const volData = state.analytics.daily_volume || {};
        const volLabels = Object.keys(volData);
        const volValues = Object.values(volData);

        state.charts.volume = new Chart(volCanvas, {
            type: 'line',
            data: {
                labels: volLabels,
                datasets: [{
                    label: 'Email Count',
                    data: volValues,
                    fill: true,
                    backgroundColor: 'rgba(59, 130, 246, 0.05)',
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    tension: 0.3,
                    pointBackgroundColor: '#3b82f6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.04)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        // C. Senders Bar Chart
        const senderCanvas = document.getElementById('sendersChart');
        if (state.charts.senders) state.charts.senders.destroy();

        const sendData = state.analytics.top_senders || {};
        // Truncate names for chart aesthetic
        const sendLabels = Object.keys(sendData).map(label => {
            return label.length > 22 ? label.substring(0, 20) + '...' : label;
        });
        const sendValues = Object.values(sendData);

        state.charts.senders = new Chart(senderCanvas, {
            type: 'bar',
            data: {
                labels: sendLabels,
                datasets: [{
                    data: sendValues,
                    backgroundColor: 'rgba(139, 92, 246, 0.75)',
                    hoverBackgroundColor: '#8b5cf6',
                    borderRadius: 6,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.04)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // 9. APP LAUNCH RUN
    async function init() {
        lucide.createIcons();
        await checkConfigStatus();
        await loadAllData();
    }

    init();
});
