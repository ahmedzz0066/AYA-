async function getState() {
  const { yt = {} } = await chrome.storage.session.get('yt');
  return yt;
}

async function setState(patch) {
  const yt = { ...(await getState()), ...patch };
  await chrome.storage.session.set({ yt });
  return yt;
}

async function ensureOffscreen() {
  try {
    await chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['USER_MEDIA'],
      justification: 'Capture tab audio for live translation'
    });
  } catch (e) {
    if (!String(e.message).includes('single offscreen')) throw e;
  }
}

async function startSession({ tabId, streamId, settings }) {
  await ensureOffscreen();
  await setState({ tabId, state: 'starting', message: 'جارٍ البدء...' });
  chrome.runtime.sendMessage({ target: 'offscreen', type: 'start', streamId, settings }).catch(() => {});
}

async function stopSession() {
  chrome.runtime.sendMessage({ target: 'offscreen', type: 'stop' }).catch(() => {});
  await setState({ state: 'idle', message: 'متوقف' });
  setTimeout(() => chrome.offscreen.closeDocument().catch(() => {}), 300);
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.target === 'offscreen') return;

  if (msg.type === 'start') {
    startSession(msg).then(() => sendResponse({ ok: true }), (e) => sendResponse({ ok: false, error: e.message }));
    return true;
  }
  if (msg.type === 'stop') {
    stopSession().then(() => sendResponse({ ok: true }));
    return true;
  }
  if (msg.type === 'getState') {
    getState().then(sendResponse);
    return true;
  }

  if (['subtitle', 'interim', 'status'].includes(msg.type) && sender.url?.endsWith('offscreen.html')) {
    (async () => {
      if (msg.type === 'status') {
        await setState({ state: msg.state, message: msg.message });
        if (msg.state === 'error') chrome.offscreen.closeDocument().catch(() => {});
      }
      const { tabId } = await getState();
      if (tabId) chrome.tabs.sendMessage(tabId, msg).catch(() => {});
    })();
  }
});

chrome.tabs.onRemoved.addListener(async (tabId) => {
  const { tabId: active } = await getState();
  if (tabId === active) stopSession();
});
