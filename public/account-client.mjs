export class SupabaseAccountClient {
  constructor({ url, publishableKey, fetchImpl = fetch }) {
    this.url = String(url || "").replace(/\/$/, "");
    this.publishableKey = String(publishableKey || "");
    this.fetchImpl = fetchImpl;
    if (!this.url || !this.publishableKey) {
      throw new Error("Configuração Supabase incompleta.");
    }
  }

  async sendOtp(email) {
    return this.request("/auth/v1/otp", {
      method: "POST",
      body: { email, create_user: true },
    });
  }

  async verifyOtp(email, token) {
    const payload = await this.request("/auth/v1/verify", {
      method: "POST",
      body: { email, token, type: "email" },
    });
    return normalizeSession(payload);
  }

  async refreshSession(session) {
    if (!session?.refresh_token) throw new Error("Sessão expirada.");
    const payload = await this.request("/auth/v1/token?grant_type=refresh_token", {
      method: "POST",
      body: { refresh_token: session.refresh_token },
    });
    return normalizeSession(payload);
  }

  async ensureSession(session) {
    if (!session?.access_token || !session?.user?.id) throw new Error("Sessão inválida.");
    if (Number(session.expires_at || 0) > Math.floor(Date.now() / 1000) + 60) return session;
    return this.refreshSession(session);
  }

  async getJourney(session) {
    const activeSession = await this.ensureSession(session);
    const query = `/rest/v1/journey_state?select=payload,schema_version,updated_at&user_id=eq.${encodeURIComponent(activeSession.user.id)}&limit=1`;
    const records = await this.request(query, { session: activeSession });
    return { session: activeSession, record: Array.isArray(records) ? records[0] || null : null };
  }

  async upsertJourney(session, payload, schemaVersion = 2) {
    const activeSession = await this.ensureSession(session);
    await this.request("/rest/v1/journey_state?on_conflict=user_id", {
      method: "POST",
      session: activeSession,
      headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
      body: [{
        user_id: activeSession.user.id,
        payload,
        schema_version: schemaVersion,
        updated_at: new Date().toISOString(),
      }],
    });
    return activeSession;
  }

  async deleteJourney(session) {
    const activeSession = await this.ensureSession(session);
    await this.request(`/rest/v1/journey_state?user_id=eq.${encodeURIComponent(activeSession.user.id)}`, {
      method: "DELETE",
      session: activeSession,
      headers: { Prefer: "return=minimal" },
    });
    return activeSession;
  }

  async saveNotificationPreference(session, { enabled, localTime, timezone }) {
    const activeSession = await this.ensureSession(session);
    await this.request("/rest/v1/notification_preferences?on_conflict=user_id", {
      method: "POST",
      session: activeSession,
      headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
      body: [{
        user_id: activeSession.user.id,
        enabled: Boolean(enabled),
        local_time: localTime,
        timezone,
        updated_at: new Date().toISOString(),
      }],
    });
    return activeSession;
  }

  async savePushSubscription(session, subscription) {
    const activeSession = await this.ensureSession(session);
    const serialized = typeof subscription.toJSON === "function" ? subscription.toJSON() : subscription;
    if (!serialized?.endpoint || !serialized?.keys?.p256dh || !serialized?.keys?.auth) {
      throw new Error("Subscrição push inválida.");
    }
    await this.request("/rest/v1/push_subscriptions?on_conflict=endpoint", {
      method: "POST",
      session: activeSession,
      headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
      body: [{
        user_id: activeSession.user.id,
        endpoint: serialized.endpoint,
        p256dh: serialized.keys.p256dh,
        auth_secret: serialized.keys.auth,
        user_agent: globalThis.navigator?.userAgent?.slice(0, 500) || "",
        active: true,
        updated_at: new Date().toISOString(),
      }],
    });
    return activeSession;
  }

  async disablePushSubscription(session, endpoint) {
    const activeSession = await this.ensureSession(session);
    await this.request(`/rest/v1/push_subscriptions?endpoint=eq.${encodeURIComponent(endpoint)}`, {
      method: "PATCH",
      session: activeSession,
      headers: { Prefer: "return=minimal" },
      body: { active: false, updated_at: new Date().toISOString() },
    });
    return activeSession;
  }

  async signOut(session) {
    if (session?.access_token) {
      await this.request("/auth/v1/logout", { method: "POST", session });
    }
  }

  async request(path, { method = "GET", body, session, headers = {} } = {}) {
    const response = await this.fetchImpl(`${this.url}${path}`, {
      method,
      headers: {
        apikey: this.publishableKey,
        "Content-Type": "application/json",
        ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
        ...headers,
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });

    const text = await response.text();
    let payload = null;
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch {
        payload = { message: text };
      }
    }
    if (!response.ok) {
      const message = payload?.msg || payload?.message || payload?.error_description || payload?.error || "Pedido não concluído.";
      throw new Error(message);
    }
    return payload;
  }
}

export function normalizeSession(payload) {
  if (!payload?.access_token || !payload?.refresh_token || !payload?.user?.id) {
    throw new Error("A resposta de autenticação não contém uma sessão válida.");
  }
  return {
    access_token: payload.access_token,
    refresh_token: payload.refresh_token,
    expires_at: Number(payload.expires_at || Math.floor(Date.now() / 1000) + Number(payload.expires_in || 3600)),
    user: {
      id: payload.user.id,
      email: payload.user.email || "",
    },
  };
}
