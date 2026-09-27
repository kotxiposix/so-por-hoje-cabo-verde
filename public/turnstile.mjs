const TURNSTILE_SCRIPT_URL = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

let loaderPromise = null;

export function normalizeTurnstileSiteKey(value) {
  if (typeof value !== "string") return "";
  const key = value.trim();
  if (key.length < 10 || key.length > 256 || !/^[A-Za-z0-9_-]+$/.test(key)) return "";
  return key;
}

export function normalizeTurnstileToken(value) {
  if (typeof value !== "string") return "";
  const token = value.trim();
  if (!token || token.length > 4096 || /[\u0000-\u001f\u007f\s]/.test(token)) return "";
  return token;
}

export function loadTurnstile({ windowRef = globalThis.window, documentRef = globalThis.document } = {}) {
  if (windowRef?.turnstile?.render) return Promise.resolve(windowRef.turnstile);
  if (!documentRef?.createElement || !documentRef?.head) {
    return Promise.reject(new Error("A verificação de segurança não está disponível neste navegador."));
  }
  if (loaderPromise) return loaderPromise;

  loaderPromise = new Promise((resolve, reject) => {
    let script = documentRef.querySelector(`script[src="${TURNSTILE_SCRIPT_URL}"]`);
    const timeout = windowRef.setTimeout(
      () => reject(new Error("A verificação de segurança demorou demasiado a responder.")),
      10000,
    );
    const finish = () => {
      windowRef.clearTimeout(timeout);
      if (windowRef?.turnstile?.render) resolve(windowRef.turnstile);
      else reject(new Error("A verificação de segurança não ficou disponível."));
    };
    const fail = () => {
      windowRef.clearTimeout(timeout);
      reject(new Error("Não foi possível carregar a verificação de segurança."));
    };

    if (!script) {
      script = documentRef.createElement("script");
      script.src = TURNSTILE_SCRIPT_URL;
      script.async = true;
      script.defer = true;
    }
    script.addEventListener("load", finish, { once: true });
    script.addEventListener("error", fail, { once: true });
    if (!script.isConnected) documentRef.head.append(script);
  }).catch((error) => {
    loaderPromise = null;
    throw error;
  });

  return loaderPromise;
}

export class TurnstileWidget {
  constructor({ container, siteKey, windowRef = globalThis.window, documentRef = globalThis.document }) {
    this.container = container;
    this.siteKey = normalizeTurnstileSiteKey(siteKey);
    this.windowRef = windowRef;
    this.documentRef = documentRef;
    this.api = null;
    this.widgetId = null;
    this.token = "";
    if (!container || !this.siteKey) {
      throw new Error("Configuração Turnstile inválida ou incompleta.");
    }
  }

  async mount() {
    this.api = await loadTurnstile({ windowRef: this.windowRef, documentRef: this.documentRef });
    this.container.hidden = false;
    this.widgetId = this.api.render(this.container, {
      sitekey: this.siteKey,
      action: "email_otp",
      appearance: "always",
      language: "pt",
      size: "flexible",
      theme: "auto",
      callback: (token) => { this.token = normalizeTurnstileToken(token); },
      "expired-callback": () => { this.token = ""; },
      "error-callback": () => { this.token = ""; },
      "timeout-callback": () => { this.token = ""; },
    });
    return this;
  }

  getToken() {
    const response = this.token || this.api?.getResponse?.(this.widgetId) || "";
    return normalizeTurnstileToken(response);
  }

  reset() {
    this.token = "";
    if (this.api && this.widgetId !== null) this.api.reset(this.widgetId);
  }
}
