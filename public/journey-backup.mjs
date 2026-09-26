export const JOURNEY_BACKUP_VERSION = 1;
export const MAX_JOURNEY_BACKUP_BYTES = 1_000_000;

export function parseJourneyBackup(text) {
  if (typeof text !== "string" || new TextEncoder().encode(text).byteLength > MAX_JOURNEY_BACKUP_BYTES) {
    throw new Error("A cópia excede o limite permitido.");
  }
  const payload = JSON.parse(text);
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Formato de cópia inválido.");
  }
  if (payload.version !== JOURNEY_BACKUP_VERSION) {
    throw new Error("Versão de cópia incompatível.");
  }
  if (!payload.progress || typeof payload.progress !== "object" || Array.isArray(payload.progress)) {
    throw new Error("A cópia não contém uma Jornada válida.");
  }
  return payload.progress;
}
