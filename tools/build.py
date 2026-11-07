"""Build the static site, one sub-site per language (see LANGS).
Usage (from repo root): python3 tools/build.py
lessons.json (grec, dossier grec/) / lessons_it.json (italien, dossier it/):
list of {date, title, title_fr, title_en, source{name,url}, paragraphs[], paragraphs_en[], fr{}, lemma{}, examples?}
paragraphs_en: English translation of each paragraph (bouton « Traduire le texte en anglais »).
lemma: {"<mot>": "<infinitif / forme du dictionnaire>"} for verbs only.
Each paragraph marks translated words as **mot** (English translation).
fr: {"<mot exactement comme dans **mot**>": "<traduction française>"} (pour le lexique mots.html)
examples (optional): {"<mot>": [["phrase grecque", "English translation", "traduction française"], ...]}
"""
import json, re, html, os, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = {
    "el": dict(file="lessons.json", out="grec/", title="Greek of the day", eyebrow="Ελληνικά κάθε μέρα", name="Greek", col="Ελληνικά", short="ΕΛ",
               tagline="Every morning, a real story from Athens in simple Greek, with the hard words translated and audio.",
               voice="el-GR-AthinaNeural", gtts="el", other=("it", "Italian of the day →"), legacy=True),
    "it": dict(file="lessons_it.json", out="it/", title="Italian of the day", eyebrow="Italiano ogni giorno", name="Italian", col="Italiano", short="IT",
               tagline="Every morning, a real story from Italy in simple Italian, with the hard words translated and audio.",
               voice="it-IT-ElsaNeural", gtts="it", other=("el", "Greek of the day →")),
}

def ex_audio_name(lang, text):
    """File name (in audio/ex/ of the language folder) of the MP3 of an example sentence."""
    return hashlib.md5((lang + "|" + text.strip()).encode("utf-8")).hexdigest()[:16] + ".mp3"
RX = re.compile(r"\*\*(.+?)\*\*\s*\((.+?)\)")
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]
DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

def fr_date(iso):
    import datetime
    d = datetime.date.fromisoformat(iso)
    return f"{DAYS[d.weekday()]}, {d.day} {MONTHS[d.month-1]} {d.year}"

CSS = """
:root{--bg:#f6f7f3;--surface:#fff;--fg:#1d221c;--muted:#5d665a;--line:#dde2d8;--accent:#4f6b2f;--soft:#e6edda;--gloss:#8a5a14;
--text:"Literata","Noto Serif",Georgia,serif;--ui:"Commissioner","Noto Sans",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root{--bg:#141712;--surface:#1c2019;--fg:#e8ebe3;--muted:#a2ab9c;--line:#2f362b;--accent:#a9c97d;--soft:#2a3420;--gloss:#e3b469;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--ui);font-size:15px;line-height:1.5}
.wrap{max-width:680px;margin:0 auto;padding-inline:18px;padding-block:20px 48px;display:flex;flex-direction:column;gap:22px}
a{color:var(--accent)}
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
h1{font-family:var(--text);font-weight:600;font-size:clamp(26px,7vw,36px);line-height:1.15;margin:4px 0;text-wrap:balance}
.sub{color:var(--muted);margin:0}
.player{position:sticky;top:0;z-index:2;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:12px;display:flex;flex-direction:column;gap:10px}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.play{font:inherit;font-size:16px;font-weight:600;padding:10px 20px;border-radius:999px;border:0;background:var(--accent);color:var(--bg);cursor:pointer;text-decoration:none}
.chip{font:inherit;font-size:13px;font-weight:500;padding:6px 12px;border-radius:999px;border:1px solid var(--line);background:transparent;color:var(--fg);cursor:pointer}
.chip[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:var(--bg)}
.label,.note{font-size:13px;color:var(--muted);margin:0}
.text{font-family:var(--text);font-size:20px;line-height:1.75;display:flex;flex-direction:column;gap:14px}
.text p{margin:0;border-radius:8px}.text[hidden]{display:none}
audio{width:100%}
.w{color:var(--accent);font-weight:600;cursor:pointer}
.g{font-family:var(--ui);font-size:.72em;font-weight:500;color:var(--gloss);white-space:nowrap}
.hide .g{display:none}.hide .w.open+.g{display:inline}
h2{font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
.vocab{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:0 18px;margin:0;padding:0;list-style:none}
.vocab li{border-bottom:1px solid var(--line);min-width:0;perspective:600px}
.vocab li.on{grid-column:1/-1}
.card{all:unset;box-sizing:border-box;width:100%;display:flex;flex-direction:column;padding:8px 0;cursor:pointer;border-radius:8px;transition:transform .25s ease,background-color .2s}
.card:disabled{cursor:default}
.card:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.card.spin{transform:rotateX(90deg)}
.on .card{background:var(--soft);padding:10px 12px}
.card .hint{font-size:11px;color:var(--accent);margin-top:2px}
.card .exg{font-family:var(--text);font-size:18px;font-weight:600;line-height:1.4}
.card .exf{color:var(--muted);font-size:14px}
.card .exf2,.vocab .fr2{color:var(--gloss);font-size:14px}
.card .speak{font-size:12px;color:var(--accent);margin-top:4px}
@media (prefers-reduced-motion:reduce){.card{transition:none}}
.vocab .gr{font-family:var(--text);font-size:17px;font-weight:600}.vocab .fr{color:var(--muted);font-size:14px}
.lem{font-weight:400;color:var(--muted);font-size:.85em}
#enBtn[aria-pressed=true]{background:#1e8e3e;border-color:#1e8e3e;color:#fff}
.list{list-style:none;margin:0;padding:0}
.list li{border-bottom:1px solid var(--line)}
.list a{display:flex;gap:12px;align-items:baseline;padding:12px 0;text-decoration:none;color:var(--fg)}
.list .d{font-variant-numeric:tabular-nums;color:var(--muted);font-size:13px;min-width:82px}
.list .t{font-family:var(--text);font-size:17px}
.list .f{color:var(--muted);font-size:13px;display:block}
"""
FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Commissioner:wght@400;500;600&family=Literata:opsz,wght@7..72,400;7..72,600&display=swap">'
FONTS += '<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">'

