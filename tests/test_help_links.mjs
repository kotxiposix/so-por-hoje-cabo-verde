import assert from "node:assert/strict";
import test from "node:test";

import { normalizeHelpAction } from "../public/help-links.mjs";

test("builds safe telephone and email actions", () => {
  assert.deepEqual(normalizeHelpAction("phone", "+238 262 31 29 / 333 72 43"), {
    href: "tel:+2382623129",
    external: false,
  });
  assert.deepEqual(normalizeHelpAction("email", "apoio@example.cv"), {
    href: "mailto:apoio@example.cv",
    external: false,
  });
});

test("accepts only credential-free HTTPS web links", () => {
  assert.deepEqual(normalizeHelpAction("web", "https://example.cv/apoio"), {
    href: "https://example.cv/apoio",
    external: true,
  });
  for (const value of ["http://example.cv", "javascript:alert(1)", "https://user:pass@example.cv"]) {
    assert.equal(normalizeHelpAction("web", value), null);
  }
});

test("rejects malformed contact actions", () => {
  assert.equal(normalizeHelpAction("phone", "123"), null);
  assert.equal(normalizeHelpAction("email", "not-an-email"), null);
  assert.equal(normalizeHelpAction("unknown", "value"), null);
});
