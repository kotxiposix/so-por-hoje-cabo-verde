import {
  addIsoDays,
  differenceInCalendarDays,
  getBestStreak,
  getCalendarDayInTimeZone,
  getCurrentStreak,
} from "./date-utils.mjs";
import { getPrivacyCopy } from "./privacy-copy.mjs";

const state = {
  daily: null,
  progress: loadProgress(),
  view: "meditation",
};

const viewHashes = {
  meditation: "meditacao",
  journey: "jornada",
  wellness: "viver-saudavel",
  help: "ajuda",
  about: "sobre",
};

const els = {
  appContent: document.querySelector("#app-content"),
  currentDate: document.querySelector("#current-date"),
  streakCount: document.querySelector("#streak-count"),
  statusCard: document.querySelector("#status-card"),
  statusTitle: document.querySelector("#status-title"),
  statusCopy: document.querySelector("#status-copy"),
  loading: document.querySelector("#loading-state"),
  error: document.querySelector("#error-state"),
  errorMessage: document.querySelector("#error-message"),
  content: document.querySelector("#meditation-content"),
  title: document.querySelector("#meditation-title"),
  body: document.querySelector("#meditation-body"),
  reflection: document.querySelector("#meditation-reflection"),
  retry: document.querySelector("#retry-button"),
  complete: document.querySelector("#complete-button"),
  completeLabel: document.querySelector("#complete-label"),
  prayer: document.querySelector("#prayer-button"),
  prayerModal: document.querySelector("#prayer-modal"),
  prayerClose: document.querySelector("#prayer-close"),
  share: document.querySelector("#share-button"),
  story: document.querySelector("#story-button"),
  reminder: document.querySelector("#reminder-button"),
  toolLabel: document.querySelector("#tool-label"),
  toolText: document.querySelector("#tool-text"),
  toolModal: document.querySelector("#tool-modal"),
  toolClose: document.querySelector("#tool-close"),
  toolModalLabel: document.querySelector("#tool-modal-label"),
  toolModalTitle: document.querySelector("#tool-modal-title"),
  toolModalText: document.querySelector("#tool-modal-text"),
  browseMeditations: document.querySelector("#browse-meditations"),
  archiveModal: document.querySelector("#archive-modal"),
  archiveClose: document.querySelector("#archive-close"),
  archivePrevious: document.querySelector("#archive-previous"),
  archiveNext: document.querySelector("#archive-next"),
  archiveToday: document.querySelector("#archive-today"),
  archiveDate: document.querySelector("#archive-date"),
  archiveFeedback: document.querySelector("#archive-feedback"),
  archiveReading: document.querySelector("#archive-reading"),
  archiveDateLabel: document.querySelector("#archive-date-label"),
  archiveTitle: document.querySelector("#archive-meditation-title"),
  archiveBody: document.querySelector("#archive-meditation-body"),
  archiveReflection: document.querySelector("#archive-meditation-reflection"),
  progressPanel: document.querySelector("#progress-panel"),
  journeyPrivacyIntro: document.querySelector("#journey-privacy-intro"),
  sobrietyDate: document.querySelector("#sobriety-date"),
  cleanDays: document.querySelector("#clean-days"),
  cleanDaysCopy: document.querySelector("#clean-days-copy"),
  cleanDaysMetric: document.querySelector("#clean-days-metric"),
  monthCount: document.querySelector("#month-count"),
  bestStreak: document.querySelector("#best-streak"),
  checkinGuidance: document.querySelector("#checkin-guidance"),
  anonymousName: document.querySelector("#anonymous-name"),
  anonymousDescription: document.querySelector("#anonymous-description"),
  anonymousForm: document.querySelector("#anonymous-form"),
  anonymousMessage: document.querySelector("#anonymous-message"),
  anonymousSubmit: document.querySelector("#anonymous-submit"),
  anonymousStatus: document.querySelector("#anonymous-status"),
  anonymousFeed: document.querySelector("#anonymous-feed"),
  gratitudeForm: document.querySelector("#gratitude-form"),
  gratitudeInput: document.querySelector("#gratitude-input"),
  gratitudeStatus: document.querySelector("#gratitude-status"),
  gratitudePrivacyNote: document.querySelector("#gratitude-privacy-note"),
  historyList: document.querySelector("#history-list"),
  exportData: document.querySelector("#export-data"),
  reminderTime: document.querySelector("#reminder-time"),
  reminderStatus: document.querySelector("#reminder-status"),
  showCleanDays: document.querySelector("#show-clean-days"),
  supportPlanForm: document.querySelector("#support-plan-form"),
  safePerson: document.querySelector("#safe-person"),
  nextMeeting: document.querySelector("#next-meeting"),
  recoveryReason: document.querySelector("#recovery-reason"),
  supportPlanStatus: document.querySelector("#support-plan-status"),
  editorialFeed: document.querySelector("#editorial-feed"),
  editorialList: document.querySelector("#editorial-list"),
  installApp: document.querySelector("#install-app"),
  pwaStatus: document.querySelector("#pwa-status"),
  moreButton: document.querySelector("#more-button"),
  moreModal: document.querySelector("#more-modal"),
  moreClose: document.querySelector("#more-close"),
  exportDataSecondary: document.querySelector("#export-data-secondary"),
  importData: document.querySelector("#import-data"),
  importStatus: document.querySelector("#import-status"),
  installAppSecondary: document.querySelector("#install-app-secondary"),
  pwaInstallStatus: document.querySelector("#pwa-install-status"),
  pwaUpdate: document.querySelector("#pwa-update"),
  notificationsSecondary: document.querySelector("#notifications-secondary"),
  disableNotifications: document.querySelector("#disable-notifications"),
  accountSummary: document.querySelector("#account-summary"),
  accountAuth: document.querySelector("#account-auth"),
  accountEmailForm: document.querySelector("#account-email-form"),
  accountEmail: document.querySelector("#account-email"),
  accountCodeForm: document.querySelector("#account-code-form"),
  accountCode: document.querySelector("#account-code"),
  accountSession: document.querySelector("#account-session"),
  accountIdentity: document.querySelector("#account-identity"),
  accountStatus: document.querySelector("#account-status"),
  syncLocalData: document.querySelector("#sync-local-data"),
  syncAccountData: document.querySelector("#sync-account-data"),
  deleteAccountData: document.querySelector("#delete-account-data"),
  deleteAccount: document.querySelector("#delete-account"),
  accountSignout: document.querySelector("#account-signout"),
  deleteLocalData: document.querySelector("#delete-local-data"),
  sosButton: document.querySelector("#sos-button"),
  sosModal: document.querySelector("#sos-modal"),
  sosClose: document.querySelector("#sos-close"),
  copySupportMessage: document.querySelector("#copy-support-message"),
  supportMessageStatus: document.querySelector("#support-message-status"),
  privacyPrincipleCopy: document.querySelector("#privacy-principle-copy"),
  privacyStorageSummary: document.querySelector("#privacy-storage-summary"),
  privacyStorageDetail: document.querySelector("#privacy-storage-detail"),
  privacyFaqAnswer: document.querySelector("#privacy-faq-answer"),
};

let currentSupport = null;
let installPrompt = null;
let reminderTimer = null;
let dayRefreshTimer = null;
let journeySyncTimer = null;
let activeModal = null;
let activeModalClose = null;
let modalReturnFocus = null;
let disabledBackgroundFocus = [];
let pendingServiceWorker = null;
let appUpdateRequested = false;
let localSupportCatalog = null;
let meditationCatalog = null;
let archiveRequestId = 0;
const trackedServiceWorkers = new WeakSet();

const accountState = {
  client: null,
  enabled: false,
  pendingEmail: "",
  session: loadAccountSession(),
  syncEnabled: localStorage.getItem("sph-account-sync") === "on",
  aiEnabled: false,
  pushEnabled: false,
  helpDirectoryEnabled: false,
  editorialContentEnabled: false,
  communityEnabled: false,
  communityPosts: [],
  communityLoaded: false,
  vapidPublicKey: "",
  pushRegistered: localStorage.getItem("sph-push-enabled") === "on",
};

const tools = {
  repair: {
    activity: "Identifica uma atitude que queres reparar hoje e escolhe uma ação concreta para mudar.",
    phrase: "Reparar também é mudar a forma como vivo.",
    challenge: "Antes de pedir desculpa, pensa que comportamento vais praticar diferente hoje.",
  },
  vigilance: {
    activity: "Escolhe uma proteção simples para a tua recuperação: reunião, chamada, oração ou descanso.",
    phrase: "A vigilância é cuidado, não medo.",
    challenge: "Repara num sinal de risco e responde com uma ação saudável antes que cresça.",
  },
  service: {
    activity: "Faz um gesto de serviço pequeno e anónimo, sem esperar reconhecimento.",
    phrase: "Servir lembra-me que não caminho sozinho.",
    challenge: "Ajuda alguém hoje sem transformar isso numa dívida.",
  },
  default: {
    activity: "Lê a meditação em voz alta e escreve uma ação pequena para praticar hoje.",
    phrase: "Hoje não preciso resolver a vida inteira; preciso cuidar deste dia.",
    challenge: "Durante uma conversa, escuta até ao fim antes de responder.",
  },
};

function loadProgress() {
  try {
    const progress = JSON.parse(localStorage.getItem("sph-progress")) || {};
    return normalizeProgress(progress);
  } catch {
    return normalizeProgress({});
  }
}

function saveProgress({ touch = true, sync = true } = {}) {
  if (touch) state.progress.updatedAt = new Date().toISOString();
  localStorage.setItem("sph-progress", JSON.stringify(state.progress));
  if (sync) queueJourneySync();
}

function normalizeProgress(progress) {
  const source = progress && typeof progress === "object" && !Array.isArray(progress) ? progress : {};
  return {
    completed: normalizeDateList(source.completed),
    sobrietyDate: isCurrentOrPastDate(source.sobrietyDate) ? source.sobrietyDate : "",
    checkins: normalizeCheckins(source.checkins),
    anonymousName: cleanStoredText(source.anonymousName, 32) || makeAnonymousName(),
    anonymousShares: normalizeAnonymousShares(source.anonymousShares),
    notifications: source.notifications === "on" ? "on" : "off",
    gratitudes: normalizeTextByDate(source.gratitudes, 240),
    reminderTime: /^([01]\d|2[0-3]):[0-5]\d$/.test(source.reminderTime) ? source.reminderTime : "07:00",
    showCleanDays: source.showCleanDays !== false,
    supportPlan: normalizeSupportPlan(source.supportPlan),
    lastReminderAt: isCurrentOrPastDate(source.lastReminderAt) ? source.lastReminderAt : "",
    updatedAt: typeof source.updatedAt === "string" ? source.updatedAt.slice(0, 32) : "",
  };
}

