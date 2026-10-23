from pathlib import Path
import sys

root = Path(sys.argv[1])
patches = Path(sys.argv[2])
module = root / "app/build.gradle.kts"
manifest = root / "app/src/main/AndroidManifest.xml"
java_target = root / "app/src/main/java/com/example/voterslip/MainActivity.java"
html = root / "app/src/main/assets/index.html"

# Copy the native bridge that implements Google Sign-In, Firebase Auth, approvals and Firestore sync.
java_target.write_text((patches / "MainActivity.java").read_text(encoding="utf-8"), encoding="utf-8")

gradle = module.read_text(encoding="utf-8")
if "play-services-auth" not in gradle:
    gradle += '\n\ndependencies {\n    implementation("com.google.android.gms:play-services-auth:21.3.0")\n}\n'
module.write_text(gradle, encoding="utf-8")

m = manifest.read_text(encoding="utf-8")
if "android.permission.INTERNET" not in m:
    m = m.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">',
                  '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n    <uses-permission android:name="android.permission.INTERNET" />')
m = m.replace('    <!-- इंटरनेट की अनुमति जान-बूझकर नहीं दी गई: ऐप पूरी तरह ऑफ़लाइन चलता है। -->\n', '')
manifest.write_text(m, encoding="utf-8")

s = html.read_text(encoding="utf-8")
if 'id="authGate"' not in s:
    ui = (patches / "auth-ui.html").read_text(encoding="utf-8")
    s = s.replace("</body>", ui + "\n</body>")
old = 'function sv(k,v){ try{ localStorage.setItem(k,v); }catch(e){} }'
new = 'function sv(k,v){ try{ localStorage.setItem(k,v); }catch(e){} try{ if(window.AuthUI && window.AuthUI.syncLocal) window.AuthUI.syncLocal(); }catch(e){} }'
if old in s:
    s = s.replace(old, new)
# Give the debounced cloud sync time to persist imported CSV/JSON before refreshing the page.
s = s.replace('sv("voterData2", JSON.stringify(c)); sv("voterEdits2","{}"); location.reload();',
              'sv("voterData2", JSON.stringify(c)); sv("voterEdits2","{}"); setTimeout(function(){ location.reload(); }, 1000);')
html.write_text(s, encoding="utf-8")
print("Google Sign-In, admin approval UI and shared Firestore sync patched.")
