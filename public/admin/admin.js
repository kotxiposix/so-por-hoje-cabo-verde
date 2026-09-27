import { SupabaseAccountClient } from "../account-client.mjs?staff=3";

const SESSION_KEY = "sph-staff-session";
const state = { client: null, session: loadSession(), roles: new Set(), resources: [], content: [] };
const els = Object.fromEntries([
  "auth-panel", "auth-summary", "auth-status", "email-form", "staff-email", "code-form", "staff-code",
  "workspace", "workspace-status", "signout", "role-list", "community-tab", "directory-tab", "content-tab", "operations-tab",
  "community-view", "directory-view", "content-view", "operations-view", "refresh-community", "community-list", "new-resource", "resource-list",
  "resource-form", "resource-id", "resource-name", "resource-category", "resource-island", "resource-municipality",
  "resource-description", "resource-phone", "resource-email", "resource-website", "resource-source",
  "resource-schedule", "resource-emergency", "review-days", "verify-resource", "retire-resource",
  "refresh-operations", "operations-summary", "operations-list", "audit-list",
  "new-content", "content-list", "content-form", "content-id", "content-name", "content-kind", "content-summary",
  "content-url", "content-image", "content-date", "content-order", "publish-content", "retire-content",
].map((id) => [id.replaceAll("-", "_"), document.getElementById(id)]));

let pendingEmail = "";
const adminTabs = [els.community_tab, els.directory_tab, els.content_tab, els.operations_tab];

function loadSession() {
  try {
    const session = JSON.parse(sessionStorage.getItem(SESSION_KEY));
    return session?.access_token && session?.refresh_token && session?.user?.id ? session : null;
  } catch { return null; }
}

function persistSession(session) {
  state.session = session;
  if (session) sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  else sessionStorage.removeItem(SESSION_KEY);
}

function setStatus(message, error = false) {
  const target = els.workspace.hidden ? els.auth_status : els.workspace_status;
  target.textContent = message;
  target.classList.toggle("error", error);
}

async function activeSession() {
  state.session = await state.client.ensureSession(state.session);
  persistSession(state.session);
  return state.session;
}

