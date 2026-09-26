export const JOURNEY_SCHEMA_VERSION = 2;

export function selectSyncableProgress(progress) {
  const source = progress && typeof progress === "object" && !Array.isArray(progress) ? progress : {};
  const {
    anonymousName,
    anonymousShares,
    notifications,
    lastReminderAt,
    ...syncable
  } = source;
  return syncable;
}

export function validateRemoteJourneyRecord(record) {
  if (!record || typeof record !== "object" || Array.isArray(record)) {
    throw new Error("A cópia da conta tem um formato inválido.");
  }

  const schemaVersion = Number(record.schema_version);
  if (!Number.isInteger(schemaVersion) || schemaVersion < 1) {
    throw new Error("A cópia da conta não indica uma versão válida.");
  }
  if (schemaVersion > JOURNEY_SCHEMA_VERSION) {
    throw new Error("A cópia da conta foi criada por uma versão mais recente da aplicação. Atualiza a aplicação antes de sincronizar.");
  }
  if (!record.payload || typeof record.payload !== "object" || Array.isArray(record.payload)) {
    throw new Error("A cópia da conta não contém uma Jornada válida.");
  }

  const updatedAt = Date.parse(record.updated_at);
  if (!Number.isFinite(updatedAt)) {
    throw new Error("A cópia da conta não tem uma data de atualização válida.");
  }

  return {
    payload: record.payload,
    schemaVersion,
    updatedAt: new Date(updatedAt).toISOString(),
  };
}

export function hasRemoteJourneyConflict(localUpdatedAt, remoteUpdatedAt) {
  const remote = Date.parse(remoteUpdatedAt);
  if (!Number.isFinite(remote)) return false;

  const local = Date.parse(localUpdatedAt);
  if (!Number.isFinite(local)) return true;
  return remote > local;
}
