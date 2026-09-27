import assert from "node:assert/strict";
import test from "node:test";

import {
  normalizeTurnstileSiteKey,
  normalizeTurnstileToken,
  TurnstileWidget,
} from "../public/turnstile.mjs";

test("normalizes only bounded Turnstile site keys", () => {
  assert.equal(normalizeTurnstileSiteKey(" 1x00000000000000000000AA "), "1x00000000000000000000AA");
  for (const value of ["", "short", "bad site key", "x".repeat(257), null]) {
    assert.equal(normalizeTurnstileSiteKey(value), "");
  }
});

test("rejects empty, oversized and whitespace-bearing challenge tokens", () => {
  assert.equal(normalizeTurnstileToken(" token.valid_123 "), "token.valid_123");
  for (const value of ["", "bad token", "bad\ntoken", "x".repeat(4097), null]) {
    assert.equal(normalizeTurnstileToken(value), "");
  }
});

test("widget keeps a one-time token and resets it after use", async () => {
  const container = { hidden: true };
  let options;
  let resetWidgetId = null;
  const turnstile = {
    render(target, receivedOptions) {
      assert.equal(target, container);
      options = receivedOptions;
      return "widget-1";
    },
    getResponse() { return ""; },
    reset(widgetId) { resetWidgetId = widgetId; },
  };
  const widget = new TurnstileWidget({
    container,
    siteKey: "1x00000000000000000000AA",
    windowRef: { turnstile },
    documentRef: {},
  });

  await widget.mount();
  assert.equal(container.hidden, false);
  assert.equal(options.action, "email_otp");
  assert.equal(options.appearance, "always");
  options.callback("challenge.valid_123");
  assert.equal(widget.getToken(), "challenge.valid_123");
  widget.reset();
  assert.equal(widget.getToken(), "");
  assert.equal(resetWidgetId, "widget-1");
});
