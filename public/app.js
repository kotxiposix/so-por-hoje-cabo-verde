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
  progressPanel: document.querySelector("#progress-panel"),
  sobrietyDate: document.querySelector("#sobriety-date"),
  cleanDays: document.querySelector("#clean-days"),
  cleanDaysCopy: document.querySelector("#clean-days-copy"),
  cleanDaysMetric: document.querySelector("#clean-days-metric"),
  monthCount: document.querySelector("#month-count"),
  bestStreak: document.querySelector("#best-streak"),
  checkinGuidance: document.querySelector("#checkin-guidance"),
  anonymousName: document.querySelector("#anonymous-name"),
  anonymousForm: document.querySelector("#anonymous-form"),
  anonymousMessage: document.querySelector("#anonymous-message"),
  anonymousFeed: document.querySelector("#anonymous-feed"),
  gratitudeForm: document.querySelector("#gratitude-form"),
  gratitudeInput: document.querySelector("#gratitude-input"),
  gratitudeStatus: document.querySelector("#gratitude-status"),
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
  installApp: document.querySelector("#install-app"),
  pwaStatus: document.querySelector("#pwa-status"),
  moreButton: document.querySelector("#more-button"),
  moreModal: document.querySelector("#more-modal"),
  moreClose: document.querySelector("#more-close"),
  exportDataSecondary: document.querySelector("#export-data-secondary"),
  importData: document.querySelector("#import-data"),
  importStatus: document.querySelector("#import-status"),
  installAppSecondary: document.querySelector("#install-app-secondary"),
  notificationsSecondary: document.querySelector("#notifications-secondary"),
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
  accountSignout: document.querySelector("#account-signout"),
  sosButton: document.querySelector("#sos-button"),
  sosModal: document.querySelector("#sos-modal"),
  sosClose: document.querySelector("#sos-close"),
  copySupportMessage: document.querySelector("#copy-support-message"),
  supportMessageStatus: document.querySelector("#support-message-status"),
};

let lastToolButton = null;
let currentSupport = null;
let installPrompt = null;
let reminderTimer = null;
let journeySyncTimer = null;

const accountState = {
  client: null,
  enabled: false,
  pendingEmail: "",
  session: loadAccountSession(),
  syncEnabled: localStorage.getItem("sph-account-sync") === "on",
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
  return {
    completed: normalizeDateList(progress.completed),
    sobrietyDate: isIsoDate(progress.sobrietyDate) ? progress.sobrietyDate : "",
    checkins: normalizeCheckins(progress.checkins),
    anonymousName: cleanStoredText(progress.anonymousName, 32) || makeAnonymousName(),
    anonymousShares: normalizeAnonymousShares(progress.anonymousShares),
    notifications: progress.notifications === "on" ? "on" : "off",
    gratitudes: normalizeTextByDate(progress.gratitudes, 240),
    reminderTime: /^([01]\d|2[0-3]):[0-5]\d$/.test(progress.reminderTime) ? progress.reminderTime : "07:00",
    showCleanDays: progress.showCleanDays !== false,
    supportPlan: normalizeSupportPlan(progress.supportPlan),
    lastReminderAt: isIsoDate(progress.lastReminderAt) ? progress.lastReminderAt : "",
    updatedAt: typeof progress.updatedAt === "string" ? progress.updatedAt.slice(0, 32) : "",
  };
}

function cleanStoredText(value, maxLength) {
  return typeof value === "string" ? value.trim().slice(0, maxLength) : "";
}

