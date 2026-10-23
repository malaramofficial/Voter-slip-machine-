from pathlib import Path
import shutil, sys
root=Path(sys.argv[1]); config=Path(sys.argv[2])
project=root/'build.gradle.kts'
module=root/'app/build.gradle.kts'
manifest=root/'app/src/main/AndroidManifest.xml'
app_config=root/'app/google-services.json'
app_config.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(config, app_config)
s=project.read_text()
if 'com.google.gms.google-services' not in s:
 s=s.replace('id("com.android.application") version "8.5.2" apply false','id("com.android.application") version "8.5.2" apply false\n    id("com.google.gms.google-services") version "4.5.0" apply false')
project.write_text(s)
s=module.read_text()
if 'com.google.gms.google-services' not in s:
 s=s.replace('id("com.android.application")','id("com.android.application")\n    id("com.google.gms.google-services")')
if 'firebase-firestore' not in s:
 s += '\n\ndependencies {\n    implementation(platform("com.google.firebase:firebase-bom:34.0.0"))\n    implementation("com.google.firebase:firebase-auth")\n    implementation("com.google.firebase:firebase-firestore")\n}\n'
module.write_text(s)
s=manifest.read_text()
if 'android.permission.INTERNET' not in s:
 s=s.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">','<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n    <uses-permission android:name="android.permission.INTERNET" />')
s=s.replace('    <!-- इंटरनेट की अनुमति जान-बूझकर नहीं दी गई: ऐप पूरी तरह ऑफ़लाइन चलता है। -->\n','')
manifest.write_text(s)
print('Firebase SDK and Android config applied')
