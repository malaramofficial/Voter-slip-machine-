package com.example.voterslip;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
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
        if(sharedListener!=null)sharedListener.remove();
        sharedListener=db.collection("voterData").document("shared").addSnapshotListener((d,e)->{
            if(e!=null||d==null||!d.exists()){js("window.AuthUI&&window.AuthUI.onCloudData(null)");return;}
            String payload=d.getString("payload");
            if(payload==null)js("window.AuthUI&&window.AuthUI.onCloudData(null)");
            else js("window.AuthUI&&window.AuthUI.onCloudData(JSON.parse("+JSONObject.quote(payload)+"))");
        });
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
    @Override protected void onDestroy(){if(sharedListener!=null)sharedListener.remove();if(web!=null){web.removeJavascriptInterface("AndroidApp");web.destroy();}super.onDestroy();}

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
        @JavascriptInterface public void saveSharedState(String payload){
            FirebaseUser u=auth.getCurrentUser();if(u==null)return;
            Runnable save=()->db.collection("voterData").document("shared").set(fields("payload",payload,"updatedBy",u.getEmail()==null?"":u.getEmail(),"updatedAt",System.currentTimeMillis()),SetOptions.merge());
            if(admin(u)){save.run();return;}
            db.collection("approvedUsers").document(u.getUid()).get().addOnSuccessListener(d->{if(d.exists())save.run();});
        }
        @JavascriptInterface public void signOut(){if(sharedListener!=null){sharedListener.remove();sharedListener=null;}auth.signOut();googleClient.signOut();js("window.AuthUI&&window.AuthUI.onSignedOut()");}
        @JavascriptInterface public void printSlip(String title){runOnUiThread(()->{String job=(title==null||title.trim().isEmpty())?"Voter-Slip":title.trim();PrintManager pm=(PrintManager)getSystemService(Context.PRINT_SERVICE);PrintDocumentAdapter a=web.createPrintDocumentAdapter(job);PrintAttributes attrs=new PrintAttributes.Builder().setMediaSize(PrintAttributes.MediaSize.ISO_A5).build();pm.print(job,a,attrs);});}
    }
}