function isIsoDate(value) {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function normalizeDateList(value) {
  if (!Array.isArray(value)) return [];
  return [...new Set(value.filter(isIsoDate))].sort().slice(-3660);
}

function normalizeCheckins(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  const allowed = new Set(["firme", "ansioso", "risco", "consumo"]);
  return Object.fromEntries(Object.entries(value)
    .filter(([day, stateValue]) => isIsoDate(day) && allowed.has(stateValue))
    .slice(-3660));
}

function normalizeTextByDate(value, maxLength) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return Object.fromEntries(Object.entries(value)
    .filter(([day, textValue]) => isIsoDate(day) && typeof textValue === "string")
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

async function setupAccount() {
  try {
    const response = await fetch("/api/v1/config", {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error("Configuração indisponível");
    const config = await response.json();
    if (!config.features?.account || !config.supabase) {
      renderAccount();
      return;
    }

    const { SupabaseAccountClient } = await import("./account-client.mjs");
    accountState.client = new SupabaseAccountClient(config.supabase);
    accountState.enabled = true;
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

function renderAccount() {
  const signedIn = accountState.enabled && Boolean(accountState.session);
  els.accountAuth.hidden = !accountState.enabled || signedIn;
  els.accountSession.hidden = !signedIn;

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

function getSyncableProgress() {
  const {
    anonymousName,
    anonymousShares,
    notifications,
    lastReminderAt,
    ...syncable
  } = state.progress;
  return syncable;
}

function enableJourneySync() {
  accountState.syncEnabled = true;
  localStorage.setItem("sph-account-sync", "on");
  renderAccount();
}

async function uploadLocalJourney({ silent = false } = {}) {
  if (!accountState.client || !accountState.session) return;
  if (!silent) els.accountStatus.textContent = "A guardar a Jornada na conta...";
  const session = await accountState.client.upsertJourney(accountState.session, getSyncableProgress());
  persistAccountSession(session);
  enableJourneySync();
  if (!silent) els.accountStatus.textContent = "Dados deste dispositivo guardados na conta.";
}

async function useAccountJourney() {
  if (!accountState.client || !accountState.session) return;
  els.accountStatus.textContent = "A procurar dados da conta...";
  const result = await accountState.client.getJourney(accountState.session);
  persistAccountSession(result.session);
  if (!result.record?.payload) {
    els.accountStatus.textContent = "Ainda não existem dados guardados nesta conta.";
    return;
  }
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
  state.progress = normalizeProgress({ ...result.record.payload, ...deviceOnly });
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
      await accountState.client.signOut(accountState.session);
    } catch {
      // The local session is still cleared when the remote logout is unavailable.
    }
  }
  persistAccountSession(null);
  accountState.syncEnabled = false;
  localStorage.removeItem("sph-account-sync");
  renderAccount();
  els.accountStatus.textContent = "Sessão terminada. Os dados locais foram mantidos.";
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
  const response = await fetch("data/meditations.json");
  if (!response.ok) {
    throw new Error("A base local de meditações não respondeu.");
  }
  const records = await response.json();
  const today = getCapeVerdeToday();
  const monthDay = `${String(today.month).padStart(2, "0")}-${String(today.day).padStart(2, "0")}`;
  const meditation = records.find((record) => record.month_day === monthDay);
  if (!meditation) {
    throw new Error(`Meditação não encontrada para ${monthDay}.`);
  }
  return {
    date: today.iso,
    weekday: today.weekday,
    month_day: meditation.month_day,
    title: meditation.title,
    body: meditation.body,
    reflection: meditation.reflection,
  };
}

function getCapeVerdeToday() {
  const parts = new Intl.DateTimeFormat("pt-PT", {
    timeZone: "Atlantic/Cape_Verde",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    weekday: "long",
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  const weekday = values.weekday.charAt(0).toUpperCase() + values.weekday.slice(1);
  return {
    year: Number(values.year),
    month: Number(values.month),
    day: Number(values.day),
    iso: `${values.year}-${values.month}-${values.day}`,
    weekday,
  };
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
  els.supportPlanStatus.textContent = "Plano guardado apenas neste dispositivo.";
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
        return `<article class="history-item">
          <time datetime="${day}">${formatShortDate(day)}</time>
          <strong>${escapeHtml(parts.join(" · "))}</strong>
          <small>${gratitude ? escapeHtml(gratitude) : ""}</small>
        </article>`;
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
  if (!("Notification" in window)) {
    els.reminderStatus.textContent = "Este navegador não disponibiliza notificações.";
    return;
  }
  if (Notification.permission !== "granted" || state.progress.notifications !== "on") {
    els.reminderStatus.textContent = "Notificações ainda não autorizadas neste dispositivo.";
    return;
  }
  els.reminderStatus.textContent = `Lembrete local preparado para ${state.progress.reminderTime}, enquanto a aplicação estiver aberta.`;
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
        saveProgress();
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

async function installApp() {
  if (!installPrompt) {
    const message = isStandalone()
      ? "A aplicação já está instalada."
      : "Usa a opção Instalar ou Adicionar ao ecrã principal no menu do navegador.";
    els.pwaStatus.textContent = message;
    els.importStatus.textContent = message;
    return;
  }
  installPrompt.prompt();
  const result = await installPrompt.userChoice;
  els.pwaStatus.textContent = result.outcome === "accepted"
    ? "Instalação iniciada."
    : "A instalação foi cancelada.";
  installPrompt = null;
  els.installApp.hidden = true;
}

function openMore() {
  els.moreModal.hidden = false;
  document.body.classList.add("modal-open");
  els.moreClose.focus();
}

function closeMore() {
  els.moreModal.hidden = true;
  document.body.classList.remove("modal-open");
  els.moreButton.focus();
}

async function importJourneyData(file) {
  if (!file) return;
  try {
    const payload = JSON.parse(await file.text());
    if (!payload.progress || typeof payload.progress !== "object") {
      throw new Error("Formato inválido");
    }
    const confirmed = window.confirm("Substituir os dados locais da Jornada pelos dados desta cópia?");
    if (!confirmed) {
      els.importStatus.textContent = "Importação cancelada.";
      return;
    }
    state.progress = normalizeProgress(payload.progress);
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

function setupPwa() {
  if ("serviceWorker" in navigator && window.location.protocol !== "file:") {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      els.pwaStatus.textContent = "O modo offline não ficou disponível neste navegador.";
    });
  }

  if (isStandalone()) {
    els.installApp.hidden = true;
    els.pwaStatus.textContent = "Aplicação instalada. O conteúdo essencial funciona parcialmente offline.";
  }
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
  const start = new Date(`${state.progress.sobrietyDate}T00:00:00`);
  const today = new Date(`${todayIso}T00:00:00`);
  return Math.max(0, diffDays(start, today));
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
    button.classList.toggle("active", button.dataset.checkin === checkin);
  });
}

function getCurrentStreak(completed, todayIso) {
  if (!todayIso) return 0;
  let count = 0;
  let cursor = new Date(`${todayIso}T00:00:00`);

  while (completed.has(toIsoDate(cursor))) {
    count += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return count;
}

function getBestStreak(completed) {
  const days = [...completed].sort();
  let best = 0;
  let current = 0;
  let previous = null;

  for (const day of days) {
    const date = new Date(`${day}T00:00:00`);
    if (!previous || diffDays(previous, date) === 1) {
      current += 1;
    } else {
      current = 1;
    }
    best = Math.max(best, current);
    previous = date;
  }
  return best;
}

function diffDays(a, b) {
  return Math.round((b - a) / 86400000);
}

function toIsoDate(date) {
  return date.toISOString().slice(0, 10);
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

function setCheckin(type) {
  if (!state.daily) return;
  state.progress.checkins[state.daily.date] = type;
  saveProgress();
  renderProgress();

  if (type === "ansioso") {
    openPrayer();
  }
  if (type === "risco" || type === "consumo") {
    showView("help");
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
  els.anonymousName.textContent = state.progress.anonymousName;
  const shares = state.progress.anonymousShares.slice(-4).reverse();
  els.anonymousFeed.innerHTML = shares.length
    ? shares.map((share) => `
        <article>
          <strong>${escapeHtml(share.name)}</strong>
          <p>${escapeHtml(share.message)}</p>
        </article>
      `).join("")
    : "<p class=\"empty-feed\">Ainda não há partilhas nesta sessão.</p>";
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
  saveProgress();
  renderAnonymousRoom();
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;",
  }[char]));
}

async function activateNotifications() {
  if (!("Notification" in window)) {
    flashStatus("Notificações indisponíveis", "Este navegador não suporta notificações locais.");
    return;
  }

  const permission = await Notification.requestPermission();
  state.progress.notifications = permission === "granted" ? "on" : "off";
  saveProgress();

  if (permission === "granted") {
    try {
      await showAppNotification("Só Por Hoje", "Notificações ativadas neste dispositivo.");
    } catch {
      // Permission is stored even when the browser suppresses the confirmation notification.
    }
    scheduleSessionReminder();
    flashStatus("Notificação ativada", "O lembrete local funciona enquanto a aplicação estiver aberta.");
    return;
  }

  flashStatus("Notificação não ativada", "Podes tentar novamente nas permissões do navegador.");
}

function openPrayer() {
  els.prayerModal.hidden = false;
  document.body.classList.add("modal-open");
  els.prayerClose.focus();
}

function closePrayer() {
  els.prayerModal.hidden = true;
  document.body.classList.remove("modal-open");
  els.prayer.focus();
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
  const cacheKey = `sph-ai-support:${state.daily.date}:${payload.user_state}:${payload.clean_days}:${payload.reading_streak}`;

  try {
    const cached = JSON.parse(localStorage.getItem(cacheKey));
    if (cached?.activity && cached?.phrase && cached?.mental_challenge) {
      currentSupport = cached;
      return cached;
    }
  } catch {
    currentSupport = null;
  }

  const response = await fetch("/api/v1/ai/daily-support", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Apoio diário respondeu com ${response.status}`);
  }

  const support = await response.json();
  currentSupport = support;
  localStorage.setItem(cacheKey, JSON.stringify(support));
  return support;
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
  lastToolButton = sourceButton;
  els.toolLabel.textContent = `${selected.label}`;
  els.toolText.textContent = "A preparar uma sugestão para este momento...";
  els.toolModalLabel.textContent = selected.label;
  els.toolModalTitle.textContent = selected.title;
  els.toolModalText.textContent = "A preparar uma sugestão para este momento...";
  els.toolModal.hidden = false;
  document.body.classList.add("modal-open");
  els.toolClose.focus();

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
  els.toolModal.hidden = true;
  document.body.classList.remove("modal-open");
  if (lastToolButton) {
    lastToolButton.focus();
  }
}

function openSos() {
  els.sosModal.hidden = false;
  document.body.classList.add("modal-open");
  els.sosClose.focus();
}

function closeSos() {
  els.sosModal.hidden = true;
  document.body.classList.remove("modal-open");
  els.sosButton.focus();
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
    window.scrollTo({ top: 0, behavior: "smooth" });
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
els.notificationsSecondary.addEventListener("click", () => activateNotifications());
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
els.accountSignout.addEventListener("click", () => signOutAccount());
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
  addAnonymousShare(els.anonymousMessage.value);
  els.anonymousMessage.value = "";
});

document.querySelectorAll(".tool-tile").forEach((button) => {
  button.addEventListener("click", () => openTool(button.dataset.tool, button));
});

document.querySelectorAll("[data-checkin]").forEach((button) => {
  button.addEventListener("click", () => setCheckin(button.dataset.checkin));
});

document.querySelectorAll(".bottom-nav button").forEach((button) => {
  button.addEventListener("click", () => showView(button.dataset.view, { updateHistory: true }));
});

window.addEventListener("popstate", () => showView(getViewFromHash()));
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPrompt = event;
  els.installApp.hidden = false;
  els.pwaStatus.textContent = "Pronta para instalar neste dispositivo.";
});
window.addEventListener("appinstalled", () => {
  installPrompt = null;
  els.installApp.hidden = true;
  els.pwaStatus.textContent = "Aplicação instalada com sucesso.";
});
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") scheduleSessionReminder();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !els.prayerModal.hidden) {
    closePrayer();
  }
  if (event.key === "Escape" && !els.toolModal.hidden) {
    closeTool();
  }
  if (event.key === "Escape" && !els.moreModal.hidden) {
    closeMore();
  }
  if (event.key === "Escape" && !els.sosModal.hidden) {
    closeSos();
  }
});

showView(getViewFromHash(), { scroll: false });
renderAccount();
setupAccount();
setupPwa();
scheduleSessionReminder();
loadToday();
