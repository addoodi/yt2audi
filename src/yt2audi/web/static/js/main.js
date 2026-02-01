document.addEventListener('DOMContentLoaded', () => {
    // Start polling loop
    setInterval(fetchStatus, 1000);
    loadProfiles();

    // Allow Enter key in input
    document.getElementById('url-input').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            submitVideo();
        }
    });
});

async function submitVideo() {
    const input = document.getElementById('url-input');
    const url = input.value.trim();
    const btn = document.getElementById('process-btn');
    const profile = document.getElementById('profile-select').value;
    const outputDir = document.getElementById('output-path-input').value.trim();
    const autoCopy = document.getElementById('usb-checkbox').checked;

    if (!url) {
        showToast('Please enter a valid URL', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = 'PROCESSING...';

    try {
        const payload = {
            url: url,
            profile_id: profile,
            custom_output_dir: outputDir || null,
            auto_copy_usb: autoCopy
        };

        const response = await fetch('/api/queue', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (response.ok) {
            const data = await response.json();
            showToast(`Task initiated [ID: ${data.id}]`, 'success');
            input.value = ''; // Clear input
        } else {
            showToast('Failed to start task', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'INITIATE';
    }
}

async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        if (response.ok) {
            const data = await response.json();
            updateDashboard(data);

            // Auto-update USB Checkbox
            const usbCheckbox = document.getElementById('usb-checkbox');
            const usbLabel = document.querySelector('label[for="usb-checkbox"]');

            if (data.system.usb_connected) {
                usbCheckbox.disabled = false;
                usbCheckbox.parentElement.style.opacity = '1';
                usbCheckbox.parentElement.title = "USB Drive Detected";
            } else {
                usbCheckbox.checked = false;
                usbCheckbox.disabled = true;
                usbCheckbox.parentElement.style.opacity = '0.5';
                usbCheckbox.parentElement.title = "No USB Drive Detected";
            }
        }
    } catch (error) {
        console.error('Status fetch failed', error);
    }
}

function updateDashboard(data) {
    // Update System Status
    const usbIndicator = document.getElementById('status-usb');
    if (data.system.usb_connected) {
        usbIndicator.classList.add('active');
        usbIndicator.style.opacity = '1';
    } else {
        usbIndicator.classList.remove('active');
        usbIndicator.style.opacity = '0.5';
    }

    // Update Jobs
    const jobsContainer = document.getElementById('active-jobs');
    const historyContainer = document.getElementById('history-list');

    // Simple diff logic: Clear active and rebuild (optimize in real React/Vue app)
    // We separate active (running/pending) from history (complete/error)

    const activeJobs = data.jobs.filter(j => j.status !== 'complete' && j.status !== 'error');
    const historyJobs = data.jobs.filter(j => j.status === 'complete' || j.status === 'error');

    // Render Active
    if (activeJobs.length === 0) {
        jobsContainer.innerHTML = '<div id="empty-state" style="text-align: center; padding: 2rem; opacity: 0.3;">NO ACTIVE OPERATIONS</div>';
    } else {
        jobsContainer.innerHTML = activeJobs.map(job => `
            <div class="job-card">
                <div class="job-info">
                    <div class="job-title" title="${job.url}">${job.title || job.url}</div>
                    <div class="job-status ${getJobStatusClass(job.stage)}">${job.stage.toUpperCase()}</div>
                </div>
                <div class="progress-container">
                    <div class="progress-bar ${job.status === 'processing' ? 'glow' : ''}" style="width: ${job.progress}%"></div>
                </div>
                <div style="text-align: right; font-size: 0.8rem; margin-top: 5px; opacity: 0.6;">${Math.round(job.progress)}%</div>
            </div>
        `).join('');
    }

    // Render History (Reverse order - newest first)
    historyContainer.innerHTML = historyJobs.slice().reverse().map(job => `
        <div class="history-item">
            <div class="history-icon" style="color: ${job.status === 'error' ? 'var(--danger-color)' : 'var(--accent-color)'}">
                ${job.status === 'error' ? '✖' : '✔'}
            </div>
            <div style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                ${job.title || job.url}
            </div>
            <div style="opacity: 0.5; max-width: 40%; overflow: hidden; text-overflow: ellipsis;" title="${job.stage}">
                ${job.stage}
            </div>
        </div>
    `).join('');
}

function getJobStatusClass(stage) {
    stage = stage.toLowerCase();
    if (stage.includes('download')) return 'downloading';
    if (stage.includes('convert')) return 'converting';
    if (stage.includes('finish') || stage.includes('complete')) return 'complete';
    if (stage.includes('fail') || stage.includes('error')) return 'error';
    return '';
}

async function loadProfiles() {
    try {
        const response = await fetch('/api/profiles');
        if (response.ok) {
            const profiles = await response.json();
            const select = document.getElementById('profile-select');
            select.innerHTML = profiles.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
        }
    } catch (e) {
        console.error('Failed to load profiles');
    }
}

function showToast(message, type = 'processed') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.borderLeftColor = type === 'error' ? 'var(--danger-color)' : 'var(--primary-color)';
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
