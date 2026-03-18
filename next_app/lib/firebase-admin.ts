import * as admin from "firebase-admin";

function initAdmin() {
  if (admin.apps.length > 0) {
    return admin.app();
  }

  const projectId = process.env.FIREBASE_PROJECT_ID || process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
  if (!projectId) {
    throw new Error("FIREBASE_PROJECT_ID is not set");
  }

  // In Cloud Run with an attached Service Account, ADC is used automatically.
  // For local dev, set GOOGLE_APPLICATION_CREDENTIALS or FIREBASE_SERVICE_ACCOUNT_JSON.
  const serviceAccountJson = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;

  if (serviceAccountJson) {
    const serviceAccount = JSON.parse(serviceAccountJson);
    return admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
      projectId,
    });
  }

  // ADC (Cloud Run / local with gcloud auth application-default login)
  return admin.initializeApp({
    credential: admin.credential.applicationDefault(),
    projectId,
  });
}

const app = initAdmin();

export const adminAuth = admin.auth(app);
export const adminDb = admin.firestore(app);
