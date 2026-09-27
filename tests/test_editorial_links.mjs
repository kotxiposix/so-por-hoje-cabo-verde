import assert from "node:assert/strict";
import test from "node:test";

import { normalizeEditorialLink } from "../public/editorial-links.mjs";

const ORIGIN = "https://soporhoje.cv";

test("normalizes internal editorial links without marking them external", () => {
  assert.deepEqual(normalizeEditorialLink("/expo#autor", ORIGIN), {
    href: "https://soporhoje.cv/expo#autor",
    external: false,
  });
});

test("accepts external HTTPS links", () => {
  assert.deepEqual(normalizeEditorialLink("https://example.cv/podcast", ORIGIN), {
    href: "https://example.cv/podcast",
    external: true,
  });
});

test("rejects unsafe, credentialed, and empty links", () => {
  for (const value of [
    "javascript:alert(1)",
    "http://example.cv/podcast",
    "https://user:secret@example.cv/private",
    "",
    null,
  ]) {
    assert.equal(normalizeEditorialLink(value, ORIGIN), null);
  }
});
