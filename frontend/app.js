// ===== CONFIG =====
const API_BASE = 'http://localhost:8000';
let allVideos = [];
let currentFilter = 'all';

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
  spawnParticles();
  setMinDateTime();
  setupDragDrop();
  loadVideos();
  setInterval(loadVideos, 30000); // auto-refresh every 30s
});

// ===== PARTICLES =====
function spawnParticles() {
  const container = document.getElementById('particles');
  for (let i = 0; i < 30; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.left = Math.random() * 100 + '%';
    p.style.animationDuration = (8 + Math.random() * 15) + 's';
    p.style.animationDelay = (Math.random() * 15) + 's';
    p.style.width = p.style.height = (1 + Math.random() * 2) + 'px';
    p.style.opacity = Math.random() * 0.6;
    container.appendChild(p);
  }
}

// ===== NAVIGATION =====
function showSection(section) {
  document.getElementById('hero').style.display = 'none';
  const main = document.getElementById('appMain');
  main.style.display = 'flex';
  switchTab(section);
}

function switchTab(tab) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.sidebar-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  const sb = document.getElementById('sb-' + tab);
  if (sb) sb.classList.add('active');
  if (tab === 'queue') loadVideos();
  if (tab === 'analytics') updateAnalytics();
}

// ===== DATETIME =====
function setMinDateTime() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  document.getElementById('scheduleTime').min = now.toISOString().slice(0, 16);
}

// ===== DRAG & DROP =====
function setupDragDrop() {
  const dz = document.getElementById('dropzone');
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
  dz.addEventListener('drop', e => {
    e.preventDefault();
    dz.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) {
      document.getElementById('videoFile').files = e.dataTransfer.files;
      updateDropzone(file);
    } else {
      showToast('Please drop a valid video file', 'error');
    }
  });
}

function handleFileSelect(input) {
  const file = input.files[0];
  if (file) updateDropzone(file);
}

function updateDropzone(file) {
  const dzInner = document.getElementById('dzInner');
  const size = (file.size / (1024 * 1024)).toFixed(1);
  dzInner.innerHTML = `
    <div class="dz-icon" style="color:#10B981">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="20 6 9 17 4 12"/></svg>
    </div>
    <p class="dz-text" style="color:#10B981;font-weight:600">${file.name}</p>
    <p class="dz-hint">${size} MB · ${file.type}</p>
  `;
}

