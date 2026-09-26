import assert from "node:assert/strict";
import test from "node:test";

import { SupabaseAccountClient, normalizeSession } from "../public/account-client.mjs";


function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

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

test("journey upsert is scoped to the signed-in user", async () => {
  let body;
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async (url, options) => {
      assert.equal(url, "https://project.supabase.co/rest/v1/journey_state?on_conflict=user_id");
      assert.equal(options.headers.Authorization, "Bearer access");
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

  await client.upsertJourney(session, { completed: ["2026-09-26"] });

  assert.equal(body[0].user_id, "user-id");
  assert.equal(body[0].schema_version, 2);
  assert.match(body[0].updated_at, /^\d{4}-\d{2}-\d{2}T/);
});

test("non-JSON failures preserve a useful message", async () => {
  const client = new SupabaseAccountClient({
    url: "https://project.supabase.co",
    publishableKey: "public-key",
    fetchImpl: async () => new Response("Serviço indisponível", { status: 503 }),
  });

  await assert.rejects(client.sendOtp("person@example.com"), /Serviço indisponível/);
});
