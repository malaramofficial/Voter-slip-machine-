# Firebase setup for Voter Slip Machine

The Firebase-enabled debug APK built successfully on 2026-10-23. The current APK is signed with this debug certificate SHA-1:

`85:58:3B:14:78:34:54:71:C7:A5:8E:71:F0:94:A0:84:28:51:31:09`

Android application ID: `com.example.voterslip`  
Firebase project: `voter-slip-machine`  
Admin account: `malaramofficial@gmail.com`

## Required one-time Firebase Console steps

1. Open [Firebase Project Settings](https://console.firebase.google.com/project/voter-slip-machine/settings/general). Under the Android app `com.example.voterslip`, add the SHA-1 fingerprint above.
2. Open [Authentication sign-in providers](https://console.firebase.google.com/project/voter-slip-machine/authentication/providers), enable **Google**, select the support email and save.
3. Open [Firestore Database](https://console.firebase.google.com/project/voter-slip-machine/firestore). Create the database if it does not exist.
4. In Firestore **Rules**, paste the contents of the repository's root `firestore.rules` and click **Publish**. The GitHub Actions workflow cannot publish rules unless the repository secret `FIREBASE_SERVICE_ACCOUNT` is configured.

Use the same APK that matches the SHA-1 above when testing Google login. A new CI debug build may use a different debug signing certificate and therefore a different SHA-1.

## What the app implements

- Google Sign-In using Firebase Authentication.
- New users can request access.
- Only the admin email above can approve or deny requests.
- Shared voter data, edits, footer and cut-slip state sync through Firestore for approved users.
- Firestore rules deny unapproved access to the shared `voterData` collection.

**Important:** A successful APK build verifies compilation, not live Google OAuth or Firestore operation. Those require the Firebase Console steps above.
