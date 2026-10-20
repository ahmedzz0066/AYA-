const DEFAULTS = {
  deepgramKey: '', anthropicKey: '', style: 'msa', glossary: '', model: '', sttModel: '',
  fontSize: 28, bottom: 14, showOriginal: false
};
const $ = (id) => document.getElementById(id);
const fields = Object.keys(DEFAULTS);
let settings = { ...DEFAULTS };
let running = false;

function renderStatus(s = {}) {
  const state = s.state || 'idle';
  running = state === 'running' || state === 'starting';
  $('status').className = 'status ' + state;
  $('status').textContent = s.message || 'متوقف';
  $('toggle').textContent = running ? '■ إيقاف الترجمة' : '▶ ابدأ الترجمة على هذا التبويب';
  $('toggle').classList.toggle('stop', running);
  $('toggle').disabled = false;
}

function renderLabels() {
  $('fontSizeVal').textContent = settings.fontSize + 'px';
  $('bottomVal').textContent = settings.bottom + '%';
}

async function init() {
  settings = { ...DEFAULTS, ...(await chrome.storage.local.get(DEFAULTS)) };
  for (const f of fields) {
    const el = $(f);
    if (el.type === 'checkbox') el.checked = settings[f];
    else el.value = settings[f];
    el.addEventListener('input', () => {
      settings[f] = el.type === 'checkbox' ? el.checked : el.type === 'range' ? Number(el.value) : el.value.trim();
      chrome.storage.local.set({ [f]: settings[f] });
      renderLabels();
    });
  }
  renderLabels();
  $('keys').open = !settings.deepgramKey || !settings.anthropicKey;
  renderStatus(await chrome.runtime.sendMessage({ type: 'getState' }));
}

$('toggle').addEventListener('click', async () => {
  $('toggle').disabled = true;
  if (running) {
    await chrome.runtime.sendMessage({ type: 'stop' });
    return renderStatus({ state: 'idle', message: 'متوقف' });
  }
  if (!settings.deepgramKey || !settings.anthropicKey) {
    $('keys').open = true;
    $('toggle').disabled = false;
    return renderStatus({ state: 'error', message: 'أدخل مفتاحَي Deepgram و Anthropic أولًا.' });
  }
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const streamId = await chrome.tabCapture.getMediaStreamId({ targetTabId: tab.id });
    const res = await chrome.runtime.sendMessage({ type: 'start', tabId: tab.id, streamId, settings });
    if (!res?.ok) throw new Error(res?.error || 'unknown');
    renderStatus({ state: 'starting', message: 'جارٍ البدء...' });
  } catch (e) {
    renderStatus({ state: 'error', message: 'تعذّر البدء: ' + e.message });
  }
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'status') renderStatus(msg);
});

init();
