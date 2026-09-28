import assert from "node:assert/strict";
import test from "node:test";

import { SupabaseAccountClient, normalizeSession } from "../public/account-client.mjs";


function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

test("accepts only a credential-free HTTPS Supabase origin", () => {
  const client = new SupabaseAccountClient({
    url: " https://project.supabase.co/ ",
    publishableKey: "public-key",
  });
  assert.equal(client.url, "https://project.supabase.co");

  for (const url of [
    "http://project.supabase.co",
    "https://user:secret@project.supabase.co",
    "https://project.supabase.co/rest/v1",
    "https://project.supabase.co?redirect=example.cv",
    "not-a-url",
  ]) {
    assert.throws(
      () => new SupabaseAccountClient({ url, publishableKey: "public-key" }),
      /Configuração Supabase inválida/,
    );
  }
});

test("rejects empty, oversized and whitespace-bearing publishable keys", () => {
  for (const publishableKey of ["", "public key", "key\nvalue", "x".repeat(4097)]) {
    assert.throws(
      () => new SupabaseAccountClient({ url: "https://project.supabase.co", publishableKey }),
      /Configuração Supabase inválida/,
    );
  }
});

test("sendOtp uses the official email OTP endpoint", async () => {
  let request;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return jsonResponse({});
    },
  });

  await client.sendOtp("person@example.com");

  assert.equal(request.url, "https://project.supabase.co/auth/v1/otp");
  assert.deepEqual(JSON.parse(request.options.body), {
    email: "person@example.com",
    create_user: true,
  });
  assert.equal(request.options.headers.apikey, "public-key");
});

test("binds browser fetch implementations to the global object", async () => {
  let receiver;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl(url, options) {
      receiver = this;
      return jsonResponse({ url, method: options.method });
    },
  });

  await client.sendOtp("person@example.com");
  assert.equal(receiver, globalThis);
});

test("staff OTP can refuse automatic account creation", async () => {
  let request;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return jsonResponse({});
    },
  });

  await client.sendOtp("staff@example.cv", { createUser: false });

  assert.equal(JSON.parse(request.options.body).create_user, false);
});

test("sendOtp forwards a valid one-time CAPTCHA token in the official Supabase shape", async () => {
  let request;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return jsonResponse({});
    },
  });

  await client.sendOtp("person@example.com", { captchaToken: "turnstile.valid-token_123" });

  assert.deepEqual(JSON.parse(request.options.body), {
    email: "person@example.com",
    create_user: true,
    gotrue_meta_security: { captcha_token: "turnstile.valid-token_123" },
  });
});

test("sendOtp never forwards malformed CAPTCHA tokens", async () => {
  let request;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return jsonResponse({});
    },
  });

  await client.sendOtp("person@example.com", { captchaToken: "bad token\nvalue" });
  assert.equal("gotrue_meta_security" in JSON.parse(request.options.body), false);
});

test("verifyOtp requests an email session", async () => {
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (url, options) => {
      assert.equal(url, "https://project.supabase.co/auth/v1/verify");
      assert.deepEqual(JSON.parse(options.body), {
        email: "person@example.com",
        token: "123456",
        type: "email",
      });
      return jsonResponse({
        access_token: "access",
        refresh_token: "refresh",
        expires_in: 3600,
        user: { id: "user-id", email: "person@example.com" },
      });
    },
  });

  const session = await client.verifyOtp("person@example.com", "123456");
  assert.equal(session.user.id, "user-id");
  assert.equal(session.access_token, "access");
});

test("journey save uses the authenticated atomic conflict endpoint", async () => {
  let request;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (url, options) => {
      request = { url, options, body: JSON.parse(options.body) };
      return jsonResponse([{ saved: true, current_updated_at: "2026-09-26T10:00:00Z" }]);
    },
  });
  const session = normalizeSession({
    access_token: "access",
    refresh_token: "refresh",
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    user: { id: "user-id", email: "person@example.com" },
  });

  const result = await client.saveJourney(
    session,
    { completed: ["2026-09-26"] },
    { expectedUpdatedAt: "2026-09-26T09:00:00Z" },
  );

  assert.equal(request.url, "https://project.supabase.co/rest/v1/rpc/save_journey_state");
  assert.equal(request.options.headers.Authorization, "Bearer access");
  assert.deepEqual(request.body, {
    p_payload: { completed: ["2026-09-26"] },
    p_schema_version: 2,
    p_expected_updated_at: "2026-09-26T09:00:00Z",
    p_force: false,
  });
  assert.equal(result.saved, true);
  assert.equal(result.updatedAt, "2026-09-26T10:00:00Z");
});

