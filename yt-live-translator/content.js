(() => {
  const CLEAR_AFTER_MS = 7000;
  let opts = { fontSize: 28, bottom: 14, showOriginal: false };
  let overlay, trEl, arEl;
  let lines = [];
  let clearTimer;

  function loadOpts() {
    chrome.storage.local.get(opts, (s) => {
      opts = { ...opts, ...s };
      applyStyle();
    });
  }

  function applyStyle() {
    if (!overlay) return;
    overlay.style.setProperty('--ytlt-size', opts.fontSize + 'px');
    overlay.style.setProperty('--ytlt-bottom', opts.bottom + '%');
  }

  function ensureOverlay() {
    if (overlay && overlay.isConnected) return;
    const host = document.querySelector('#movie_player') || document.querySelector('.html5-video-player') || document.body;
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'ytlt-overlay';
      trEl = document.createElement('div');
      trEl.className = 'ytlt-tr';
      arEl = document.createElement('div');
      arEl.className = 'ytlt-ar';
      overlay.append(trEl, arEl);
    }
    host.appendChild(overlay);
    applyStyle();
  }

  function show() {
    overlay.classList.add('ytlt-visible');
    clearTimeout(clearTimer);
    clearTimer = setTimeout(() => {
      lines = [];
      arEl.textContent = '';
      trEl.textContent = '';
      overlay.classList.remove('ytlt-visible');
    }, CLEAR_AFTER_MS);
  }

  function render(tr) {
    arEl.textContent = lines.join('\n');
    arEl.style.whiteSpace = 'pre-line';
    trEl.textContent = opts.showOriginal ? tr || '' : '';
    show();
  }

  function onSubtitle(msg) {
    // Failed translation: show the Turkish text so the viewer still sees something.
    const text = msg.ar || msg.tr;
    lines.push(text);
    while (lines.length > 2 || lines.join(' ').length > 130) {
      if (lines.length === 1) break;
      lines.shift();
    }
    render(msg.tr);
  }

  function showError(message) {
    ensureOverlay();
    lines = [];
    arEl.textContent = '';
    trEl.textContent = '⚠ ' + message;
    show();
  }

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === 'subtitle') {
      ensureOverlay();
      onSubtitle(msg);
    } else if (msg.type === 'interim') {
      if (!opts.showOriginal) return;
      ensureOverlay();
      trEl.textContent = msg.tr;
      show();
    } else if (msg.type === 'status' && msg.state === 'error') {
      showError(msg.message);
    } else if (msg.type === 'status' && msg.state === 'idle' && overlay) {
      lines = [];
      overlay.classList.remove('ytlt-visible');
    }
  });

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local') return;
    for (const [k, v] of Object.entries(changes)) if (k in opts) opts[k] = v.newValue;
    applyStyle();
  });

  loadOpts();
})();
