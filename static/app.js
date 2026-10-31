(() => {
"use strict";
const V = "1.1";
const P = {youtube:["YouTube","youtube.com","youtu.be"],tiktok:["TikTok","tiktok.com"],instagram:["Instagram","instagram.com"],
  facebook:["Facebook","facebook.com","fb.watch"],x:["X (Twitter)","x.com","twitter.com"],snapchat:["Snapchat","snapchat.com"],
  vimeo:["Vimeo","vimeo.com"],dailymotion:["Dailymotion","dailymotion.com"],reddit:["Reddit","reddit.com"]};
const $ = id => document.getElementById(id);
let hint = "", busy = false;

function detect(u) {
  try { const h = new URL(u).hostname.toLowerCase();
    for (const k in P) if (P[k].slice(1).some(d => h === d || h.endsWith("." + d))) return k;
  } catch (e) {}
  return null;
}

// API helper (no session token)
async function api(path, body) {
  const r = await fetch(path, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
  let j = {}; try { j = await r.json(); } catch (e) {}
  if (!r.ok) { const e = new Error(j.error || "Something went wrong."); e.kind = j.kind; throw e; }
  return j;
}

function showErr(m) { $("err").textContent = m; $("err").hidden = !m; }

// --- LOCAL STORAGE HISTORY LOGIC ---
function loadHistory() {
  try {
    const hist = JSON.parse(localStorage.getItem("clipkeep_history") || "[]");
    const container = $("historyContainer");
    if (hist.length === 0) { container.hidden = true; return; }
    
    container.innerHTML = "";
    hist.forEach(url => {
      const chip = document.createElement("div");
      chip.className = "history-chip";
      const shortUrl = url.length > 30 ? url.substring(0, 27) + "..." : url;
      chip.append("🔗 " + shortUrl + " ");
      const x = document.createElement("span"); x.textContent = "×"; chip.appendChild(x);
      
      chip.onclick = (e) => {
        if(e.target.tagName === 'SPAN') return; 
        $("url").value = url;
        onInput();
        go();
      };
      
      chip.querySelector("span").onclick = (e) => {
        e.stopPropagation();
        const newHist = hist.filter(h => h !== url);
        localStorage.setItem("clipkeep_history", JSON.stringify(newHist));
        loadHistory();
      };
      
      container.appendChild(chip);
    });
    container.hidden = false;
  } catch (e) { console.error("History load failed", e); }
}

function saveHistory(url) {
  if (!url) return;
  try {
    let hist = JSON.parse(localStorage.getItem("clipkeep_history") || "[]");
    hist = hist.filter(h => h !== url);
    hist.unshift(url);
    hist = hist.slice(0, 5);
    localStorage.setItem("clipkeep_history", JSON.stringify(hist));
    loadHistory();
  } catch (e) {}
}
// ------------------------------------

function onInput() {
  const v = $("url").value.trim(), k = detect(v), ask = !!v && !k;
  if (!ask) hint = "";
  $("chip").hidden = !k; if (k) $("chip").textContent = "✓ " + P[k][0] + " detected";
  $("pick").hidden = !ask;
  document.querySelectorAll("#sites button").forEach(b => b.classList.toggle("on", b.dataset.k === (k || hint)));
  $("go").disabled = busy || !v || (ask && !hint); showErr("");
}

function buildPicker() {
  for (const k in P) { 
    const b = document.createElement("button"); b.type = "button"; b.textContent = P[k][0]; b.dataset.k = k;
    b.onclick = () => { const v = $("url").value.trim(); if (v && !detect(v)) { hint = k; onInput(); } };
    $("sites").appendChild(b); 
  }
}

function render(d) {
  $("ti").textContent = d.title;
  const th = $("th"); if (d.thumb) { th.src = d.thumb; th.hidden = false; } else th.hidden = true;
  $("fm").replaceChildren(...d.formats.map(f => {
    const a = document.createElement("a"); a.href = f.url; a.target = "_blank"; a.rel = "noopener noreferrer nofollow";
    a.textContent = f.label + " · " + f.ext.toUpperCase() + (f.size ? " · " + (f.size/1048576).toFixed(1) + " MB" : ""); 
    return a; 
  }));
  $("res").hidden = false; $("res").scrollIntoView({behavior:"smooth", block:"nearest"});
}

async function go() {
  busy = true; $("go").disabled = true; $("goLabel").textContent = "Working…"; $("load").hidden = false; $("res").hidden = true; showErr("");
  const currentUrl = $("url").value.trim();
  const body = {url: currentUrl, platform: hint, website: $("website").value};
  
  try {
    const d = await api("/api/parse", body);
    render(d);
    saveHistory(currentUrl);
  } catch (e) { 
    showErr(e.message); 
  }
  
  busy = false; $("goLabel").textContent = "Download"; $("load").hidden = true; onInput();
}

function modal(readonly) { $("terms").hidden = false; $("agree").hidden = readonly; $("close").hidden = !readonly; }

buildPicker();
loadHistory();

$("url").addEventListener("input", onInput);
$("go").addEventListener("click", go);
$("url").addEventListener("keydown", e => { if (e.key === "Enter" && !$("go").disabled) go(); });
["tosLink","tosLink2","tosLink3"].forEach(id => $(id).addEventListener("click", e => { e.preventDefault(); modal(true); }));
$("close").addEventListener("click", () => { $("terms").hidden = true; });

// "I agree" button: remember consent and unlock the input
$("agree").addEventListener("click", () => {
  try { localStorage.setItem("tos", JSON.stringify({v:V, t:Date.now()})); } catch (e) {}
  $("terms").hidden = true; 
  $("url").disabled = false; 
  $("url").focus(); 
});

modal(false);
})();
