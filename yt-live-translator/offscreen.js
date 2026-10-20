// Runs the whole live pipeline: tab audio -> Deepgram (Turkish STT) -> Claude (Arabic translation).

let cfg = null;
let active = false;
let media = null;
let playCtx = null;
let anaCtx = null;
let ws = null;
let everOpened = false;
let retries = 0;

let pending = [];
let flushTimer = null;
let interimText = '';
let translateChain = Promise.resolve();
const history = [];

const STYLES = {
  msa: 'simple, natural Modern Standard Arabic (فصحى مبسطة), the kind used in subtitled Turkish TV dramas',
  levantine: 'light, natural white Levantine (Shami) dialect, like Arabic-dubbed Turkish series',
  white: 'a neutral white Arabic dialect (لهجة بيضاء) that every Arab viewer understands easily'
};

function send(msg) {
  chrome.runtime.sendMessage(msg).catch(() => {});
}

function status(state, message) {
  send({ type: 'status', state, message });
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.target !== 'offscreen') return;
  if (msg.type === 'start') start(msg);
  if (msg.type === 'stop') stop();
});

async function start({ streamId, settings }) {
  await stop(true);
  cfg = settings;
  active = true;
  everOpened = false;
  retries = 0;
  history.length = 0;
  status('starting', 'جارٍ التقاط صوت التبويب...');

  try {
    media = await navigator.mediaDevices.getUserMedia({
      audio: { mandatory: { chromeMediaSource: 'tab', chromeMediaSourceId: streamId } },
      video: false
    });

    // Keep the tab audible: capturing a tab mutes it unless we play it back ourselves.
    playCtx = new AudioContext();
    playCtx.createMediaStreamSource(media).connect(playCtx.destination);

    anaCtx = new AudioContext({ sampleRate: 16000 });
    await anaCtx.audioWorklet.addModule('pcm-worklet.js');
    const node = new AudioWorkletNode(anaCtx, 'pcm-processor');
    const mute = anaCtx.createGain();
    mute.gain.value = 0;
    anaCtx.createMediaStreamSource(media).connect(node);
    node.connect(mute).connect(anaCtx.destination);
    node.port.onmessage = (e) => {
      if (ws && ws.readyState === WebSocket.OPEN) ws.send(e.data);
    };
  } catch (e) {
    await stop(true);
    status('error', 'تعذّر التقاط صوت التبويب: ' + e.message);
    return;
  }

  connect();
}

function connect() {
  const params = new URLSearchParams({
    model: cfg.sttModel || 'nova-2',
    language: 'tr',
    encoding: 'linear16',
    sample_rate: '16000',
    channels: '1',
    interim_results: 'true',
    smart_format: 'true',
    punctuate: 'true',
    endpointing: '400',
    utterance_end_ms: '1200'
  });
  ws = new WebSocket('wss://api.deepgram.com/v1/listen?' + params, ['token', cfg.deepgramKey]);

  ws.onopen = () => {
    everOpened = true;
    retries = 0;
    status('running', 'الترجمة الفورية تعمل');
  };

  ws.onmessage = (e) => {
    let m;
    try { m = JSON.parse(e.data); } catch { return; }
    if (m.type === 'UtteranceEnd') return flush();
    if (m.type !== 'Results') return;
    const text = (m.channel?.alternatives?.[0]?.transcript || '').trim();
    if (m.is_final) {
      interimText = '';
      if (text) onFinal(text, m.speech_final);
    } else {
      interimText = text;
      pushInterim();
    }
  };

  ws.onclose = () => {
    if (!active) return;
    if (!everOpened) {
      stop();
      status('error', 'فشل الاتصال بـ Deepgram. تأكد من صحة المفتاح والاتصال بالإنترنت.');
    } else if (retries++ < 5) {
      status('starting', 'إعادة الاتصال...');
      setTimeout(() => active && connect(), 1000 * retries);
    } else {
      stop();
      status('error', 'انقطع الاتصال بخدمة التعرّف على الصوت.');
    }
  };
}

function pushInterim() {
  const tr = [...pending, interimText].filter(Boolean).join(' ');
  if (tr) send({ type: 'interim', tr });
}

function onFinal(text, speechFinal) {
  pending.push(text);
  clearTimeout(flushTimer);
  if (speechFinal || pending.join(' ').length > 140) flush();
  else {
    pushInterim();
    flushTimer = setTimeout(flush, 1500);
  }
}

function flush() {
  clearTimeout(flushTimer);
  const text = pending.join(' ').trim();
  pending = [];
  if (!text) return;
  translateChain = translateChain.then(() => translate(text)).catch(() => {});
}

async function translate(tr) {
  if (!active) return;
  const style = STYLES[cfg.style] || STYLES.msa;
  const glossary = (cfg.glossary || '').trim();
  const system =
    'You are a professional subtitle translator for Turkish TV dramas (diziler). ' +
    `Translate the Turkish speech transcript into ${style}.\n` +
    'Rules:\n' +
    '- The transcript comes from live speech recognition and may contain mistakes, missing punctuation or cut sentences: use the previous lines as context to infer the intended meaning.\n' +
    '- Translate meaning and emotion, not word-for-word. Keep idioms natural, keep it short and readable as a subtitle (at most two short lines).\n' +
    '- Transliterate character names consistently in Arabic script and never translate them.\n' +
    '- Do not add explanations, quotes, notes or the Turkish text. Output ONLY the Arabic translation.\n' +
    '- If the input is only noise, music or filler with no meaning, output nothing.' +
    (glossary ? `\n- Character names / glossary (Turkish=Arabic), always follow it:\n${glossary}` : '');

  const context = history.slice(-6).map((h) => `${h.tr}  =>  ${h.ar}`).join('\n');
  const content = (context ? `Previous lines (Turkish => Arabic):\n${context}\n\n` : '') + `Translate now:\n${tr}`;

  try {
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': cfg.anthropicKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify({
        model: cfg.model || 'claude-haiku-5-5',
        max_tokens: 300,
        system,
        messages: [{ role: 'user', content }]
      })
    });
    if (res.status === 401 || res.status === 403 || res.status === 404) {
      const detail = res.status === 404 ? 'اسم النموذج غير صحيح' : 'مفتاح Anthropic غير صحيح';
      await stop();
      status('error', detail);
      return;
    }
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    const ar = (data.content || []).map((b) => b.text || '').join('').trim();
    if (!active) return;
    history.push({ tr, ar });
    if (ar) send({ type: 'subtitle', tr, ar });
  } catch (e) {
    // Fall back to the Turkish text so the viewer is never left with a blank screen.
    send({ type: 'subtitle', tr, ar: '', failed: true });
  }
}

async function stop(silent) {
  active = false;
  clearTimeout(flushTimer);
  pending = [];
  interimText = '';
  if (ws) {
    ws.onclose = null;
    try { if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'CloseStream' })); } catch {}
    try { ws.close(); } catch {}
    ws = null;
  }
  if (media) media.getTracks().forEach((t) => t.stop());
  media = null;
  for (const c of [playCtx, anaCtx]) if (c) await c.close().catch(() => {});
  playCtx = anaCtx = null;
  if (!silent) status('idle', 'متوقف');
}