test("journey save reports an atomic conflict without overwriting", async () => {
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async () => jsonResponse([{
      saved: false,
      current_updated_at: "2026-09-26T11:00:00Z",
    }]),
  });
  const session = normalizeSession({
    access_token: "access",
    refresh_token: "refresh",
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    user: { id: "user-id", email: "person@example.com" },
  });

  const result = await client.saveJourney(session, {}, {
    expectedUpdatedAt: "2026-09-26T09:00:00Z",
  });

  assert.equal(result.saved, false);
  assert.equal(result.updatedAt, "2026-09-26T11:00:00Z");
});

test("non-JSON failures preserve a useful message", async () => {
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async () => new Response("Serviço indisponível", { status: 503 }),
  });

  await assert.rejects(client.sendOtp("person@example.com"), /Serviço indisponível/);
});

test("journey deletion is limited to the signed-in user", async () => {
  let request;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return new Response(null, { status: 204 });
    },
  });
  const session = normalizeSession({
    access_token: "access",
    refresh_token: "refresh",
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    user: { id: "user-id", email: "person@example.com" },
  });

  await client.deleteJourney(session);

  assert.equal(request.url, "https://project.supabase.co/rest/v1/journey_state?user_id=eq.user-id");
  assert.equal(request.options.method, "DELETE");
  assert.equal(request.options.headers.Authorization, "Bearer access");
});

test("push subscription stores only the signed-in user's endpoint and keys", async () => {
  let body;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (_url, options) => {
      body = JSON.parse(options.body);
      return new Response(null, { status: 204 });
    },
  });
  const session = normalizeSession({
    access_token: "access",
    refresh_token: "refresh",
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    user: { id: "user-id", email: "person@example.com" },
  });

  await client.savePushSubscription(session, {
    endpoint: "https://push.example/subscription",
    keys: { p256dh: "public-client-key", auth: "auth-secret" },
  });

  assert.equal(body[0].user_id, "user-id");
  assert.equal(body[0].endpoint, "https://push.example/subscription");
  assert.equal(body[0].active, true);
});

test("push subscription refuses unsafe endpoints and malformed keys before transport", async () => {
  let requests = 0;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async () => {
      requests += 1;
      return new Response(null, { status: 204 });
    },
  });
  const session = normalizeSession({
    access_token: "access",
    refresh_token: "refresh",
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    user: { id: "user-id", email: "person@example.com" },
  });

  await assert.rejects(client.savePushSubscription(session, {
    endpoint: "http://internal.example/push",
    keys: { p256dh: "validKeyMaterial_123456", auth: "validAuth_123" },
  }), /Subscrição push inválida/);
  await assert.rejects(client.savePushSubscription(session, {
    endpoint: "https://push.example/one",
    keys: { p256dh: "short", auth: "validAuth_123" },
  }), /Subscrição push inválida/);
  assert.equal(requests, 0);
});

test("notification preference is scoped to the signed-in user", async () => {
  let request;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (url, options) => {
      request = { url, options, body: JSON.parse(options.body) };
      return new Response(null, { status: 204 });
    },
  });
  const session = normalizeSession({
    access_token: "access",
    refresh_token: "refresh",
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    user: { id: "user-id", email: "person@example.com" },
  });

  await client.saveNotificationPreference(session, {
    enabled: true,
    localTime: "08:30",
    timezone: "Atlantic/Cape_Verde",
  });

  assert.match(request.url, /notification_preferences\?on_conflict=user_id$/);
  assert.equal(request.body[0].user_id, "user-id");
  assert.equal(request.body[0].enabled, true);
  assert.equal(request.body[0].local_time, "08:30");
  assert.equal(request.body[0].timezone, "Atlantic/Cape_Verde");
});

test("push subscription deactivation targets one encoded endpoint", async () => {
  let request;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (url, options) => {
      request = { url, options, body: JSON.parse(options.body) };
      return new Response(null, { status: 204 });
    },
  });
  const session = normalizeSession({
    access_token: "access",
    refresh_token: "refresh",
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    user: { id: "user-id", email: "person@example.com" },
  });

  await client.disablePushSubscription(session, "https://push.example/subscription?id=one&key=two");

  assert.match(request.url, /endpoint=eq\.https%3A%2F%2Fpush\.example%2Fsubscription%3Fid%3Done%26key%3Dtwo$/);
  assert.equal(request.options.method, "PATCH");
  assert.equal(request.body.active, false);
  assert.equal(request.options.headers.Authorization, "Bearer access");
});

test("account deletion uses the platform endpoint with the active access token", async () => {
  let request;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    platformFetchImpl: async (url, options) => {
      request = { url, options };
      return jsonResponse({ deleted: true });
    },
  });
  const session = normalizeSession({
    access_token: "access",
    refresh_token: "refresh",
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    user: { id: "untrusted-client-id", email: "person@example.com" },
  });

  await client.deleteAccount(session);

  assert.equal(request.url, "/api/v1/account");
  assert.equal(request.options.method, "DELETE");
  assert.equal(request.options.headers.Authorization, "Bearer access");
});
