/**
 * NutriAI — Frontend Application Logic
 * Nutrition Agentic AI | IBM Granite via watsonx.ai
 */

'use strict';

// ── State ─────────────────────────────────────────────────────────────────────
const state = {
  currentPlan: null,
  currentMdFilename: null,
  userProfile: {},
  chatContext: {},
};

// ── DOM helpers ───────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const hide = (id) => $( id)?.classList.add('hidden');
const show = (id) => $(id)?.classList.remove('hidden');

// ══════════════════════════════════════════════════════════════════════════════
// NAVIGATION
// ══════════════════════════════════════════════════════════════════════════════
function switchPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const panel = document.getElementById(`panel-${name}`);
  if (panel) panel.classList.add('active');
  const btn = document.querySelector(`[data-panel="${name}"]`);
  if (btn) btn.classList.add('active');

  if (name === 'saved') loadSavedPlans();
}

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => switchPanel(btn.dataset.panel));
});

// ══════════════════════════════════════════════════════════════════════════════
// LIVE BMI CALCULATION
// ══════════════════════════════════════════════════════════════════════════════
const bmiInputs = ['weight_kg', 'height_cm'];
bmiInputs.forEach(id => {
  document.getElementById(id)?.addEventListener('input', updateBMI);
});

async function updateBMI() {
  const weight = parseFloat($('weight_kg')?.value);
  const height = parseFloat($('height_cm')?.value);
  const badge = $('bmiDisplay');
  if (!badge) return;

  if (!weight || !height || weight <= 0 || height <= 0) {
    badge.classList.add('hidden');
    return;
  }

  try {
    const resp = await fetch('/api/bmi', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weight_kg: weight, height_cm: height }),
    });
    const data = await resp.json();
    if (data.bmi) {
      const cat = data.category.toLowerCase().replace(' ', '');
      badge.className = `bmi-badge ${cat}`;
      badge.innerHTML = `<span>⚖️</span> <span>BMI: <strong>${data.bmi}</strong> — ${data.category}</span>`;
      badge.classList.remove('hidden');
    }
  } catch (_) {
    // graceful degradation — local fallback
    const bmi = weight / Math.pow(height / 100, 2);
    let cat = 'Normal weight';
    if (bmi < 18.5) cat = 'Underweight';
    else if (bmi >= 25 && bmi < 30) cat = 'Overweight';
    else if (bmi >= 30) cat = 'Obese';
    badge.className = `bmi-badge ${cat.toLowerCase().replace(' ', '')}`;
    badge.innerHTML = `<span>⚖️</span> <span>BMI: <strong>${bmi.toFixed(1)}</strong> — ${cat}</span>`;
    badge.classList.remove('hidden');
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// MEDICAL CHECKBOXES
// ══════════════════════════════════════════════════════════════════════════════
$('medNone')?.addEventListener('change', (e) => {
  if (e.target.checked) {
    document.querySelectorAll('#medicalCheckboxes input[type=checkbox]').forEach(cb => {
      if (cb.id !== 'medNone') cb.checked = false;
    });
  }
});

document.querySelectorAll('#medicalCheckboxes input[type=checkbox]:not(#medNone)').forEach(cb => {
  cb.addEventListener('change', () => {
    if (cb.checked) $('medNone').checked = false;
  });
});

function getMedicalHistory() {
  const checked = [];
  document.querySelectorAll('#medicalCheckboxes input[type=checkbox]:not(#medNone):checked').forEach(cb => {
    checked.push(cb.value);
  });
  const custom = $('medical_custom')?.value?.trim();
  if (custom) checked.push(custom);
  if (checked.length === 0 || $('medNone')?.checked) return 'None reported';
  return checked.join(', ');
}

// ══════════════════════════════════════════════════════════════════════════════
// PLAN GENERATION
// ══════════════════════════════════════════════════════════════════════════════
$('profileForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  await generatePlan();
});