async function platformRequest(path, options = {}) {
  const session = await activeSession();
  const response = await fetch(path, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${session.access_token}`,
      ...options.headers,
    },
    cache: "no-store",
  });
  let payload = null;
  try { payload = await response.json(); } catch { /* Preserve the generic message. */ }
  if (!response.ok) throw new Error(payload?.detail || "Pedido administrativo não concluído.");
  return payload;
}

async function authenticate() {
  const profile = await platformRequest("/api/v1/admin/me");
  state.roles = new Set(profile.roles || []);
  els.auth_panel.hidden = true;
  els.workspace.hidden = false;
  els.signout.hidden = false;
  els.role_list.replaceChildren(...[...state.roles].map((role) => {
    const badge = document.createElement("span");
    badge.textContent = role;
    return badge;
  }));
  const canModerate = state.roles.has("admin") || state.roles.has("moderator");
  const canEditHelp = state.roles.has("admin") || state.roles.has("help_editor");
  const canEditContent = state.roles.has("admin") || state.roles.has("content_editor");
  const canOperate = state.roles.has("admin");
  els.community_tab.hidden = !canModerate;
  els.directory_tab.hidden = !canEditHelp;
  els.content_tab.hidden = !canEditContent;
  els.operations_tab.hidden = !canOperate;
  const initialView = canOperate ? "operations" : canEditContent ? "content" : canEditHelp ? "directory" : "community";
  try {
    await showView(initialView);
  } catch (error) {
    setStatus(error.message || "Não foi possível carregar esta área.", true);
  }
}

async function showView(view) {
  const views = {
    community: [els.community_tab, els.community_view, loadCommunity],
    directory: [els.directory_tab, els.directory_view, loadResources],
    content: [els.content_tab, els.content_view, loadContent],
    operations: [els.operations_tab, els.operations_view, loadOperations],
  };
  if (!views[view] || views[view][0].hidden) return;
  Object.entries(views).forEach(([name, [tab, section]]) => {
    const active = name === view;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
    section.hidden = !active;
  });
  await views[view][2]();
}

function moveAdminTab(current, key) {
  const available = adminTabs.filter((tab) => !tab.hidden);
  const index = available.indexOf(current);
  if (index < 0) return;
  let nextIndex = index;
  if (key === "ArrowLeft") nextIndex = (index - 1 + available.length) % available.length;
  if (key === "ArrowRight") nextIndex = (index + 1) % available.length;
  if (key === "Home") nextIndex = 0;
  if (key === "End") nextIndex = available.length - 1;
  const next = available[nextIndex];
  next.focus();
  showView(next.dataset.adminView).catch((error) => setStatus(error.message, true));
}

function emptyState(message) {
  const node = document.createElement("p");
  node.className = "empty-state";
  node.textContent = message;
  return node;
}

async function loadCommunity() {
  setStatus("A atualizar a fila...");
  const posts = await platformRequest("/api/v1/admin/community/pending?limit=100");
  els.community_list.replaceChildren();
  if (!posts.length) els.community_list.append(emptyState("Não existem partilhas pendentes."));
  posts.forEach((post) => els.community_list.append(renderPost(post)));
  setStatus(`${posts.length} partilha(s) pendente(s).`);
}

function renderPost(post) {
  const article = document.createElement("article");
  article.className = "moderation-record";
  const heading = document.createElement("div");
  heading.className = "record-heading";
  const name = document.createElement("strong");
  name.textContent = post.pseudonym || "Pseudónimo indisponível";
  const time = document.createElement("time");
  time.dateTime = post.created_at || "";
  time.textContent = post.created_at ? new Date(post.created_at).toLocaleString("pt-CV") : "Data indisponível";
  heading.append(name, time);
  const body = document.createElement("p");
  body.textContent = post.body || "";
  article.append(heading, body);
  const flags = Array.isArray(post.review_flags) ? post.review_flags : [];
  if (flags.length) {
    const warning = document.createElement("p");
    warning.className = "flag";
    warning.textContent = `Revisão obrigatória: ${flags.join(", ")}`;
    article.append(warning);
  }
  const actions = document.createElement("div");
  actions.className = "record-actions";
  const note = document.createElement("input");
  note.placeholder = "Nota interna opcional";
  note.maxLength = 500;
  actions.append(note);
  [["Publicar", "published", "success-button"], ["Rejeitar", "rejected", "danger-button"], ["Ocultar", "hidden", "quiet-button"]]
    .forEach(([label, decision, className]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = className;
      button.textContent = label;
      if (decision === "published" && flags.length) button.disabled = true;
      button.addEventListener("click", () => moderatePost(post.id, decision, note.value));
      actions.append(button);
    });
  article.append(actions);
  return article;
}

async function moderatePost(id, status, note) {
  const labels = { published: "publicar", rejected: "rejeitar", hidden: "ocultar" };
  if (!window.confirm(`Confirmar: ${labels[status]} esta partilha?`)) return;
  setStatus("A guardar a decisão...");
  try {
    await platformRequest(`/api/v1/admin/community/posts/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify({ status, note: note.trim() || null }),
    });
    await loadCommunity();
  } catch (error) { setStatus(error.message, true); }
}

async function loadResources() {
  setStatus("A atualizar os recursos...");
  state.resources = await platformRequest("/api/v1/admin/help/resources?limit=500");
  renderResourceList();
  setStatus(`${state.resources.length} recurso(s) no diretório.`);
}

function renderResourceList() {
  const selectedId = els.resource_id.value;
  els.resource_list.replaceChildren();
  if (!state.resources.length) els.resource_list.append(emptyState("Ainda não existem recursos."));
  state.resources.forEach((resource) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "resource-item";
    button.setAttribute("aria-current", String(resource.id === selectedId));
    const name = document.createElement("strong");
    name.textContent = resource.name || "Sem nome";
    const status = document.createElement("small");
    status.textContent = `${resource.verification_status || "draft"} · ${resource.category || "other"}`;
    button.append(name, status);
    button.addEventListener("click", () => fillResource(resource));
    els.resource_list.append(button);
  });
}

