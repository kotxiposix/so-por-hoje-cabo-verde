import { hasRemoteJourneyConflict } from "./journey-sync.mjs";

function normalizeTimestamp(value) {
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? new Date(timestamp).toISOString() : "";
}

export function createJourneySyncCursor(userId, updatedAt) {
  const normalizedUserId = typeof userId === "string" ? userId.trim() : "";
  const normalizedUpdatedAt = normalizeTimestamp(updatedAt);
  if (!normalizedUserId || !normalizedUpdatedAt) return null;
  return { userId: normalizedUserId, updatedAt: normalizedUpdatedAt };
}

export function readJourneySyncCursor(serialized, userId) {
  if (!serialized || !userId) return "";
  try {
    const cursor = JSON.parse(serialized);
    if (cursor?.userId !== userId) return "";
    return normalizeTimestamp(cursor.updatedAt);
  } catch {
    return "";
  }
}

export function shouldPauseAutomaticSync({
  knownRemoteUpdatedAt,
  remoteExists,
  remoteUpdatedAt,
  localUpdatedAt,
}) {
  const known = normalizeTimestamp(knownRemoteUpdatedAt);
  if (known) {
    if (!remoteExists) return true;
    return normalizeTimestamp(remoteUpdatedAt) !== known;
  }
  if (!remoteExists) return false;
  return hasRemoteJourneyConflict(localUpdatedAt, remoteUpdatedAt);
}
