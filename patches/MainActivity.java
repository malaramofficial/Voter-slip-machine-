package com.example.voterslip;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.util.Base64;
import android.os.Bundle;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import org.json.JSONObject;
import org.json.JSONArray;
import com.google.android.gms.auth.api.signin.GoogleSignIn;
import com.google.android.gms.auth.api.signin.GoogleSignInClient;
import com.google.android.gms.auth.api.signin.GoogleSignInOptions;
import com.google.android.gms.common.api.ApiException;
import com.google.firebase.auth.AuthCredential;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.auth.GoogleAuthProvider;
import com.google.firebase.firestore.DocumentSnapshot;
import com.google.firebase.firestore.DocumentChange;
import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.ListenerRegistration;
import com.google.firebase.firestore.SetOptions;
import java.util.HashMap;
import java.util.Map;

public class MainActivity extends Activity {
    private static final int REQ_FILE = 1001, REQ_GOOGLE = 1002;
    private static final String START_URL = "file:///android_asset/index.html";
    private static final String ADMIN = "malaramofficial@gmail.com";
    private WebView web;
    private ValueCallback<Uri[]> fileCallback;
    private FirebaseAuth auth;
    private FirebaseFirestore db;
    private GoogleSignInClient googleClient;
    private ListenerRegistration sharedListener;
    private ListenerRegistration cutsListener;
    private boolean cutsInitialSnapshotHandled;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        auth = FirebaseAuth.getInstance();
        db = FirebaseFirestore.getInstance();
        GoogleSignInOptions opts = new GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestEmail().requestIdToken(getString(R.string.default_web_client_id)).build();
        googleClient = GoogleSignIn.getClient(this, opts);
        web = new WebView(this);
        setContentView(web);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true); s.setAllowContentAccess(false);
        s.setAllowFileAccessFromFileURLs(false); s.setAllowUniversalAccessFromFileURLs(false);
        s.setBuiltInZoomControls(false);
        web.addJavascriptInterface(new Bridge(), "AndroidApp");
        web.setWebViewClient(new WebViewClient() {
            @SuppressWarnings("deprecation") @Override public boolean shouldOverrideUrlLoading(WebView v, String url) {
                return !url.startsWith("file:///android_asset/");
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> cb, FileChooserParams p) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = cb;
                try { startActivityForResult(p.createIntent(), REQ_FILE); }
                catch (Exception e) { fileCallback = null; return false; }
                return true;
            }
        });
        if (state != null) web.restoreState(state); else web.loadUrl(START_URL);
    }
    private void js(String s) { runOnUiThread(() -> { if (web != null) web.evaluateJavascript(s, null); }); }
    private boolean admin(FirebaseUser u) { return u != null && u.getEmail() != null && ADMIN.equalsIgnoreCase(u.getEmail()); }
    private String userJson(FirebaseUser u) {
        JSONObject o = new JSONObject();
        try { o.put("uid",u.getUid()); o.put("email",u.getEmail()); o.put("name",u.getDisplayName()); o.put("photo",u.getPhotoUrl()==null?"":u.getPhotoUrl().toString()); o.put("admin",admin(u)); } catch(Exception ignored) {}
        return o.toString();
    }
    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if (requestCode == REQ_FILE) {
            if (fileCallback != null) { fileCallback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(resultCode,data)); fileCallback=null; }
            return;
        }
        if (requestCode == REQ_GOOGLE) {
            try {
                String token = GoogleSignIn.getSignedInAccountFromIntent(data).getResult(ApiException.class).getIdToken();
                if (token == null) { js("window.AuthUI&&window.AuthUI.onError('Google ID token नहीं मिला। Firebase OAuth सेटिंग जाँचें।')"); return; }
                AuthCredential c = GoogleAuthProvider.getCredential(token,null);
                auth.signInWithCredential(c).addOnSuccessListener(r -> {
                    js("window.AuthUI&&window.AuthUI.onUser("+userJson(r.getUser())+")"); checkAccess();
                }).addOnFailureListener(e -> js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote("Firebase लॉगिन विफल: "+e.getLocalizedMessage())+")"));
            } catch(Exception e) { js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote("Google लॉगिन विफल: "+e.getLocalizedMessage())+")"); }
        }
    }
    private void checkAccess() {
        FirebaseUser u=auth.getCurrentUser();
        if(u==null){js("window.AuthUI&&window.AuthUI.onAccess(false,false,'signedout')");return;}
        if(admin(u)){js("window.AuthUI&&window.AuthUI.onAccess(true,true,'approved')");watchShared();loadRequests();return;}
        db.collection("approvedUsers").document(u.getUid()).get().addOnSuccessListener(d->{
            if(d.exists()){js("window.AuthUI&&window.AuthUI.onAccess(true,false,'approved')");watchShared();}
            else db.collection("accessRequests").document(u.getUid()).get().addOnSuccessListener(r->{
                String status=r.exists()?r.getString("status"):"none";
                js("window.AuthUI&&window.AuthUI.onAccess(false,false,"+JSONObject.quote(status==null?"pending":status)+")");
            }).addOnFailureListener(e->js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote(e.getLocalizedMessage())+")"));
        }).addOnFailureListener(e->js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote("अनुमति जाँच विफल: "+e.getLocalizedMessage())+")"));
    }
    private void watchShared() {
        watchCuts();
        if(sharedListener!=null)sharedListener.remove();
        sharedListener=db.collection("voterData").document("shared").addSnapshotListener((d,e)->{
            if(e!=null||d==null||!d.exists()){js("window.AuthUI&&window.AuthUI.onCloudData(null)");return;}
            String legacy=d.getString("payload");
            if(legacy!=null){js("window.AuthUI&&window.AuthUI.onCloudData(JSON.parse("+JSONObject.quote(legacy)+"))");return;}
            Long n=d.getLong("chunkCount");
            if(n==null||n<=0){js("window.AuthUI&&window.AuthUI.onCloudData(null)");return;}
            int count=n.intValue();
            db.collection("voterData").document("shared").collection("chunks").get().addOnSuccessListener(snap->{
                String[] parts=new String[count];
                for(DocumentSnapshot p:snap.getDocuments()){
                    Long ix=p.getLong("index");String part=p.getString("part");
                    if(ix!=null&&ix>=0&&ix<count&&part!=null)parts[ix.intValue()]=part;
                }
                StringBuilder joined=new StringBuilder();
                for(String part:parts){if(part==null){js("window.AuthUI&&window.AuthUI.onError('Firebase डेटा अधूरा है; दोबारा सिंक करें।')");return;}joined.append(part);}
                String payload=joined.toString();
                js("window.AuthUI&&window.AuthUI.onCloudData(JSON.parse("+JSONObject.quote(payload)+"))");
            }).addOnFailureListener(err->js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote("Firebase डेटा लोड नहीं हुआ: "+err.getLocalizedMessage())+")"));
        });
    }
    private String cutDocId(String voterKey) {
        return Base64.encodeToString(voterKey.getBytes(java.nio.charset.StandardCharsets.UTF_8),
                Base64.URL_SAFE | Base64.NO_WRAP | Base64.NO_PADDING);
    }

    private void watchCuts() {
        if (cutsListener != null) cutsListener.remove();
        cutsInitialSnapshotHandled = false;
        cutsListener = db.collection("voterData").document("shared").collection("cuts")
            .addSnapshotListener((snap, error) -> {
                if (error != null || snap == null) {
                    if (error != null) js("window.AuthUI&&window.AuthUI.onError(" + JSONObject.quote("कटिंग की लाइव स्थिति लोड नहीं हुई: " + error.getLocalizedMessage()) + ")");
                    return;
                }
                if (!cutsInitialSnapshotHandled) {
                    cutsInitialSnapshotHandled = true;
                    js("window.AuthUI&&window.AuthUI.onCloudCutsReady(" + snap.isEmpty() + ")");
                }
                for (DocumentChange change : snap.getDocumentChanges()) {
                    DocumentSnapshot d = change.getDocument();
                    String voterKey = d.getString("voterKey");
                    if (voterKey == null) continue;
                    boolean exists = change.getType() != DocumentChange.Type.REMOVED;
                    String payload = d.getString("payload");
                    js("window.AuthUI&&window.AuthUI.onCloudCut(" + JSONObject.quote(voterKey) + "," +
                        JSONObject.quote(payload == null ? "{}" : payload) + "," + exists + ")");
                }
            });
    }

    private void withCutWriteAccess(FirebaseUser u, String voterKey, Runnable action) {
        if (u == null) {
            js("window.AuthUI&&window.AuthUI.onCutSaveFailed(" + JSONObject.quote(voterKey) + ",'पहले लॉगिन करें।')");
            return;
        }
        if (admin(u)) { action.run(); return; }
        db.collection("approvedUsers").document(u.getUid()).get().addOnSuccessListener(d -> {
            if (d.exists()) action.run();
            else js("window.AuthUI&&window.AuthUI.onCutSaveFailed(" + JSONObject.quote(voterKey) + ",'इस खाते को साझा डेटा बदलने की अनुमति नहीं है।')");
        }).addOnFailureListener(e ->
            js("window.AuthUI&&window.AuthUI.onCutSaveFailed(" + JSONObject.quote(voterKey) + "," +
               JSONObject.quote("अनुमति जाँच विफल: " + e.getLocalizedMessage()) + ")"));
    }
    private void loadRequests() {
        if(!admin(auth.getCurrentUser()))return;
        db.collection("accessRequests").whereEqualTo("status","pending").get().addOnSuccessListener(snap->{
            JSONArray a=new JSONArray();
            for(DocumentSnapshot d:snap.getDocuments()){
                JSONObject o=new JSONObject();
                try{o.put("uid",d.getId());o.put("email",d.getString("email"));o.put("name",d.getString("name"));a.put(o);}catch(Exception ignored){}
            }
            js("window.AuthUI&&window.AuthUI.onRequests("+a.toString()+")");
        }).addOnFailureListener(e->js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote("अनुरोध सूची नहीं खुली: "+e.getLocalizedMessage())+")"));
    }
    private Map<String,Object> fields(Object... kv){Map<String,Object> m=new HashMap<>();for(int i=0;i+1<kv.length;i+=2)m.put(String.valueOf(kv[i]),kv[i+1]);return m;}
    @Override protected void onSaveInstanceState(Bundle out){super.onSaveInstanceState(out);if(web!=null)web.saveState(out);}
    @Override public void onBackPressed(){if(web!=null)web.evaluateJavascript("(window.appBack && window.appBack()) === true",v->{if(!"true".equals(v))finish();});else finish();}
    @Override protected void onDestroy(){if(sharedListener!=null)sharedListener.remove();if(cutsListener!=null)cutsListener.remove();if(web!=null){web.removeJavascriptInterface("AndroidApp");web.destroy();}super.onDestroy();}

    private class Bridge {
        @JavascriptInterface public void signIn(){runOnUiThread(()->startActivityForResult(googleClient.getSignInIntent(),REQ_GOOGLE));}
        @JavascriptInterface public String getSession(){FirebaseUser u=auth.getCurrentUser();return u==null?"null":userJson(u);}
        @JavascriptInterface public void refreshAccess(){checkAccess();}
        @JavascriptInterface public void requestAccess(){
            FirebaseUser u=auth.getCurrentUser();if(u==null){js("window.AuthUI&&window.AuthUI.onError('पहले Google लॉगिन करें।')");return;}
            if(admin(u)){checkAccess();return;}
            db.collection("accessRequests").document(u.getUid()).get().addOnSuccessListener(old->{
                if(old.exists()){checkAccess();return;}
                db.collection("accessRequests").document(u.getUid()).set(fields("uid",u.getUid(),"email",u.getEmail(),"name",u.getDisplayName()==null?"":u.getDisplayName(),"status","pending","createdAt",System.currentTimeMillis()))
                .addOnSuccessListener(v->checkAccess()).addOnFailureListener(e->js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote(e.getLocalizedMessage())+")"));
            }).addOnFailureListener(e->js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote(e.getLocalizedMessage())+")"));
        }
        @JavascriptInterface public void refreshRequests(){loadRequests();}
        @JavascriptInterface public void approveUser(String uid,String email,String name){
            if(!admin(auth.getCurrentUser()))return;
            db.collection("approvedUsers").document(uid).set(fields("uid",uid,"email",email,"name",name,"approvedBy",ADMIN,"approvedAt",System.currentTimeMillis()))
            .addOnSuccessListener(v->db.collection("accessRequests").document(uid).update("status","approved").addOnCompleteListener(t->{loadRequests();js("window.AuthUI&&window.AuthUI.onAdminAction('यूज़र को अनुमति मिल गई।')");}))
            .addOnFailureListener(e->js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote(e.getLocalizedMessage())+")"));
        }
        @JavascriptInterface public void denyUser(String uid){
            if(!admin(auth.getCurrentUser()))return;
            db.collection("accessRequests").document(uid).update("status","denied").addOnSuccessListener(v->{loadRequests();js("window.AuthUI&&window.AuthUI.onAdminAction('अनुरोध अस्वीकार हुआ।')");})
            .addOnFailureListener(e->js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote(e.getLocalizedMessage())+")"));
        }
        @JavascriptInterface public void adminUploadSharedState(String payload){
            FirebaseUser u=auth.getCurrentUser();
            if(!admin(u)){js("window.AuthUI&&window.AuthUI.onManualUploadResult(false,'केवल अधिकृत एडमिन अपलोड कर सकता है।')");return;}
            if(payload==null||payload.trim().isEmpty()){js("window.AuthUI&&window.AuthUI.onManualUploadResult(false,'अपलोड करने के लिए डेटा खाली है।')");return;}
            final String upload=payload;
            final int chunkSize=400000;
            final int count=Math.max(1,(upload.length()+chunkSize-1)/chunkSize);
            if(count>450){js("window.AuthUI&&window.AuthUI.onManualUploadResult(false,'डेटा बहुत बड़ा है; सुरक्षित बैचों में अपलोड करना होगा।')");return;}
            com.google.firebase.firestore.WriteBatch batch=db.batch();
            for(int i=0;i<count;i++){
                int start=i*chunkSize,end=Math.min(upload.length(),start+chunkSize);
                batch.set(db.collection("voterData").document("shared").collection("chunks").document(String.format(java.util.Locale.US,"p%05d",i)),fields("index",i,"part",upload.substring(start,end)));
            }
            batch.commit().addOnSuccessListener(v->
                db.collection("voterData").document("shared").set(fields("chunkCount",count,"updatedBy",u.getEmail()==null?"":u.getEmail(),"updatedAt",System.currentTimeMillis()),SetOptions.merge())
                .addOnSuccessListener(done->js("window.AuthUI&&window.AuthUI.onManualUploadResult(true,'अपलोड सफल! कुल डेटा Firebase पर सेव हो गया।')"))
                .addOnFailureListener(err->js("window.AuthUI&&window.AuthUI.onManualUploadResult(false,"+JSONObject.quote("डेटा के हिस्से सेव हुए, लेकिन Firebase स्थिति अपडेट नहीं हुई: "+err.getLocalizedMessage())+")"))
            ).addOnFailureListener(err->js("window.AuthUI&&window.AuthUI.onManualUploadResult(false,"+JSONObject.quote("Firebase अपलोड विफल: "+err.getLocalizedMessage())+")"));
        }
        @JavascriptInterface public void saveSharedState(String payload){
            FirebaseUser u=auth.getCurrentUser();if(u==null||payload==null)return;
            Runnable save=()->{
                final int chunkSize=400000;
                final int count=Math.max(1,(payload.length()+chunkSize-1)/chunkSize);
                com.google.firebase.firestore.WriteBatch batch=db.batch();
                for(int i=0;i<count;i++){
                    int start=i*chunkSize,end=Math.min(payload.length(),start+chunkSize);
                    batch.set(db.collection("voterData").document("shared").collection("chunks").document(String.format(java.util.Locale.US,"p%05d",i)),fields("index",i,"part",payload.substring(start,end)));
                }
                batch.commit().addOnSuccessListener(v->db.collection("voterData").document("shared").set(fields("chunkCount",count,"updatedBy",u.getEmail()==null?"":u.getEmail(),"updatedAt",System.currentTimeMillis()),SetOptions.merge()))
                  .addOnFailureListener(err->js("window.AuthUI&&window.AuthUI.onError("+JSONObject.quote("Firebase में डेटा सेव नहीं हुआ: "+err.getLocalizedMessage())+")"));
            };
            if(admin(u)){save.run();return;}
            db.collection("approvedUsers").document(u.getUid()).get().addOnSuccessListener(d->{if(d.exists())save.run();});
        }
        @JavascriptInterface public void createVoterCut(String voterKey, String payload) {
            if (voterKey == null || voterKey.isEmpty() || payload == null || payload.isEmpty()) {
                js("window.AuthUI&&window.AuthUI.onCutSaveFailed(" + JSONObject.quote(voterKey == null ? "" : voterKey) + ",'पर्ची का डेटा अधूरा है।')");
                return;
            }
            final JSONObject parsed;
            try { parsed = new JSONObject(payload); }
            catch (Exception e) { js("window.AuthUI&&window.AuthUI.onCutSaveFailed(" + JSONObject.quote(voterKey) + ",'पर्ची का डेटा पढ़ा नहीं जा सका।')"); return; }
            FirebaseUser u = auth.getCurrentUser();
            withCutWriteAccess(u, voterKey, () -> {
                com.google.firebase.firestore.DocumentReference ref = db.collection("voterData").document("shared").collection("cuts").document(cutDocId(voterKey));
                Map<String,Object> cut = fields("voterKey", voterKey, "payload", parsed.toString(), "updatedBy", u.getEmail() == null ? "" : u.getEmail(), "updatedAt", System.currentTimeMillis());
                db.runTransaction(transaction -> {
                    DocumentSnapshot old = transaction.get(ref);
                    if (old.exists()) throw new IllegalStateException("ALREADY_CUT");
                    transaction.set(ref, cut);
                    return null;
                }).addOnSuccessListener(v -> js("window.AuthUI&&window.AuthUI.onCutSaved(" + JSONObject.quote(voterKey) + "," + JSONObject.quote(parsed.toString()) + ")"))
                  .addOnFailureListener(e -> {
                    String message = e.getMessage() != null && e.getMessage().contains("ALREADY_CUT") ? "यह पर्ची दूसरे काउंटर से पहले ही कट चुकी है। डेटा रीफ़्रेश कर लें।" : "पर्ची Firebase में सेव नहीं हुई: " + e.getLocalizedMessage();
                    js("window.AuthUI&&window.AuthUI.onCutSaveFailed(" + JSONObject.quote(voterKey) + "," + JSONObject.quote(message) + ")");
                  });
            });
        }

        @JavascriptInterface public void removeVoterCut(String voterKey) {
            if (voterKey == null || voterKey.isEmpty()) return;
            FirebaseUser u = auth.getCurrentUser();
            withCutWriteAccess(u, voterKey, () -> {
                com.google.firebase.firestore.DocumentReference ref = db.collection("voterData").document("shared").collection("cuts").document(cutDocId(voterKey));
                db.runTransaction(transaction -> { DocumentSnapshot old = transaction.get(ref); if (old.exists()) transaction.delete(ref); return null; })
                  .addOnSuccessListener(v -> js("window.AuthUI&&window.AuthUI.onCutRemoved(" + JSONObject.quote(voterKey) + ")"))
                  .addOnFailureListener(e -> js("window.AuthUI&&window.AuthUI.onCutSaveFailed(" + JSONObject.quote(voterKey) + "," + JSONObject.quote("पर्ची की स्थिति नहीं बदली: " + e.getLocalizedMessage()) + ")"));
            });
        }

        @JavascriptInterface public void migrateLegacyCuts(String json) {
            FirebaseUser u = auth.getCurrentUser();
            if (u == null || json == null || json.trim().isEmpty()) return;
            withCutWriteAccess(u, "", () -> {
                try {
                    JSONObject all = new JSONObject(json);
                    java.util.Iterator<String> keys = all.keys();
                    while (keys.hasNext()) {
                        String voterKey = keys.next(); Object value = all.opt(voterKey);
                        if (!(value instanceof JSONObject)) continue;
                        String payload = ((JSONObject) value).toString();
                        com.google.firebase.firestore.DocumentReference ref = db.collection("voterData").document("shared").collection("cuts").document(cutDocId(voterKey));
                        Map<String,Object> cut = fields("voterKey", voterKey, "payload", payload, "updatedBy", u.getEmail() == null ? "" : u.getEmail(), "updatedAt", System.currentTimeMillis());
                        db.runTransaction(transaction -> { DocumentSnapshot old = transaction.get(ref); if (!old.exists()) transaction.set(ref, cut); return null; });
                    }
                } catch (Exception ignored) { }
            });
        }
        @JavascriptInterface public void signOut(){if(sharedListener!=null){sharedListener.remove();sharedListener=null;}if(cutsListener!=null){cutsListener.remove();cutsListener=null;}auth.signOut();googleClient.signOut();js("window.AuthUI&&window.AuthUI.onSignedOut()");}
        @JavascriptInterface public void printSlip(String title){runOnUiThread(()->{String job=(title==null||title.trim().isEmpty())?"Voter-Slip":title.trim();PrintManager pm=(PrintManager)getSystemService(Context.PRINT_SERVICE);PrintDocumentAdapter a=web.createPrintDocumentAdapter(job);PrintAttributes attrs=new PrintAttributes.Builder().setMediaSize(PrintAttributes.MediaSize.ISO_A5).build();pm.print(job,a,attrs);});}
    }
}