function fillResource(resource = null) {
  const value = resource || {};
  els.resource_id.value = value.id || "";
  els.resource_name.value = value.name || "";
  els.resource_category.value = value.category || "information";
  els.resource_island.value = value.island || "";
  els.resource_municipality.value = value.municipality || "";
  els.resource_description.value = value.description || "";
  els.resource_phone.value = value.phone || "";
  els.resource_email.value = value.email || "";
  els.resource_website.value = value.website || "";
  els.resource_source.value = value.source_url || "";
  els.resource_schedule.value = Array.isArray(value.schedule) ? value.schedule.join("\n") : "";
  els.resource_emergency.checked = Boolean(value.is_emergency);
  els.verify_resource.disabled = !value.id;
  els.retire_resource.disabled = !value.id;
  renderResourceList();
  els.resource_name.focus();
}

function resourcePayload() {
  return {
    name: els.resource_name.value.trim(),
    category: els.resource_category.value,
    island: els.resource_island.value.trim() || null,
    municipality: els.resource_municipality.value.trim() || null,
    description: els.resource_description.value.trim() || null,
    phone: els.resource_phone.value.trim() || null,
    email: els.resource_email.value.trim() || null,
    website: els.resource_website.value.trim() || null,
    source_url: els.resource_source.value.trim() || null,
    schedule: els.resource_schedule.value.split("\n").map((line) => line.trim()).filter(Boolean),
    is_emergency: els.resource_emergency.checked,
  };
}

async function saveResource(event) {
  event.preventDefault();
  const id = els.resource_id.value;
  const method = id ? "PUT" : "POST";
  const path = id ? `/api/v1/admin/help/resources/${encodeURIComponent(id)}` : "/api/v1/admin/help/resources";
  setStatus("A guardar o rascunho...");
  try {
    const saved = await platformRequest(path, { method, body: JSON.stringify(resourcePayload()) });
    await loadResources();
    fillResource(saved);
    setStatus("Rascunho guardado. Uma alteração exige nova verificação.");
  } catch (error) { setStatus(error.message, true); }
}

async function verifyResource() {
  const id = els.resource_id.value;
  if (!id || !window.confirm("Confirmar os dados e tornar este recurso público até à próxima revisão?")) return;
  try {
    const reviewDays = Number(els.review_days.value);
    const saved = await platformRequest(`/api/v1/admin/help/resources/${encodeURIComponent(id)}/verify`, {
      method: "POST", body: JSON.stringify({ review_days: reviewDays }),
    });
    await loadResources();
    fillResource(saved);
    setStatus("Recurso verificado.");
  } catch (error) { setStatus(error.message, true); }
}

async function retireResource() {
  const id = els.resource_id.value;
  if (!id || !window.confirm("Retirar este recurso da lista pública?")) return;
  try {
    await platformRequest(`/api/v1/admin/help/resources/${encodeURIComponent(id)}/retire`, { method: "POST" });
    await loadResources();
    fillResource();
    setStatus("Recurso retirado da lista pública.");
  } catch (error) { setStatus(error.message, true); }
}

async function loadContent() {
  setStatus("A atualizar o catálogo editorial...");
  state.content = await platformRequest("/api/v1/admin/content?limit=500");
  renderContentList();
  setStatus(`${state.content.length} conteúdo(s) no catálogo.`);
}

function renderContentList() {
  const selectedId = els.content_id.value;
  els.content_list.replaceChildren();
  if (!state.content.length) els.content_list.append(emptyState("Ainda não existem conteúdos editoriais."));
  state.content.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "resource-item";
    button.setAttribute("aria-current", String(item.id === selectedId));
    const title = document.createElement("strong");
    title.textContent = item.title || "Sem título";
    const status = document.createElement("small");
    status.textContent = `${item.status || "draft"} · ${item.kind || "resource"}`;
    button.append(title, status);
    button.addEventListener("click", () => fillContent(item));
    els.content_list.append(button);
  });
}

function fillContent(item = null) {
  const value = item || {};
  els.content_id.value = value.id || "";
  els.content_name.value = value.title || "";
  els.content_kind.value = value.kind || "podcast";
  els.content_summary.value = value.summary || "";
  els.content_url.value = value.url || "";
  els.content_image.value = value.image_url || "";
  els.content_date.value = value.display_date || "";
  els.content_order.value = Number.isInteger(value.sort_order) ? value.sort_order : 0;
  els.publish_content.disabled = !value.id;
  els.retire_content.disabled = !value.id;
  renderContentList();
  els.content_name.focus();
}

