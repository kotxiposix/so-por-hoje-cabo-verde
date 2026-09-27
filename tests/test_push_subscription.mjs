import assert from "node:assert/strict";
import test from "node:test";

import {
  normalizePushEndpoint,
  normalizePushSubscription,
} from "../public/push-subscription.mjs";

const valid = {
  endpoint: "https://push.example/registration/one",
  keys: {
    p256dh: "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789_-ab",
    auth: "0123456789abcdef_-AB",
  },
};

test("normalizes a credential-free HTTPS push subscription", () => {
  assert.deepEqual(normalizePushSubscription(valid), valid);
});

test("rejects unsafe push endpoints", () => {
  for (const endpoint of [
    "http://push.example/one",
    "https://user:secret@push.example/one",
    "https://127.0.0.1/push",
    "https://service.internal/push",
    "javascript:alert(1)",
    "",
  ]) {
    assert.equal(normalizePushEndpoint(endpoint), "");
    assert.equal(normalizePushSubscription({ ...valid, endpoint }), null);
  }
});

test("rejects missing, short, oversized and malformed key material", () => {
  for (const keys of [
    {},
    { p256dh: "short", auth: valid.keys.auth },
    { p256dh: valid.keys.p256dh, auth: "short" },
    { p256dh: `${valid.keys.p256dh}!`, auth: valid.keys.auth },
    { p256dh: "x".repeat(513), auth: valid.keys.auth },
  ]) {
    assert.equal(normalizePushSubscription({ ...valid, keys }), null);
  }
});