JS = r"""
(function(){
  var LANG = document.documentElement.dataset.learn || 'el';
  var a = document.getElementById('voice');
  document.querySelectorAll('[data-rate]').forEach(function(b){
    b.addEventListener('click', function(){
      if (a) a.playbackRate = +b.dataset.rate;
      document.querySelectorAll('[data-rate]').forEach(function(x){ x.setAttribute('aria-pressed', x === b); });
    });
  });
  document.addEventListener('click', function(e){ var w = e.target.closest('.w'); if (w) w.classList.toggle('open'); });
  var tts = null, re = new RegExp('^' + LANG, 'i');
  function pickVoice(){ if (!window.speechSynthesis) return; tts = speechSynthesis.getVoices().filter(function(v){ return re.test(v.lang); })[0] || null; }
  pickVoice(); if (window.speechSynthesis) speechSynthesis.onvoiceschanged = pickVoice;
  // Lecture des phrases avec Web Audio : la sortie son reste éveillée en continu (une fois lancée au
  // premier toucher), donc l'iPhone ou le casque ne coupent plus le début. Les MP3 sont préchargés.
  // Si Web Audio n'est pas disponible ou échoue : lecteur audio classique, puis voix du téléphone.
  var player = new Audio(), timer = null, ctx = null, node = null, token = 0, cache = {};
  player.preload = 'auto';
  try { if (navigator.audioSession) navigator.audioSession.type = 'playback'; } catch (e) {}
  function wake(){
    var C = window.AudioContext || window.webkitAudioContext;
    if (!C) return;
    if (!ctx) {
      ctx = new C();
      // son silencieux en boucle, très faible, pour garder la sortie audio active
      var b = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate), d = b.getChannelData(0);
      for (var k = 0; k < d.length; k++) d[k] = (Math.random() * 2 - 1) * 0.003; // ~ -50 dB : inaudible, mais assez pour que les casques Bluetooth ne se mettent pas en veille
      var keep = ctx.createBufferSource(); keep.buffer = b; keep.loop = true; keep.connect(ctx.destination); keep.start(0);
    }
    if (ctx.state !== 'running') return ctx.resume();
    return null;
  }
  function load(url){
    if (!cache[url]) cache[url] = fetch(url).then(function(r){ if (!r.ok) throw r; return r.arrayBuffer(); })
      .then(function(b){ return new Promise(function(ok, ko){ ctx.decodeAudioData(b, ok, ko); }); });
    cache[url].catch(function(){ delete cache[url]; });
    return cache[url];
  }
  function preload(urls){ if (ctx) urls.forEach(function(u){ if (u) load(u); }); }
  function stopAll(){
    token++; player.pause(); clearTimeout(timer);
    if (node) { try { node.stop(); } catch (e) {} node = null; }
    if (window.speechSynthesis) speechSynthesis.cancel();
  }
  function playElement(text, url){
    player.src = url; player.currentTime = 0;
    var pr = player.play(); if (pr && pr.catch) pr.catch(function(){ fallback(text); });
  }
  function say(text, url){
    stopAll();
    if (!url) { fallback(text); return; }
    var waking = wake();
    if (!ctx) { playElement(text, url); return; }
    var my = token;
    // Si l'iPhone avait coupé le son (écran verrouillé, onglet en arrière-plan), on attend qu'il
    // soit vraiment reparti et on attend encore 0,3 s ; l'amorce d'1 s est toujours jouée en entier.
    Promise.all([load(url), waking ? Promise.resolve(waking).catch(function(){}) : null]).then(function(r){
      if (my !== token) return;
      if (ctx.state !== 'running') { playElement(text, url); return; }
      node = ctx.createBufferSource(); node.buffer = r[0]; node.connect(ctx.destination);
      node.start(ctx.currentTime + (waking ? 0.3 : 0)); // toute l'amorce d'1 s avant la voix, même avec un casque
    }).catch(function(){ if (my === token) playElement(text, url); });
  }
  function fallback(text){
    if (!tts) return;
    // 1 s de silence avant la phrase pour ne pas perdre le début
    timer = setTimeout(function(){ var u = new SpeechSynthesisUtterance(text); u.voice = tts; u.lang = tts.lang; u.rate = 0.9; speechSynthesis.speak(u); }, 1000);
  }
  function esc(t){ var d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
  document.querySelectorAll('.card').forEach(function(c){
    var ex = JSON.parse(c.dataset.ex || '[]'), i = -1;
    if (!ex.length) return;
    var head = '<span class="gr">' + esc(c.dataset.gr) + (c.dataset.lem ? ' <span class="lem">(' + esc(c.dataset.lem) + ')</span>' : '') + '</span>';
    c.addEventListener('click', function(){
      if (a && !a.paused) a.pause();
      i = (i + 1) % (ex.length + 1);
      if (i < ex.length) { say(ex[i][0], ex[i][3]); preload(ex.map(function(e){ return e[3]; })); } else stopAll();
      c.classList.add('spin');
      setTimeout(function(){
        var li = c.parentNode;
        if (i === ex.length) { i = -1; li.classList.remove('on'); stopAll();
          c.innerHTML = head + '<span class="fr">' + esc(c.dataset.tr) + '</span>' + (c.dataset.fr ? '<span class="fr2">' + esc(c.dataset.fr) + '</span>' : '') + '<span class="hint">' + ex.length + ' sentence' + (ex.length > 1 ? 's' : '') + ' ↻</span>';
        } else { li.classList.add('on');
          c.innerHTML = '<span class="exg">' + esc(ex[i][0]) + '</span><span class="exf">' + esc(ex[i][1]) + '</span>' + (ex[i][2] ? '<span class="exf2">' + esc(ex[i][2]) + '</span>' : '') + '<span class="hint">' + esc(c.dataset.gr) + ' · ' + (i + 1) + '/' + ex.length + ' — tap for the next one ↻</span>';
        }
        c.classList.remove('spin');
      }, 160);
    });
  });
  var gb = document.getElementById('glossBtn'), eb = document.getElementById('enBtn'), text = document.getElementById('text'), en = document.getElementById('textEn');
  gb.addEventListener('click', function(){
    var show = gb.getAttribute('aria-pressed') !== 'true';
    gb.setAttribute('aria-pressed', show); gb.textContent = show ? 'Translations shown' : 'Translations hidden';
    text.classList.toggle('hide', !show);
  });
  if (eb) eb.addEventListener('click', function(){
    var on = eb.getAttribute('aria-pressed') !== 'true';
    eb.setAttribute('aria-pressed', on);
    text.hidden = on; en.hidden = !on;
  });
})();
"""