function contentPayload() {
  return {
    kind: els.content_kind.value,
    title: els.content_name.value.trim(),
    summary: els.content_summary.value.trim(),
    url: els.content_url.value.trim() || null,
    image_url: els.content_image.value.trim() || null,
    display_date: els.content_date.value.trim() || null,
    sort_order: Number(els.content_order.value || 0),
  };
}

async function saveContent(event) {
  event.preventDefault();
  const id = els.content_id.value;
  const path = id ? `/api/v1/admin/content/${encodeURIComponent(id)}` : "/api/v1/admin/content";
  setStatus("A guardar o rascunho...");
  try {
    const saved = await platformRequest(path, {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(contentPayload()),
    });
    await loadContent();
    fillContent(saved);
    setStatus("Rascunho guardado. Revê a ligação antes de publicar.");
  } catch (error) { setStatus(error.message, true); }
}

async function publishContent() {
  const id = els.content_id.value;
  if (!id || !window.confirm("Publicar este conteúdo em Viver Saudável?")) return;
  try {
    const saved = await platformRequest(`/api/v1/admin/content/${encodeURIComponent(id)}/publish`, { method: "POST" });
    await loadContent();
    fillContent(saved);
    setStatus("Conteúdo publicado.");
  } catch (error) { setStatus(error.message, true); }
}

async function retireContent() {
  const id = els.content_id.value;
  if (!id || !window.confirm("Retirar este conteúdo da plataforma?")) return;
  try {
    await platformRequest(`/api/v1/admin/content/${encodeURIComponent(id)}/retire`, { method: "POST" });
    await loadContent();
    fillContent();
    setStatus("Conteúdo retirado.");
  } catch (error) { setStatus(error.message, true); }
}

function summaryMetric(label, value) {
  const article = document.createElement("article");
  const caption = document.createElement("span");
  caption.textContent = label;
  const total = document.createElement("strong");
  total.textContent = String(value ?? 0);
  article.append(caption, total);
  return article;
}

async function loadOperations() {
  setStatus("A atualizar os envios...");
  const [payload, auditEvents] = await Promise.all([
    platformRequest("/api/v1/admin/operations/send-logs?limit=100"),
    platformRequest("/api/v1/admin/operations/audit-events?limit=100"),
  ]);
  const summary = payload?.summary || {};
  const entries = Array.isArray(payload?.entries) ? payload.entries : [];
  els.operations_summary.replaceChildren(
    summaryMetric("Registos", summary.total),
    summaryMetric("Enviados", summary.sent),
    summaryMetric("Falharam", summary.failed),
  );
  els.operations_list.replaceChildren();
  if (!entries.length) els.operations_list.append(emptyState("Ainda não existem registos de envio."));
  entries.slice().reverse().forEach((entry) => {
    const article = document.createElement("article");
    article.className = "operation-record";
    const date = document.createElement("strong");
    date.textContent = entry.send_date || "Data indisponível";
    const channel = document.createElement("span");
    channel.textContent = entry.channel || "Canal indisponível";
    const status = document.createElement("span");
    status.className = `operation-status${entry.status === "failed" ? " failed" : ""}`;
    status.textContent = entry.status === "sent" ? "Enviado" : "Falhou";
    const time = document.createElement("time");
    time.dateTime = entry.sent_at || "";
    time.textContent = entry.sent_at ? new Date(entry.sent_at).toLocaleString("pt-CV") : "Hora indisponível";
    article.append(date, channel, status, time);
    els.operations_list.append(article);
  });
  const events = Array.isArray(auditEvents) ? auditEvents : [];
  renderAuditEvents(events);
  setStatus(`${entries.length} envio(s) e ${events.length} evento(s) editorial(is).`);
}

