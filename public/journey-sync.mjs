export const JOURNEY_SCHEMA_VERSION = 2;

export const SYNCABLE_PROGRESS_FIELDS = Object.freeze([
  "completed",
  "sobrietyDate",
  "checkins",
  "gratitudes",
  "supportPlan",
  "updatedAt",
]);

export const DEVICE_ONLY_PROGRESS_FIELDS = Object.freeze([
  "anonymousName",
  "anonymousShares",
  "notifications",
  "lastReminderAt",
  "reminderTime",
  "showCleanDays",
]);

export function selectSyncableProgress(progress) {
  const source = progress && typeof progress === "object" && !Array.isArray(progress) ? progress : {};
  const syncable = {};
  SYNCABLE_PROGRESS_FIELDS.forEach((field) => {
    if (Object.hasOwn(source, field)) syncable[field] = source[field];
  });
  return syncable;
}

export function mergeRemoteJourneyProgress(remoteProgress, localProgress) {
  const remote = remoteProgress && typeof remoteProgress === "object" && !Array.isArray(remoteProgress)
    ? remoteProgress
    : {};
  const local = localProgress && typeof localProgress === "object" && !Array.isArray(localProgress)
    ? localProgress
    : {};
  const merged = { ...remote };
  DEVICE_ONLY_PROGRESS_FIELDS.forEach((field) => {
    if (Object.hasOwn(local, field)) merged[field] = local[field];
  });
  return merged;
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
