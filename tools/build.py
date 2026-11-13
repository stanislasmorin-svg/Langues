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
import math
import json, re, html, os, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://masimera.com/"

def seo(path, title, desc, kind="website"):
    """meta description, canonical and share preview (WhatsApp, Facebook...) for a page at BASE+path."""
    e = lambda x: html.escape(x, quote=True)
    url = BASE + path
    return (f'<meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(url)}">'
            f'<meta property="og:type" content="{kind}"><meta property="og:site_name" content="Masimera">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:url" content="{e(url)}"><meta property="og:image" content="{BASE}icon-512.png">'
            f'<meta name="twitter:card" content="summary">')
LANGS = {
    "el": dict(file="lessons.json", out="grec/", title="Greek of the day", eyebrow="Ελληνικά κάθε μέρα", name="Greek", col="Ελληνικά", short="ΕΛ",
               tagline="Every morning, a real story from Athens in simple Greek, with the hard words translated and audio.",
               verbs="verbs_el.json", place="Athens", voice="el-GR-AthinaNeural", gtts="el", other=("it", "Italian of the day →"), legacy=True),
    "it": dict(file="lessons_it.json", out="it/", title="Italian of the day", eyebrow="Italiano ogni giorno", name="Italian", col="Italiano", short="IT",
               tagline="Every morning, a real story from Italy in simple Italian, with the hard words translated and audio.",
               verbs="verbs_it.json", place="Italy", voice="it-IT-ElsaNeural", gtts="it", other=("el", "Greek of the day →")),
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
.sitefoot{border-top:1px solid var(--line);margin-top:8px;padding-top:14px;font-size:14px;color:var(--muted);display:flex;flex-wrap:wrap;gap:6px}
.toplink{float:right;font-size:14px;margin-top:2px}
:root{--bg:#f6f7f9;--surface:#fff;--fg:#1c1f24;--muted:#5b6370;--line:#dde1e8;--accent:#1a56b4;--soft:#e4ecf8;--gloss:#8a5a14;
--text:"Times New Roman",Times,"Liberation Serif","Noto Serif",serif;--ui:"Times New Roman",Times,"Liberation Serif","Noto Serif",serif}
@media (prefers-color-scheme:dark){:root{--bg:#13161b;--surface:#1b1f26;--fg:#e7eaef;--muted:#a0a8b4;--line:#2d333d;--accent:#8ab4f8;--soft:#1f2b3d;--gloss:#e3b469;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--ui);font-size:16px;line-height:1.5}
.wrap{max-width:680px;margin:0 auto;padding-inline:18px;padding-block:20px 48px;display:flex;flex-direction:column;gap:22px}
a{color:var(--accent)}
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
h1{font-family:var(--text);font-weight:600;font-size:clamp(26px,7vw,36px);line-height:1.15;margin:4px 0;text-wrap:balance}
.sub{color:var(--muted);margin:0}
.topnav{font-size:14px;margin:6px 0 2px;gap:6px}
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
#enBtn[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:var(--bg)}
.list{list-style:none;margin:0;padding:0}
.list li{border-bottom:1px solid var(--line)}
.list a{display:flex;gap:12px;align-items:baseline;padding:12px 0;text-decoration:none;color:var(--fg)}
.list .d{font-variant-numeric:tabular-nums;color:var(--muted);font-size:13px;min-width:82px}
.list .t{font-family:var(--text);font-size:17px}
.list .f{color:var(--muted);font-size:13px;display:block}
"""
FONTS = ''
FONTS += '<meta name="google" content="notranslate">'
FONTS += '<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">'

GA_ID = "G-GPPTJ2QQFS"
GA = ("<style>#ckb{position:fixed;left:12px;right:12px;bottom:12px;z-index:50;max-width:560px;margin:0 auto;background:var(--surface,#fff);color:var(--fg,#1c1f24);"
      "border:1px solid var(--line,#dde1e8);border-radius:14px;padding:12px 14px;box-shadow:0 6px 24px rgba(0,0,0,.15);display:flex;flex-wrap:wrap;gap:10px;align-items:center;font-size:15px}"
      "#ckb p{margin:0;flex:1 1 220px}#ckb button{font:inherit;font-weight:600;padding:8px 16px;border-radius:999px;cursor:pointer;border:1px solid var(--accent,#1a56b4)}"
      "#ckb .y{background:var(--accent,#1a56b4);color:var(--bg,#fff)}#ckb .n{background:transparent;color:var(--accent,#1a56b4)}</style>"
      "<script>(function(){var K='masimera-consent',ID='" + GA_ID + "';"
      "function get(){try{return localStorage.getItem(K)}catch(e){return null}}function set(v){try{localStorage.setItem(K,v)}catch(e){}}"
      "function load(){if(window.__ga)return;window.__ga=1;window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};"
      "gtag('js',new Date());gtag('config',ID);var s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+ID;document.head.appendChild(s)}"
      "var c=get();if(c==='yes'){load();return}if(c==='no')return;"
      "document.addEventListener('DOMContentLoaded',function(){var b=document.createElement('div');b.id='ckb';b.setAttribute('role','dialog');b.setAttribute('aria-label','Cookies');"
      "b.innerHTML='<p>This site uses Google Analytics cookies.</p><button class=\"n\" type=\"button\">Decline</button><button class=\"y\" type=\"button\">Accept</button>';"
      "b.querySelector('.y').onclick=function(){set('yes');b.remove();load()};b.querySelector('.n').onclick=function(){set('no');b.remove()};document.body.appendChild(b)})})();</script>")
FONTS += GA

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
  if (gb) gb.addEventListener('click', function(){
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
(function(){
  var b = document.getElementById('shareBtn'); if (!b) return;
  b.addEventListener('click', function(){
    var url = location.href.split('?')[0].split('#')[0], title = document.title;
    if (navigator.share) { navigator.share({title: title, url: url}).catch(function(){}); return; }
    var done = function(){ b.textContent = 'Link copied ✓'; setTimeout(function(){ b.textContent = 'Share this lesson'; }, 2000); };
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function(){ prompt('Copy this link:', url); });
    else prompt('Copy this link:', url);
  });
})();
"""


SPEAKER = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
           '<path d="M11 5 6 9H3v6h3l5 4z" fill="currentColor"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/></svg>')

QUIZ_CSS = """
.qcard{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:10px}
.qcard .k{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.qcard .t{font-size:20px;font-weight:600}
#q,#end{display:flex;flex-direction:column;gap:14px}[hidden]{display:none!important}
.qhead{display:flex;justify-content:space-between;align-items:center;font-size:14px;color:var(--muted)}
.bar{height:6px;background:var(--line);border-radius:99px;overflow:hidden}.bar i{display:block;height:100%;background:var(--accent);width:0;transition:width .3s}
.ask{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:6px;text-align:center}
.ask .en{font-size:26px;font-weight:600}.ask .fr{color:var(--gloss);font-size:18px}.ask .tag{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.opt{font:inherit;font-size:21px;padding:16px 10px;border-radius:12px;border:1px solid var(--line);background:var(--surface);color:var(--fg);cursor:pointer}
.opt:hover:not(:disabled){border-color:var(--accent)}.opt:disabled{cursor:default}
.opt.ok{background:#e3f4e8;border-color:#2e7d4f;color:#1b5e38}.opt.ko{background:#fbe5e5;border-color:#c0392b;color:#8e2a20}
@media (prefers-color-scheme:dark){.opt.ok{background:#173a26;color:#9fe0b7}.opt.ko{background:#3d1a17;color:#f2aaa2}}
.fb{min-height:64px;font-size:16px;text-align:center}.fb .exg{font-size:18px}.fb .exe{color:var(--muted);font-size:14px}
.say{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;margin-left:6px;vertical-align:middle;border-radius:50%;border:1px solid var(--line);background:var(--surface);color:var(--accent);cursor:pointer;padding:0}
.say:hover{border-color:var(--accent)}.say svg{width:18px;height:18px}
.score{font-size:64px;font-weight:600;text-align:center;line-height:1;margin:8px 0}
.center{text-align:center}.center .row{justify-content:center}
.miss{list-style:none;padding:0;margin:0}.miss li{border-bottom:1px solid var(--line);padding:8px 0;display:flex;justify-content:space-between;gap:10px}
.miss b{font-size:18px}
"""

def quiz_items(s, lang, outdir, all_lemmas):
    """Up to 10 quiz questions. Uses s["quiz"] (written by the daily task) if present,
    otherwise picks non-verb words of the lesson automatically (older lessons)."""
    words, frm, lem, ex = [], s.get("fr", {}), s.get("lemma", {}), s.get("examples", {})
    for p in s["paragraphs"]:
        for m in RX.finditer(p):
            words.append((m.group(1), m.group(2)))
    gloss = dict(words)
    if s.get("quiz"):
        base = [(q["word"], q.get("gr") or lem.get(q["word"]) or q["word"], q["en"], q.get("fr", frm.get(q["word"], ""))) for q in s["quiz"] if q.get("word") in gloss]
    else:
        base = [(w, w, en, frm.get(w, "")) for w, en in words if w not in lem][:10]
    nouns = [w for w, _ in words if w not in lem]
    verbs = sorted(set(lem.values()))
    out = []
    for w, gr, en, fr in base[:10]:
        is_verb = w in lem
        pool = [v for v in (verbs if is_verb else nouns) if v != gr]
        if is_verb and len(pool) < 3:
            pool += [v for v in all_lemmas if v != gr and v not in pool][:3 - len(pool)]
        pairs = ex.get(w, [])
        e = (pairs[1] if is_verb and len(pairs) > 1 else pairs[0]) if pairs else ["", "", ""]
        e = list(e[:3]) + [""] * (3 - len(e[:3]))
        au = ""
        if e[0]:
            n = ex_audio_name(lang, e[0]); fpath = os.path.join(outdir, "audio", "ex", n)
            if os.path.exists(fpath):
                au = "../audio/ex/" + n + "?v=" + hashlib.md5(open(fpath, "rb").read()).hexdigest()[:8]
        out.append(dict(gr=gr, en=en, fr=fr, pool=pool, ex=e, au=au))
    return out if len(out) >= 4 else []

QUIZ_JS = r"""
function sh(a){for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t}return a}
var i=0,score=0,miss=[],$=function(x){return document.getElementById(x)},AU=new Audio(),N=D.length;
var CH=parseInt(new URLSearchParams(location.search).get('challenge'),10);if(!(CH>=0&&CH<=N))CH=null;
if(CH!==null){$('chal').hidden=false;$('chal').textContent='A friend scored '+CH+'/'+N+' on this quiz. Can you beat them?';}
function esc(t){var d=document.createElement('div');d.textContent=t;return d.innerHTML}
function play(){if(!D[i].au)return;AU.src=D[i].au;AU.currentTime=0;AU.play().catch(function(){})}
function show(){var it=D[i];$('n').textContent='Question '+(i+1)+' / '+N;$('bar').style.width=(i/N*100)+'%';
 $('en').textContent=it.en;$('fr').textContent=it.fr;$('fb').innerHTML='';$('next').hidden=true;
 var o=sh([it.gr].concat(sh(it.pool.slice()).slice(0,3)));$('opts').innerHTML='';
 o.forEach(function(w){var b=document.createElement('button');b.className='opt';b.type='button';b.textContent=w;b.onclick=function(){pick(b,w)};$('opts').appendChild(b)})}
function pick(btn,w){var it=D[i],ok=w===it.gr;[].forEach.call($('opts').children,function(b){b.disabled=true;if(b.textContent===it.gr)b.classList.add('ok')});
 if(ok){score++}else{btn.classList.add('ko');miss.push(it)}
 $('pts').textContent=score+(score===1?' point':' points');
 $('fb').innerHTML=(ok?'<strong>Correct!</strong>':'<strong>The answer: '+esc(it.gr)+'</strong>')+(it.ex[0]?'<div class="exg">'+esc(it.ex[0])+(it.au?'<button class="say" type="button" aria-label="Listen" onclick="play()">'+SPK+'</button>':'')+'</div><div class="exe">'+esc(it.ex[1])+(it.ex[2]?' · '+esc(it.ex[2]):'')+'</div>':'');
 $('next').hidden=false;$('next').textContent=i==N-1?'See my score':'Next →';$('next').focus()}
$('next').onclick=function(){AU.pause();i++;if(i<N)show();else end()};
function end(){$('q').hidden=true;$('end').hidden=false;$('sc').textContent=score+' / '+N;
 $('msg').textContent=score==N?'Perfect! '+BRAVO:score>=N*0.7?'Very good! See you tomorrow.':score>=N*0.4?'Not bad. Read the lesson again and retry.':'Keep going: a little every day goes a long way.';
 if(CH!==null)$('msg').textContent=score>CH?'You beat your friend ('+CH+'/'+N+')!':score==CH?'Tie with your friend ('+CH+'/'+N+')!':'Your friend wins this time ('+CH+'/'+N+'). Try again!';
 $('share').textContent='Challenge a friend';
 $('rev').hidden=!miss.length;$('miss').innerHTML=miss.map(function(m){return '<li><b>'+esc(m.gr)+'</b><span>'+esc(m.en)+(m.fr?' · '+esc(m.fr):'')+'</span></li>'}).join('')}
$('again').onclick=function(){i=0;score=0;miss=[];sh(D);$('end').hidden=true;$('q').hidden=false;$('pts').textContent='0 points';show()};
$('share').onclick=function(){var t='I got '+score+'/'+N+' on today\'s '+LANG+' quiz on Masimera. Can you beat me?',u=location.href.split('?')[0].split('#')[0]+'?challenge='+score;
 if(navigator.share)navigator.share({text:t,url:u}).catch(function(){});else if(navigator.clipboard)navigator.clipboard.writeText(t+' '+u).then(function(){$('share').textContent='Copied ✓'})};
show();
"""


SHARE_CSS = """
.brandmini{display:inline-flex;align-items:center;gap:8px;font-weight:600;font-size:16px;color:var(--fg);text-decoration:none;margin-bottom:10px}
.brandmini img{width:24px;height:24px;border-radius:6px}
.pitch{margin:8px 0 0;font-size:15px;color:var(--muted)}
.chal{background:var(--soft);border-radius:12px;padding:12px 14px;font-weight:600;margin-top:10px}
.signup{background:var(--soft);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:10px;text-align:left;margin-top:16px}
.signup h2{margin:0;color:var(--fg);font-size:17px;letter-spacing:0;text-transform:none}
.signup p{margin:0;font-size:14px;color:var(--muted)}
.signup form{display:flex;flex-direction:column;gap:10px}
.signup input[type=email],.signup select{font:inherit;font-size:16px;padding:10px 14px;border-radius:10px;border:1px solid var(--line);background:var(--surface);color:var(--fg);width:100%}
.signup .hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.signup button.play{align-self:flex-start}
"""

FOOTER = '<footer class="sitefoot"><a href="/method.html">The Masimera method</a><span>·</span><a href="/">Home</a></footer>'

def brand_mini():
    return '<a class="brandmini" href="/"><img src="/icon-192.png" alt="">Masimera</a>'

def pitch(L):
    return (f'<p class="pitch"><b>Masimera</b>: every morning, a real news story from {L["place"]} '
            f'in simple {L["name"]}, with audio. 15 minutes a day.</p>')

def signup_box(L):
    opts = "".join(f'<option{" selected" if o == L["name"] else ""}>{o}</option>' for o in ("Greek", "Italian", "Greek and Italian"))
    return f"""<section class="signup"><h2>Want a new lesson and quiz every morning?</h2>
<p>A real news story in simple {L["name"]}, with audio and the hard words translated. Free, one email a day.</p>
<form action="{FORM_ACTION}" method="POST">
<input type="hidden" name="_subject" value="Masimera sign-up">
<input type="hidden" name="_next" value="https://masimera.com/thanks.html">
<input type="hidden" name="_template" value="table">
<input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<input type="email" name="email" required placeholder="you@example.com" autocomplete="email" aria-label="Your email">
<select name="language" aria-label="Language">{opts}</select>
<button class="play" type="submit">Sign up</button>
</form></section>"""

def quiz_page(s, items, lang, L):
    bravo = "Μπράβο!" if lang == "el" else "Bravo!"
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    t = html.escape(s["title"])
    return f"""<!doctype html><html lang="en" translate="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{L["name"]} quiz · {t} · Masimera</title><meta name="robots" content="noindex">{seo(L["out"] + "quiz/" + s["date"] + ".html", "Can you beat my score? " + L["name"] + " quiz · Masimera", f"A 2-minute {L['name']} quiz on today's news: {s['title']}. 10 words, 4 choices each.")}{FONTS}<style>{CSS}{QUIZ_CSS}{SHARE_CSS}</style></head><body><div class="wrap">
<header>{brand_mini()}<br><span class="eyebrow">{L["name"]} quiz · {fr_date(s["date"])}</span><h1>Quiz of the day</h1>
<p class="sub">{len(items)} words from the lesson: <a href="../cours/{s["date"]}.html">{t}</a></p>{pitch(L)}
<p class="chal" id="chal" hidden></p></header>
<div id="q">
<div class="qhead"><span id="n"></span><span id="pts">0 points</span></div>
<div class="bar"><i id="bar"></i></div>
<div class="ask"><span class="tag">Choose the {L["name"]} word</span><span class="en" id="en"></span><span class="fr" id="fr"></span></div>
<div class="opts" id="opts"></div>
<div class="fb" id="fb" aria-live="polite"></div>
<div class="row" style="justify-content:center"><button class="play" id="next" type="button" hidden>Next →</button></div>
</div>
<div id="end" class="center" hidden>
<h2>Your score</h2><div class="score" id="sc"></div><p class="sub" id="msg"></p>
<div class="row"><button class="play" id="share" type="button">Share my score</button><button class="chip" id="again" type="button">Try again</button></div>
<section id="rev" style="text-align:left;margin-top:12px" hidden><h2>Words to review</h2><ul class="miss" id="miss"></ul></section>
{signup_box(L)}
<p class="row"><a href="../cours/{s["date"]}.html">← Back to the lesson</a> · <a href="../mots.html">All words</a></p>
</div>
{FOOTER}
</div><script>var D={data},SPK={json.dumps(SPEAKER)},LANG={json.dumps(L["name"])},BRAVO={json.dumps(bravo)};{QUIZ_JS}</script></body></html>"""

def lesson_page(s, prev, nxt, lang, L, outdir, has_quiz=False):
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
    quiz_card = (f'<section class="qcard"><span class="k">Quiz of the day</span><span class="t">Ready to test yourself?</span>'
                 f'<span class="sub">10 words from this lesson · about 2 minutes</span><div class="row"><a class="play" href="../quiz/{s["date"]}.html">Start the quiz →</a></div></section>\n')
    src_html = f'<p class="note">Source: <a href="{html.escape(src["url"])}" target="_blank" rel="noopener">{html.escape(src["name"])}</a></p>' if src else ""
    return f"""<!doctype html><html lang="en" translate="no" data-learn="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(s["title"])} · Easy {L["name"]} reading with audio · Masimera</title>{seo(L["out"] + "cours/" + s["date"] + ".html", s["title"] + " · Easy " + L["name"] + " with audio", (s.get("title_en") or s.get("title_fr","")) + ". A real news story from " + L["place"] + " in simple " + L["name"] + ", with audio and " + str(len(words)) + " words translated into English and French.", "article")}{FONTS}<style>{CSS}{QUIZ_CSS if has_quiz else ""}</style></head><body><div class="wrap">
<header><span class="eyebrow">{fr_date(s["date"])}</span><nav class="row topnav">{" · ".join(nav)}</nav><h1>{html.escape(s["title"])}</h1><p class="sub">{html.escape(s.get("title_en") or s.get("title_fr",""))}</p></header>
<section class="player">
  {player}
</section>
<section><h2>The {len(words)} words</h2>{'<p class="note" style="margin:-4px 0 10px">Tap a word to see example sentences in ' + L["name"] + ', with English and French translations.</p>' if ex else ""}<ul class="vocab">{vocab}</ul></section>
<section><h2>The text</h2><div class="text hide" id="text" lang="{lang}">{"".join(paras_html)}</div><div class="text" id="textEn" lang="en" hidden>{en_html}</div></section>
<div class="row"><button class="chip" id="glossBtn" aria-pressed="false">Translations hidden</button>{'<button class="chip" id="enBtn" aria-pressed="false">Show English translation</button>' if en_html else ""}</div>
{src_html}
{quiz_card if has_quiz else ""}<div class="row"><button class="chip" id="shareBtn" type="button">Share this lesson</button></div>
<nav class="row">{" · ".join(nav)}</nav>
{FOOTER}
</div><script>{JS}</script></body></html>"""

def index_page(lessons, lang, L):
    items = "".join(f'<li><a href="cours/{s["date"]}.html"><span class="d">{s["date"][8:10]}/{s["date"][5:7]}/{s["date"][:4]}</span><span><span class="t">{html.escape(s["title"])}</span><span class="f">{html.escape(s.get("title_en") or s.get("title_fr",""))}</span></span></a></li>' for s in lessons)
    o = LANGS[L["other"][0]]
    other = "../" + o["out"]
    head = f'<a class="play" href="cours/{lessons[0]["date"]}.html">Read today\'s lesson →</a> ' if lessons else ""
    return f"""<!doctype html><html lang="en" translate="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{L["title"]} · Learn {L["name"]} with simple news and audio · Masimera</title>{seo(L["out"], L["title"] + " · Masimera", L["tagline"] + " All lessons, free.")}{FONTS}<style>{CSS}</style></head><body><div class="wrap">
<header><span class="eyebrow">{L["eyebrow"]}</span><h1>{L["title"]}</h1><p class="sub">{L["tagline"]}</p></header>
<p class="row">{head}<a href="mots.html">All words (FR · EN · {L["short"]})</a> · <a href="../index.html">Home</a></p>
<section><h2>All lessons</h2><ul class="list">{items or '<li class="note">The first lesson is coming soon.</li>'}</ul></section>
{FOOTER}
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


WORDS_QUIZ_JS = r"""
(function(){
var LANG=document.body.dataset.lang, PAGE=location.href.split('?')[0].split('#')[0];
var $=function(x){return document.getElementById(x)};
function esc(t){var d=document.createElement('div');d.textContent=t;return d.innerHTML}
function sh(a){for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t}return a}
var ALL=[].map.call(document.querySelectorAll('.vocab .card'),function(c){var ex=JSON.parse(c.dataset.ex||'[]');var e=ex[0]||null;
 return {fr:c.dataset.gr,en:c.dataset.fr,gr:c.dataset.tr.split(' · ')[0],v:c.dataset.v==='1',ex:e?e.slice(0,3):null,au:e&&e[3]?e[3]:''}});
var ch=parseInt(new URLSearchParams(location.search).get('challenge'),10); if(!(ch>=0&&ch<=10))ch=null;
if(ch!==null){$('wqTitle').textContent='A friend scored '+ch+'/10. Can you beat them?';$('wqStart').textContent='Accept the challenge →';}
var D=[],i=0,score=0,miss=[],AU=new Audio();
function pickSet(){var pool=sh(ALL.slice()),seen={},out=[];for(var k=0;k<pool.length&&out.length<10;k++){var w=pool[k];if(seen[w.gr])continue;seen[w.gr]=1;out.push(w)}return out}
function start(){D=pickSet();i=0;score=0;miss=[];$('wqIntro').hidden=true;$('wqEnd').hidden=true;$('wqQ').hidden=false;$('wqPts').textContent='0 points';show();$('wq').scrollIntoView({block:'start'})}
function show(){var it=D[i];$('wqN').textContent='Question '+(i+1)+' / 10';$('wqBar').style.width=(i*10)+'%';
 $('wqEn').textContent=it.fr;$('wqFr').textContent=it.en;$('wqFb').innerHTML='';$('wqNext').hidden=true;
 var others=sh(ALL.filter(function(o){return o.v===it.v&&o.gr!==it.gr&&o.fr!==it.fr})).map(function(o){return o.gr}).filter(function(g,k,a){return a.indexOf(g)===k}).slice(0,3);
 var o=sh([it.gr].concat(others));$('wqOpts').innerHTML='';
 o.forEach(function(w){var b=document.createElement('button');b.className='opt';b.type='button';b.textContent=w;b.onclick=function(){pick(b,w)};$('wqOpts').appendChild(b)})}
window.wqPlay=function(){var it=D[i];if(!it.au)return;AU.src=it.au;AU.currentTime=0;AU.play().catch(function(){})};
function pick(btn,w){var it=D[i],ok=w===it.gr;[].forEach.call($('wqOpts').children,function(b){b.disabled=true;if(b.textContent===it.gr)b.classList.add('ok')});
 if(ok)score++;else{btn.classList.add('ko');miss.push(it)}
 $('wqPts').textContent=score+(score===1?' point':' points');
 $('wqFb').innerHTML=(ok?'<strong>Correct!</strong>':'<strong>The answer: '+esc(it.gr)+'</strong>')+(it.ex?'<div class="exg">'+esc(it.ex[0])+(it.au?'<button class="say" type="button" aria-label="Listen" onclick="wqPlay()">'+SPK+'</button>':'')+'</div><div class="exe">'+esc(it.ex[1])+(it.ex[2]?' · '+esc(it.ex[2]):'')+'</div>':'');
 $('wqNext').hidden=false;$('wqNext').textContent=i==9?'See my score':'Next →'}
$('wqNext').onclick=function(){AU.pause();i++;if(i<10)show();else end()};
function end(){$('wqQ').hidden=true;$('wqEnd').hidden=false;$('wqBar').style.width='100%';$('wqSc').textContent=score+' / 10';
 var m=score==10?'Perfect!':score>=7?'Very good!':score>=4?'Not bad!':'Keep going: a little every day goes a long way.';
 if(ch!==null)m=score>ch?'You beat your friend ('+ch+'/10)!':score==ch?'Tie with your friend ('+ch+'/10)!':'Your friend wins this time ('+ch+'/10). Try again!';
 $('wqMsg').textContent=m;$('wqShare').textContent='Challenge a friend';
 $('wqRev').hidden=!miss.length;$('wqMiss').innerHTML=miss.map(function(x){return '<li><b>'+esc(x.gr)+'</b><span>'+esc(x.fr)+' · '+esc(x.en)+'</span></li>'}).join('')}
$('wqStart').onclick=start;$('wqAgain').onclick=start;
$('wqShare').onclick=function(){var u=PAGE+'?challenge='+score+'#wq',t='I got '+score+'/10 on the Masimera '+LANG+' challenge. Can you beat me?';
 if(navigator.share)navigator.share({text:t,url:u}).catch(function(){});
 else if(navigator.clipboard)navigator.clipboard.writeText(t+' '+u).then(function(){$('wqShare').textContent='Link copied ✓'});else prompt('Copy this link:',u)};
})();
"""

def words_quiz_html(L):
    return f"""<section class="qcard" id="wq">
<div id="wqIntro"><span class="k">{L["name"]} challenge</span><div class="t" id="wqTitle" style="margin:6px 0">Want to take the quiz?</div>
<p class="sub" style="margin:0 0 12px">10 random words from all the lessons. A new quiz every time.</p>
<div class="row"><button class="play" id="wqStart" type="button">Start the quiz →</button></div></div>
<div id="wqQ" hidden style="display:flex;flex-direction:column;gap:14px">
<div class="qhead"><span id="wqN"></span><span id="wqPts">0 points</span></div><div class="bar"><i id="wqBar"></i></div>
<div class="ask"><span class="tag">Choose the {L["name"]} word</span><span class="en" id="wqEn"></span><span class="fr" id="wqFr" style="color:var(--muted)"></span></div>
<div class="opts" id="wqOpts"></div><div class="fb" id="wqFb" aria-live="polite"></div>
<div class="row" style="justify-content:center"><button class="play" id="wqNext" type="button" hidden>Next →</button></div></div>
<div id="wqEnd" class="center" hidden><h2>Your score</h2><div class="score" id="wqSc"></div><p class="sub" id="wqMsg"></p>
<div class="row" style="margin-top:10px"><button class="play" id="wqShare" type="button">Challenge a friend</button><button class="chip" id="wqAgain" type="button">New quiz</button></div>
<section id="wqRev" style="text-align:left;margin-top:14px" hidden><h2>Words to review</h2><ul class="miss" id="wqMiss"></ul></section>{signup_box(L)}</div>
</section>"""

def sort_key(w):
    import unicodedata
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if not unicodedata.combining(c))

def gloss_page(lessons, lang, L):
    """One card per French word (French alphabetical order); a card lists every Greek/Italian word with that meaning."""
    outdir = os.path.join(ROOT, L["out"])
    vp = os.path.join(ROOT, L.get("verbs", ""))
    verbs = json.load(open(vp, encoding="utf-8")) if L.get("verbs") and os.path.exists(vp) else {}
    groups = {}
    for s in sorted(lessons, key=lambda s: s["date"]):
        fr = s.get("fr", {}); lem = s.get("lemma", {}); ex = s.get("examples", {})
        for p in s["paragraphs"]:
            for m in RX.finditer(p):
                w, en = m.group(1), m.group(2)
                f_all = fr.get(w, "").strip() or en
                vb = verbs.get(lem.get(w, ""))
                if vb:  # verbs: French infinitive, dictionary form, English infinitive
                    f_all, en = vb["fr"], vb["en"]
                lead = re.match(r"^\([^)]*\)\s*", f_all)
                lead = lead.group(0) if lead else ""
                terms = [t.strip() for t in re.split(r"\s*[,;/]\s*", f_all[len(lead):]) if t.strip()] or [f_all]
                for t in terms:
                    f = (lead + t) if lead else t
                    base = t.lstrip("\"«“ ")
                    skey, plain = fr_key(base)
                    key = (skey.replace("œ", "oe").replace("æ", "ae"), plain.lower())
                    g = groups.setdefault(key, dict(fr=f, words=[], en=[], ex=[], d=s["date"], v=bool(vb)))
                    label = lem[w] if vb else (f"{w} ({lem[w]})" if lem.get(w) else w)
                    if label not in g["words"]: g["words"].append(label)
                    for e_t in [x.strip() for x in en.split(",") if x.strip()]:
                        if e_t.lower() not in [y.lower() for y in g["en"]]: g["en"].append(e_t)
                    for e in ex.get(w, []):
                        if len(e) < 2 or any(x[0] == e[0] for x in g["ex"]): continue
                        e = list(e[:3]) + [""] * (3 - len(e[:3]))
                        n = ex_audio_name(lang, e[0]); fp = os.path.join(outdir, "audio", "ex", n)
                        if os.path.exists(fp):
                            e.append("audio/ex/" + n + "?v=" + hashlib.md5(open(fp, "rb").read()).hexdigest()[:8])
                        g["ex"].append(e)
    rows = sorted(groups.items(), key=lambda kv: kv[0])
    out, cur = [], None
    for key, g in rows:
        ch = (key[0][:1] or "#").upper()
        if ch != cur:
            cur = ch; out.append(f'<li class="letter">{html.escape(ch)}</li>')
        g["ex"] = g["ex"][:6]
        gr, en, n = " · ".join(g["words"]), ", ".join(g["en"]), len(g["ex"])
        hint = f'<span class="hint">{n} sentence{"s" if n > 1 else ""} ↻</span>' if n else ""
        data = html.escape(json.dumps(g["ex"][:6], ensure_ascii=False), quote=True)
        srch = html.escape(" ".join([g["fr"], gr, en, key[0]]).lower(), quote=True)
        out.append(f'<li data-s="{srch}"><button class="card" type="button" data-ex="{data}" data-gr="{html.escape(g["fr"])}" data-tr="{html.escape(gr)}" data-fr="{html.escape(en)}" data-lem="" data-v="{1 if g["v"] else 0}"'
                   f'{"" if n else " disabled"}><span class="gr">{html.escape(g["fr"])}</span><span class="fr">{html.escape(gr)}</span><span class="fr2">{html.escape(en)}</span>{hint}</button>'
                   f'<a class="from" href="cours/{g["d"]}.html">lesson of {g["d"][8:10]}/{g["d"][5:7]}</a></li>')
    js = """(function(){var q=document.getElementById('q');q.addEventListener('input',function(){var v=q.value.trim().toLowerCase();
document.querySelectorAll('.vocab li[data-s]').forEach(function(r){r.hidden=v&&r.dataset.s.indexOf(v)<0;});
document.querySelectorAll('.vocab li.letter').forEach(function(r){r.hidden=!!v;});});})();"""
    extra = (".vocab li.letter{grid-column:1/-1;border:0;padding:18px 0 2px;font-size:15px;font-weight:600;color:var(--accent)}"
             ".vocab .from{display:block;font-size:12px;color:var(--muted);padding:0 0 8px}.vocab li[hidden]{display:none}"
             ".lexc .card>.gr{font-family:var(--ui);color:var(--gloss)}.lexc .card>.fr{font-family:var(--text);font-size:17px;font-weight:600;color:var(--fg)}"
             ".lexc .card>.fr2{color:var(--muted)}")
    return f"""<!doctype html><html lang="en" translate="no" data-learn="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{L["name"]} vocabulary list with English and French · Masimera</title>{seo(L["out"] + "mots.html", L["name"] + " vocabulary · Masimera", "All the " + L["name"] + " words from the Masimera daily lessons, translated into English and French, with example sentences and audio.")}{FONTS}<style>{CSS}{GLOSS_CSS}{QUIZ_CSS}{SHARE_CSS}{extra}</style></head><body data-lang="{L["name"]}"><div class="wrap">
<header>{brand_mini()}<br><span class="eyebrow">{L["col"]}</span><h1>All words</h1><p class="sub">All the words from the lessons. Tap a word to see and hear example sentences.</p>{pitch(L)}</header>
{words_quiz_html(L)}
<input class="search" id="q" type="search" placeholder="Search (French, English or {L["name"]})…" autocomplete="off">
<ul class="vocab lexc">{"".join(out)}</ul>
<nav class="row"><a href="index.html">All lessons</a> · <a href="../index.html">Home</a></nav>
{FOOTER}
</div><script>{js}</script><script>var SPK={json.dumps(SPEAKER)};{WORDS_QUIZ_JS}</script><script>{JS}</script></body></html>"""

def build(lang, L):
    path = os.path.join(ROOT, L["file"])
    lessons = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    lessons.sort(key=lambda s: s["date"], reverse=True)
    outdir = os.path.join(ROOT, L["out"])
    os.makedirs(os.path.join(outdir, "cours"), exist_ok=True)
    os.makedirs(os.path.join(outdir, "quiz"), exist_ok=True)
    all_lemmas = sorted({v for x in lessons for v in x.get("lemma", {}).values()})
    for i, s in enumerate(lessons):
        prev = lessons[i + 1] if i + 1 < len(lessons) else None
        nxt = lessons[i - 1] if i > 0 else None
        items = quiz_items(s, lang, outdir, all_lemmas)
        if items:
            open(os.path.join(outdir, "quiz", s["date"] + ".html"), "w", encoding="utf-8").write(quiz_page(s, items, lang, L))
        open(os.path.join(outdir, "cours", s["date"] + ".html"), "w", encoding="utf-8").write(lesson_page(s, prev, nxt, lang, L, outdir, bool(items)))
    open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(index_page(lessons, lang, L))
    open(os.path.join(outdir, "mots.html"), "w", encoding="utf-8").write(gloss_page(lessons, lang, L))
    print(f"{lang}: built {len(lessons)} lesson(s)")

def redirect(target):
    t = html.escape(target, quote=True)
    return (f'<!doctype html><html lang="en" translate="no"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={t}">'
            f'<meta name="robots" content="noindex"><link rel="canonical" href="{t}"><title>Redirecting</title></head><body><p><a href="{t}">This lesson has moved: click here</a></p>'
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
    return f"""<!doctype html><html lang="en" translate="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Masimera · Learn Greek or Italian with simple daily news and audio</title>
{seo("", "Masimera · 15 minutes a day to learn Greek or Italian", "Every morning, a real local news story in simple Greek or Italian, with the hard words translated and audio. 15 minutes a day, free.")}
{FONTS}<style>{CSS}{HOME_CSS}</style></head><body><div class="wrap">
<header><a class="toplink" href="/method.html">The Masimera method</a><span class="eyebrow">15 minutes a day</span><h1 class="brand">Masimera</h1>
<p class="meaning">μάθημα (lesson) + μέρα (day): the lesson of the day</p></header>
<p class="lead">Every morning, a real news story, rewritten in simple sentences, with audio and the hard words translated into English and French. Slow and steady: a little every day, and you progress.</p>
<section><h2>Today's lessons</h2><div class="langs">{"".join(cards)}</div></section>
<section><h2>How it works</h2><ol class="steps">
<li><b>1</b><div><strong>Read a real story</strong><span>Local news, rewritten and simplified according to your level.</span></div></li>
<li><b>2</b><div><strong>Listen</strong><span>A natural voice reads the text. Slow it down if you need to.</span></div></li>
<li><b>3</b><div><strong>Learn 20 to 30 words</strong><span>Each word in English and French, with short example sentences you can hear.</span></div></li>
<li><b>4</b><div><strong>Come back tomorrow</strong><span>A new lesson every morning. All the words you've met stay in your glossary.</span></div></li>
</ol></section>
<section class="join" id="join"><h2 style="margin:0">Get it every morning</h2>
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
{FOOTER}
</div></body></html>"""

from math import erf as _erf, sqrt as _sqrt

def _chart_spoken():
    # Nation 2006, Table 13: conversation, cumulative coverage (word families, + proper nouns from 3,000)
    pts = [(0, 0.0), (1000, 84.0), (2000, 89.35), (3000, 96.03), (6000, 97.67), (7000, 97.95)]  # 1,000: measured on Masimera lessons
    L, R, T, B, XM, YLO, XLO = 56, 560, 30, 270, 8000, 0, 0
    x = lambda w: L + (w - XLO) / (XM - XLO) * (R - L)
    y = lambda p: B - (p - YLO) / (100 - YLO) * (B - T)
    out = ['<p class="ctitle"><b>With 3,000 word families, you understand about 96% of everyday conversation</b><br><span>Share of the words of native conversation you know, by vocabulary size</span></p>',
           '<div class="cscroll"><svg viewBox="0 0 760 330" role="img" aria-label="With 3,000 word families, you understand about 96% of everyday conversation" class="chart">']
    for p in (0, 20, 40, 60, 80, 100):
        out.append(f'<line x1="{L}" x2="{R}" y1="{y(p):.1f}" y2="{y(p):.1f}" class="cg"/><text x="{L-8}" y="{y(p)+4:.1f}" text-anchor="end" class="cl">{p}%</text>')
    for w in range(XLO, XM + 1, 1000):
        out.append(f'<text x="{x(w):.1f}" y="{B+18}" text-anchor="middle" class="cl">{w:,}</text>')
    out.append(f'<text x="{R}" y="{B+40}" text-anchor="end" class="cl">Word families you know</text>')
    for p, dy, lab in ((98, -3, ["98%: comfortable"]), (95, 13, ["95%: you can follow", "and guess the rest"])):
        tl = "".join(f'<tspan x="{R+8}" dy="{0 if i == 0 else 17}">{t}</tspan>' for i, t in enumerate(lab))
        out.append(f'<line x1="{L}" x2="{R}" y1="{y(p):.1f}" y2="{y(p):.1f}" class="cr"/><text x="{R+8}" y="{y(p)+dy:.1f}" class="cl">{tl}</text>')
    # smooth trend: least-squares fit of 100 - A·e^(-w/k1) - (100-A)·e^(-w/k2) to the points (dots show the real values)
    fit = lambda w: 100 - 79.5 * math.exp(-w / 300) - 20.5 * math.exp(-w / 2450)
    curve = [(w, fit(w)) for w in range(0, XM + 1, 25)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x(w):.1f},{y(p):.1f}" for i, (w, p) in enumerate(curve))
    out.append(f'<path d="{path}" class="cline"/>')
    for w, p in pts:
        out.append(f'<circle cx="{x(w):.1f}" cy="{y(p):.1f}" r="4.5" class="{'copen' if w == 1000 else 'cdot'}"><title>{w:,} word families: {p:.0f}%</title></circle>')
        if w == 1000:
            out.append(f'<text x="{x(w)+12:.1f}" y="{y(p)+42:.1f}" class="cv">84%<tspan class="cl"> (measured on Masimera lessons)</tspan></text>')
        elif w and w != 6000:
            out.append(f'<text x="{x(w) + (8 if w == 3000 else 0):.1f}" y="{y(p) + 22:.1f}" text-anchor="{'start' if w == 3000 else 'middle'}" class="cv">{p:.0f}%</text>')
    out.append("</svg></div>")
    return "".join(out)

def _chart_cefr():
    # Milton & Alexiou: learner vocabulary (lemmatised words) per CEFR level, low-high across the languages they report
    # (French, Greek, English); C1-C2 tests were capped at 5,000 words, so those are low estimates.
    lv = [("A1", 1160, 1500), ("A2", 1650, 2500), ("B1", 2420, 3290), ("B2", 2630, 3960), ("C1", 3210, 4500), ("C2", 3525, 5000)]
    L, R, T, B, YM = 70, 740, 30, 270, 5500
    band = (R - L) / len(lv)
    x = lambda i: L + band * (i + 0.5)
    y = lambda w: B - w / YM * (B - T)
    out = ['<p class="ctitle"><b>You reach B1 with roughly 3,000 words</b><br><span>Words learners know at each level (dictionary words): middle point and range across studies</span></p>',
           '<div class="cscroll"><svg viewBox="0 0 760 320" role="img" aria-label="You reach B1 with roughly 3,000 words" class="chart">']
    for w in range(0, 5001, 1000):
        out.append(f'<line x1="{L}" x2="{R}" y1="{y(w):.1f}" y2="{y(w):.1f}" class="cg"/><text x="{L-8}" y="{y(w)+4:.1f}" text-anchor="end" class="cl">{w:,}</text>')
    for i, (name, lo, hi) in enumerate(lv):
        mid = (lo + hi) / 2
        cls = "cdot" if name == "B1" else "cdotm"
        out.append(f'<line x1="{x(i):.1f}" x2="{x(i):.1f}" y1="{y(lo):.1f}" y2="{y(hi):.1f}" class="cwh"/>'
                   f'<line x1="{x(i)-8:.1f}" x2="{x(i)+8:.1f}" y1="{y(lo):.1f}" y2="{y(lo):.1f}" class="cwh"/><line x1="{x(i)-8:.1f}" x2="{x(i)+8:.1f}" y1="{y(hi):.1f}" y2="{y(hi):.1f}" class="cwh"/>'
                   f'<circle cx="{x(i):.1f}" cy="{y(mid):.1f}" r="5" class="{cls}"><title>{name}: {lo:,} to {hi:,} words</title></circle>'
                   f'<text x="{x(i)+12:.1f}" y="{y(mid)+5:.1f}" class="cv">{round(mid, -2):,.0f}</text>'
                   f'<text x="{x(i):.1f}" y="{B+20}" text-anchor="middle" class="cl">{name}</text>')
    out.append(f'<text x="{R}" y="{B+42}" text-anchor="end" class="cl">C1 and C2 are likely higher: the tests stopped at 5,000 words</text></svg></div>')
    return "".join(out)

LEVELS = [(1, "A, easy", 97, 99, 100, "4–5", "60–75"), (2, "A", 96, 99, 99, "5", "70–85"), (3, "A", 95, 98, 99, "5–6", "80–95"),
          (4, "B, medium", 92, 97, 98, "6–7", "100–120"), (5, "B (today's lessons)", 89, 95, 97, "7–8", "110–145"),
          (6, "B", 87, 94, 97, "8–9", "125–155"), (7, "B", 85, 93, 96, "9–10", "140–170"), (8, "C, advanced", 82, 91, 95, "10–12", "160–190"),
          (9, "C", 79, 89, 94, "12–14", "175–205"), (10, "C", 76, 87, 93, "14–16", "190–220")]

def _levels_table():
    rows = "".join(f'<tr{" class=cur" if n == 5 else ""}><td>{n}</td><td>{base}</td><td>{a}%</td><td>{b}%</td><td>{c}%</td><td>{sl}</td><td>{ln}</td></tr>' for n, base, a, b, c, sl, ln in LEVELS)
    return ('<div class="tscroll"><table class="lv"><thead><tr><th>Level</th><th>Base text</th><th>Among the 2,000 most common</th><th>Among the 5,000</th><th>Among the 10,000</th>'
            f'<th>Words per sentence</th><th>Text length (words)</th></tr></thead><tbody>{rows}</tbody></table></div>')

CHART_CSS = """
.ctitle{margin:6px 0 0;font-size:16px}.ctitle span{font-size:14px;color:var(--muted)}.cscroll{overflow-x:auto;margin:4px 0}.chart{width:100%;min-width:600px;height:auto;font-family:var(--ui);font-size:15px}
.chart .ct{font-size:19px;font-weight:600;fill:var(--fg)}.chart .cs,.chart .cl{fill:var(--muted)}.chart .cv{fill:var(--fg)}
.chart .cg{stroke:var(--line)}.chart .cr{stroke:var(--muted);stroke-dasharray:3 3}.chart .cline{fill:none;stroke:var(--accent);stroke-width:2.5}
.chart .cdot{fill:var(--accent)}.chart .cdotm{fill:var(--muted)}.chart .cmut{stroke:var(--line);stroke-width:2.5}.chart .clead{stroke:var(--muted);stroke-width:.75}.chart .copen{fill:var(--bg);stroke:var(--accent);stroke-width:2}.chart .cwh{stroke:var(--muted);stroke-width:1.5}
.tscroll{overflow-x:auto}.lv{border-collapse:collapse;width:100%;font-size:14px}.lv th{font-size:12px;font-weight:600;text-align:left;color:var(--muted);padding:6px 8px 6px 0;border-bottom:1px solid var(--line);vertical-align:bottom}
.lv td{padding:7px 8px 7px 0;border-bottom:1px solid var(--line);white-space:nowrap}.lv tr.cur td{font-weight:700}
"""

METHOD_CSS = """
.cards3{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.c3{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:8px}
.c3 h3{margin:0;font-size:18px}.c3 .lbl{font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-top:4px}
.c3 p{margin:0;font-size:15px;line-height:1.5}
.nums{width:100%;border-collapse:collapse}.nums td{padding:9px 8px 9px 0;border-bottom:1px solid var(--line);vertical-align:baseline}
.nums td:last-child{text-align:right;font-weight:600;white-space:nowrap}
.big{font-size:20px;line-height:1.5;margin:0}
.keys{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:4px 0 8px}
.key{border-top:3px solid var(--accent);padding:12px 2px 0}
.key b{display:block;font-size:26px;line-height:1.15;color:var(--accent);margin-bottom:6px}
.key p{margin:0;font-size:16px;line-height:1.5}
.src{font-size:13px;color:var(--muted)}.src li{margin:4px 0}
"""

def method_page():
    srcs = [("Brysbaert et al., 2016", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4965448"),
            ("Milton & Alexiou, vocabulary size and CEFR levels", "https://www.enl.auth.gr/gala/14th/Papers/English%20papers/Milton&Alexiou.pdf"),
            ("Nation, 2006", "https://www.wgtn.ac.nz/__data/assets/pdf_file/0018/1626120/2006-How-large-a-vocab.pdf"),
            ("Matsuoka & Hirsh, 2010 (on Hu & Nation, 2000)", "https://files.eric.ed.gov/fulltext/EJ887877.pdf"),
            ("Chen & Feng, 2017", "https://www.degruyterbrill.com/document/doi/10.1515/cjal-2017-0004/html?lang=en"),
            ("Roediger & Karpicke, 2006", "https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf"),
            ("Ellis, 2002", "https://www.cambridge.org/core/product/C4A2C08A0900E306078B9819D7ABF428"),
            ("Cepeda et al., 2006", "https://pubmed.ncbi.nlm.nih.gov/16719566/")]
    src_html = "".join(f'<li><a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(t)}</a></li>' for t, u in srcs)
    return f"""<!doctype html><html lang="en" translate="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Masimera method · How to learn a language with simple daily news</title>{seo("method.html", "The Masimera method", "How we understand a language: words, sentence structure and working out the rest. How many words you need, and why 15 minutes of simple news a day works.")}{FONTS}<style>{CSS}{SHARE_CSS}{METHOD_CSS}{CHART_CSS}</style></head><body><div class="wrap">
<header>{brand_mini()}<br><span class="eyebrow">The Masimera method</span><h1>How you really learn to understand a language</h1>
<p class="big">Understanding a language rests on three things: knowing the words, seeing how sentences are built, and working out what you don't know yet. Masimera trains all three, every day, in 15 minutes.</p></header>

<section class="keys">
<div class="key"><b>3,000 words</b><p>are enough to follow about 96% of everyday conversation, roughly level B1. The most common words do most of the work.</p></div>
<div class="key"><b>Hear, not just read</b><p>Knowing a word is not the same as catching it in a spoken sentence. Text and audio together train both.</p></div>
<div class="key"><b>15 minutes a day</b><p>Meeting words again and again, and recalling them, makes them stick far better than cramming.</p></div>
</section>

<section><h2>How many words do you need?</h2>
<table class="nums"><tbody>
<tr><td>Get by day to day (level A2)</td><td>1,500 – 2,200 words</td></tr>
<tr><td>Hold a conversation on everyday topics (B1)</td><td>2,500 – 3,300 words</td></tr>
<tr><td>Read a novel without a dictionary</td><td>8,000 – 9,000 word families</td></tr>
<tr><td>An educated native speaker understands</td><td>about 42,000 words</td></tr>
</tbody></table>
<p class="note" style="margin-top:10px">A word means a dictionary word: <i>eat, eats, ate, eaten</i> count as one.</p>
<p>The good news: a few thousand common words do most of the work. In our lessons, about <b>9 words in 10</b> are among the 2,000 most common words of the language. We translate the rest.</p></section>

<section><h2>Where do you stand?</h2>
{_chart_spoken()}
<p>The first few thousand words do most of the work: with 2,000 word families you already know 9 words in 10 of what native speakers say. Beyond 3,000, each new word adds little to everyday understanding.</p>
<p style="border-left:3px solid var(--accent);padding:4px 0 4px 14px"><b>But knowing a word is not the same as hearing it.</b> In real speech, words run into each other: there are no gaps between them, and the sentence goes by only once. These percentages assume you can tell where each word starts and ends, and follow how the sentence is built. For most learners, that is the real hurdle. That's why every Masimera lesson pairs the text with its audio: first you see the words, then you learn to hear them.</p>
{_chart_cefr()}
<p>The levels are close together in words: each step is a few hundred to a thousand new words. A short lesson every day, with 20 to 30 words, covers that ground steadily.</p></section>

<section><h2>Three layers, trained every day</h2><div class="cards3">
<div class="c3"><h3>1. Knowing the words</h3>
<span class="lbl">What research says</span><p>A word sticks after meeting it several times: around 10 encounters give strong results. Recalling a word from memory fixes it far better than rereading it (61% remembered a week later, versus 40%).</p>
<span class="lbl">What Masimera does</span><p>The most common words first, the rest translated. Every word comes back in the text, two example sentences, the audio and the quiz, which makes you recall it.</p></div>
<div class="c3"><h3>2. Seeing how sentences are built</h3>
<span class="lbl">What research says</span><p>We pick up grammar by meeting the same patterns again and again, more than by learning rules.</p>
<span class="lbl">What Masimera does</span><p>Short sentences, one idea each, so the structure stands out. The same patterns come back every day. Each verb shows its dictionary form, and a full translation lets you check you understood the sentence, not just the words.</p></div>
<div class="c3"><h3>3. Working out the rest</h3>
<span class="lbl">What research says</span><p>You can guess an unknown word from context only if you understand almost everything around it: 95% of the words for some readers, 98% for most.</p>
<span class="lbl">What Masimera does</span><p>Every text is tuned to stay in that zone. Translations are hidden by default: you try to guess first, then tap the word to check.</p></div>
</div></section>

<section><h2>Our levels</h2>
<p>Coming soon: every lesson in 10 levels. Today's lessons are level 5. Each level up uses a few more rare words and slightly longer sentences; the words outside the most common ones are the ones we translate.</p>
{_levels_table()}
<p class="note" style="margin-top:8px">These are starting targets, adjusted over time with readers' "Too easy? / Too hard?" choices and quiz scores.</p></section>

<section><h2>Little, but every day</h2>
<p>Spreading learning over time makes it stick far better than cramming. That's why Masimera is one short lesson each morning, built on a real local news story: you remember better what actually interests you, and you want to come back tomorrow.</p>
<p class="row"><a class="play" href="/">Read today's lesson →</a><a href="/#join">Get it every morning</a></p></section>

<section><h2>Sources</h2><ul class="src">{src_html}</ul></section>
{FOOTER}
</div></body></html>"""

def thanks_page():
    return f"""<!doctype html><html lang="en" translate="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thank you · Masimera</title><meta name="robots" content="noindex">{FONTS}<style>{CSS}</style></head><body><div class="wrap">
<header><span class="eyebrow">Masimera</span><h1>You're in!</h1>
<p class="sub">Your first lesson arrives tomorrow morning, around 6 am (Paris time). If you don't see it, check your spam folder.</p></header>
<p class="row"><a class="play" href="index.html">Back to today's lessons</a></p>
{FOOTER}
</div></body></html>"""

def main():
    for lang, L in LANGS.items():
        build(lang, L)
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(home_page())
    open(os.path.join(ROOT, "thanks.html"), "w", encoding="utf-8").write(thanks_page())
    open(os.path.join(ROOT, "method.html"), "w", encoding="utf-8").write(method_page())
    # anciennes adresses du grec (avant le dossier grec/) → redirection
    for lang, L in LANGS.items():
        if not L.get("legacy"): continue
        os.makedirs(os.path.join(ROOT, "cours"), exist_ok=True)
        for s in json.load(open(os.path.join(ROOT, L["file"]), encoding="utf-8")):
            open(os.path.join(ROOT, "cours", s["date"] + ".html"), "w", encoding="utf-8").write(redirect(f'../{L["out"]}cours/{s["date"]}.html'))
        open(os.path.join(ROOT, "mots.html"), "w", encoding="utf-8").write(redirect(f'{L["out"]}mots.html'))
    open(os.path.join(ROOT, ".nojekyll"), "w").close()
    urls = [(BASE, None), (BASE + "method.html", None)]
    for lang, L in LANGS.items():
        ls = sorted(json.load(open(os.path.join(ROOT, L["file"]), encoding="utf-8")), key=lambda s: s["date"], reverse=True)
        last = ls[0]["date"] if ls else None
        urls += [(BASE + L["out"], last), (BASE + L["out"] + "mots.html", last)]
        urls += [(f'{BASE}{L["out"]}cours/{s["date"]}.html', s["date"]) for s in ls]
    sm = "".join(f"<url><loc>{u}</loc>{f'<lastmod>{d}</lastmod>' if d else ''}</url>" for u, d in urls)
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + sm + "</urlset>\n")
    open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")

if __name__ == "__main__":
    main()
