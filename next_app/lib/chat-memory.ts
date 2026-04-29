/**
 * chat-memory.ts
 *
 * Persistent memory for Lilly across sessions, stored in Firestore.
 *
 * Schema:
 *   users/{userId}/lilly_exchanges/{docId}:
 *     user_message:       string
 *     assistant_response: string
 *     event_type:         string   // 'chat' | 'screen_open'
 *     subject_name:       string   // name of the natal chart subject
 *     created_at:         string   // ISO timestamp
 *
 *   users/{userId}/lilly_summary (single document):
 *     content:        string   // Anthropic-generated summary
 *     updated_at:     string
 *     exchange_count: number   // total exchanges summarized
 *
 * Behaviour:
 *   - saveExchange()       — called after every chat turn
 *   - getRecentHistory()   — reads last N exchanges + summary (if exists)
 *   - summarizeIfNeeded()  — when total exchanges > SUMMARY_THRESHOLD,
 *                            compresses oldest exchanges into a summary
 *                            using Anthropic and removes them from Firestore
 */

import { getAdminDb } from "@/lib/firebase-admin";
import { getAnthropicClient } from "@/lib/anthropic-client";

// ── Config ────────────────────────────────────────────────────────────────────

const RECENT_EXCHANGES = 5;        // exchanges injected into each context
const SUMMARY_THRESHOLD = 50;      // trigger summarization above this count
const EXCHANGES_TO_SUMMARIZE = 30; // how many oldest exchanges to compress

// ── Types ─────────────────────────────────────────────────────────────────────

export interface LillyExchange {
  user_message:       string;
  assistant_response: string;
  event_type:         string;
  subject_name:       string;
  created_at:         string;
}

export interface LillyMemoryContext {
  /** Narrative summary of older conversations (may be empty string) */
  summary:   string;
  /** Most recent exchanges in chronological order */
  exchanges: LillyExchange[];
}

// ── saveExchange ──────────────────────────────────────────────────────────────

/**
 * Persists one user↔Lilly exchange to Firestore.
 * Non-blocking: errors are logged but not rethrown so the API response
 * is never delayed by storage failures.
 */
export async function saveExchange(
  userId:     string,
  exchange:   Omit<LillyExchange, "created_at">,
): Promise<void> {
  try {
    const db = getAdminDb();
    await db
      .collection("users")
      .doc(userId)
      .collection("lilly_exchanges")
      .add({ ...exchange, created_at: new Date().toISOString() });
  } catch (err) {
    console.error("[chat-memory] saveExchange error:", err);
  }
}

// ── getRecentHistory ──────────────────────────────────────────────────────────

/**
 * Returns the most recent exchanges plus any existing summary.
 * Returns an empty context without throwing if the user has no history
 * or if Firestore is unavailable.
 */
export async function getRecentHistory(userId: string): Promise<LillyMemoryContext> {
  const empty: LillyMemoryContext = { summary: "", exchanges: [] };
  try {
    const db = getAdminDb();
    const userRef = db.collection("users").doc(userId);

    // Read summary and exchanges in parallel
    const [summarySnap, exchangesSnap] = await Promise.all([
      userRef.collection("lilly_summary").doc("current").get(),
      userRef
        .collection("lilly_exchanges")
        .orderBy("created_at", "desc")
        .limit(RECENT_EXCHANGES)
        .get(),
    ]);

    const summary: string = summarySnap.exists
      ? (summarySnap.data()?.content ?? "")
      : "";

    const exchanges: LillyExchange[] = exchangesSnap.docs
      .map((doc) => doc.data() as LillyExchange)
      .reverse(); // chronological order (oldest first)

    return { summary, exchanges };
  } catch (err) {
    console.error("[chat-memory] getRecentHistory error:", err);
    return empty;
  }
}

// ── summarizeIfNeeded ─────────────────────────────────────────────────────────

/**
 * Checks if total exchange count exceeds SUMMARY_THRESHOLD.
 * If so, fetches the oldest EXCHANGES_TO_SUMMARIZE exchanges,
 * generates a narrative summary with Anthropic, stores it in
 * lilly_summary/current, and deletes the compressed exchanges.
 *
 * Designed to be called fire-and-forget after saveExchange().
 */
