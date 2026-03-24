import * as admin from "firebase-admin";

function getApp(): admin.app.App {
  if (admin.apps.length > 0) return admin.apps[0]!;

  const projectId = process.env.FIREBASE_PROJECT_ID || process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
  if (!projectId) throw new Error("FIREBASE_PROJECT_ID is not set");

  const serviceAccountJson = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
  if (serviceAccountJson) {
    return admin.initializeApp({
      credential: admin.credential.cert(JSON.parse(serviceAccountJson)),
      projectId,
    });
  }

  // ADC (Cloud Run with attached SA, or local with gcloud auth application-default login)
  return admin.initializeApp({
    credential: admin.credential.applicationDefault(),
    projectId,
  });
}

export function getAdminAuth() { return admin.auth(getApp()); }
export function getAdminDb()   { return admin.firestore(getApp()); }
