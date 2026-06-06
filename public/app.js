const state = {
  daily: null,
  progress: loadProgress(),
  view: "meditation",
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
};

let lastToolButton = null;

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

function saveProgress() {
  localStorage.setItem("sph-progress", JSON.stringify(state.progress));
}

function normalizeProgress(progress) {
  return {
    completed: Array.isArray(progress.completed) ? progress.completed : [],
    sobrietyDate: progress.sobrietyDate || "",
    checkins: progress.checkins && typeof progress.checkins === "object" ? progress.checkins : {},
    anonymousName: progress.anonymousName || makeAnonymousName(),
    anonymousShares: Array.isArray(progress.anonymousShares) ? progress.anonymousShares : [],
    notifications: progress.notifications || "off",
  };
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
  return [
    "BOM DIA GUERREIROS",
    "MEDITAÇÃO DO DIA",
    formatGroupDateLine(daily.date, daily.weekday),
    daily.title,
    daily.body,
    "SÓ POR HOJE:",
    daily.reflection,
    "Fonte oficial: Narcóticos Anónimos Portugal",
    "© NA World Services, Inc. Reprinted by permission.",
    "https://na-pt.erlog.pt/sph.php",
  ].join("\n\n");
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

function renderRewards(cleanDays, readingStreak) {
  document.querySelectorAll("[data-reward]").forEach((item) => {
    const target = Number(item.dataset.reward);
    item.classList.toggle("unlocked", cleanDays >= target || readingStreak >= target);
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

  if (navigator.share) {
    await navigator.share({ title: "Só Por Hoje", text });
  } else {
    await navigator.clipboard.writeText(text);
    flashStatus("Mensagem copiada", "O texto completo ficou pronto para colar no Messenger.");
  }
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
    new Notification("Só Por Hoje", {
      body: "Notificações ativadas. A versão app poderá lembrar a meditação diária automaticamente.",
      icon: "icon-512.png",
    });
    flashStatus("Notificação ativada", "No navegador, o lembrete real precisa de versão PWA/app.");
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

function openTool(type, sourceButton) {
  const theme = detectTheme();
  const labels = {
    activity: { label: "◎ Ferramenta prática", title: "Atividade do dia" },
    phrase: { label: "✦ Inspiração curta", title: "Frase do dia" },
    challenge: { label: "⌖ Exercício de presença", title: "Desafio mental" },
  };
  const selected = labels[type];
  lastToolButton = sourceButton;
  els.toolLabel.textContent = `${selected.label}`;
  els.toolText.textContent = tools[theme][type];
  els.toolModalLabel.textContent = selected.label;
  els.toolModalTitle.textContent = selected.title;
  els.toolModalText.textContent = tools[theme][type];
  els.toolModal.hidden = false;
  document.body.classList.add("modal-open");
  els.toolClose.focus();
}

function closeTool() {
  els.toolModal.hidden = true;
  document.body.classList.remove("modal-open");
  if (lastToolButton) {
    lastToolButton.focus();
  }
}

function detectTheme() {
  const text = `${state.daily?.title || ""} ${state.daily?.body || ""}`.toLowerCase();
  if (text.includes("repara")) return "repair";
  if (text.includes("vigil")) return "vigilance";
  if (text.includes("serv")) return "service";
  return "default";
}

function showView(view) {
  state.view = view;
  document.querySelectorAll(".bottom-nav button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelectorAll(".view-section").forEach((section) => {
    section.hidden = section.dataset.section !== view;
  });

  if (view === "meditation") {
    els.toolLabel.textContent = "✦ Pensamento de recuperação";
    els.toolText.textContent = "O maior ato de coragem é continuar, mesmo quando tudo parece difícil.";
  }
  renderProgress();
  window.scrollTo({ top: 0, behavior: "smooth" });
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
els.reminder.addEventListener("click", () => activateNotifications());
els.sobrietyDate.addEventListener("change", (event) => setSobrietyDate(event.target.value));
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
  button.addEventListener("click", () => showView(button.dataset.view));
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !els.prayerModal.hidden) {
    closePrayer();
  }
  if (event.key === "Escape" && !els.toolModal.hidden) {
    closeTool();
  }
});

loadToday();