function cleanStoredText(value, maxLength) {
  return typeof value === "string" ? value.trim().slice(0, maxLength) : "";
}

function isIsoDate(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

function isCurrentOrPastDate(value) {
  return isIsoDate(value) && value <= getCapeVerdeToday().iso;
}

function normalizeDateList(value) {
  if (!Array.isArray(value)) return [];
  return [...new Set(value.filter(isCurrentOrPastDate))].sort().slice(-3660);
}

function normalizeCheckins(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  const allowed = new Set(["firme", "ansioso", "risco", "consumo"]);
  return Object.fromEntries(Object.entries(value)
    .filter(([day, stateValue]) => isCurrentOrPastDate(day) && allowed.has(stateValue))
    .slice(-3660));
}

function normalizeTextByDate(value, maxLength) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return Object.fromEntries(Object.entries(value)
    .filter(([day, textValue]) => isCurrentOrPastDate(day) && typeof textValue === "string")
    .map(([day, textValue]) => [day, cleanStoredText(textValue, maxLength)])
    .filter(([, textValue]) => textValue)
    .slice(-3660));
}

function normalizeAnonymousShares(value) {
  if (!Array.isArray(value)) return [];
  return value
    .filter((share) => share && typeof share === "object")
    .map((share) => ({
      name: cleanStoredText(share.name, 32) || "Anónimo",
      message: cleanStoredText(share.message, 280),
      date: typeof share.date === "string" ? share.date.slice(0, 32) : "",
    }))
    .filter((share) => share.message)
    .slice(-20);
}

function normalizeSupportPlan(value) {
  const plan = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  return {
    safePerson: cleanStoredText(plan.safePerson, 60),
    nextMeeting: cleanStoredText(plan.nextMeeting, 100),
    recoveryReason: cleanStoredText(plan.recoveryReason, 240),
  };
}

function loadAccountSession() {
  try {
    const session = JSON.parse(localStorage.getItem("sph-account-session"));
    if (!session?.access_token || !session?.refresh_token || !session?.user?.id) return null;
    return session;
  } catch {
    return null;
  }
}

function persistAccountSession(session) {
  accountState.session = session;
  if (session) {
    localStorage.setItem("sph-account-session", JSON.stringify(session));
  } else {
    localStorage.removeItem("sph-account-session");
  }
}

function clearAiSupportCache() {
  Object.keys(localStorage)
    .filter((key) => key.startsWith("sph-ai-support:"))
    .forEach((key) => localStorage.removeItem(key));
}

