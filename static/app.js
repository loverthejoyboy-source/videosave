(() => {
"use strict";
const V = "1.0";
const P = {youtube:["YouTube","youtube.com","youtu.be"],tiktok:["TikTok","tiktok.com"],instagram:["Instagram","instagram.com"],
  facebook:["Facebook","facebook.com","fb.watch"],x:["X (Twitter)","x.com","twitter.com"],vimeo:["Vimeo","vimeo.com"],
  dailymotion:["Dailymotion","dailymotion.com","dai.ly"],reddit:["Reddit","reddit.com","redd.it"]};
const $ = id => document.getElementById(id);
let token = "", hint = "", busy = false;

function detect(u) {
  try { const h = new URL(u).hostname.toLowerCase();
    for (const k in P) if (P[k].slice(1).some(d => h === d || h.endsWith("." + d))) return k;
  } catch (e) {}
  return null;
}
async function api(path, body, tok) {
  const r = await fetch(path, {method:"POST", headers:{"Content-Type":"application/json","X-Token":tok||""}, body:JSON.stringify(body)});
  let j = {}; try { j = await r.json(); } catch (e) {}
  if (!r.ok) { const e = new Error(j.error || "Something went wrong. Please try again."); e.kind = j.kind; throw e; }
  return j;
}
async function getToken() { token = (await api("/api/token", {agree:true, v:V})).token; }
function showErr(m) { $("err").textContent = m; $("err").hidden = !m; }

function onInput() {
  const v = $("url").value.trim(), k = detect(v), ask = !!v && !k;
  if (!ask) hint = "";
  $("chip").hidden = !k; if (k) $("chip").textContent = "✓ " + P[k][0] + " detected";
  $("pick").hidden = !ask;
  document.querySelectorAll("#sites button").forEach(b => b.classList.toggle("on", b.dataset.k === (k || hint)));
  $("go").disabled = busy || !v || (ask && !hint); showErr("");
}
function buildPicker() {
  for (const k in P) { const b = document.createElement("button"); b.type = "button"; b.textContent = P[k][0]; b.dataset.k = k;
    b.onclick = () => { const v = $("url").value.trim(); if (v && !detect(v)) { hint = k; onInput(); } };
    $("sites").appendChild(b); }
}
function render(d) {
  $("ti").textContent = d.title;
  const th = $("th"); if (d.thumb) { th.src = d.thumb; th.hidden = false; } else th.hidden = true;
  $("fm").replaceChildren(...d.formats.map(f => {
    const a = document.createElement("a"); a.href = f.url; a.target = "_blank"; a.rel = "noopener noreferrer nofollow";
    a.textContent = f.label + " · " + f.ext.toUpperCase() + (f.size ? " · " + (f.size/1048576).toFixed(1) + " MB" : ""); return a; }));
  $("res").hidden = false; $("res").scrollIntoView({behavior:"smooth", block:"nearest"});
}
async function go() {
  busy = true; $("go").disabled = true; $("goLabel").textContent = "Working…"; $("load").hidden = false; $("res").hidden = true; showErr("");
  const body = {url:$("url").value.trim(), platform:hint, website:$("website").value};
  try {
    let d;
    try { d = await api("/api/parse", body, token); }
    catch (e) { if (e.kind !== "token") throw e; await getToken(); d = await api("/api/parse", body, token); }
    render(d);
  } catch (e) { showErr(e.message); }
  busy = false; $("goLabel").textContent = "Download"; $("load").hidden = true; onInput();
}
function modal(readonly) { $("terms").hidden = false; $("agree").hidden = readonly; $("close").hidden = !readonly; (readonly ? $("close") : $("agree")).focus(); }

buildPicker();
$("url").addEventListener("input", onInput);
$("go").addEventListener("click", go);
$("url").addEventListener("keydown", e => { if (e.key === "Enter" && !$("go").disabled) go(); });
["tosLink","tosLink2","tosLink3"].forEach(id => $(id).addEventListener("click", e => { e.preventDefault(); modal(true); }));
$("close").addEventListener("click", () => { $("terms").hidden = true; });
$("agree").addEventListener("click", async () => {
  $("agree").disabled = true;
  try { await getToken(); } catch (e) { $("agree").disabled = false; alert(e.message); return; }
  try { localStorage.setItem("tos", JSON.stringify({v:V, t:Date.now()})); } catch (e) {}
  $("terms").hidden = true; $("url").disabled = false; $("url").focus(); $("agree").disabled = false;
});
modal(false); // shown on every page load
})();