async function generatePlan() {
  if (!validateForm()) return;

  const profile = collectProfile();
  state.userProfile = profile;
  state.chatContext = {
    name: profile.name,
    age: profile.age,
    diet_preference: profile.diet_preference,
    medical_history: profile.medical_history,
  };

  showLoadingState();
  animateLoadingSteps();

  try {
    const resp = await fetch('/api/generate-plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    });
    const data = await resp.json();

    if (data.success) {
      state.currentPlan = data.plan;
      state.currentMdFilename = data.md_filename;
      showResultState(data);
    } else {
      showErrorState(data.error || 'Failed to generate plan. Please try again.');
    }
  } catch (err) {
    showErrorState(`Network error: ${err.message}. Make sure the server is running.`);
  }
}

function collectProfile() {
  return {
    name: $('name')?.value?.trim() || '',
    age: parseInt($('age')?.value) || '',
    gender: $('gender')?.value || 'female',
    diet_preference: $('diet_preference')?.value || 'veg',
    medical_history: getMedicalHistory(),
    activity_level: $('activity_level')?.value || 'moderate',
    health_goal: $('health_goal')?.value || 'general wellness',
    location_city: $('location_city')?.value?.trim() || '',
    location_country: $('location_country')?.value?.trim() || '',
    allergies: $('allergies')?.value?.trim() || 'None',
    weight_kg: parseFloat($('weight_kg')?.value) || '',
    height_cm: parseFloat($('height_cm')?.value) || '',
  };
}

function validateForm() {
  let valid = true;
  const required = {
    name: 'Full Name',
    age: 'Age',
    location_city: 'City',
    location_country: 'Country',
  };
  for (const [id, label] of Object.entries(required)) {
    const el = $(id);
    if (!el?.value?.trim()) {
      el?.classList.add('error');
      el?.focus();
      alert(`Please fill in: ${label}`);
      valid = false;
      break;
    } else {
      el?.classList.remove('error');
    }
  }
  const age = parseInt($('age')?.value);
  if (valid && (isNaN(age) || age < 5 || age > 110)) {
    alert('Please enter a valid age between 5 and 110.');
    valid = false;
  }
  return valid;
}

// ── Loading state ──────────────────────────────────────────────────────────
function showLoadingState() {
  hide('welcomeState');
  hide('resultState');
  hide('errorState');
  show('loadingState');
  $('generateBtn').disabled = true;
  $('generateBtn').textContent = '⏳ Generating…';
}

let stepTimer = null;
function animateLoadingSteps() {
  const steps = ['step1', 'step2', 'step3', 'step4', 'step5'];
  let i = 0;
  // Reset all
  steps.forEach(s => { const el = $(s); if (el) { el.className = 'step'; } });
  $('step1')?.classList.add('active');

  stepTimer = setInterval(() => {
    if (i < steps.length - 1) {
      $(steps[i])?.classList.remove('active');
      $(steps[i])?.classList.add('done');
      i++;
      $(steps[i])?.classList.add('active');
    } else {
      clearInterval(stepTimer);
    }
  }, 1400);
}

function stopLoadingAnimation() {
  clearInterval(stepTimer);
}

// ── Result state ───────────────────────────────────────────────────────────
function showResultState(data) {
  stopLoadingAnimation();
  hide('loadingState');
  hide('welcomeState');
  hide('errorState');

  // Stats bar
  const summary = data.profile_summary || {};
  const statsHtml = buildStatsBar(summary);
  $('statsBar').innerHTML = statsHtml;

  // Plan title
  $('planTitle').textContent = `${summary.name || 'Your'}'s Nutrition Plan`;

  // Render markdown
  $('planContent').innerHTML = renderMarkdown(data.plan || '');

  show('resultState');
  $('generateBtn').disabled = false;
  $('generateBtn').innerHTML = '<span class="btn-icon">✨</span> Regenerate Plan';
}

function buildStatsBar(summary) {
  const chips = [];
  if (summary.name) chips.push(stat('👤', 'Name', summary.name));
  if (summary.age) chips.push(stat('🎂', 'Age', `${summary.age} yrs`));
  if (summary.diet) chips.push(stat('🥦', 'Diet', capitalize(summary.diet)));
  if (summary.bmi) chips.push(stat('⚖️', 'BMI', `${summary.bmi} (${summary.bmi_category})`));
  if (summary.tdee) chips.push(stat('🔥', 'TDEE', `${summary.tdee} kcal/day`));
  if (summary.goal) chips.push(stat('🎯', 'Goal', capitalize(summary.goal)));
  return chips.join('');
}

function stat(icon, label, value) {
  return `<div class="stat-chip">
    <span>${icon}</span>
    <div><div class="stat-label">${label}</div><div class="stat-value">${value}</div></div>
  </div>`;
}

// ── Error state ────────────────────────────────────────────────────────────
function showErrorState(msg) {
  stopLoadingAnimation();
  hide('loadingState');
  hide('welcomeState');
  hide('resultState');
  $('errorMsg').textContent = msg;
  show('errorState');
  $('generateBtn').disabled = false;
  $('generateBtn').innerHTML = '<span class="btn-icon">✨</span> Generate My Nutrition Plan';
}

function resetUI() {
  hide('resultState');
  hide('errorState');
  hide('loadingState');
  show('welcomeState');
  $('generateBtn').disabled = false;
  $('generateBtn').innerHTML = '<span class="btn-icon">✨</span> Generate My Nutrition Plan';
}

// ── Download plan ──────────────────────────────────────────────────────────
function downloadPlan() {
  if (!state.currentMdFilename) {
    // Fallback: client-side blob download
    const blob = new Blob([state.currentPlan || ''], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nutrition_plan.md';
    a.click();
    URL.revokeObjectURL(url);
    return;
  }
  window.location.href = `/api/download-plan/${state.currentMdFilename}`;
}

function copyPlan() {
  if (!state.currentPlan) return;
  navigator.clipboard.writeText(state.currentPlan).then(() => {
    const btn = document.querySelector('[onclick="copyPlan()"]');
    const orig = btn.textContent;
    btn.textContent = '✅ Copied!';
    setTimeout(() => { btn.textContent = orig; }, 2000);
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// CHAT / Q&A
// ══════════════════════════════════════════════════════════════════════════════
async function sendMessage() {
  const input = $('chatInput');
  const question = input?.value?.trim();
  if (!question) return;

  input.value = '';
  hide('quickQuestions');

  appendMessage('user', question, '🧑');
  const thinkingId = appendThinkingMessage();
  $('sendBtn').disabled = true;

  try {
    const resp = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, context: state.chatContext }),
    });
    const data = await resp.json();
    removeMessage(thinkingId);

    if (data.success) {
      appendMessage('bot', data.answer, '🥗');
    } else {
      appendMessage('bot', `⚠️ ${data.error || 'Something went wrong. Please try again.'}`, '⚠️');
    }
  } catch (err) {
    removeMessage(thinkingId);
    appendMessage('bot', `❌ Network error: ${err.message}`, '❌');
  } finally {
    $('sendBtn').disabled = false;
    input.focus();
  }
}

function askQuick(question) {
  const input = $('chatInput');
  if (input) input.value = question;
  sendMessage();
}

function appendMessage(role, text, avatar) {
  const messages = $('chatMessages');
  const id = `msg-${Date.now()}`;
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.id = id;
  div.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-bubble">${renderMarkdown(text)}</div>
  `;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return id;
}

function appendThinkingMessage() {
  const messages = $('chatMessages');
  const id = `thinking-${Date.now()}`;
  const div = document.createElement('div');
  div.className = 'message bot thinking';
  div.id = id;
  div.innerHTML = `
    <div class="message-avatar">🥗</div>
    <div class="message-bubble">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>
  `;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return id;
}

function removeMessage(id) {
  document.getElementById(id)?.remove();
}

// ══════════════════════════════════════════════════════════════════════════════
// SAVED PLANS
// ══════════════════════════════════════════════════════════════════════════════
async function loadSavedPlans() {
  const list = $('savedPlansList');
  if (!list) return;
  list.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:40px">Loading…</p>';

  try {
    const resp = await fetch('/api/plans');
    const data = await resp.json();

    if (!data.plans?.length) {
      list.innerHTML = `
        <div class="empty-state">
          <span>📂</span>
          <p>No plans saved yet. Generate your first nutrition plan!</p>
          <button class="btn btn-primary btn-sm" onclick="switchPanel('plan')">Create Plan</button>
        </div>`;
      return;
    }

    list.innerHTML = data.plans.map(p => {
      const date = new Date(p.modified * 1000).toLocaleString();
      return `
        <div class="plan-item">
          <div class="plan-item-info">
            <div class="plan-item-name">📄 ${p.filename}</div>
            <div class="plan-item-meta">${date} · ${p.size_kb} KB</div>
          </div>
          <div class="plan-item-actions">
            <a class="btn btn-outline btn-sm" href="/api/download-plan/${encodeURIComponent(p.filename)}">⬇️ Download</a>
          </div>
        </div>`;
    }).join('');
  } catch (_) {
    list.innerHTML = '<p style="text-align:center;color:var(--red);padding:40px">Failed to load plans.</p>';
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// MARKDOWN RENDERER (lightweight, no external deps)
// ══════════════════════════════════════════════════════════════════════════════
function renderMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);

  // Headings
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Horizontal rule
  html = html.replace(/^---$/gm, '<hr>');

  // Blockquote
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');
  // Merge consecutive blockquotes
  html = html.replace(/<\/blockquote>\n<blockquote>/g, '\n');

  // Bold & italic
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Tables
  html = renderTables(html);

  // Unordered lists
  html = renderLists(html);

  // Paragraphs (double newline)
  html = html.replace(/\n\n+/g, '</p><p>');
  html = html.replace(/^(?!<[hbtupo])/m, '<p>');
  html = html + '</p>';

  // Single newlines inside paragraphs → <br>
  html = html.replace(/(?<!>)\n(?!<)/g, '<br>');

  // Clean up empty paragraphs
  html = html.replace(/<p><\/p>/g, '');
  html = html.replace(/<p>(<h[1-6]|<hr|<blockquote|<ul|<ol|<table)/g, '$1');
  html = html.replace(/(<\/h[1-6]>|<\/ul>|<\/ol>|<\/table>|<hr>|<\/blockquote>)<\/p>/g, '$1');

  return html;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderTables(html) {
  return html.replace(/((?:^[^\n]+\|[^\n]*\n)+)/gm, (block) => {
    const rows = block.trim().split('\n');
    if (rows.length < 2) return block;
    const isSep = (r) => /^[\s|:-]+$/.test(r);
    let out = '<table>';
    let inBody = false;
    for (let i = 0; i < rows.length; i++) {
      if (isSep(rows[i])) { inBody = true; continue; }
      const cells = rows[i].split('|').map(c => c.trim()).filter(c => c !== '');
      const tag = (!inBody && i === 0) ? 'th' : 'td';
      out += '<tr>' + cells.map(c => `<${tag}>${c}</${tag}>`).join('') + '</tr>';
    }
    out += '</table>';
    return out;
  });
}

function renderLists(html) {
  // Convert markdown bullet lines to <ul><li> blocks
  html = html.replace(/((?:^[-*•] .+\n?)+)/gm, (block) => {
    const items = block.trim().split('\n')
      .map(line => line.replace(/^[-*•]\s+/, '').trim())
      .filter(Boolean);
    return '<ul>' + items.map(i => `<li>${i}</li>`).join('') + '</ul>';
  });
  // Numbered lists
  html = html.replace(/((?:^\d+\. .+\n?)+)/gm, (block) => {
    const items = block.trim().split('\n')
      .map(line => line.replace(/^\d+\.\s+/, '').trim())
      .filter(Boolean);
    return '<ol>' + items.map(i => `<li>${i}</li>`).join('') + '</ol>';
  });
  return html;
}

// ══════════════════════════════════════════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════════════════════════════════════════
function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Health check (shows connected status)
  fetch('/api/health').then(r => r.json()).then(d => {
    console.log(`✅ NutriAI connected | Model: ${d.model}`);
  }).catch(() => {
    console.warn('⚠️ Backend not reachable');
  });
});
