from pathlib import Path
import sys

root = Path(sys.argv[1])
html_path = root / "app/src/main/assets/index.html"
s = html_path.read_text(encoding="utf-8")
s = s.replace('<h1>🗳️ वोटर पर्ची जनरेटर</h1>\n  <small id="hdrSub"></small>', '<h1>🗳️ वोटर पर्ची जनरेटर</h1>\n  <small id="hdrSub"></small>\n  <div style="margin-top:4px;font-size:13px;color:#e8f2ff;font-weight:600">डेवलपर: Mala Ram Godara</div>')

s = s.replace(
'  .actions { text-align:center; }',
'''  .actions { text-align:center; }
  .stats { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin-bottom:12px; }
  .stat { background:#fff; border:1px solid var(--bd); border-radius:10px; padding:12px 8px; text-align:center; }
  .stat strong { display:block; font-size:24px; color:var(--c); }
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
      <div class="stat"><strong id="totalCount">0</strong><span>कुल वोटर</span></div>
      <div class="stat"><strong id="cutCount">0</strong><span>पर्ची कट चुकी</span></div>
      <div class="stat"><strong id="leftCount">0</strong><span>बाकी पर्चियाँ</span></div>
    </div>
    <div class="progress"><div id="cutProgress"></div></div>
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
  if(cur!==null) updateMarkButton();
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
$("showHistory").onclick = function(){ renderHistory(); $("historyPanel").classList.remove("hide"); $("historyPanel").scrollIntoView({behavior:"smooth",block:"start"}); };
$("closeHistory").onclick = function(){ $("historyPanel").classList.add("hide"); };
$("historySearch").addEventListener("input",renderHistory);
$("historyList").addEventListener("click",function(e){ var b=e.target.closest("[data-uncut]"); if(!b) return; var k=b.getAttribute("data-uncut"); if(confirm("इस पर्ची को वापस बाकी में करें?")){ delete CUTS[k]; sv("voterCuts3",JSON.stringify(CUTS)); updateCutDashboard(); renderHistory(); if(cur!==null) showSlip(cur); } });''')
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
