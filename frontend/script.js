const API_BASE = 'https://views-telegram.onrender.com';

// DOM elements
const statusIndicator = document.getElementById('statusIndicator');
const statusLabel = document.getElementById('statusLabel');
const targetDisplay = document.getElementById('targetDisplay');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const linkInput = document.getElementById('linkInput');
const liveViewsEl = document.getElementById('liveViews');
const tokenErrorsEl = document.getElementById('tokenErrors');
const proxyErrorsEl = document.getElementById('proxyErrors');
const activeThreadsEl = document.getElementById('activeThreads');

let pollingInterval = null;
let isRunning = false;

// Parse Telegram link
function parseLink(link) {
  const match = link.match(/https?:\/\/t\.me\/([^/]+)\/(\d+)/);
  if (!match) return null;
  return { channel: match[1], post: parseInt(match[2]) };
}

// Update UI berdasarkan status
function updateUI(status) {
  isRunning = status.running;
  if (isRunning) {
    statusIndicator.classList.add('active');
    statusLabel.textContent = 'Bot Aktif';
    targetDisplay.textContent = `Channel: @${status.channel || '?'} | Post: ${status.post || '?'}`;
    startBtn.disabled = true;
    stopBtn.disabled = false;
  } else {
    statusIndicator.classList.remove('active');
    statusLabel.textContent = 'Bot Tidak Aktif';
    targetDisplay.textContent = 'Masukkan link untuk mulai';
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }

  // Statistik (fallback ke 0 jika tidak ada)
  liveViewsEl.textContent = status.views ?? 0;
  tokenErrorsEl.textContent = status.token_errors ?? 0;
  proxyErrorsEl.textContent = status.proxy_errors ?? 0;
  activeThreadsEl.textContent = status.active_threads ?? 0;
}

// Poll status
async function fetchStatus() {
  try {
    const response = await fetch(`${API_BASE}/status`);
    if (!response.ok) throw new Error('Gagal fetch status');
    const data = await response.json();
    updateUI(data);
  } catch (error) {
    console.error('Polling error:', error);
  }
}

function startPolling() {
  if (pollingInterval) clearInterval(pollingInterval);
  fetchStatus(); // immediate
  pollingInterval = setInterval(fetchStatus, 2000);
}

function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
}

// Start bot
async function startBot() {
  const link = linkInput.value.trim();
  if (!link) {
    alert('Masukkan link postingan Telegram terlebih dahulu.');
    return;
  }
  const parsed = parseLink(link);
  if (!parsed) {
    alert('Format link salah. Gunakan: https://t.me/channel/post');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel: parsed.channel, post: parsed.post })
    });
    const data = await response.json();
    if (!response.ok) {
      alert(data.message || 'Gagal memulai bot.');
      return;
    }
    // Mulai polling
    startPolling();
  } catch (error) {
    alert('Gagal menghubungi backend.');
  }
}

// Stop bot
async function stopBot() {
  try {
    const response = await fetch(`${API_BASE}/stop`, { method: 'POST' });
    const data = await response.json();
    if (!response.ok) {
      alert(data.message || 'Gagal menghentikan bot.');
      return;
    }
    stopPolling();
    // Refresh status final
    await fetchStatus();
  } catch (error) {
    alert('Gagal menghubungi backend.');
  }
}

// Event listeners
startBtn.addEventListener('click', startBot);
stopBtn.addEventListener('click', stopBot);

// Initial check
fetchStatus();

// Cleanup polling when page unloads (optional)
window.addEventListener('beforeunload', () => stopPolling());