async function setupAccount() {
  try {
    const response = await fetch("/api/v1/config", {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error("Configuração indisponível");
    const config = await response.json();
    accountState.helpDirectoryEnabled = Boolean(config.features?.helpDirectory);
    accountState.editorialContentEnabled = Boolean(config.features?.editorialContent);
    accountState.communityEnabled = Boolean(config.features?.community);
    if (accountState.helpDirectoryEnabled) {
      await loadVerifiedHelpResources();
    }
    if (accountState.editorialContentEnabled) {
      await loadEditorialContent();
    }
    if (accountState.communityEnabled) {
      await loadPublishedCommunity();
    }
    if (!config.features?.account || !config.supabase) {
      renderAccount();
      return;
    }

    const { SupabaseAccountClient } = await import("./account-client.mjs");
    accountState.client = new SupabaseAccountClient(config.supabase);
    accountState.enabled = true;
    accountState.aiEnabled = Boolean(config.features?.ai);
    accountState.pushEnabled = Boolean(config.features?.push && config.push?.vapidPublicKey);
    accountState.vapidPublicKey = config.push?.vapidPublicKey || "";
    if (accountState.session) {
      try {
        persistAccountSession(await accountState.client.ensureSession(accountState.session));
      } catch {
        persistAccountSession(null);
        accountState.syncEnabled = false;
        localStorage.removeItem("sph-account-sync");
      }
    }
    renderAccount();
  } catch {
    renderAccount();
  }
}

function editorialKindLabel(kind) {
  return {
    podcast: "Podcast",
    video: "Vídeo",
    story: "História",
    resource: "Recurso",
    exhibition: "Exposição",
    event: "Evento",
  }[kind] || "Conteúdo";
}

function safeSameOriginImage(value) {
  try {
    const url = new URL(value, window.location.origin);
    return url.origin === window.location.origin ? url.href : "";
  } catch {
    return "";
  }
}

function renderEditorialContent(items) {
  els.editorialList.replaceChildren();
  items.forEach((item) => {
    const link = document.createElement("a");
    link.className = "editorial-item";
    link.href = item.url;
    link.target = "_blank";
    link.rel = "noreferrer";
    const imageUrl = safeSameOriginImage(item.image_url);
    if (imageUrl) {
      const image = document.createElement("img");
      image.src = imageUrl;
      image.alt = "";
      image.loading = "lazy";
      link.classList.add("has-image");
      link.append(image);
    }
    const copy = document.createElement("div");
    const kind = document.createElement("span");
    kind.textContent = editorialKindLabel(item.kind);
    const title = document.createElement("h4");
    title.textContent = item.title || "Conteúdo";
    const summary = document.createElement("p");
    summary.textContent = item.summary || "";
    copy.append(kind, title, summary);
    if (item.display_date) {
      const date = document.createElement("time");
      date.textContent = item.display_date;
      copy.append(date);
    }
    link.append(copy);
    els.editorialList.append(link);
  });
  els.editorialFeed.hidden = !items.length;
}

async function loadEditorialContent() {
  try {
    const response = await fetch("/api/v1/content?limit=50", {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error("Catálogo indisponível");
    const items = await response.json();
    renderEditorialContent(Array.isArray(items) ? items : []);
  } catch {
    els.editorialFeed.hidden = true;
    els.editorialList.replaceChildren();
  }
}

function renderAccount() {
  const signedIn = accountState.enabled && Boolean(accountState.session);
  els.accountAuth.hidden = !accountState.enabled || signedIn;
  els.accountSession.hidden = !signedIn;
  renderPrivacyState();
  renderAnonymousRoom();

  if (!accountState.enabled) {
    els.accountSummary.textContent = "A conta opcional ainda não está configurada neste ambiente. Continuas no modo local e anónimo.";
    els.accountStatus.textContent = "A exportação manual continua disponível.";
    return;
  }
  if (!signedIn) {
    els.accountSummary.textContent = "Entra com um código por email para sincronizar a Jornada entre dispositivos.";
    els.accountStatus.textContent = "Nada será sincronizado antes da tua escolha.";
    return;
  }

  els.accountIdentity.textContent = accountState.session.user.email || "conta verificada";
  els.accountSummary.textContent = accountState.syncEnabled
    ? "A Jornada está ligada à tua conta. Alterações locais serão sincronizadas."
    : "Sessão iniciada. Escolhe qual cópia da Jornada queres usar.";
  els.accountStatus.textContent = accountState.syncEnabled ? "Sincronização ativa." : "Sincronização à espera da tua decisão.";
}

function renderPrivacyState() {
  const copy = getPrivacyCopy({
    accountEnabled: accountState.enabled,
    signedIn: accountState.enabled && Boolean(accountState.session),
    syncEnabled: accountState.syncEnabled,
  });
  els.privacyPrincipleCopy.textContent = copy.principle;
  els.privacyStorageSummary.textContent = copy.summary;
  els.privacyStorageDetail.textContent = copy.detail;
  els.journeyPrivacyIntro.textContent = copy.journeyIntro;
  els.gratitudePrivacyNote.textContent = copy.gratitudeNote;
  els.privacyFaqAnswer.textContent = copy.faqAnswer;
}

function appendHelpLink(container, label, href) {
  if (!href) return null;
  const link = document.createElement("a");
  link.textContent = label;
  link.href = href;
  if (href.startsWith("http")) {
    link.target = "_blank";
    link.rel = "noreferrer";
  }
  container.append(link);
  return link;
}

function primaryTelephone(value) {
  const match = String(value || "").match(/\+?\d[\d\s-]{5,}/);
  return match ? match[0].replace(/(?!^)\D/g, "") : "";
}

function createHelpResourceCard(resource) {
  const categoryLabels = {
    emergency: "Apoio imediato",
    health: "Saúde",
    treatment: "Tratamento",
    meeting: "Reunião",
    family: "Família",
    information: "Informação",
    other: "Recurso",
  };
  const article = document.createElement("article");
  const heading = document.createElement("div");
  heading.className = "resource-heading";
  const name = document.createElement("strong");
  name.textContent = resource.name || "Recurso de apoio";
  const status = document.createElement("span");
  status.className = "resource-status verified";
  status.textContent = categoryLabels[resource.category] || "Verificado";
  heading.append(name, status);
  article.append(heading);

  const location = [resource.municipality, resource.island].filter(Boolean).join(" · ");
  if (location) {
    const locationLine = document.createElement("p");
    locationLine.textContent = location;
    article.append(locationLine);
  }
  if (resource.description) {
    const description = document.createElement("p");
    description.textContent = resource.description;
    article.append(description);
  }
  if (Array.isArray(resource.schedule) && resource.schedule.length) {
    const schedule = document.createElement("ul");
    schedule.className = "schedule-list";
    resource.schedule.forEach((item) => {
      const entry = document.createElement("li");
      entry.textContent = item;
      schedule.append(entry);
    });
    article.append(schedule);
  }

  const actions = document.createElement("div");
  actions.className = "help-actions";
  const telephone = primaryTelephone(resource.phone);
  const phoneLink = appendHelpLink(actions, resource.is_emergency ? "Ligar agora" : "Ligar", telephone ? `tel:${telephone}` : "");
  if (phoneLink && resource.is_emergency) phoneLink.classList.add("help-primary");
  appendHelpLink(actions, "Email", resource.email ? `mailto:${resource.email}` : "");
  appendHelpLink(actions, "Site", resource.website || "");
  appendHelpLink(actions, "Fonte", resource.source_url || "");
  if (actions.childElementCount) article.append(actions);

  if (resource.review_due_at) {
    const review = document.createElement("p");
    review.className = "resource-review";
    review.textContent = `Verificação válida até ${new Date(`${resource.review_due_at}T12:00:00`).toLocaleDateString("pt-CV")}.`;
    article.append(review);
  }
  return article;
}

function renderHelpResourceGroup(list, resources, emptyTitle, emptyCopy) {
  list.replaceChildren();
  if (!resources.length) {
    const empty = document.createElement("article");
    const title = document.createElement("strong");
    title.textContent = emptyTitle;
    const copy = document.createElement("p");
    copy.textContent = emptyCopy;
    empty.append(title, copy);
    list.append(empty);
    return;
  }
  resources.forEach((resource) => list.append(createHelpResourceCard(resource)));
}

function renderVerifiedHelpResources(resources) {
  const meetingList = document.querySelector("#verified-meeting-list");
  const helpList = document.querySelector("#verified-help-list");
  const source = document.querySelector("#help-directory-source");
  if (!meetingList || !helpList || !source) return;

  const meetings = resources.filter((resource) => ["meeting", "family"].includes(resource.category));
  const support = resources.filter((resource) => !["meeting", "family"].includes(resource.category));
  renderHelpResourceGroup(
    meetingList,
    meetings,
    "Reuniões em revisão",
    "Ainda não existem reuniões com verificação válida no diretório.",
  );
  renderHelpResourceGroup(
    helpList,
    support,
    "Diretório em revisão",
    "Ainda não existem recursos com verificação válida. Usa as opções de apoio imediato acima.",
  );

  source.replaceChildren();
  const note = document.createElement("p");
  note.textContent = "Este diretório mostra apenas recursos com fonte registada e revisão ainda válida. Confirma sempre o atendimento antes da deslocação.";
  source.append(note);
}

function renderHelpDirectoryUnavailable() {
  const meetingList = document.querySelector("#verified-meeting-list");
  const helpList = document.querySelector("#verified-help-list");
  const source = document.querySelector("#help-directory-source");
  if (!meetingList || !helpList || !source) return;
  renderHelpResourceGroup(meetingList, [], "Reuniões temporariamente indisponíveis", "Confirma diretamente com os grupos antes de te deslocares.");
  renderHelpResourceGroup(helpList, [], "Diretório temporariamente indisponível", "Usa as opções de apoio imediato acima ou procura um serviço de saúde próximo.");
  source.replaceChildren();
}

async function loadVerifiedHelpResources() {
  try {
    const response = await fetch("/api/v1/help/resources", {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error("Diretório indisponível");
    const resources = await response.json();
    renderVerifiedHelpResources(Array.isArray(resources) ? resources : []);
  } catch {
    renderHelpDirectoryUnavailable();
  }
}

async function requestAccountCode(email) {
  const normalizedEmail = email.trim().toLowerCase();
  if (!accountState.client || !normalizedEmail) return;
  els.accountStatus.textContent = "A enviar código...";
  await accountState.client.sendOtp(normalizedEmail);
  accountState.pendingEmail = normalizedEmail;
  els.accountCodeForm.hidden = false;
  els.accountCode.focus();
  els.accountStatus.textContent = "Código enviado. Verifica o email e introduz o código recebido.";
}

async function verifyAccountCode(token) {
  if (!accountState.client || !accountState.pendingEmail) return;
  els.accountStatus.textContent = "A verificar código...";
  const session = await accountState.client.verifyOtp(accountState.pendingEmail, token.trim());
  persistAccountSession(session);
  accountState.pendingEmail = "";
  els.accountCode.value = "";
  renderAccount();
}

function enableJourneySync() {
  accountState.syncEnabled = true;
  localStorage.setItem("sph-account-sync", "on");
  renderAccount();
}

function pauseJourneySync(message) {
  accountState.syncEnabled = false;
  localStorage.removeItem("sph-account-sync");
  renderAccount();
  els.accountStatus.textContent = message;
}

async function uploadLocalJourney({ silent = false } = {}) {
  if (!accountState.client || !accountState.session) return;
  if (!silent) els.accountStatus.textContent = "A guardar a Jornada na conta...";
  const {
    hasRemoteJourneyConflict,
    selectSyncableProgress,
    validateRemoteJourneyRecord,
  } = await import("./journey-sync.mjs");
  const remoteResult = await accountState.client.getJourney(accountState.session);
  persistAccountSession(remoteResult.session);
  let expectedUpdatedAt = null;
  if (remoteResult.record) {
    const remote = validateRemoteJourneyRecord(remoteResult.record);
    expectedUpdatedAt = remote.updatedAt;
    if (silent && hasRemoteJourneyConflict(state.progress.updatedAt, remote.updatedAt)) {
      pauseJourneySync("Existem alterações mais recentes noutro dispositivo. Escolhe qual cópia da Jornada queres usar.");
      return;
    }
  }
  const result = await accountState.client.saveJourney(accountState.session, selectSyncableProgress(state.progress), {
    expectedUpdatedAt,
    force: !silent,
  });
  persistAccountSession(result.session);
  if (!result.saved) {
    pauseJourneySync("A Jornada mudou noutro dispositivo durante a sincronização. Escolhe qual cópia queres usar.");
    return;
  }
  enableJourneySync();
  if (!silent) els.accountStatus.textContent = "Dados deste dispositivo guardados na conta.";
}

async function useAccountJourney() {
  if (!accountState.client || !accountState.session) return;
  els.accountStatus.textContent = "A procurar dados da conta...";
  const result = await accountState.client.getJourney(accountState.session);
  persistAccountSession(result.session);
  if (!result.record) {
    els.accountStatus.textContent = "Ainda não existem dados guardados nesta conta.";
    return;
  }
  const { validateRemoteJourneyRecord } = await import("./journey-sync.mjs");
  const remote = validateRemoteJourneyRecord(result.record);
  const confirmed = window.confirm("Substituir a Jornada deste dispositivo pela cópia guardada na conta?");
  if (!confirmed) {
    els.accountStatus.textContent = "Nenhum dado foi alterado.";
    return;
  }

  const deviceOnly = {
    anonymousName: state.progress.anonymousName,
    anonymousShares: state.progress.anonymousShares,
    notifications: state.progress.notifications,
    lastReminderAt: state.progress.lastReminderAt,
  };
  state.progress = normalizeProgress({ ...remote.payload, ...deviceOnly });
  saveProgress({ touch: false, sync: false });
  enableJourneySync();
  renderProgress();
  renderAnonymousRoom();
  els.accountStatus.textContent = "Cópia da conta aplicada neste dispositivo.";
}

function queueJourneySync() {
  if (!accountState.syncEnabled || !accountState.client || !accountState.session) return;
  if (journeySyncTimer) window.clearTimeout(journeySyncTimer);
  journeySyncTimer = window.setTimeout(() => {
    uploadLocalJourney({ silent: true }).catch(() => {
      els.accountStatus.textContent = "A sincronização será tentada novamente quando houver ligação.";
    });
  }, 1200);
}

async function signOutAccount() {
  if (accountState.client && accountState.session) {
    try {
      await removeRemotePushRegistration();
    } catch {
      // Signing out must continue even when push cleanup is unavailable.
    }
    try {
      await accountState.client.signOut(accountState.session);
    } catch {
      // The local session is still cleared when the remote logout is unavailable.
    }
  }
  persistAccountSession(null);
  clearAiSupportCache();
  accountState.syncEnabled = false;
  localStorage.removeItem("sph-account-sync");
  renderAccount();
  els.accountStatus.textContent = "Sessão terminada. Os dados locais foram mantidos.";
}

async function deleteAccountJourney() {
  if (!accountState.client || !accountState.session) return;
  const confirmed = window.confirm("Apagar definitivamente a cópia sincronizada da Jornada? Os dados deste dispositivo serão mantidos.");
  if (!confirmed) {
    els.accountStatus.textContent = "A cópia da conta foi mantida.";
    return;
  }
  els.accountStatus.textContent = "A apagar a cópia da conta...";
  persistAccountSession(await accountState.client.deleteJourney(accountState.session));
  accountState.syncEnabled = false;
  localStorage.removeItem("sph-account-sync");
  renderAccount();
  els.accountStatus.textContent = "Cópia sincronizada apagada. Os dados deste dispositivo foram mantidos.";
}

async function deleteCurrentAccount() {
  if (!accountState.client || !accountState.session) return;
  const confirmed = window.confirm(
    "Eliminar definitivamente a conta, todos os dados sincronizados e os dados Só Por Hoje deste dispositivo? Esta ação não pode ser desfeita.",
  );
  if (!confirmed) {
    els.accountStatus.textContent = "A conta foi mantida.";
    return;
  }
  els.accountStatus.textContent = "A eliminar a conta...";
  try {
    await removeRemotePushRegistration();
  } catch {
    // Account deletion cascades to the remote subscription records.
  }
  try {
    await accountState.client.deleteAccount(accountState.session);
  } catch (error) {
    els.accountStatus.textContent = error.message || "Não foi possível eliminar a conta.";
    return;
  }
  Object.keys(localStorage)
    .filter((key) => key.startsWith("sph-"))
    .forEach((key) => localStorage.removeItem(key));
  window.location.reload();
}

async function deleteDeviceData() {
  const confirmed = window.confirm("Apagar todos os dados Só Por Hoje guardados neste dispositivo? Esta ação não pode ser desfeita.");
  if (!confirmed) {
    els.accountStatus.textContent = "Os dados deste dispositivo foram mantidos.";
    return;
  }
  if (accountState.client && accountState.session) {
    try {
      await removeRemotePushRegistration();
    } catch {
      // Local deletion must still be possible while push cleanup is unavailable.
    }
    try {
      await accountState.client.signOut(accountState.session);
    } catch {
      // Local deletion must still be possible while offline.
    }
  }
  Object.keys(localStorage)
    .filter((key) => key.startsWith("sph-"))
    .forEach((key) => localStorage.removeItem(key));
  window.location.reload();
}

function makeAnonymousName() {
  return `Guerreiro${Math.floor(100 + Math.random() * 900)}`;
}

function showMode(mode) {
  els.loading.hidden = mode !== "loading";
  els.error.hidden = mode !== "error";
  els.content.hidden = mode !== "content";
}

async function loadToday() {
  showMode("loading");
  try {
    const response = await fetch("/api/v1/today");
    if (!response.ok) {
      throw new Error(`API respondeu com ${response.status}`);
    }
    state.daily = await response.json();
    renderMeditation();
  } catch (error) {
    try {
      state.daily = await loadTodayFromStaticData();
      renderMeditation();
    } catch (fallbackError) {
      els.errorMessage.textContent = fallbackError.message || error.message || "A meditação não carregou.";
      showMode("error");
    }
  }
}

async function loadTodayFromStaticData() {
  const today = getCapeVerdeToday();
  return loadMeditationForDate(today.iso);
}

async function loadMeditationCatalog() {
  if (meditationCatalog) return meditationCatalog;
  const response = await fetch("data/meditations.json");
  if (!response.ok) throw new Error("A base local de meditações não respondeu.");
  const records = await response.json();
  meditationCatalog = new Map(records.map((record) => [record.month_day, record]));
  return meditationCatalog;
}

async function loadMeditationForDate(isoDate) {
  if (!isIsoDate(isoDate)) throw new Error("Escolhe uma data válida.");
  const records = await loadMeditationCatalog();
  const monthDay = isoDate.slice(5);
  const meditation = records.get(monthDay);
  if (!meditation) {
    throw new Error(`Meditação não encontrada para ${monthDay}.`);
  }
  const date = new Date(`${isoDate}T12:00:00Z`);
  const weekdayText = new Intl.DateTimeFormat("pt-PT", {
    weekday: "long",
    timeZone: "Atlantic/Cape_Verde",
  }).format(date);
  return {
    date: isoDate,
    weekday: weekdayText.charAt(0).toUpperCase() + weekdayText.slice(1),
    month_day: meditation.month_day,
    title: meditation.title,
    body: meditation.body,
    reflection: meditation.reflection,
  };
}

async function renderArchiveMeditation(isoDate) {
  const requestId = ++archiveRequestId;
  const today = getCapeVerdeToday().iso;
  if (!isIsoDate(isoDate) || isoDate > today) {
    els.archiveReading.hidden = true;
    els.archiveFeedback.textContent = "Escolhe uma data válida até hoje.";
    return;
  }

  els.archiveFeedback.textContent = "A carregar meditação...";
  els.archiveReading.hidden = true;
  try {
    const daily = await loadMeditationForDate(isoDate);
    if (requestId !== archiveRequestId) return;
    els.archiveDate.value = isoDate;
    els.archiveDateLabel.dateTime = isoDate;
    els.archiveDateLabel.textContent = formatDateLine(daily.date, daily.weekday);
    els.archiveTitle.textContent = daily.title;
    els.archiveBody.textContent = daily.body;
    els.archiveReflection.textContent = daily.reflection;
    els.archivePrevious.disabled = false;
    els.archiveNext.disabled = isoDate >= today;
    els.archiveFeedback.textContent = "";
    els.archiveReading.hidden = false;
  } catch (error) {
    if (requestId !== archiveRequestId) return;
    els.archiveFeedback.textContent = error.message || "Não foi possível abrir esta meditação.";
  }
}

function openArchiveForDate(isoDate, returnFocus) {
  const today = getCapeVerdeToday().iso;
  els.archiveDate.max = today;
  els.archiveDate.value = isIsoDate(isoDate) && isoDate <= today ? isoDate : today;
  renderArchiveMeditation(els.archiveDate.value);
  openModal(els.archiveModal, closeArchive, returnFocus, els.archiveDate);
}

function openArchive() {
  openArchiveForDate(state.daily?.date || getCapeVerdeToday().iso, els.browseMeditations);
}

function closeArchive() {
  archiveRequestId += 1;
  closeModal(els.archiveModal);
}

function moveArchiveDate(offset) {
  const selected = els.archiveDate.value || getCapeVerdeToday().iso;
  const nextDate = addIsoDays(selected, offset);
  if (nextDate <= getCapeVerdeToday().iso) renderArchiveMeditation(nextDate);
}

function getCapeVerdeToday() {
  return getCalendarDayInTimeZone();
}

function refreshForNewDay() {
  const today = getCapeVerdeToday().iso;
  if (!state.daily || state.daily.date === today) return;
  currentSupport = null;
  loadToday();
}

function scheduleDayRefreshCheck() {
  if (dayRefreshTimer) window.clearTimeout(dayRefreshTimer);
  const nextMinute = 60_000 - (Date.now() % 60_000) + 100;
  dayRefreshTimer = window.setTimeout(() => {
    refreshForNewDay();
    scheduleDayRefreshCheck();
  }, nextMinute);
}

function renderMeditation() {
  const daily = state.daily;
  els.currentDate.textContent = formatDateLine(daily.date, daily.weekday);
  els.title.textContent = daily.title;
  els.body.textContent = daily.body;
  els.reflection.textContent = daily.reflection;
  els.sobrietyDate.max = daily.date;
  showMode("content");
  renderProgress();
  renderAnonymousRoom();
}

function formatDateLine(isoDate, weekday) {
  const date = new Date(`${isoDate}T00:00:00`);
  const day = String(date.getDate()).padStart(2, "0");
  const month = date.toLocaleDateString("pt-PT", { month: "long" });
  return `${weekday}, ${day} de ${month}`;
}

function formatGroupDateLine(isoDate, weekday) {
  const date = new Date(`${isoDate}T00:00:00`);
  const shortWeekday = weekday.replace("-feira", "");
  const day = String(date.getDate()).padStart(2, "0");
  const month = date.toLocaleDateString("pt-PT", { month: "long" });
  const capitalizedMonth = month.charAt(0).toUpperCase() + month.slice(1);
  return `${shortWeekday}, ${day} de ${capitalizedMonth} de ${date.getFullYear()}`;
}

function composeGroupMessage(daily) {
  const header = [
    "BOM DIA GUERREIROS",
    "MEDITAÇÃO DO DIA",
    formatGroupDateLine(daily.date, daily.weekday),
  ].join("\n\n");
  const body = daily.body.replace("\n\n", "\n\n\n");

  return `${header}\n\n\n${daily.title}\n\n\n${body}\n\n\nSÓ POR HOJE:\n\n${daily.reflection}\n\n\nsoporhoje.cv\n\n\nFonte oficial: Narcóticos Anónimos Portugal\n© NA World Services, Inc. Reprinted by permission.`;
}

function renderProgress() {
  const today = state.daily?.date;
  const completed = new Set(state.progress.completed);
  const doneToday = today && completed.has(today);
  const currentStreak = getCurrentStreak(completed, today);
  const monthPrefix = today?.slice(0, 7);
  const monthTotal = [...completed].filter((day) => day.startsWith(monthPrefix)).length;
  const cleanDays = getCleanDays(today);

  els.streakCount.textContent = `${currentStreak} ${currentStreak === 1 ? "leitura seguida" : "leituras seguidas"}`;
  els.statusCard.hidden = !doneToday || state.view !== "meditation";
  els.complete.setAttribute(
    "aria-label",
    doneToday ? "Meditação lida hoje" : "Marcar meditação como lida",
  );
  els.complete.setAttribute("aria-pressed", String(Boolean(doneToday)));
  els.completeLabel.textContent = "✓";
  els.sobrietyDate.value = state.progress.sobrietyDate;
  els.cleanDaysMetric.textContent = cleanDays;
  els.monthCount.textContent = monthTotal;
  els.bestStreak.textContent = getBestStreak(completed);
  renderCleanDays(cleanDays);
  renderCheckinGuidance();
  renderRewards(cleanDays, currentStreak);
  renderGratitude();
  renderJourneyHistory();
  renderJourneySettings();
  renderSupportPlan();
}

function renderSupportPlan() {
  if (!els.supportPlanForm) return;
  els.safePerson.value = state.progress.supportPlan.safePerson;
  els.nextMeeting.value = state.progress.supportPlan.nextMeeting;
  els.recoveryReason.value = state.progress.supportPlan.recoveryReason;
}

function saveSupportPlan() {
  state.progress.supportPlan = normalizeSupportPlan({
    safePerson: els.safePerson.value,
    nextMeeting: els.nextMeeting.value,
    recoveryReason: els.recoveryReason.value,
  });
  saveProgress();
  renderSupportPlan();
  els.supportPlanStatus.textContent = accountState.syncEnabled
    ? "Plano guardado e preparado para sincronizar."
    : "Plano guardado neste dispositivo.";
}

function renderGratitude() {
  const today = state.daily?.date;
  if (!today || !els.gratitudeInput) return;
  const value = state.progress.gratitudes[today] || "";
  els.gratitudeInput.value = value;
  els.gratitudeStatus.textContent = value ? "Gratidão guardada para hoje." : "";
}

function saveGratitude(value) {
  const today = state.daily?.date;
  if (!today) return;
  const gratitude = value.trim();
  if (gratitude) {
    state.progress.gratitudes[today] = gratitude;
    els.gratitudeStatus.textContent = "Gratidão guardada para hoje.";
  } else {
    delete state.progress.gratitudes[today];
    els.gratitudeStatus.textContent = "A gratidão de hoje foi removida.";
  }
  saveProgress();
  renderJourneyHistory();
}

function renderJourneyHistory() {
  if (!els.historyList) return;
  const days = new Set([
    ...state.progress.completed,
    ...Object.keys(state.progress.checkins),
    ...Object.keys(state.progress.gratitudes),
  ]);
  const recent = [...days].sort().reverse().slice(0, 10);
  const labels = {
    firme: "Firme",
    ansioso: "Serenidade",
    risco: "Em risco",
    consumo: "Recomeço",
  };

  els.historyList.innerHTML = recent.length
    ? recent.map((day) => {
        const parts = [];
        if (state.progress.completed.includes(day)) parts.push("Meditação lida");
        if (state.progress.checkins[day]) parts.push(labels[state.progress.checkins[day]] || "Check-in");
        if (state.progress.gratitudes[day]) parts.push("Gratidão");
        const gratitude = state.progress.gratitudes[day];
        return `<button class="history-item" type="button" data-history-date="${day}" aria-label="Abrir meditação de ${formatShortDate(day)}">
          <time datetime="${day}">${formatShortDate(day)}</time>
          <strong>${escapeHtml(parts.join(" · "))}</strong>
          <small>${gratitude ? escapeHtml(gratitude) : ""}</small>
          <span class="history-open" aria-hidden="true">›</span>
        </button>`;
      }).join("")
    : '<p class="history-empty">O teu histórico começa quando fizeres o primeiro check-in, leitura ou gratidão.</p>';
}

function formatShortDate(isoDate) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString("pt-PT", {
    day: "2-digit",
    month: "short",
  });
}

function renderJourneySettings() {
  if (!els.reminderTime || !els.showCleanDays) return;
  els.reminderTime.value = state.progress.reminderTime;
  els.showCleanDays.checked = state.progress.showCleanDays;
  const metric = els.cleanDaysMetric.closest("div");
  if (metric) metric.hidden = !state.progress.showCleanDays;
  renderReminderStatus();
}

function renderReminderStatus() {
  if (els.disableNotifications) {
    els.disableNotifications.hidden = state.progress.notifications !== "on";
  }
  if (!("Notification" in window)) {
    els.reminderStatus.textContent = "Este navegador não disponibiliza notificações.";
    return;
  }
  if (Notification.permission !== "granted" || state.progress.notifications !== "on") {
    els.reminderStatus.textContent = "Notificações ainda não autorizadas neste dispositivo.";
    return;
  }
  els.reminderStatus.textContent = accountState.pushEnabled && accountState.pushRegistered
    ? `Notificação diária preparada para ${state.progress.reminderTime}, mesmo com a aplicação fechada.`
    : `Lembrete local preparado para ${state.progress.reminderTime}, enquanto a aplicação estiver aberta.`;
}

function scheduleSessionReminder() {
  if (reminderTimer) {
    window.clearTimeout(reminderTimer);
    reminderTimer = null;
  }
  renderReminderStatus();
  if (!("Notification" in window) || Notification.permission !== "granted" || state.progress.notifications !== "on") {
    return;
  }

  const [hour, minute] = state.progress.reminderTime.split(":").map(Number);
  const now = new Date();
  const next = new Date(now);
  next.setHours(hour, minute, 0, 0);
  if (next <= now) next.setDate(next.getDate() + 1);

  reminderTimer = window.setTimeout(async () => {
    try {
      const today = getCapeVerdeToday().iso;
      if (state.progress.lastReminderAt !== today) {
        await showAppNotification("Só Por Hoje", "A meditação de hoje está pronta. Um dia de cada vez.");
        state.progress.lastReminderAt = today;
        saveProgress({ touch: false, sync: false });
      }
    } finally {
      scheduleSessionReminder();
    }
  }, next.getTime() - now.getTime());
}

async function showAppNotification(title, body) {
  if ("serviceWorker" in navigator) {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration) {
      await registration.showNotification(title, {
        body,
        icon: "/icon-512.png",
        badge: "/favicon-32.png",
        tag: "sph-daily-reminder",
      });
      return;
    }
  }
  new Notification(title, { body, icon: "icon-512.png", tag: "sph-daily-reminder" });
}

function exportJourneyData() {
  const payload = {
    exportedAt: new Date().toISOString(),
    version: 1,
    progress: state.progress,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `so-por-hoje-jornada-${getCapeVerdeToday().iso}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function isStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
}

function getInstallGuidance() {
  const userAgent = window.navigator.userAgent || "";
  const isIos = /iPad|iPhone|iPod/.test(userAgent)
    || (window.navigator.platform === "MacIntel" && window.navigator.maxTouchPoints > 1);
  if (isIos) {
    return "No Safari, toca em Partilhar e depois em Adicionar ao ecrã principal.";
  }
  if (/Android/i.test(userAgent)) {
    return "No menu do navegador, escolhe Instalar aplicação ou Adicionar ao ecrã principal.";
  }
  return "No menu do navegador, escolhe Instalar aplicação. Esta opção pode aparecer também na barra de endereço.";
}

function updateInstallAction() {
  const installed = isStandalone();
  els.installApp.hidden = installed || !installPrompt;
  els.installAppSecondary.hidden = installed;
  if (installed) {
    els.pwaInstallStatus.textContent = "Aplicação instalada neste dispositivo.";
    return;
  }
  els.installAppSecondary.textContent = installPrompt ? "Instalar aplicação" : "Como instalar";
}

async function installApp() {
  if (!installPrompt) {
    const message = isStandalone()
      ? "A aplicação já está instalada."
      : getInstallGuidance();
    els.pwaStatus.textContent = message;
    els.pwaInstallStatus.textContent = message;
    return;
  }
  installPrompt.prompt();
  const result = await installPrompt.userChoice;
  const message = result.outcome === "accepted"
    ? "Instalação iniciada."
    : "A instalação foi cancelada.";
  els.pwaStatus.textContent = message;
  els.pwaInstallStatus.textContent = message;
  installPrompt = null;
  updateInstallAction();
}

function openModal(modal, closeHandler, returnFocus, initialFocus) {
  activeModal = modal;
  activeModalClose = closeHandler;
  modalReturnFocus = returnFocus;
  modal.hidden = false;
  els.appContent.setAttribute("aria-hidden", "true");
  if ("inert" in els.appContent) {
    els.appContent.inert = true;
  } else {
    disabledBackgroundFocus = [...els.appContent.querySelectorAll(
      'a[href], button, input, textarea, select, [tabindex]',
    )].map((element) => ({ element, tabindex: element.getAttribute("tabindex") }));
    disabledBackgroundFocus.forEach(({ element }) => element.setAttribute("tabindex", "-1"));
  }
  document.body.classList.add("modal-open");
  window.requestAnimationFrame(() => initialFocus.focus());
}

function closeModal(modal) {
  if (modal.hidden) return;
  modal.hidden = true;
  els.appContent.removeAttribute("aria-hidden");
  if ("inert" in els.appContent) {
    els.appContent.inert = false;
  } else {
    disabledBackgroundFocus.forEach(({ element, tabindex }) => {
      if (tabindex === null) element.removeAttribute("tabindex");
      else element.setAttribute("tabindex", tabindex);
    });
    disabledBackgroundFocus = [];
  }
  document.body.classList.remove("modal-open");
  const returnFocus = modalReturnFocus;
  activeModal = null;
  activeModalClose = null;
  modalReturnFocus = null;
  if (returnFocus?.isConnected) returnFocus.focus();
}

function getModalFocusableElements(modal) {
  return [...modal.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )].filter((element) => (
    !element.hidden
    && element.getAttribute("aria-hidden") !== "true"
    && element.getClientRects().length > 0
  ));
}

function trapModalFocus(event) {
  if (!activeModal || event.key !== "Tab") return;
  const focusable = getModalFocusableElements(activeModal);
  if (!focusable.length) {
    event.preventDefault();
    return;
  }
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && (document.activeElement === first || !activeModal.contains(document.activeElement))) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && (document.activeElement === last || !activeModal.contains(document.activeElement))) {
    event.preventDefault();
    first.focus();
  }
}

document.addEventListener("focusin", (event) => {
  if (!activeModal || activeModal.contains(event.target)) return;
  getModalFocusableElements(activeModal)[0]?.focus();
});

function openMore() {
  openModal(els.moreModal, closeMore, els.moreButton, els.moreClose);
}

function closeMore() {
  closeModal(els.moreModal);
}

async function importJourneyData(file) {
  if (!file) return;
  try {
    const { MAX_JOURNEY_BACKUP_BYTES, parseJourneyBackup } = await import("./journey-backup.mjs");
    if (file.size > MAX_JOURNEY_BACKUP_BYTES) throw new Error("Cópia demasiado grande");
    const progress = parseJourneyBackup(await file.text());
    const confirmed = window.confirm("Substituir os dados locais da Jornada pelos dados desta cópia?");
    if (!confirmed) {
      els.importStatus.textContent = "Importação cancelada.";
      return;
    }
    state.progress = normalizeProgress(progress);
    saveProgress();
    renderProgress();
    renderAnonymousRoom();
    els.importStatus.textContent = "Dados importados com sucesso.";
  } catch {
    els.importStatus.textContent = "Não foi possível importar esta cópia.";
  } finally {
    els.importData.value = "";
  }
}

function updateConnectivityStatus() {
  if (pendingServiceWorker) return;
  if (!navigator.onLine) {
    els.pwaStatus.textContent = "Sem ligação. A meditação, a Jornada e o apoio local continuam disponíveis.";
    return;
  }
  els.pwaStatus.textContent = isStandalone()
    ? "Aplicação instalada. O conteúdo essencial está disponível offline."
    : "A plataforma pode funcionar parcialmente offline depois da primeira visita.";
}

function offerAppUpdate(worker) {
  pendingServiceWorker = worker;
  els.pwaUpdate.hidden = false;
  els.pwaStatus.textContent = "Existe uma nova versão pronta para atualizar.";
}

function trackInstallingServiceWorker(worker) {
  if (!worker || trackedServiceWorkers.has(worker)) return;
  trackedServiceWorkers.add(worker);
  const checkState = () => {
    if (worker.state === "installed" && navigator.serviceWorker.controller) {
      offerAppUpdate(worker);
    }
  };
  checkState();
  worker.addEventListener("statechange", checkState);
}

function watchServiceWorkerRegistration(registration) {
  if (registration.waiting && navigator.serviceWorker.controller) {
    offerAppUpdate(registration.waiting);
  }
  trackInstallingServiceWorker(registration.installing);
  registration.addEventListener("updatefound", () => {
    trackInstallingServiceWorker(registration.installing);
  });
}

function activateAppUpdate() {
  if (!pendingServiceWorker) return;
  appUpdateRequested = true;
  els.pwaUpdate.disabled = true;
  els.pwaStatus.textContent = "A atualizar a aplicação...";
  pendingServiceWorker.postMessage({ type: "SKIP_WAITING" });
}

function setupPwa() {
  if ("serviceWorker" in navigator && window.location.protocol !== "file:") {
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (!appUpdateRequested) return;
      appUpdateRequested = false;
      window.location.reload();
    });
    navigator.serviceWorker.register("/sw.js")
      .then(watchServiceWorkerRegistration)
      .catch(() => {
        els.pwaStatus.textContent = "O modo offline não ficou disponível neste navegador.";
      });
  }

  updateInstallAction();
  updateConnectivityStatus();
}

function renderCleanDays(cleanDays) {
  if (!state.progress.sobrietyDate) {
    els.cleanDays.textContent = "Ainda não definida";
    els.cleanDaysCopy.textContent = "Define a tua data para contar os dias limpos.";
    return;
  }

  els.cleanDays.textContent = `${cleanDays} ${cleanDays === 1 ? "dia limpo" : "dias limpos"}`;
  els.cleanDaysCopy.textContent = cleanDays === 0
    ? "Hoje também conta. Um passo de cada vez."
    : "Continua a caminhar com apoio, presença e humildade.";
}

function getCleanDays(todayIso) {
  if (!state.progress.sobrietyDate || !todayIso) return 0;
  return Math.max(0, differenceInCalendarDays(state.progress.sobrietyDate, todayIso));
}

function getTodayCheckin() {
  const today = state.daily?.date;
  return today ? state.progress.checkins[today] || "" : "";
}

function renderRewards(cleanDays, readingStreak) {
  document.querySelectorAll("[data-reward]").forEach((item) => {
    const target = Number(item.dataset.reward);
    const unlocked = item.dataset.rewardSource === "clean"
      ? cleanDays >= target
      : cleanDays >= target || readingStreak >= target;
    item.classList.toggle("unlocked", unlocked);
  });
}

function renderCheckinGuidance() {
  const today = state.daily?.date;
  const checkin = today ? state.progress.checkins[today] : "";
  const guidance = {
    firme: "Boa. Mantém o básico: meditação, água, descanso, reunião ou uma chamada honesta.",
    ansioso: "Faz uma pausa curta, abre a Oração da Serenidade e fala com alguém antes de ficares sozinho com a ansiedade.",
    risco: "Escolhe proteção agora: sai do local de risco, liga para alguém de confiança e procura uma reunião ou ajuda próxima.",
    consumo: "Sem culpa paralisante. Hoje é dia de pedir ajuda, falar a verdade e recomeçar com proteção.",
  };
  els.checkinGuidance.textContent = guidance[checkin] || "Escolhe um estado para receber uma sugestão prática para hoje.";

  document.querySelectorAll("[data-checkin]").forEach((button) => {
    const isActive = button.dataset.checkin === checkin;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function completeToday() {
  if (!state.daily) return;
  const completed = new Set(state.progress.completed);
  completed.add(state.daily.date);
  state.progress.completed = [...completed].sort();
  saveProgress();
  renderProgress();
  flashStatus("Meditação lida!", "Um dia de cada vez.");
}

function setSobrietyDate(value) {
  if (value && state.daily && value > state.daily.date) {
    els.sobrietyDate.value = state.progress.sobrietyDate;
    els.cleanDaysCopy.textContent = "A data de sobriedade não pode estar no futuro.";
    return;
  }
  state.progress.sobrietyDate = value;
  saveProgress();
  renderProgress();
}

function setCheckin(type, sourceButton) {
  if (!state.daily) return;
  state.progress.checkins[state.daily.date] = type;
  saveProgress();
  renderProgress();

  if (type === "ansioso") {
    openPrayer(sourceButton);
  }
  if (type === "risco" || type === "consumo") {
    showView("help", { updateHistory: true });
    window.requestAnimationFrame(() => els.sosButton.focus());
  }
}

async function shareMeditation() {
  if (!state.daily) return;
  const text = composeGroupMessage(state.daily);

  await copyPlainText(text);
  flashStatus("Meditação copiada", "Copiada para a área de transferência.");
}

async function copyPlainText(text) {
  if (navigator.clipboard?.write && window.ClipboardItem) {
    const blob = new Blob([text], { type: "text/plain" });
    await navigator.clipboard.write([new ClipboardItem({ "text/plain": blob })]);
    return;
  }

  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.setAttribute("readonly", "");
  textArea.style.position = "fixed";
  textArea.style.left = "-9999px";
  textArea.style.top = "0";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  const copied = document.execCommand("copy");
  textArea.remove();
  if (!copied) {
    throw new Error("Não foi possível copiar a meditação.");
  }
}

async function shareStoryImage() {
  if (!state.daily) return;

  flashStatus("A preparar imagem", "A gerar formato 9:16 para status ou stories.");
  const blob = await buildStoryImage(state.daily);
  const filename = `so-por-hoje-${state.daily.date}.png`;
  const file = new File([blob], filename, { type: "image/png" });

  if (navigator.canShare?.({ files: [file] }) && navigator.share) {
    await navigator.share({
      title: "Só Por Hoje",
      text: "Meditação diária Só Por Hoje",
      files: [file],
    });
    flashStatus("Imagem pronta", "Escolhe onde queres partilhar.");
    return;
  }

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  flashStatus("Imagem descarregada", "Pronta para publicar nos stories ou status.");
}

async function buildStoryImage(daily) {
  const canvas = document.createElement("canvas");
  canvas.width = 1080;
  canvas.height = 1920;
  const ctx = canvas.getContext("2d");
  const background = await loadImage("expo/hero-banner.jpg");
  const logo = await loadImage("icon-512.png");
  const intro = getIntroText(daily.body);

  ctx.fillStyle = "#164f68";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.filter = "blur(16px)";
  drawCoverImage(ctx, background, -36, -36, canvas.width + 72, canvas.height + 72);
  ctx.restore();

  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "rgba(18, 76, 99, 0.44)");
  gradient.addColorStop(0.5, "rgba(135, 106, 87, 0.34)");
  gradient.addColorStop(1, "rgba(7, 34, 54, 0.68)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.shadowColor = "rgba(0, 0, 0, 0.38)";
  ctx.shadowBlur = 18;
  ctx.shadowOffsetY = 8;
  ctx.fillStyle = "#ffffff";
  ctx.textAlign = "center";
  ctx.textBaseline = "top";

  drawTextBlock(ctx, "MEDITAÇÃO DO DIA", 540, 225, 820, 34, 1.22, "900 34px system-ui", true);
  drawTextBlock(ctx, formatStoryDateLine(daily.date, daily.weekday).toUpperCase(), 540, 305, 850, 38, 1.2, "900 38px system-ui", true);
  drawTextBlock(ctx, daily.title.toUpperCase(), 540, 425, 850, 44, 1.12, "900 44px system-ui", true);

  const introEndY = drawTextBlock(ctx, intro, 540, 535, 860, 38, 1.16, "italic 900 38px system-ui", true, 5);
  const reflectionLabelY = Math.min(introEndY + 90, 1020);
  drawTextBlock(ctx, "SÓ POR HOJE:", 540, reflectionLabelY, 820, 40, 1.14, "900 40px system-ui", true);
  drawTextBlock(ctx, daily.reflection, 540, reflectionLabelY + 95, 850, 38, 1.14, "italic 900 38px system-ui", true, 7);

  ctx.shadowBlur = 12;
  ctx.beginPath();
  ctx.arc(540, 1540, 112, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(255, 255, 255, 0.92)";
  ctx.fill();
  ctx.save();
  ctx.beginPath();
  ctx.arc(540, 1540, 92, 0, Math.PI * 2);
  ctx.clip();
  ctx.drawImage(logo, 448, 1448, 184, 184);
  ctx.restore();

  ctx.shadowBlur = 0;
  ctx.fillStyle = "#ffffff";
  drawTextBlock(ctx, "soporhoje.cv", 540, 1705, 760, 30, 1.1, "900 30px system-ui", true);

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob);
      } else {
        reject(new Error("Não foi possível gerar a imagem."));
      }
    }, "image/png");
  });
}

function getIntroText(body) {
  return body.split(/\n{2,}/)[0].replace(/\s+/g, " ").trim();
}

function formatStoryDateLine(isoDate, weekday) {
  const date = new Date(`${isoDate}T00:00:00`);
  const day = String(date.getDate()).padStart(2, "0");
  const month = date.toLocaleDateString("pt-PT", { month: "long" });
  return `${weekday}, ${day} de ${month} de ${date.getFullYear()}`;
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = src;
  });
}

function drawCoverImage(ctx, image, x, y, width, height) {
  const scale = Math.max(width / image.naturalWidth, height / image.naturalHeight);
  const drawWidth = image.naturalWidth * scale;
  const drawHeight = image.naturalHeight * scale;
  ctx.drawImage(image, x + (width - drawWidth) / 2, y + (height - drawHeight) / 2, drawWidth, drawHeight);
}

function drawTextBlock(ctx, text, x, y, maxWidth, fontSize, lineHeight, font, centered = false, maxLines = Infinity) {
  ctx.font = font;
  ctx.textAlign = centered ? "center" : "left";
  const words = text.split(/\s+/);
  const lines = [];
  let line = "";

  for (const word of words) {
    const testLine = line ? `${line} ${word}` : word;
    if (ctx.measureText(testLine).width > maxWidth && line) {
      lines.push(line);
      line = word;
    } else {
      line = testLine;
    }
  }
  if (line) lines.push(line);

  const visibleLines = lines.slice(0, maxLines);
  if (lines.length > maxLines) {
    const last = visibleLines[visibleLines.length - 1];
    visibleLines[visibleLines.length - 1] = `${last.replace(/[,.!?;:]*$/, "")}...`;
  }

  visibleLines.forEach((visibleLine, index) => {
    ctx.fillText(visibleLine, x, y + index * fontSize * lineHeight);
  });
  return y + visibleLines.length * fontSize * lineHeight;
}

function flashStatus(title, copy) {
  els.statusTitle.textContent = title;
  els.statusCopy.textContent = copy;
  els.statusCard.hidden = false;
  window.setTimeout(() => {
    els.statusTitle.textContent = "Meditação lida!";
    els.statusCopy.textContent = "Um dia de cada vez.";
    renderProgress();
  }, 2400);
}

function renderAnonymousRoom() {
  if (accountState.communityEnabled) {
    const signedIn = accountState.enabled && Boolean(accountState.session);
    els.anonymousName.textContent = "Comunidade moderada";
    els.anonymousDescription.textContent = signedIn
      ? "As partilhas entram numa fila privada e só aparecem depois de revisão humana. Não incluas nomes, contactos ou ligações."
      : "Podes ler partilhas aprovadas. Para partilhar ou denunciar, entra com uma conta validada no menu Mais.";
    els.anonymousMessage.disabled = !signedIn;
    els.anonymousSubmit.disabled = !signedIn;
    els.anonymousSubmit.textContent = "Enviar para moderação";
    renderPublishedCommunity();
    return;
  }

  els.anonymousDescription.textContent = "Nesta fase, as partilhas ficam guardadas apenas neste dispositivo. Não são enviadas nem vistas por outras pessoas, e podes eliminá-las individualmente.";
  els.anonymousMessage.disabled = false;
  els.anonymousSubmit.disabled = false;
  els.anonymousSubmit.textContent = "Guardar partilha";
  els.anonymousName.textContent = state.progress.anonymousName;
  const shares = state.progress.anonymousShares
    .map((share, index) => ({ share, index }))
    .slice(-4)
    .reverse();
  els.anonymousFeed.replaceChildren();
  if (!shares.length) {
    const empty = document.createElement("p");
    empty.className = "empty-feed";
    empty.textContent = "Ainda não há partilhas nesta sessão.";
    els.anonymousFeed.append(empty);
    return;
  }
  shares.forEach(({ share, index }) => {
    const article = document.createElement("article");
    const heading = document.createElement("div");
    heading.className = "anonymous-share-heading";
    const name = document.createElement("strong");
    name.textContent = share.name;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "anonymous-delete";
    remove.dataset.anonymousDelete = String(index);
    remove.setAttribute("aria-label", "Eliminar esta partilha local");
    remove.textContent = "Eliminar";
    const body = document.createElement("p");
    body.textContent = share.message;
    heading.append(name, remove);
    article.append(heading, body);
    els.anonymousFeed.append(article);
  });
}

function renderPublishedCommunity() {
  els.anonymousFeed.replaceChildren();
  if (!accountState.communityLoaded) {
    const loading = document.createElement("p");
    loading.className = "empty-feed";
    loading.textContent = "A carregar partilhas aprovadas...";
    els.anonymousFeed.append(loading);
    return;
  }
  if (!accountState.communityPosts.length) {
    const empty = document.createElement("p");
    empty.className = "empty-feed";
    empty.textContent = "Ainda não existem partilhas públicas aprovadas.";
    els.anonymousFeed.append(empty);
    return;
  }
  const canReport = accountState.enabled && Boolean(accountState.session);
  accountState.communityPosts.forEach((post) => {
    const article = document.createElement("article");
    const heading = document.createElement("div");
    heading.className = "anonymous-share-heading";
    const name = document.createElement("strong");
    name.textContent = post.pseudonym || "Anónimo";
    heading.append(name);
    if (canReport) {
      const report = document.createElement("button");
      report.type = "button";
      report.className = "anonymous-report";
      report.dataset.communityReport = post.id;
      report.textContent = "Denunciar";
      heading.append(report);
    }
    const body = document.createElement("p");
    body.textContent = post.body || "";
    article.append(heading, body);
    els.anonymousFeed.append(article);
  });
}

async function authenticatedCommunityRequest(path, options = {}) {
  if (!accountState.client || !accountState.session) throw new Error("Entra na conta para continuar.");
  const session = await accountState.client.ensureSession(accountState.session);
  persistAccountSession(session);
  const response = await fetch(path, {
    ...options,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${session.access_token}`,
    },
  });
  let payload = null;
  try { payload = await response.json(); } catch { /* Keep the generic message. */ }
  if (!response.ok) throw new Error(payload?.detail || "Não foi possível concluir o pedido.");
  return payload;
}

async function loadPublishedCommunity() {
  try {
    const response = await fetch("/api/v1/community/posts?limit=20", {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error("Comunidade indisponível");
    const posts = await response.json();
    accountState.communityPosts = Array.isArray(posts) ? posts : [];
    accountState.communityLoaded = true;
  } catch {
    accountState.communityPosts = [];
    accountState.communityLoaded = true;
    els.anonymousStatus.textContent = "As partilhas públicas estão temporariamente indisponíveis.";
  }
  renderAnonymousRoom();
}

async function submitAnonymousShare(message) {
  const cleanMessage = message.trim();
  if (!cleanMessage) return;
  if (!accountState.communityEnabled) {
    addAnonymousShare(cleanMessage);
    els.anonymousMessage.value = "";
    return;
  }
  els.anonymousStatus.textContent = "A enviar para revisão...";
  await authenticatedCommunityRequest("/api/v1/community/posts", {
    method: "POST",
    body: JSON.stringify({ body: cleanMessage }),
  });
  els.anonymousMessage.value = "";
  els.anonymousStatus.textContent = "Partilha recebida. Só ficará pública depois de revisão humana.";
}

async function reportCommunityPost(postId) {
  if (!window.confirm("Denunciar esta partilha para revisão da equipa?")) return;
  els.anonymousStatus.textContent = "A enviar denúncia...";
  await authenticatedCommunityRequest(`/api/v1/community/posts/${encodeURIComponent(postId)}/reports`, {
    method: "POST",
    body: JSON.stringify({ reason: "unsafe", details: null }),
  });
  els.anonymousStatus.textContent = "Denúncia recebida pela equipa.";
}

function addAnonymousShare(message) {
  const cleanMessage = message.trim();
  if (!cleanMessage) return;

  state.progress.anonymousShares.push({
    name: state.progress.anonymousName,
    message: cleanMessage,
    date: new Date().toISOString(),
  });
  state.progress.anonymousShares = state.progress.anonymousShares.slice(-20);
  saveProgress({ touch: false, sync: false });
  renderAnonymousRoom();
}

function removeAnonymousShare(index) {
  if (!Number.isInteger(index) || index < 0 || index >= state.progress.anonymousShares.length) return;
  const confirmed = window.confirm("Eliminar esta partilha guardada neste dispositivo?");
  if (!confirmed) return;
  state.progress.anonymousShares.splice(index, 1);
  saveProgress({ touch: false, sync: false });
  renderAnonymousRoom();
}

async function activateNotifications() {
  if (!("Notification" in window)) {
    flashStatus("Notificações indisponíveis", "Este navegador não suporta notificações locais.");
    return;
  }

  const permission = await Notification.requestPermission();
  state.progress.notifications = permission === "granted" ? "on" : "off";
  saveProgress({ touch: false, sync: false });

  if (permission === "granted") {
    let pushActive = false;
    if (accountState.pushEnabled && accountState.session) {
      try {
        pushActive = await registerPushNotifications();
      } catch {
        accountState.pushRegistered = false;
        localStorage.removeItem("sph-push-enabled");
      }
    }
    try {
      await showAppNotification("Só Por Hoje", "Notificações ativadas neste dispositivo.");
    } catch {
      // Permission is stored even when the browser suppresses the confirmation notification.
    }
    scheduleSessionReminder();
    flashStatus(
      "Notificação ativada",
      pushActive
        ? "O lembrete diário pode chegar mesmo com a aplicação fechada."
        : "O lembrete local funciona enquanto a aplicação estiver aberta.",
    );
    return;
  }

  flashStatus("Notificação não ativada", "Podes tentar novamente nas permissões do navegador.");
}

function urlBase64ToUint8Array(value) {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  return Uint8Array.from([...raw].map((character) => character.charCodeAt(0)));
}

async function registerPushNotifications() {
  if (!accountState.pushEnabled || !accountState.client || !accountState.session) return false;
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return false;
  const registration = await navigator.serviceWorker.ready;
  let subscription = await registration.pushManager.getSubscription();
  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(accountState.vapidPublicKey),
    });
  }
  let session = await accountState.client.savePushSubscription(accountState.session, subscription);
  session = await accountState.client.saveNotificationPreference(session, {
    enabled: true,
    localTime: state.progress.reminderTime,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Atlantic/Cape_Verde",
  });
  persistAccountSession(session);
  accountState.pushRegistered = true;
  localStorage.setItem("sph-push-enabled", "on");
  renderReminderStatus();
  return true;
}

async function removeRemotePushRegistration() {
  if (!("serviceWorker" in navigator)) return;
  const registration = await navigator.serviceWorker.getRegistration();
  const subscription = await registration?.pushManager?.getSubscription();
  let remoteError = null;
  if (subscription && accountState.client && accountState.session) {
    try {
      persistAccountSession(await accountState.client.disablePushSubscription(accountState.session, subscription.endpoint));
    } catch (error) {
      remoteError = error;
    }
  }
  if (subscription) await subscription.unsubscribe();
  accountState.pushRegistered = false;
  localStorage.removeItem("sph-push-enabled");
  if (remoteError) throw remoteError;
}

async function disableNotifications() {
  state.progress.notifications = "off";
  saveProgress({ touch: false, sync: false });
  let remoteUpdatePending = false;
  try {
    await removeRemotePushRegistration();
    if (accountState.pushEnabled && accountState.client && accountState.session) {
      persistAccountSession(await accountState.client.saveNotificationPreference(accountState.session, {
        enabled: false,
        localTime: state.progress.reminderTime,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Atlantic/Cape_Verde",
      }));
    }
  } catch {
    remoteUpdatePending = true;
  } finally {
    scheduleSessionReminder();
    flashStatus(
      "Notificações desativadas",
      remoteUpdatePending
        ? "Foram desligadas neste dispositivo; o servidor será atualizado quando voltares a iniciar sessão."
        : "O navegador pode manter a permissão, mas a plataforma deixou de enviar lembretes.",
    );
  }
}

async function updateRemoteReminderTime() {
  if (!accountState.pushRegistered || !accountState.client || !accountState.session) return;
  persistAccountSession(await accountState.client.saveNotificationPreference(accountState.session, {
    enabled: true,
    localTime: state.progress.reminderTime,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "Atlantic/Cape_Verde",
  }));
}

function openPrayer(sourceButton = els.prayer) {
  openModal(els.prayerModal, closePrayer, sourceButton, els.prayerClose);
}

function closePrayer() {
  closeModal(els.prayerModal);
}

async function loadLocalDailySupport(payload) {
  if (!localSupportCatalog) {
    const response = await fetch("/data/daily_support.json");
    if (!response.ok) throw new Error("Catálogo local indisponível");
    localSupportCatalog = await response.json();
  }
  const { selectDailySupport } = await import("./offline-support.mjs");
  const monthDay = payload.daily.month_day || payload.daily.date?.slice(5);
  const support = selectDailySupport(localSupportCatalog, monthDay, payload.user_state || "standard");
  if (!support) throw new Error("Apoio local não encontrado");
  return support;
}

async function getDailySupport() {
  if (!state.daily) {
    return tools.default;
  }

  const completed = new Set(state.progress.completed);
  const payload = {
    daily: state.daily,
    user_state: getTodayCheckin(),
    clean_days: getCleanDays(state.daily.date),
    reading_streak: getCurrentStreak(completed, state.daily.date),
    language: "pt-CV",
  };
  let authorization = "";
  let cacheOwner = "local";
  if (accountState.aiEnabled && accountState.client && accountState.session) {
    try {
      const session = await accountState.client.ensureSession(accountState.session);
      persistAccountSession(session);
      authorization = `Bearer ${session.access_token}`;
      cacheOwner = session.user.id;
    } catch {
      authorization = "";
    }
  }
  const supportMode = authorization ? "ai" : "local";
  const cacheKey = `sph-ai-support:${supportMode}:${cacheOwner}:${state.daily.date}:${payload.user_state}:${payload.clean_days}:${payload.reading_streak}`;

  try {
    const cached = JSON.parse(localStorage.getItem(cacheKey));
    if (cached?.activity && cached?.phrase && cached?.mental_challenge) {
      currentSupport = cached;
      return cached;
    }
  } catch {
    currentSupport = null;
  }

  if (!authorization) {
    const support = await loadLocalDailySupport(payload);
    currentSupport = support;
    localStorage.setItem(cacheKey, JSON.stringify(support));
    return support;
  }

  if (!navigator.onLine) return loadLocalDailySupport(payload);

  try {
    const response = await fetch("/api/v1/ai/daily-support", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authorization ? { Authorization: authorization } : {}),
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Apoio diário respondeu com ${response.status}`);
    }

    const support = await response.json();
    currentSupport = support;
    localStorage.setItem(cacheKey, JSON.stringify(support));
    return support;
  } catch {
    return loadLocalDailySupport(payload);
  }
}

function getSupportText(support, type) {
  if (type === "activity") return support.activity;
  if (type === "phrase") return support.phrase;
  if (type === "challenge") return support.mental_challenge;
  return "";
}

async function openTool(type, sourceButton) {
  const theme = detectTheme();
  const labels = {
    activity: { label: "◎ Ferramenta prática", title: "Atividade do dia" },
    phrase: { label: "✦ Inspiração curta", title: "Frase do dia" },
    challenge: { label: "⌖ Exercício de presença", title: "Desafio mental" },
  };
  const selected = labels[type];
  els.toolLabel.textContent = `${selected.label}`;
  els.toolText.textContent = "A preparar uma sugestão para este momento...";
  els.toolModalLabel.textContent = selected.label;
  els.toolModalTitle.textContent = selected.title;
  els.toolModalText.textContent = "A preparar uma sugestão para este momento...";
  openModal(els.toolModal, closeTool, sourceButton, els.toolClose);

  try {
    const support = await getDailySupport();
    const text = getSupportText(support, type);
    els.toolText.textContent = text;
    els.toolModalText.textContent = text;
  } catch {
    const fallback = tools[theme][type];
    els.toolText.textContent = fallback;
    els.toolModalText.textContent = fallback;
  }
}

function closeTool() {
  closeModal(els.toolModal);
}

function openSos() {
  openModal(els.sosModal, closeSos, els.sosButton, els.sosClose);
}

function closeSos() {
  closeModal(els.sosModal);
}

async function copySupportMessage() {
  const message = "Preciso de ajuda agora. Podes ligar-me ou ficar comigo enquanto procuro apoio?";
  await copyPlainText(message);
  els.supportMessageStatus.textContent = "Mensagem copiada. Envia-a a uma pessoa segura.";
}

function detectTheme() {
  const text = `${state.daily?.title || ""} ${state.daily?.body || ""}`.toLowerCase();
  if (text.includes("repara")) return "repair";
  if (text.includes("vigil")) return "vigilance";
  if (text.includes("serv")) return "service";
  return "default";
}

function getViewFromHash() {
  const hash = window.location.hash.replace(/^#/, "");
  return Object.keys(viewHashes).find((view) => viewHashes[view] === hash) || "meditation";
}

function showView(view, options = {}) {
  if (!viewHashes[view]) return;

  const { updateHistory = false, scroll = true } = options;
  state.view = view;
  document.querySelectorAll(".bottom-nav button").forEach((button) => {
    const isActive = button.dataset.view === view;
    button.classList.toggle("active", isActive);
    if (isActive) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  });
  document.querySelectorAll(".view-section").forEach((section) => {
    section.hidden = section.dataset.section !== view;
  });

  if (updateHistory) {
    const nextHash = `#${viewHashes[view]}`;
    if (window.location.hash !== nextHash) {
      window.history.pushState({ view }, "", nextHash);
    }
  }

  if (view === "meditation") {
    els.toolLabel.textContent = "✦ Pensamento de recuperação";
    els.toolText.textContent = "O maior ato de coragem é continuar, mesmo quando tudo parece difícil.";
  }
  renderProgress();
  if (scroll) {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
  }
}

els.retry.addEventListener("click", loadToday);
els.complete.addEventListener("click", completeToday);
els.prayer.addEventListener("click", openPrayer);
els.prayerClose.addEventListener("click", closePrayer);
els.prayerModal.addEventListener("click", (event) => {
  if (event.target === els.prayerModal) {
    closePrayer();
  }
});
els.toolClose.addEventListener("click", closeTool);
els.toolModal.addEventListener("click", (event) => {
  if (event.target === els.toolModal) {
    closeTool();
  }
});
els.browseMeditations.addEventListener("click", openArchive);
els.archiveClose.addEventListener("click", closeArchive);
els.archiveModal.addEventListener("click", (event) => {
  if (event.target === els.archiveModal) closeArchive();
});
els.archiveDate.addEventListener("change", (event) => renderArchiveMeditation(event.target.value));
els.archivePrevious.addEventListener("click", () => moveArchiveDate(-1));
els.archiveNext.addEventListener("click", () => moveArchiveDate(1));
els.archiveToday.addEventListener("click", () => renderArchiveMeditation(getCapeVerdeToday().iso));
els.historyList.addEventListener("click", (event) => {
  const historyItem = event.target.closest("[data-history-date]");
  if (historyItem) openArchiveForDate(historyItem.dataset.historyDate, historyItem);
});
els.share.addEventListener("click", () => shareMeditation().catch(() => {
  flashStatus("Partilha indisponível", "Tente copiar o texto manualmente.");
}));
els.story.addEventListener("click", () => shareStoryImage().catch(() => {
  flashStatus("Imagem indisponível", "Não foi possível gerar a imagem agora.");
}));
els.reminder.addEventListener("click", () => activateNotifications());
els.sobrietyDate.addEventListener("change", (event) => setSobrietyDate(event.target.value));
els.gratitudeForm.addEventListener("submit", (event) => {
  event.preventDefault();
  saveGratitude(els.gratitudeInput.value);
});
els.exportData.addEventListener("click", exportJourneyData);
els.reminderTime.addEventListener("change", (event) => {
  state.progress.reminderTime = event.target.value || "07:00";
  saveProgress();
  scheduleSessionReminder();
  updateRemoteReminderTime().catch(() => {
    els.reminderStatus.textContent = "A nova hora ficou guardada neste dispositivo e será sincronizada quando houver ligação.";
  });
});
els.showCleanDays.addEventListener("change", (event) => {
  state.progress.showCleanDays = event.target.checked;
  saveProgress();
  renderJourneySettings();
});
els.supportPlanForm.addEventListener("submit", (event) => {
  event.preventDefault();
  saveSupportPlan();
});
els.installApp.addEventListener("click", () => installApp());
els.moreButton.addEventListener("click", openMore);
els.moreClose.addEventListener("click", closeMore);
els.moreModal.addEventListener("click", (event) => {
  if (event.target === els.moreModal) closeMore();
});
els.exportDataSecondary.addEventListener("click", exportJourneyData);
els.importData.addEventListener("change", (event) => importJourneyData(event.target.files[0]));
els.installAppSecondary.addEventListener("click", () => installApp());
els.pwaUpdate.addEventListener("click", activateAppUpdate);
els.notificationsSecondary.addEventListener("click", () => activateNotifications());
els.disableNotifications.addEventListener("click", () => disableNotifications());
els.accountEmailForm.addEventListener("submit", (event) => {
  event.preventDefault();
  requestAccountCode(els.accountEmail.value).catch((error) => {
    els.accountStatus.textContent = error.message || "Não foi possível enviar o código agora.";
  });
});
els.accountCodeForm.addEventListener("submit", (event) => {
  event.preventDefault();
  verifyAccountCode(els.accountCode.value).catch((error) => {
    els.accountStatus.textContent = error.message || "O código não pôde ser confirmado.";
  });
});
els.syncLocalData.addEventListener("click", () => {
  uploadLocalJourney().catch((error) => {
    els.accountStatus.textContent = error.message || "Não foi possível guardar os dados na conta.";
  });
});
els.syncAccountData.addEventListener("click", () => {
  useAccountJourney().catch((error) => {
    els.accountStatus.textContent = error.message || "Não foi possível obter os dados da conta.";
  });
});
els.deleteAccountData.addEventListener("click", () => {
  deleteAccountJourney().catch((error) => {
    els.accountStatus.textContent = error.message || "Não foi possível apagar a cópia da conta.";
  });
});
els.deleteAccount.addEventListener("click", () => deleteCurrentAccount());
els.accountSignout.addEventListener("click", () => signOutAccount());
els.deleteLocalData.addEventListener("click", () => deleteDeviceData());
els.sosButton.addEventListener("click", openSos);
els.sosClose.addEventListener("click", closeSos);
els.sosModal.addEventListener("click", (event) => {
  if (event.target === els.sosModal) closeSos();
});
els.copySupportMessage.addEventListener("click", () => copySupportMessage().catch(() => {
  els.supportMessageStatus.textContent = "Não foi possível copiar. Escreve a uma pessoa segura e pede companhia.";
}));
els.anonymousForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitAnonymousShare(els.anonymousMessage.value).catch((error) => {
    els.anonymousStatus.textContent = error.message || "Não foi possível enviar a partilha.";
  });
});
els.anonymousFeed.addEventListener("click", (event) => {
  const report = event.target.closest("[data-community-report]");
  if (report) {
    reportCommunityPost(report.dataset.communityReport).catch((error) => {
      els.anonymousStatus.textContent = error.message || "Não foi possível enviar a denúncia.";
    });
    return;
  }
  const button = event.target.closest("[data-anonymous-delete]");
  if (!button) return;
  removeAnonymousShare(Number(button.dataset.anonymousDelete));
});