def lesson_page(s, prev, nxt, lang, L, outdir):
    words, paras_html, plain = [], [], []
    frm = s.get("fr", {})
    for p in s["paragraphs"]:
        out, last = "", 0
        for m in RX.finditer(p):
            out += html.escape(p[last:m.start()])
            f = frm.get(m.group(1), "")
            words.append((m.group(1), m.group(2), f))
            gl = m.group(2) + (f" · {f}" if f else "")
            out += f'<span class="w">{html.escape(m.group(1))}</span><span class="g"> ({html.escape(gl)})</span>'
            last = m.end()
        out += html.escape(p[last:])
        paras_html.append(f"<p>{out}</p>")
        plain.append(RX.sub(r"\1", p))
    chunks = [s["title"] + "."] + plain
    gt = f"https://translate.google.com/?sl={lang}&tl=en&op=translate&text=" + __import__("urllib.parse").parse.quote("\n\n".join(chunks))
    mp3 = os.path.join(outdir, "audio", s["date"] + ".mp3")
    if os.path.exists(mp3):
        ver = __import__("hashlib").md5(open(mp3, "rb").read()).hexdigest()[:8]
        player = (f'<audio id="voice" controls preload="metadata" src="../audio/{s["date"]}.mp3?v={ver}"></audio>'
                  '<div class="row"><span class="label">Speed</span>'
                  '<button class="chip" data-rate="0.85" aria-pressed="false">0.85×</button>'
                  '<button class="chip" data-rate="1" aria-pressed="true">1×</button></div>')
    else:
        player = (f'<p class="note">The audio is on its way (a few minutes). Meanwhile: '
                  f'<a href="{html.escape(gt)}" target="_blank" rel="noopener">listen in Google Translate</a>.</p>')
    ex = s.get("examples", {})
    lem = s.get("lemma", {})
    def with_audio(p):
        p = list(p[:3]) + [""] * (3 - len(p[:3]))
        n = ex_audio_name(lang, p[0])
        f = os.path.join(outdir, "audio", "ex", n)
        if os.path.exists(f):
            ver = __import__("hashlib").md5(open(f, "rb").read()).hexdigest()[:8]
            p.append("../audio/ex/" + n + "?v=" + ver)
        return p
    def card(a, b, f=""):
        pairs = [with_audio(p) for p in ex.get(a, []) if len(p) >= 2]
        lm = lem.get(a, "")
        lm_html = f' <span class="lem">({html.escape(lm)})</span>' if lm else ""
        data = html.escape(json.dumps(pairs, ensure_ascii=False), quote=True)
        hint = f'<span class="hint">{len(pairs)} sentence{"s" if len(pairs) > 1 else ""} ↻</span>' if pairs else ""
        return (f'<li><button class="card" type="button" data-ex="{data}" data-gr="{html.escape(a)}" data-tr="{html.escape(b)}" data-fr="{html.escape(f)}" data-lem="{html.escape(lm)}"'
                f'{"" if pairs else " disabled"}><span class="gr">{html.escape(a)}{lm_html}</span><span class="fr">{html.escape(b)}</span>{f'<span class="fr2">{html.escape(f)}</span>' if f else ""}{hint}</button></li>')
    vocab = "".join(card(a, b, f) for a, b, f in words)
    nav = []
    if prev: nav.append(f'<a href="{prev["date"]}.html">← Previous lesson</a>')
    nav.append('<a href="../index.html">All lessons</a>')
    nav.append('<a href="../mots.html">All words</a>')
    en_html = "".join(f"<p>{html.escape(p)}</p>" for p in s.get("paragraphs_en", []))
    if nxt: nav.append(f'<a href="{nxt["date"]}.html">Next lesson →</a>')
    src = s.get("source")
    src_html = f'<p class="note">Source: <a href="{html.escape(src["url"])}" target="_blank" rel="noopener">{html.escape(src["name"])}</a></p>' if src else ""
    return f"""<!doctype html><html lang="en" data-learn="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(s["title"])} · Masimera</title>{FONTS}<style>{CSS}</style></head><body><div class="wrap">
<header><span class="eyebrow">{fr_date(s["date"])}</span><h1>{html.escape(s["title"])}</h1><p class="sub">{html.escape(s.get("title_en") or s.get("title_fr",""))}</p></header>
<section class="player">
  {player}
</section>
<section><h2>The {len(words)} words</h2>{'<p class="note" style="margin:-4px 0 10px">Tap a word to see example sentences in ' + L["name"] + ', with English and French translations.</p>' if ex else ""}<ul class="vocab">{vocab}</ul></section>
<section><h2>The text</h2><div class="text hide" id="text">{"".join(paras_html)}</div><div class="text" id="textEn" lang="en" hidden>{en_html}</div></section>
<div class="row"><button class="chip" id="glossBtn" aria-pressed="false">Translations hidden</button>{'<button class="chip" id="enBtn" aria-pressed="false">Show English translation</button>' if en_html else ""}</div>
{src_html}
<nav class="row">{" · ".join(nav)}</nav>
</div><script>{JS}</script></body></html>"""

