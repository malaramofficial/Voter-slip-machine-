from pathlib import Path
import sys

root = Path(sys.argv[1])
html_path = root / "app/src/main/assets/index.html"
s = html_path.read_text(encoding="utf-8")

# Force a true mobile viewport and fluid sizing in the embedded WebView.
viewport = '<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">'
if 'name="viewport"' in s:
    s = s.replace('width=device-width, initial-scale=1', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover', 1)
else:
    s = s.replace("<head>", "<head>\\n" + viewport, 1)
s = s.replace('<h1>🗳️ वोटर पर्ची जनरेटर</h1>\n  <small id="hdrSub"></small>', '<h1>🗳️ वोटर पर्ची जनरेटर</h1>\n  <small id="hdrSub"></small>\n  <div style="margin-top:4px;font-size:13px;color:#e8f2ff;font-weight:600">डेवलपर: Mala Ram Godara</div>')

s = s.replace(
'  .actions { text-align:center; }',
'''  .actions { text-align:center; }
  .stats { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin-bottom:12px; }
  .stat { background:#fff; border:1px solid var(--bd); border-radius:10px; padding:12px 8px; text-align:center; }
  .stat strong { display:block; font-size:24px; color:var(--c); }\n  .status-count { display:block; width:100%; border:0; background:transparent; color:var(--c); font-size:24px; font-weight:800; padding:0 0 4px; cursor:pointer; }
  .stat span { font-size:12px; color:#4a5a6a; }
  .progress { height:8px; background:#e1e8ef; border-radius:8px; overflow:hidden; margin-top:8px; }
  .progress > div { height:100%; width:0; background:#15803d; transition:width .2s; }
  .cutTag { display:inline-block; color:#166534; background:#dcfce7; border-radius:5px; padding:2px 5px; font-size:12px; font-weight:bold; }
  .historyItem { padding:10px 0; border-bottom:1px solid var(--bd); }
  .historyItem:last-child { border-bottom:0; }
  .muted { color:#5b6b7b; font-size:13px; }''')
s = s.replace(
'  <section class="card" id="searchCard">',
'''  <section class="card" id="cutDashboard">
    <b>📊 पर्ची प्रगति</b>
    <div class="stats" style="margin-top:8px">
      <div class="stat"><button id="totalCount" class="status-count" data-kind="all">0</button><span>कुल वोटर</span></div>
      <div class="stat"><button id="cutCount" class="status-count" data-kind="cut">0</button><span>पर्ची कट चुकी</span></div>
      <div class="stat"><button id="leftCount" class="status-count" data-kind="left">0</button><span>बाकी पर्चियाँ</span></div>
    </div>
    <div class="progress"><div id="cutProgress"></div></div>
    <div class="row" style="margin-top:12px;gap:6px;flex-wrap:wrap">
      <button class="alt" data-page="home">🏠 होम</button><button class="alt" data-page="wards">🏘️ वार्ड रिपोर्ट</button><button class="alt" data-page="cut">✅ कटी पर्चियाँ</button><button class="alt" data-page="left">⏳ बाकी पर्चियाँ</button>
    </div>
    <div style="margin-top:16px" id="wardPage" class="hide"><b>🏘️ वार्ड-वार पर्ची रिपोर्ट</b><p class="muted">किसी वार्ड की संख्या पर क्लिक करके उस वार्ड की कटी या बाकी पर्चियों के नाम देखें।</p><div id="wardStats" style="margin-top:8px;overflow-x:auto"></div></div>
    <div style="margin-top:16px" id="statusPage" class="hide"><b id="statusPageTitle">पर्ची सूची</b><input id="statusSearch" type="search" placeholder="नाम / पिता का नाम / मकान नंबर खोजें" style="width:100%;margin-top:10px"><div id="statusList" style="margin-top:8px"></div></div>
    <div class="row" style="margin-top:10px"><button class="alt" id="showHistory">📋 पर्ची हिस्ट्री देखें</button></div>
  </section>
  <section class="card hide" id="historyPanel">
    <div class="row" style="justify-content:space-between"><b>📋 पर्ची काटने की हिस्ट्री</b><button class="alt" id="closeHistory">बंद करें</button></div>
    <input id="historySearch" type="search" placeholder="नाम / पिता का नाम / मकान नंबर खोजें" style="width:100%;margin-top:10px">
    <div id="historyList" style="margin-top:8px"></div>
  </section>
  <section class="card" id="searchCard">''')
s = s.replace(
'      <button id="print">🖨️ Print Slip</button>\n      <button class="alt" id="edit">✏️ सुधारें</button>',
'      <button id="print">🖨️ Print Slip</button>\n      <button id="markCut">✓ पर्ची काटें</button>\n      <button class="alt" id="edit">✏️ सुधारें</button>')
s = s.replace('var DATA = BASE, EDITS = {}, cur = null;', 'var DATA = BASE, EDITS = {}, CUTS = {}, cur = null;')
s = s.replace(
'  try{ EDITS = JSON.parse(ld("voterEdits2")||"{}") || {}; }catch(e){ EDITS = {}; }',
'  try{ EDITS = JSON.parse(ld("voterEdits2")||"{}") || {}; }catch(e){ EDITS = {}; }\n  try{ CUTS = JSON.parse(ld("voterCuts3")||"{}") || {}; }catch(e){ CUTS = {}; }')
s = s.replace('  status();\n}', '  status();\n  updateCutDashboard();\n}', 1)
old_status = '''function status(){
  var n = DATA.length, chk = DATA.filter(function(d){ return d.c && !EDITS[key(d)]; }).length;
  $("status").textContent = "कुल " + n + " वोटर लोड" + (chk ? " • " + chk + " रिकॉर्ड स्कैन से पढ़े गए हैं और जाँच-योग्य (⚠) हैं" : "");
}'''
new_status = old_status + '''
function cutCount(){ return DATA.filter(function(d){ return !!CUTS[key(d)]; }).length; }
function updateCutDashboard(){
  var total = DATA.length, cut = cutCount(), left = Math.max(0,total-cut);
  $("totalCount").textContent = total; $("cutCount").textContent = cut; $("leftCount").textContent = left;
  $("cutProgress").style.width = (total ? Math.round(cut*100/total) : 0) + "%";
  renderWardStats();
  if(cur!==null) updateMarkButton();
}
function renderWardStats(){
  var wards = {};
  DATA.forEach(function(d){
    var r=rec(d), ward=String(r.w||"").trim()||"अनिर्दिष्ट";
    if(!wards[ward]) wards[ward]={total:0,cut:0};
    wards[ward].total++;
    if(CUTS[key(d)]) wards[ward].cut++;
  });
  var names=Object.keys(wards).sort(function(a,b){
    var na=parseInt(a,10), nb=parseInt(b,10);
    if(!isNaN(na)&&!isNaN(nb)) return na-nb;
    return a.localeCompare(b,"hi");
  });
  var total=0, cut=0;
  names.forEach(function(w){ total+=wards[w].total; cut+=wards[w].cut; });
  if(!names.length){ $("wardStats").innerHTML='<p class="muted">वोटर डेटा लोड होने पर वार्ड-वार रिपोर्ट यहाँ दिखेगी।</p>'; return; }
  $("wardStats").innerHTML='<table style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr style="background:#eef4fa"><th style="padding:8px;text-align:left">वार्ड</th><th style="padding:8px;text-align:right">कुल</th><th style="padding:8px;text-align:right">कट चुकी</th><th style="padding:8px;text-align:right">बाकी</th></tr></thead><tbody>'+
    names.map(function(w){var x=wards[w];return '<tr style="border-bottom:1px solid var(--bd)"><td style="padding:8px">वार्ड '+esc(w)+'</td><td style="padding:8px;text-align:right"><button class="alt ward-filter" data-ward="'+esc(w)+'" data-kind="all">'+x.total+'</button></td><td style="padding:8px;text-align:right;color:#166534;font-weight:bold"><button class="alt ward-filter" data-ward="'+esc(w)+'" data-kind="cut">'+x.cut+'</button></td><td style="padding:8px;text-align:right;font-weight:bold"><button class="alt ward-filter" data-ward="'+esc(w)+'" data-kind="left">'+(x.total-x.cut)+'</button></td></tr>';}).join('')+
    '<tr style="background:#f4f7fa;font-weight:bold"><td style="padding:8px">कुल</td><td style="padding:8px;text-align:right">'+total+'</td><td style="padding:8px;text-align:right">'+cut+'</td><td style="padding:8px;text-align:right">'+(total-cut)+'</td></tr></tbody></table>';
}
function showDataPage(page){
  $("wardPage").classList.toggle("hide",page!=="wards");
  $("statusPage").classList.toggle("hide",page!=="cut"&&page!=="left");
  if(page==="cut"||page==="left"){ renderStatusList(page==="cut"?"cut":"left",""); $("statusPageTitle").textContent=page==="cut"?"✅ जिनकी पर्ची कट चुकी है":"⏳ जिनकी पर्ची बाकी है"; }
}
function renderStatusList(kind, ward){
  var q=norm($("statusSearch").value||""), list=$("statusList"), rows=[];
  DATA.forEach(function(d){var r=rec(d), w=String(r.w||"").trim()||"अनिर्दिष्ट", done=!!CUTS[key(d)]; if(ward!==""&&w!==ward)return; if(kind==="cut"&&!done)return; if(kind==="left"&&done)return; if(kind==="all"&&false)return; var hay=norm(r.n+" "+r.r+" "+r.h);if(q&&hay.indexOf(q)<0)return; rows.push({d:d,r:r,done:done,w:w});});
  if(!rows.length){list.innerHTML='<p class="muted">इस श्रेणी में कोई वोटर नहीं मिला।</p>';return;}
  list.innerHTML=rows.map(function(x){return '<div class="historyItem"><b>'+esc(x.r.n)+'</b> '+(x.done?'<span class="cutTag">पर्ची कट चुकी</span>':'<span class="muted">पर्ची बाकी</span>')+'<div class="muted">वार्ड '+esc(x.w)+' • क्रमांक '+esc(x.r.s)+' • मकान '+esc(x.r.h)+'</div><div class="muted">'+esc(x.r.t)+' का नाम: '+esc(x.r.r)+'</div><button class="alt" style="margin-top:6px" data-open-voter="'+esc(key(x.d))+'">वोटर की पर्ची खोलें</button></div>';}).join('');
}
function updateMarkButton(){
  if(cur===null) return;
  var r=DATA[cur], done=!!CUTS[key(r)], b=$("markCut");
  b.textContent = done ? "✓ पर्ची कट चुकी — हटाएँ" : "✓ पर्ची काटें";
  b.className = done ? "alt" : "";
}
function markCut(){
  if(cur===null) return;
  var d=DATA[cur], k=key(d), r=rec(d);
  if(CUTS[k]){
    if(!confirm("क्या इस पर्ची को हिस्ट्री से हटाकर फिर से बाकी में दिखाना है?")) return;
    delete CUTS[k];
  } else {
    if(!confirm("क्या इस वोटर की पर्ची वास्तव में काट/प्रिंट कर दी है? पुष्टि करने पर यह पर्ची कट चुकी में गिनी जाएगी।")) return;
    CUTS[k]={w:r.w,s:r.s,n:r.n,t:r.t,rel:r.r,h:r.h,at:new Date().toISOString()};
  }
  sv("voterCuts3",JSON.stringify(CUTS)); updateCutDashboard(); renderHistory();
  if(cur!==null) showSlip(cur);
}
function renderHistory(){
  var q=norm($("historySearch").value||""), list=$("historyList"), entries=[];
  DATA.forEach(function(d){ var c=CUTS[key(d)]; if(!c) return; var r=rec(d), str=norm(r.n+" "+r.r+" "+r.h); if(q && str.indexOf(q)<0) return; entries.push({d:d,r:r,c:c}); });
  entries.sort(function(a,b){ return String(b.c.at||"").localeCompare(String(a.c.at||"")); });
  if(!entries.length){ list.innerHTML='<p class="muted">'+(q?'इस खोज से कोई पर्ची नहीं मिली।':'अभी किसी पर्ची को कट चुकी के रूप में दर्ज नहीं किया गया है।')+'</p>'; return; }
  list.innerHTML=entries.map(function(x){ var r=x.r, c=x.c, dt=c.at?new Date(c.at).toLocaleString('hi-IN'):'समय उपलब्ध नहीं'; return '<div class="historyItem"><b>'+esc(r.n)+'</b> <span class="cutTag">पर्ची कट चुकी</span><div class="muted">वार्ड '+r.w+' • क्रमांक '+r.s+' • मकान '+esc(r.h)+'</div><div class="muted">'+esc(r.t)+' का नाम: '+esc(r.r)+'</div><div class="muted">समय: '+esc(dt)+'</div><button class="alt" style="margin-top:6px" data-uncut="'+esc(key(x.d))+'">वापस बाकी में करें</button></div>'; }).join('');
}'''
if old_status not in s: raise SystemExit("status function not found; refusing partial patch")
s = s.replace(old_status, new_status)

# Apply Firestore snapshots inside the app's existing closure, without WebView reload.
cloud_hook = r'''\nwindow.applyCloudSnapshot = function(snapshot){
  if(!snapshot || typeof snapshot !== "object") return;
  var previousKey = (cur !== null && DATA[cur]) ? key(DATA[cur]) : null;
  try {
    if(Object.prototype.hasOwnProperty.call(snapshot,"voterData2")) {
      var incoming = JSON.parse(String(snapshot.voterData2));
      if(Array.isArray(incoming)) DATA = incoming;
    }
    if(Object.prototype.hasOwnProperty.call(snapshot,"voterEdits2")) {
      var nextEdits = JSON.parse(String(snapshot.voterEdits2));
      if(nextEdits && typeof nextEdits === "object") EDITS = nextEdits;
    }
    if(Object.prototype.hasOwnProperty.call(snapshot,"voterCuts3")) {
      var nextCuts = JSON.parse(String(snapshot.voterCuts3));
      if(nextCuts && typeof nextCuts === "object") CUTS = nextCuts;
    }
  } catch(e) { console.warn("Cloud snapshot apply failed",e); return; }
  status();
  if(typeof updateCutDashboard === "function") updateCutDashboard();
  if(typeof renderHistory === "function" && $("historyPanel") && !$("historyPanel").classList.contains("hide")) renderHistory();
  if(previousKey){ var nextIndex = DATA.findIndex(function(d){return key(d)===previousKey;}); cur = nextIndex >= 0 ? nextIndex : null; }
  var editBox = $("editBox");
  var editing = editBox && !editBox.classList.contains("hide") && editBox.contains(document.activeElement);
  if(!editing && cur !== null && typeof showSlip === "function") showSlip(cur);
  var searchCard = $("searchCard");
  if(searchCard){ searchCard.querySelectorAll("input[type='search'],input[type='text']").forEach(function(input){ input.dispatchEvent(new Event("input",{bubbles:true})); }); }
};
'''
if 'window.applyCloudSnapshot = function(snapshot)' not in s:
    hook_marker = 'function status(){'
    if hook_marker not in s: raise SystemExit("status hook marker not found; refusing partial patch")
    s = s.replace(hook_marker, cloud_hook + "\n" + hook_marker, 1)
s = s.replace(
'''    return '<div class="res" data-i="'+p[1]+'"><span><b>#'+r.s+'</b> '+esc(r.n)+(r.c?' <span class="chk">⚠</span>':'')+''',
'''    return '<div class="res" data-i="'+p[1]+'"><span><b>#'+r.s+'</b> '+esc(r.n)+(CUTS[key(d)]?' <span class="cutTag">पर्ची कट चुकी</span>':'')+(r.c?' <span class="chk">⚠</span>':'')+''')
s = s.replace(
'''    (booth?'<tr><td>मतदान केंद्र</td><td>'+esc(booth)+'</td></tr>':'')+
    '</table>'+''',
'''    (booth?'<tr><td>मतदान केंद्र</td><td>'+esc(booth)+'</td></tr>':'')+
    (CUTS[key(d)]?'<tr><td>पर्ची स्थिति</td><td><span class="cutTag">पर्ची कट चुकी</span><br>'+esc(new Date(CUTS[key(d)].at).toLocaleString('hi-IN'))+'</td></tr>':'')+
    '</table>'+''')
s = s.replace(
'  $("editBox").classList.add("hide");\n  $("searchCard").classList.add("hide");',
'  $("editBox").classList.add("hide");\n  updateMarkButton();\n  $("searchCard").classList.add("hide");')
s = s.replace(
'$("print").onclick = doPrint;',
'''$("print").onclick = doPrint;
$("markCut").onclick = markCut;
document.querySelectorAll("[data-page]").forEach(function(b){b.onclick=function(){showDataPage(b.getAttribute("data-page"));};});
document.querySelector(".stats").addEventListener("click",function(e){var b=e.target.closest(".status-count");if(!b)return;var kind=b.getAttribute("data-kind");$("wardPage").classList.add("hide");$("statusPage").classList.remove("hide");$("statusPageTitle").textContent=kind==="cut"?"✅ सभी कटी पर्चियाँ":kind==="left"?"⏳ सभी बाकी पर्चियाँ":"👥 सभी वोटर";renderStatusList(kind,"");$("statusPage").scrollIntoView({behavior:"smooth",block:"start"});});
$("wardStats").addEventListener("click",function(e){var b=e.target.closest(".ward-filter");if(!b)return;var w=b.getAttribute("data-ward"),kind=b.getAttribute("data-kind");$("wardPage").classList.add("hide");$("statusPage").classList.remove("hide");$("statusPageTitle").textContent="वार्ड "+w+" — "+(kind==="cut"?"कटी पर्चियाँ":kind==="left"?"बाकी पर्चियाँ":"सभी वोटर");renderStatusList(kind,w);$("statusPage").scrollIntoView({behavior:"smooth",block:"start"});});
$("statusSearch").addEventListener("input",function(){var title=$("statusPageTitle").textContent,kind=title.indexOf("कटी")>=0?"cut":title.indexOf("बाकी")>=0?"left":"all";var m=title.match(/वार्ड\\s+([^ —]+)/);renderStatusList(kind,m?m[1]:"");});
$("statusList").addEventListener("click",function(e){var b=e.target.closest("[data-open-voter]");if(!b)return;var k=b.getAttribute("data-open-voter"),i=DATA.findIndex(function(d){return key(d)===k;});if(i>=0)showSlip(i);});
$("markCut").onclick = markCut;
$("showHistory").onclick = function(){ renderHistory(); $("historyPanel").classList.remove("hide"); $("historyPanel").scrollIntoView({behavior:"smooth",block:"start"}); };
$("closeHistory").onclick = function(){ $("historyPanel").classList.add("hide"); };
$("historySearch").addEventListener("input",renderHistory);
$("historyList").addEventListener("click",function(e){ var b=e.target.closest("[data-uncut]"); if(!b) return; var k=b.getAttribute("data-uncut"); if(confirm("इस पर्ची को वापस बाकी में करें?")){ delete CUTS[k]; sv("voterCuts3",JSON.stringify(CUTS)); updateCutDashboard(); renderHistory(); if(cur!==null) showSlip(cur); } });''')

# Add app-like navigation and group the main cards into separate views.
nav_css = r'''
/* App-like bottom navigation */
#vsmBottomNav{position:fixed;z-index:9990;left:10px;right:10px;bottom:calc(8px + env(safe-area-inset-bottom,0px));display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;padding:7px 7px calc(7px + env(safe-area-inset-bottom,0px));background:rgba(255,255,255,.98);border:1px solid #e1e8f0;border-radius:0 0 24px 24px;box-shadow:0 -4px 18px #18324b12;backdrop-filter:blur(14px)}
#vsmBottomNav button{border:0;border-radius:12px;background:transparent;color:#8491a2;min-height:53px;padding:6px 2px;font-size:11px;font-weight:700;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px}
#vsmBottomNav button .vsm-ico{font-size:21px;line-height:1.1}
#vsmBottomNav button.active{background:transparent;color:#2167a8;box-shadow:none;transform:none}
#vsmBottomNav button:focus-visible{outline:2px solid #93c5fd;outline-offset:2px}
#vsmBottomNav button span:last-child{white-space:nowrap}
/* Keep the app header visible while the content area scrolls. */
body>header,body>.header,body>#header,body>.app-header,body>.topbar{
 position:sticky!important;top:0!important;z-index:9980!important;
 padding-top:calc(10px + env(safe-area-inset-top,0px))!important;
 box-shadow:0 5px 18px #00152b24;
}
body{padding-bottom:100px!important;background:#f3f6fb!important;color:#172b43}
.card{border-radius:16px!important;border:1px solid #e2eaf3!important;box-shadow:0 5px 18px #15395b0b!important;margin:12px 10px!important;padding:15px!important}
button{min-height:42px;border-radius:11px!important;font-weight:700!important;letter-spacing:.05px}
input,select,textarea{max-width:100%;border-radius:11px!important;border:1px solid #cbd7e5!important;padding:12px!important;font-size:16px!important}
input:focus,select:focus,textarea:focus{outline:2px solid #8dbbfa!important;border-color:#3679d8!important}
h1{line-height:1.25!important;font-size:clamp(20px,5.2vw,28px)!important}
#vsmBottomNav{padding-bottom:calc(7px + env(safe-area-inset-bottom,0px))}
.vsm-nav-hidden{display:none!important}
@media(max-width:360px){#vsmBottomNav{left:6px;right:6px;padding:5px;gap:3px}#vsmBottomNav button{font-size:10px;min-height:49px}}
@media(min-width:760px){#vsmBottomNav{left:auto;right:22px;bottom:18px;width:360px}body{padding-bottom:90px!important}.card{max-width:900px;margin:14px auto!important}}
'''
if 'id="vsmBottomNav"' not in s:
    home_css = r"""
#vsmHomeDashboard{padding:18px 12px 8px;background:#f1f5fb;color:#20364d}
#vsmHomeDashboard .vsm-greet{font-size:27px;font-weight:800;letter-spacing:-.4px;margin:3px 5px 4px}
#vsmHomeDashboard .vsm-sub{font-size:15px;color:#748397;margin:0 5px 18px}
#vsmHomeDashboard .vsm-home-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
#vsmHomeDashboard .vsm-tile{appearance:none;text-align:left;background:#fff;border:1px solid #e0e7ef;border-radius:22px;padding:17px 15px;min-height:166px;box-shadow:0 2px 4px #17324d06;color:#20364d;display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-start;gap:10px}
#vsmHomeDashboard .vsm-tile .vsm-tile-icon{width:58px;height:58px;border-radius:19px;display:grid;place-items:center;font-size:27px;background:#e4efff;color:#2566a2}
#vsmHomeDashboard .vsm-tile:nth-child(2) .vsm-tile-icon{background:#e0f6ed;color:#18845c}
#vsmHomeDashboard .vsm-tile:nth-child(3) .vsm-tile-icon{background:#fff0d7;color:#a66a17}
#vsmHomeDashboard .vsm-tile:nth-child(4) .vsm-tile-icon{background:#f0e6ff;color:#7443b3}
#vsmHomeDashboard .vsm-tile strong{font-size:21px;line-height:1.25}
#vsmHomeDashboard .vsm-tile small{font-size:13px;color:#778495;line-height:1.5}
#vsmHomeDashboard .vsm-data-card{margin-top:14px;background:#fff;border:1px solid #e0e7ef;border-radius:22px;padding:18px;box-shadow:0 2px 4px #17324d06}
#vsmHomeDashboard .vsm-data-top{display:flex;justify-content:space-between;align-items:center;font-size:21px;font-weight:800}
#vsmHomeDashboard .vsm-loaded{font-size:12px;border-radius:20px;padding:5px 10px;background:#dcf7e8;color:#21845a}
#vsmHomeDashboard .vsm-total-label{margin-top:18px;font-size:14px;color:#7b8796}
#vsmHomeDashboard .vsm-total{font-size:43px;line-height:1.25;font-weight:800;color:#173a5b;margin:3px 0 12px}
#vsmHomeDashboard .vsm-bar{height:8px;border-radius:20px;background:#e7edf4;overflow:hidden}
#vsmHomeDashboard .vsm-bar span{display:block;width:0;height:100%;background:#347fca;border-radius:20px}
#vsmHomeDashboard .vsm-note{margin-top:12px;color:#7b8796;font-size:13px}
@media(max-width:360px){#vsmHomeDashboard .vsm-greet{font-size:24px}#vsmHomeDashboard .vsm-tile{padding:13px;min-height:152px}#vsmHomeDashboard .vsm-tile strong{font-size:18px}}
"""
    s = s.replace("</style>", nav_css + "\n" + home_css + "\n</style>", 1)
    dashboard = r"""
<section id="vsmHomeDashboard" aria-label="होम डैशबोर्ड">
  <div class="vsm-greet">नमस्कार!</div>
  <div class="vsm-sub">आज आप क्या करना चाहते हैं?</div>
  <div class="vsm-home-grid">
    <button type="button" class="vsm-tile" data-home-go="search"><span class="vsm-tile-icon">⌕</span><strong>वोटर खोजें</strong><small>नाम, पिता या मकान नंबर</small></button>
    <button type="button" class="vsm-tile" data-home-go="search"><span class="vsm-tile-icon">▣</span><strong>पर्ची बनाएँ</strong><small>वोटर की पर्ची खोलें</small></button>
    <button type="button" class="vsm-tile" data-home-go="search"><span class="vsm-tile-icon">♧</span><strong>वोटर सूची</strong><small>वार्ड और परिवार</small></button>
    <button type="button" class="vsm-tile" data-home-go="reports"><span class="vsm-tile-icon">▥</span><strong>रिपोर्ट</strong><small>कुल वोटर और आँकड़े</small></button>
  </div>
  <div class="vsm-data-card">
    <div class="vsm-data-top"><span>वोटर डेटा</span><span class="vsm-loaded" id="vsmDataState">जाँच जारी</span></div>
    <div class="vsm-total-label">कुल वोटर</div>
    <div class="vsm-total" id="vsmTotalVoters">—</div>
    <div class="vsm-bar"><span id="vsmDataBar"></span></div>
    <div class="vsm-note" id="vsmDataNote">डेटा लोड होने पर कुल संख्या यहाँ दिखेगी।</div>
  </div>
</section>
"""
    if 'id="vsmHomeDashboard"' not in s:
        insert_at = s.find('<section class="card"')
        if insert_at < 0:
            insert_at = s.find('<section')
        if insert_at >= 0:
            s = s[:insert_at] + dashboard + "\n" + s[insert_at:]
    nav_html = r"""
<nav id="vsmBottomNav" aria-label="मुख्य नेविगेशन">
  <button type="button" data-vsm-page="home" class="active"><span class="vsm-ico">⌂</span><span>होम</span></button>
  <button type="button" data-vsm-page="search"><span class="vsm-ico">⌕</span><span>वोटर खोजें</span></button>
  <button type="button" data-vsm-page="reports"><span class="vsm-ico">▤</span><span>रिपोर्ट</span></button>
  <button type="button" data-vsm-page="tools"><span class="vsm-ico">⚙</span><span>डेटा / टूल्स</span></button>
</nav>
<script>
(function(){
 function init(){
  var nav=document.getElementById("vsmBottomNav");
  if(!nav||nav.dataset.ready==="1")return;nav.dataset.ready="1";
  var cards=Array.prototype.slice.call(document.querySelectorAll(".card"));
  function group(c){
   var id=(c.id||"").toLowerCase(),t=(c.innerText||c.textContent||"").toLowerCase();
   if(id==="cutdashboard"||id==="historypanel"||/वार्ड-वार|पर्ची प्रगति|पर्ची हिस्ट्री|कटी पर्चियाँ|बाकी पर्चियाँ/.test(t))return "reports";
   if(id==="searchcard"||/नाम \/ पिता|वोटर खोज|खोजें|सर्च/.test(t))return "search";
   if(/आयात|इम्पोर्ट|import|export|निर्यात|बैकअप|backup|csv|json|डेटा अपलोड|डेटा डाउनलोड|फाइल चुनें|फाइल अपलोड/.test(t))return "tools";
   if(/पर्ची|वोटर|मतदाता/.test(t))return "search";
   return "home";
  }
  cards.forEach(function(c){c.dataset.vsmGroup=group(c)});
  function show(page){
   var home=document.getElementById("vsmHomeDashboard");
   if(home)home.style.display=page==="home"?"block":"none";
   nav.querySelectorAll("button[data-vsm-page]").forEach(function(b){b.classList.toggle("active",b.dataset.vsmPage===page)});
   cards.forEach(function(c){
    var g=c.dataset.vsmGroup||"home";
    var visible=page==="home"?false:
      page==="search"?(g==="search"||/slip|result|edit/i.test(c.id||"")):
      page==="reports"?(g==="reports"||c.id==="cutDashboard"||c.id==="historyPanel"):g==="tools";
    c.classList.toggle("vsm-nav-hidden",!visible);
   });
   window.scrollTo({top:0,behavior:"smooth"});
  }
  nav.addEventListener("click",function(e){var b=e.target.closest("button[data-vsm-page]");if(b)show(b.dataset.vsmPage)});
  document.querySelectorAll("[data-home-go]").forEach(function(b){b.addEventListener("click",function(){show(b.getAttribute("data-home-go"));});});
  function syncHomeData(){
   var total=document.getElementById("totalCount"),cut=document.getElementById("cutCount"),state=document.getElementById("vsmDataState"),num=document.getElementById("vsmTotalVoters"),bar=document.getElementById("vsmDataBar"),note=document.getElementById("vsmDataNote");
   if(!num)return;
   var n=total?parseInt(total.textContent.replace(/[^0-9]/g,""),10):0, k=cut?parseInt(cut.textContent.replace(/[^0-9]/g,""),10):0;
   if(n>0){num.textContent=n.toLocaleString("en-IN");state.textContent="लोडेड";bar.style.width=Math.round((k||0)*100/n)+"%";note.textContent="आपके लोड किए गए वोटर रिकॉर्ड";}else{num.textContent="—";state.textContent="डेटा नहीं";bar.style.width="0%";note.textContent="PDF से वोटर डेटा लोड होने पर संख्या यहाँ दिखेगी।";}
  }
  syncHomeData();setInterval(syncHomeData,1200);
  window.VoterSlipNav={show:show};show("home");
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();
</script>
"""
    s = s.replace("</body>", nav_html + "\n</body>", 1)

html_path.write_text(s, encoding="utf-8")

java_path = root / "app/src/main/java/com/example/voterslip/MainActivity.java"
j = java_path.read_text(encoding="utf-8")
j = j.replace('import android.app.Activity;\n', '''import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
''')
old = '''        super.onCreate(savedInstanceState);

        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();'''
new = '''        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(8, 43, 82));
        getWindow().setNavigationBarColor(Color.rgb(8, 43, 82));
        showSplash();
        new Handler(Looper.getMainLooper()).postDelayed(() -> initializeWebView(savedInstanceState), 1700);
    }

    private void showSplash() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(28), dp(28), dp(28), dp(28));
        GradientDrawable bg = new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{Color.rgb(11, 79, 138), Color.rgb(5, 33, 67)});
        root.setBackground(bg);

        TextView icon = new TextView(this);
        icon.setText("🗳️");
        icon.setTextSize(54);
        icon.setGravity(Gravity.CENTER);
        root.addView(icon, new LinearLayout.LayoutParams(-1, dp(88)));

        TextView title = new TextView(this);
        title.setText("वोटर पर्ची जनरेटर");
        title.setTextSize(27);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setTextColor(Color.WHITE);
        title.setGravity(Gravity.CENTER);
        root.addView(title, new LinearLayout.LayoutParams(-1, dp(52)));

        TextView owner = new TextView(this);
        owner.setText("डेवलपर: Mala Ram Godara");
        owner.setTextSize(18);
        owner.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        owner.setTextColor(Color.rgb(255, 226, 145));
        owner.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams ownerLp = new LinearLayout.LayoutParams(-1, dp(48));
        ownerLp.topMargin = dp(8);
        root.addView(owner, ownerLp);

        TextView subtitle = new TextView(this);
        subtitle.setText("आपका वोटर पर्ची जनरेटर");
        subtitle.setTextSize(14);
        subtitle.setTextColor(Color.rgb(225, 237, 249));
        subtitle.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams subLp = new LinearLayout.LayoutParams(-1, dp(36));
        subLp.topMargin = dp(4);
        root.addView(subtitle, subLp);

        ProgressBar progress = new ProgressBar(this);
        progress.setIndeterminate(true);
        LinearLayout.LayoutParams progressLp = new LinearLayout.LayoutParams(dp(42), dp(42));
        progressLp.topMargin = dp(28);
        root.addView(progress, progressLp);
        setContentView(root);
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private void initializeWebView(Bundle savedInstanceState) {
        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();'''
if old not in j: raise SystemExit("MainActivity onCreate pattern not found")
j = j.replace(old, new)
j = j.replace('        web.saveState(outState);', '        if (web != null) web.saveState(outState);')
j = j.replace('''        web.evaluateJavascript("(window.appBack && window.appBack()) === true", value -> {''',
'''        if (web == null) { finish(); return; }
        web.evaluateJavascript("(window.appBack && window.appBack()) === true", value -> {''')
java_path.write_text(j, encoding="utf-8")

print("Patched voter-slip dashboard/history and splash screen.")