function renderAuditEvents(events) {
  const actionLabels = {
    "community.published": "Partilha publicada",
    "community.hidden": "Partilha ocultada",
    "community.rejected": "Partilha rejeitada",
    "help.created": "Recurso criado",
    "help.updated": "Recurso atualizado",
    "help.verified": "Recurso verificado",
    "help.retired": "Recurso retirado",
    "help.stale": "Recurso expirado",
    "content.created": "Conteúdo criado",
    "content.updated": "Conteúdo atualizado",
    "content.published": "Conteúdo publicado",
    "content.retired": "Conteúdo retirado",
  };
  els.audit_list.replaceChildren();
  if (!events.length) els.audit_list.append(emptyState("Ainda não existem eventos editoriais."));
  events.forEach((event) => {
    const article = document.createElement("article");
    article.className = "operation-record audit-record";
    const action = document.createElement("strong");
    action.textContent = actionLabels[event.action] || "Ação editorial";
    const actor = document.createElement("span");
    actor.textContent = event.actor_ref || "Conta indisponível";
    const target = document.createElement("span");
    target.textContent = event.target_ref || "Item indisponível";
    const time = document.createElement("time");
    time.dateTime = event.created_at || "";
    time.textContent = event.created_at ? new Date(event.created_at).toLocaleString("pt-CV") : "Hora indisponível";
    article.append(action, actor, target, time);
    els.audit_list.append(article);
  });
}

async function initialize() {
  try {
    const response = await fetch("/api/v1/config", { cache: "no-store" });
    const config = await response.json();
    if (!config.features?.staffAdmin || !config.supabase) {
      els.email_form.hidden = true;
      els.auth_summary.textContent = "A área da equipa ainda não está configurada neste ambiente.";
      return;
    }
    state.client = new SupabaseAccountClient(config.supabase);
    if (state.session) {
      try {
        await authenticate();
      } catch (error) {
        persistSession(null);
        els.email_form.hidden = false;
        els.auth_summary.textContent = "Usa a conta previamente autorizada pela administração.";
        setStatus(error.message || "A sessão terminou. Entra novamente.", true);
      }
      return;
    }
    els.email_form.hidden = false;
    els.auth_summary.textContent = "Usa a conta previamente autorizada pela administração.";
  } catch (error) {
    persistSession(null);
    setStatus(error.message || "Não foi possível iniciar a área da equipa.", true);
  }
}

els.email_form.addEventListener("submit", async (event) => {
  event.preventDefault();
  pendingEmail = els.staff_email.value.trim().toLowerCase();
  try {
    setStatus("A enviar o código...");
    await state.client.sendOtp(pendingEmail, { createUser: false });
    els.code_form.hidden = false;
    els.staff_code.focus();
    setStatus("Código enviado para a conta autorizada.");
  } catch (error) { setStatus(error.message, true); }
});

els.code_form.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    persistSession(await state.client.verifyOtp(pendingEmail, els.staff_code.value.trim()));
    await authenticate();
  } catch (error) { persistSession(null); setStatus(error.message, true); }
});

els.signout.addEventListener("click", async () => {
  try { await state.client?.signOut(state.session); } catch { /* Local sign-out still proceeds. */ }
  persistSession(null);
  window.location.reload();
});
els.community_tab.addEventListener("click", () => showView("community").catch((error) => setStatus(error.message, true)));
els.directory_tab.addEventListener("click", () => showView("directory").catch((error) => setStatus(error.message, true)));
els.content_tab.addEventListener("click", () => showView("content").catch((error) => setStatus(error.message, true)));
els.operations_tab.addEventListener("click", () => showView("operations").catch((error) => setStatus(error.message, true)));
adminTabs.forEach((tab) => {
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    moveAdminTab(tab, event.key);
  });
});
els.refresh_community.addEventListener("click", () => loadCommunity().catch((error) => setStatus(error.message, true)));
els.refresh_operations.addEventListener("click", () => loadOperations().catch((error) => setStatus(error.message, true)));
els.new_resource.addEventListener("click", () => fillResource());
els.resource_form.addEventListener("submit", saveResource);
els.verify_resource.addEventListener("click", verifyResource);
els.retire_resource.addEventListener("click", retireResource);
els.new_content.addEventListener("click", () => fillContent());
els.content_form.addEventListener("submit", saveContent);
els.publish_content.addEventListener("click", publishContent);
els.retire_content.addEventListener("click", retireContent);

initialize();