def index_page(lessons, lang, L):
    items = "".join(f'<li><a href="cours/{s["date"]}.html"><span class="d">{s["date"][8:10]}/{s["date"][5:7]}/{s["date"][:4]}</span><span><span class="t">{html.escape(s["title"])}</span><span class="f">{html.escape(s.get("title_en") or s.get("title_fr",""))}</span></span></a></li>' for s in lessons)
    o = LANGS[L["other"][0]]
    other = "../" + o["out"]
    head = f'<a class="play" href="cours/{lessons[0]["date"]}.html">Read today\'s lesson →</a> ' if lessons else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{L["title"]} · Masimera</title>{FONTS}<style>{CSS}</style></head><body><div class="wrap">
<header><span class="eyebrow">{L["eyebrow"]}</span><h1>{L["title"]}</h1><p class="sub">{L["tagline"]}</p></header>
<p class="row">{head}<a href="mots.html">All words (FR · EN · {L["short"]})</a> · <a href="{other}index.html">{L["other"][1]}</a> · <a href="../index.html">Home</a></p>
<section><h2>All lessons</h2><ul class="list">{items or '<li class="note">The first lesson is coming soon.</li>'}</ul></section>
</div></body></html>"""

ARTICLES = re.compile(r"^(?:l'|l’|d'|d’|le |la |les |un |une |des |du |de la |de l'|de l’|de |à |au |aux |se |s'|a |ont |est |sont |va |vont |va |s’)", re.I)

def fr_key(w):
    import unicodedata
    w = w.strip()
    for _ in range(2):
        w = ARTICLES.sub("", w)
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if not unicodedata.combining(c)), w

GLOSS_CSS = """
.search{font:inherit;font-size:16px;width:100%;padding:10px 14px;border-radius:10px;border:1px solid var(--line);background:var(--surface);color:var(--fg)}
.lex{width:100%;border-collapse:collapse}
.lex th{text-align:left;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);padding:6px 8px 6px 0;border-bottom:1px solid var(--line)}
.lex td{padding:8px 8px 8px 0;border-bottom:1px solid var(--line);vertical-align:baseline}
.lex td:first-child{font-weight:500}.lex td:nth-child(2){color:var(--muted)}
.lex td:last-child a{font-family:var(--text);font-size:17px;font-weight:600;text-decoration:none}
.lex tr.letter td{border:0;padding:18px 0 4px;font-size:13px;font-weight:600;color:var(--accent)}
"""

def gloss_page(lessons, lang, L):
    seen, rows = set(), []
    for s in sorted(lessons, key=lambda s: s["date"]):
        fr = s.get("fr", {}); lem = s.get("lemma", {})
        for p in s["paragraphs"]:
            for m in RX.finditer(p):
                gr, en = m.group(1), m.group(2)
                if lem.get(gr): gr = f"{gr} ({lem[gr]})"
                f = fr.get(gr, "")
                k = (f.lower(), en.lower(), gr.lower())
                if k in seen: continue
                seen.add(k); rows.append((f, en, gr, s["date"]))
    rows.sort(key=lambda r: (fr_key(r[0]), r[1].lower()))
    out, cur = [], None
    for f, en, gr, d in rows:
        ch = (fr_key(f)[0][:1] or "#").upper()
        if ch != cur:
            cur = ch; out.append(f'<tr class="letter"><td colspan="3">{html.escape(ch)}</td></tr>')
        out.append(f'<tr data-s="{html.escape((f+" "+en+" "+gr).lower(), quote=True)}"><td>{html.escape(f)}</td><td>{html.escape(en)}</td>'
                   f'<td><a href="cours/{d}.html" title="Lesson of {d}">{html.escape(gr)}</a></td></tr>')
    js = """(function(){var q=document.getElementById('q');q.addEventListener('input',function(){var v=q.value.trim().toLowerCase();
document.querySelectorAll('.lex tr[data-s]').forEach(function(r){r.hidden=v&&r.dataset.s.indexOf(v)<0;});
document.querySelectorAll('.lex tr.letter').forEach(function(r){r.hidden=!!v;});});})();"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>All words · {L["title"]} · Masimera</title>{FONTS}<style>{CSS}{GLOSS_CSS}</style></head><body><div class="wrap">
<header><span class="eyebrow">{L["col"]}</span><h1>All words</h1><p class="sub">{len(rows)} words from the lessons, in French alphabetical order. Tap a word in {L["name"]} to open its lesson.</p></header>
<input class="search" id="q" type="search" placeholder="Search (French, English or {L["name"]})…" autocomplete="off">
<table class="lex"><thead><tr><th>Français</th><th>English</th><th>{L["col"]}</th></tr></thead><tbody>{"".join(out)}</tbody></table>
<nav class="row"><a href="index.html">All lessons</a> · <a href="../index.html">Home</a></nav>
</div><script>{js}</script></body></html>"""

def build(lang, L):
    path = os.path.join(ROOT, L["file"])
    lessons = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    lessons.sort(key=lambda s: s["date"], reverse=True)
    outdir = os.path.join(ROOT, L["out"])
    os.makedirs(os.path.join(outdir, "cours"), exist_ok=True)
    for i, s in enumerate(lessons):
        prev = lessons[i + 1] if i + 1 < len(lessons) else None
        nxt = lessons[i - 1] if i > 0 else None
        open(os.path.join(outdir, "cours", s["date"] + ".html"), "w", encoding="utf-8").write(lesson_page(s, prev, nxt, lang, L, outdir))
    open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(index_page(lessons, lang, L))
    open(os.path.join(outdir, "mots.html"), "w", encoding="utf-8").write(gloss_page(lessons, lang, L))
    print(f"{lang}: built {len(lessons)} lesson(s)")

def redirect(target):
    t = html.escape(target, quote=True)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={t}">'
            f'<link rel="canonical" href="{t}"><title>Redirecting</title></head><body><p><a href="{t}">This lesson has moved: click here</a></p>'
            f'<script>location.replace({json.dumps(target)} + location.hash)</script></body></html>')

# Formulaire d'inscription : FormSubmit envoie chaque inscription par e-mail (objet « Masimera sign-up »),
# et la tâche du matin ajoute les nouvelles adresses à abonnes.txt.
FORM_ACTION = "https://formsubmit.co/stanislas.morin@gmail.com"

HOME_CSS = """
.brand{font-family:var(--text);font-weight:600;font-size:clamp(40px,12vw,64px);line-height:1;margin:6px 0 4px;letter-spacing:-.01em}
.meaning{font-family:var(--text);font-style:italic;color:var(--muted);margin:0}
.lead{font-size:18px;line-height:1.55;margin:0;text-wrap:pretty}
.langs{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.lang{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:8px}
.lang .k{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.lang .t{font-family:var(--text);font-size:19px;font-weight:600;line-height:1.3}
.lang .f{color:var(--muted);font-size:14px;margin-top:-4px}
.lang .row{margin-top:auto;padding-top:6px}
.lang .play{font-size:15px;padding:9px 16px}
.steps{list-style:none;margin:0;padding:0;display:grid;gap:12px}
.steps li{display:grid;grid-template-columns:28px 1fr;gap:10px;align-items:baseline}
.steps b{font-family:var(--text);font-size:18px;color:var(--accent)}
.steps strong{display:block}.steps span{color:var(--muted);font-size:14px}
.join{background:var(--soft);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:10px}
.join p{margin:0}
.join form{display:flex;flex-direction:column;gap:10px}
.join input[type=email],.join select{font:inherit;font-size:16px;padding:10px 14px;border-radius:10px;border:1px solid var(--line);background:var(--surface);color:var(--fg);width:100%}
.join .hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.join button.play{align-self:flex-start}
.join .small{font-size:13px;color:var(--muted)}
"""

def home_page():
    cards = []
    for lang, L in LANGS.items():
        path = os.path.join(ROOT, L["file"])
        lessons = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
        lessons.sort(key=lambda s: s["date"], reverse=True)
        lang_name = L["name"]
        if lessons:
            s = lessons[0]
            body = (f'<span class="t">{html.escape(s["title"])}</span>'
                    f'<span class="f">{html.escape(s.get("title_en") or s.get("title_fr", ""))}</span>'
                    f'<div class="row"><a class="play" href="{L["out"]}cours/{s["date"]}.html">Today\'s lesson →</a>'
                    f'<a href="{L["out"]}index.html">All {len(lessons)} lessons</a></div>')
        else:
            body = '<span class="f">The first lesson is coming soon.</span>'
        cards.append(f'<div class="lang"><span class="k">{lang_name} · {L["eyebrow"]}</span>{body}</div>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Masimera · 15 minutes a day to learn a language</title>
<meta name="description" content="Every morning, a real local news story in simple Greek or Italian, with the hard words translated and audio. 15 minutes a day.">
{FONTS}<style>{CSS}{HOME_CSS}</style></head><body><div class="wrap">
<header><span class="eyebrow">15 minutes a day</span><h1 class="brand">Masimera</h1>
<p class="meaning">μάθημα (lesson) + μέρα (day): the lesson of the day</p></header>
<p class="lead">Every morning, a real news story, rewritten in simple sentences, with audio and the hard words translated into English and French. Slow and steady: a little every day, and you progress.</p>
<section><h2>Today's lessons</h2><div class="langs">{"".join(cards)}</div></section>
<section><h2>How it works</h2><ol class="steps">
<li><b>1</b><div><strong>Read a real story</strong><span>Local news from Athens or Italy, written so simply a child could follow it.</span></div></li>
<li><b>2</b><div><strong>Listen</strong><span>A natural voice reads the text. Slow it down if you need to.</span></div></li>
<li><b>3</b><div><strong>Learn 20 to 30 words</strong><span>Each word in English and French, with short example sentences you can hear.</span></div></li>
<li><b>4</b><div><strong>Come back tomorrow</strong><span>A new lesson every morning. All the words you've met stay in your glossary.</span></div></li>
</ol></section>
<section class="join"><h2 style="margin:0">Get it every morning</h2>
<p>The lesson arrives in your inbox at 6 am, with one button to open it.</p>
<form action="{FORM_ACTION}" method="POST">
<input type="hidden" name="_subject" value="Masimera sign-up">
<input type="hidden" name="_next" value="https://masimera.com/thanks.html">
<input type="hidden" name="_template" value="table">
<input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<label class="small" for="em">Your email</label>
<input id="em" type="email" name="email" required placeholder="you@example.com" autocomplete="email">
<label class="small" for="lg">Language</label>
<select id="lg" name="language"><option>Greek</option><option>Italian</option><option>Greek and Italian</option></select>
<button class="play" type="submit">Sign up</button>
<p class="small">Free. One email a day. Reply "stop" to any email to unsubscribe.</p>
</form></section>
</div></body></html>"""

def thanks_page():
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thank you · Masimera</title>{FONTS}<style>{CSS}</style></head><body><div class="wrap">
<header><span class="eyebrow">Masimera</span><h1>You're in!</h1>
<p class="sub">Your first lesson arrives tomorrow morning, around 6 am (Paris time). If you don't see it, check your spam folder.</p></header>
<p class="row"><a class="play" href="index.html">Back to today's lessons</a></p>
</div></body></html>"""

def main():
    for lang, L in LANGS.items():
        build(lang, L)
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(home_page())
    open(os.path.join(ROOT, "thanks.html"), "w", encoding="utf-8").write(thanks_page())
    # anciennes adresses du grec (avant le dossier grec/) → redirection
    for lang, L in LANGS.items():
        if not L.get("legacy"): continue
        os.makedirs(os.path.join(ROOT, "cours"), exist_ok=True)
        for s in json.load(open(os.path.join(ROOT, L["file"]), encoding="utf-8")):
            open(os.path.join(ROOT, "cours", s["date"] + ".html"), "w", encoding="utf-8").write(redirect(f'../{L["out"]}cours/{s["date"]}.html'))
        open(os.path.join(ROOT, "mots.html"), "w", encoding="utf-8").write(redirect(f'{L["out"]}mots.html'))
    open(os.path.join(ROOT, ".nojekyll"), "w").close()

if __name__ == "__main__":
    main()