document.querySelectorAll(".tool-tile").forEach((button) => {
  button.addEventListener("click", () => openTool(button.dataset.tool, button));
});

document.querySelectorAll("[data-checkin]").forEach((button) => {
  button.addEventListener("click", () => setCheckin(button.dataset.checkin, button));
});

document.querySelectorAll(".bottom-nav button").forEach((button) => {
  button.addEventListener("click", () => showView(button.dataset.view, { updateHistory: true }));
});

window.addEventListener("popstate", () => showView(getViewFromHash()));
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPrompt = event;
  updateInstallAction();
  els.pwaStatus.textContent = "Pronta para instalar neste dispositivo.";
  els.pwaInstallStatus.textContent = "A aplicação está pronta para instalar.";
});
window.addEventListener("appinstalled", () => {
  installPrompt = null;
  updateInstallAction();
  els.pwaStatus.textContent = "Aplicação instalada com sucesso.";
  els.pwaInstallStatus.textContent = "Aplicação instalada com sucesso.";
});
window.addEventListener("online", updateConnectivityStatus);
window.addEventListener("offline", updateConnectivityStatus);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") {
    refreshForNewDay();
    scheduleSessionReminder();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && activeModalClose) {
    event.preventDefault();
    activeModalClose();
    return;
  }
  trapModalFocus(event);
});

showView(getViewFromHash(), { scroll: false });
renderAccount();
setupAccount();
setupPwa();
scheduleSessionReminder();
scheduleDayRefreshCheck();
loadToday();