export async function summarizeIfNeeded(userId: string): Promise<void> {
  try {
    const db = getAdminDb();
    const exchangesRef = db
      .collection("users")
      .doc(userId)
      .collection("lilly_exchanges");

    // Count total exchanges
    const countSnap = await exchangesRef.count().get();
    const total = countSnap.data().count;
    if (total <= SUMMARY_THRESHOLD) return;

    // Fetch oldest exchanges to summarize
    const oldSnap = await exchangesRef
      .orderBy("created_at", "asc")
      .limit(EXCHANGES_TO_SUMMARIZE)
      .get();

    if (oldSnap.empty) return;

    // Build text for summarization
    const exchangeLines = oldSnap.docs
      .map((doc) => {
        const d = doc.data() as LillyExchange;
        return `[${d.created_at.slice(0, 10)} · ${d.event_type}]\nUser: ${d.user_message}\nLilly: ${d.assistant_response}`;
      })
      .join("\n\n---\n\n");

    // Generate summary
    const client = getAnthropicClient();
    const result = await client.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 512,
      system:
        "Eres un archivista astrológico. Resume el historial de conversación entre el usuario y Lilly " +
        "(su intérprete astrológica) en 3-6 frases densas. Preserva: temas consultados, insights clave, " +
        "preguntas del usuario, preferencias expresadas, eventos biográficos mencionados. " +
        "Escribe en español, primera persona plural ('conversamos sobre...'). Sin saludos ni conclusiones.",
      messages: [{ role: "user", content: exchangeLines }],
    });

    const summaryText =
      result.content[0]?.type === "text" ? result.content[0].text : "";
    if (!summaryText) return;

    // Fetch existing summary to prepend
    const prevSummarySnap = await db
      .collection("users")
      .doc(userId)
      .collection("lilly_summary")
      .doc("current")
      .get();
    const prevContent: string = prevSummarySnap.exists
      ? (prevSummarySnap.data()?.content ?? "")
      : "";

    const combinedSummary = prevContent
      ? `${prevContent}\n\n${summaryText}`
      : summaryText;

    // Batch: write new summary + delete old exchanges
    const batch = db.batch();

    batch.set(
      db.collection("users").doc(userId).collection("lilly_summary").doc("current"),
      {
        content:        combinedSummary,
        updated_at:     new Date().toISOString(),
        exchange_count: (prevSummarySnap.data()?.exchange_count ?? 0) + oldSnap.size,
      }
    );

    for (const doc of oldSnap.docs) {
      batch.delete(doc.ref);
    }

    await batch.commit();
    console.log(`[chat-memory] Summarized ${oldSnap.size} exchanges for uid=${userId}`);
  } catch (err) {
    console.error("[chat-memory] summarizeIfNeeded error:", err);
  }
}

// ── formatMemoryForPrompt ─────────────────────────────────────────────────────

/**
 * Converts a LillyMemoryContext into a structured string block
 * ready to be injected into the context block.
 *
 * Returns empty string if there is no memory to inject
 * (avoids polluting the prompt with an empty section).
 */
export function formatMemoryForPrompt(memory: LillyMemoryContext): string {
  const hasContent = memory.summary || memory.exchanges.length > 0;
  if (!hasContent) return "";

  const lines: string[] = [];
  lines.push("═══════════════════════════════════════");
  lines.push("MEMORIA BIOGRÁFICA — sesiones anteriores");
  lines.push("═══════════════════════════════════════");
  lines.push("");

  if (memory.summary) {
    lines.push("RESUMEN HISTÓRICO");
    lines.push(memory.summary);
    lines.push("");
  }

  if (memory.exchanges.length > 0) {
    lines.push(`ÚLTIMAS ${memory.exchanges.length} CONVERSACIONES`);
    for (const ex of memory.exchanges) {
      const date = ex.created_at.slice(0, 10);
      lines.push(`[${date} · ${ex.event_type}]`);
      lines.push(`Usuario: ${ex.user_message}`);
      lines.push(`Lilly: ${ex.assistant_response}`);
      lines.push("");
    }
  }

  return lines.join("\n");
}