// ===== UPLOAD =====
async function handleUpload(e) {
  e.preventDefault();

  const file = document.getElementById('videoFile').files[0];
  if (!file) { showToast('Please select a video file', 'error'); return; }

  const btn = document.getElementById('submitBtn');
  const progress = document.getElementById('uploadProgress');
  const upFill = document.getElementById('upFill');
  const upLabel = document.getElementById('upLabel');

  btn.disabled = true;
  btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:spin 1s linear infinite"><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg> Scheduling...`;
  progress.style.display = 'block';

  // Simulate progress
  let prog = 0;
  const interval = setInterval(() => {
    prog = Math.min(prog + Math.random() * 15, 90);
    upFill.style.width = prog + '%';
    upLabel.textContent = prog < 40 ? 'Uploading to Drive...' : 'Saving schedule...';
  }, 400);

  try {
    const formData = new FormData();
    formData.append('title', document.getElementById('videoTitle').value);
    formData.append('description', document.getElementById('videoDesc').value);
    formData.append('tags', document.getElementById('videoTags').value);
    formData.append('scheduled_time', new Date(document.getElementById('scheduleTime').value).toISOString());
    formData.append('privacy_status', document.getElementById('privacyStatus').value);
    formData.append('is_short', document.getElementById('isShort').checked);
    formData.append('repeat_weekly', document.getElementById('repeatWeekly').checked);
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
    const data = await res.json();

    clearInterval(interval);

    if (res.ok && data.video_id) {
      upFill.style.width = '100%';
      upLabel.textContent = 'Done!';
      await new Promise(r => setTimeout(r, 500));
      showModal(`Video "${document.getElementById('videoTitle').value}" has been scheduled successfully!`);
      e.target.reset();
      resetDropzone();
      loadVideos();
    } else {
      throw new Error(data.detail || data.error || 'Upload failed');
    }
  } catch (err) {
    clearInterval(interval);
    showToast('Upload failed: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12l7 7 7-7"/></svg> Schedule Video`;
    setTimeout(() => { progress.style.display = 'none'; upFill.style.width = '0%'; }, 1000);
  }
}

function resetDropzone() {
  document.getElementById('dzInner').innerHTML = `
    <div class="dz-icon">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    </div>
    <p class="dz-text">Drop your video here or <span>browse files</span></p>
    <p class="dz-hint">MP4, MOV, AVI — Max 2GB</p>
  `;
}

// ===== LOAD VIDEOS =====
async function loadVideos() {
  try {
    const res = await fetch(`${API_BASE}/videos`);
    if (!res.ok) throw new Error('API error');
    allVideos = await res.json();
    renderVideoList();
    updateStats();
    updateHeroCard();
  } catch (err) {
    // Use demo data if API is offline
    if (allVideos.length === 0) {
      allVideos = getDemoVideos();
      renderVideoList();
      updateStats();
      updateHeroCard();
    }
  }
}

function getDemoVideos() {
  const now = new Date();
  const future = new Date(now.getTime() + 3600000);
  const past = new Date(now.getTime() - 86400000);
  return [
    { id: 1, title: 'How to Build a SaaS in 30 Days', description: 'Step by step guide', tags: 'saas, startup', privacy_status: 'public', scheduled_time: future.toISOString(), status: 'Pending', is_short: false },
    { id: 2, title: 'My Morning Routine 2025', description: 'Productivity tips', tags: 'routine, productivity', privacy_status: 'public', scheduled_time: past.toISOString(), status: 'Uploaded', is_short: false },
    { id: 3, title: 'Top 10 VS Code Extensions', description: 'Extensions I use daily', tags: 'vscode, coding', privacy_status: 'public', scheduled_time: past.toISOString(), status: 'Failed', is_short: true },
  ];
}

// ===== RENDER VIDEO LIST =====
function renderVideoList() {
  const list = document.getElementById('videoList');
  const empty = document.getElementById('emptyState');

  const filtered = currentFilter === 'all' ? allVideos : allVideos.filter(v => v.status === currentFilter);

  if (filtered.length === 0) {
    list.innerHTML = '';
    list.appendChild(empty);
    empty.style.display = 'block';
    return;
  }

  empty.style.display = 'none';
  list.innerHTML = filtered.map(video => `
    <div class="video-card" id="vc-${video.id}">
      <div class="vc-thumb">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M9.5 7.5L16.5 12L9.5 16.5V7.5Z" fill="white" opacity="0.8"/></svg>
      </div>
      <div class="vc-info">
        <div class="vc-title">${escHtml(video.title)}</div>
        <div class="vc-meta">
          <span>${formatDate(video.scheduled_time)}</span>
          <span>${video.privacy_status}</span>
          ${video.is_short ? '<span>🩳 Short</span>' : ''}
          <span class="badge-status badge-${video.status}">${statusIcon(video.status)} ${video.status}</span>
        </div>
      </div>
      <div class="vc-actions">
        ${video.status === 'Pending' ? `<button class="vc-btn" onclick="uploadNow(${video.id})">Upload Now</button>` : ''}
      </div>
    </div>
  `).join('');
}

function filterQueue(filter, btn) {
  currentFilter = filter;
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  renderVideoList();
}

// ===== UPLOAD NOW =====
async function uploadNow(videoId) {
  showToast('Triggering upload...', 'info');
  try {
    const res = await fetch(`${API_BASE}/upload-now/${videoId}`, { method: 'POST' });
    const data = await res.json();
    if (data.message) {
      showToast('Upload triggered successfully!', 'success');
      setTimeout(loadVideos, 2000);
    } else {
      showToast(data.error || 'Failed to trigger upload', 'error');
    }
  } catch (err) {
    showToast('Could not reach the server', 'error');
  }
}

// ===== RUN SCHEDULER =====
async function triggerScheduler() {
  showToast('Running scheduler...', 'info');
  try {
    const res = await fetch(`${API_BASE}/run-scheduler`);
    const data = await res.json();
    showToast('Scheduler executed!', 'success');
    setTimeout(loadVideos, 2000);
  } catch (err) {
    showToast('Could not reach the server', 'error');
  }
}

// ===== CONNECT GOOGLE =====
function connectGoogle() {
  showToast('Redirecting to Google OAuth...', 'info');
  setTimeout(() => window.open(`${API_BASE}/login`, '_blank'), 500);
}

// ===== STATS =====
function updateStats() {
  const total = allVideos.length;
  const uploaded = allVideos.filter(v => v.status === 'Uploaded').length;
  const pending = allVideos.filter(v => v.status === 'Pending').length;
  const failed = allVideos.filter(v => v.status === 'Failed').length;

  animateNum('statTotal', total);
  animateNum('statUploaded', uploaded);
  animateNum('statPending', pending);

  const badge = document.getElementById('queueBadge');
  badge.textContent = pending;
  badge.style.display = pending > 0 ? 'inline-block' : 'none';
}

function updateAnalytics() {
  const total = allVideos.length;
  const uploaded = allVideos.filter(v => v.status === 'Uploaded').length;
  const pending = allVideos.filter(v => v.status === 'Pending').length;
  const failed = allVideos.filter(v => v.status === 'Failed').length;

  animateNum('acTotal', total);
  animateNum('acUploaded', uploaded);
  animateNum('acPending', pending);
  animateNum('acFailed', failed);

  drawDonut(uploaded, pending, failed);

  const recentList = document.getElementById('recentList');
  const recent = [...allVideos].reverse().slice(0, 5);
  recentList.innerHTML = recent.map(v => `
    <div class="recent-item">
      <div class="vc-thumb" style="width:36px;height:28px;border-radius:6px;flex-shrink:0">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M9.5 7.5L16.5 12L9.5 16.5V7.5Z" fill="white" opacity="0.8"/></svg>
      </div>
      <span class="ri-title">${escHtml(v.title)}</span>
      <span class="badge-status badge-${v.status}" style="font-size:0.68rem">${v.status}</span>
    </div>
  `).join('');
}

function drawDonut(uploaded, pending, failed) {
  const canvas = document.getElementById('donutChart');
  const ctx = canvas.getContext('2d');
  const total = uploaded + pending + failed || 1;
  const data = [
    { val: uploaded, color: '#10B981', label: 'Published' },
    { val: pending, color: '#F59E0B', label: 'Pending' },
    { val: failed, color: '#FF0040', label: 'Failed' },
  ];

  ctx.clearRect(0, 0, 200, 200);
  let startAngle = -Math.PI / 2;
  const cx = 100, cy = 100, r = 75, inner = 45;

  data.forEach(d => {
    if (d.val === 0) return;
    const slice = (d.val / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, startAngle, startAngle + slice);
    ctx.closePath();
    ctx.fillStyle = d.color;
    ctx.fill();
    startAngle += slice;
  });

  // Inner hole
  ctx.beginPath();
  ctx.arc(cx, cy, inner, 0, Math.PI * 2);
  ctx.fillStyle = '#111118';
  ctx.fill();

  // Center text
  ctx.fillStyle = '#f0f0f8';
  ctx.font = 'bold 22px Space Grotesk, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(total, cx, cy - 6);
  ctx.font = '12px Inter, sans-serif';
  ctx.fillStyle = '#5a5a7a';
  ctx.fillText('total', cx, cy + 12);

  // Legend
  const legend = document.getElementById('donutLegend');
  legend.innerHTML = data.map(d => `
    <div class="legend-item">
      <span class="legend-dot" style="background:${d.color}"></span>
      <span style="color:#9090b0">${d.label}</span>
      <span style="margin-left:auto;font-weight:600">${d.val}</span>
    </div>
  `).join('');
}

// ===== HERO CARD =====
function updateHeroCard() {
  const pending = allVideos.filter(v => v.status === 'Pending').sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time));
  const upcoming = document.getElementById('heroUpcoming');

  if (pending.length > 0) {
    const next = pending[0];
    upcoming.querySelector('.uv-title').textContent = next.title;
    upcoming.querySelector('.uv-time').textContent = formatDate(next.scheduled_time);
    const now = Date.now();
    const sched = new Date(next.scheduled_time).getTime();
    const pct = Math.max(0, Math.min(100, ((now - (sched - 86400000)) / 86400000) * 100));
    document.getElementById('heroProgress').style.width = pct + '%';
  }
}

// ===== HELPERS =====
function formatDate(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function statusIcon(status) {
  if (status === 'Uploaded') return '✅';
  if (status === 'Failed') return '❌';
  return '⏳';
}

function escHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function animateNum(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = parseInt(el.textContent) || 0;
  const duration = 600;
  const startTime = performance.now();
  const update = (now) => {
    const progress = Math.min((now - startTime) / duration, 1);
    el.textContent = Math.round(start + (target - start) * progress);
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

// ===== TOAST =====
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  const icons = {
    success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
    error: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FF0040" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    info: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9333EA" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
  };
  toast.className = `toast ${type}`;
  toast.innerHTML = `${icons[type] || icons.info}<span style="flex:1;font-size:0.875rem">${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ===== MODAL =====
function showModal(msg) {
  document.getElementById('modalMsg').textContent = msg;
  document.getElementById('successModal').style.display = 'flex';
}
function closeModal() {
  document.getElementById('successModal').style.display = 'none';
}

// Add spin keyframe dynamically
const style = document.createElement('style');
style.textContent = '@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }';
document.head.appendChild(style);
