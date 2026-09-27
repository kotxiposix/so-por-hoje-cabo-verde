import assert from "node:assert/strict";
import test from "node:test";

import {
  normalizePublishedEditorialItem,
  normalizePublishedEditorialItems,
} from "../public/editorial-content.mjs";

const origin = "https://soporhoje.cv";
const validItem = {
  id: "4948B21E-FACF-4BC8-A60E-8800B488DFEE",
  kind: "podcast",
  title: "  Conversa sobre recuperação ",
  summary: " Uma conversa honesta sobre apoio e recomeços. ",
  url: "/expo#experiencia",
  image_url: "/expo/hero-banner.jpg",
  display_date: " Setembro de 2026 ",
};

test("normalizes the published editorial contract", () => {
  assert.deepEqual(normalizePublishedEditorialItem(validItem, origin), {
    id: validItem.id.toLowerCase(),
    kind: "podcast",
    title: "Conversa sobre recuperação",
    summary: "Uma conversa honesta sobre apoio e recomeços.",
    url: "https://soporhoje.cv/expo#experiencia",
    image_url: "https://soporhoje.cv/expo/hero-banner.jpg",
    display_date: "Setembro de 2026",
  });
});

test("rejects malformed records and unsafe destinations", () => {
  assert.equal(normalizePublishedEditorialItem({ ...validItem, id: "item-one" }, origin), null);
  assert.equal(normalizePublishedEditorialItem({ ...validItem, kind: "advert" }, origin), null);
  assert.equal(normalizePublishedEditorialItem({ ...validItem, title: "x".repeat(161) }, origin), null);
  assert.equal(normalizePublishedEditorialItem({ ...validItem, url: "javascript:alert(1)" }, origin), null);
  assert.equal(normalizePublishedEditorialItem({ ...validItem, url: "http://example.cv" }, origin), null);
});

test("keeps valid content while dropping external or unsafe images", () => {
  const external = normalizePublishedEditorialItem({
    ...validItem,
    image_url: "https://images.example.cv/cover.jpg",
  }, origin);
  const unsafe = normalizePublishedEditorialItem({
    ...validItem,
    image_url: "javascript:alert(1)",
  }, origin);

  assert.equal(external.image_url, "");
  assert.equal(unsafe.image_url, "");
});

test("filters duplicate identifiers and respects the public limit", () => {
  const second = {
    ...validItem,
    id: "e00acccc-0f83-4132-8949-cd090a217c20",
    title: "Segundo conteúdo",
  };
  const result = normalizePublishedEditorialItems([
    validItem,
    { ...validItem },
    { ...validItem, id: "invalid" },
    second,
  ], origin, 2);

  assert.deepEqual(result.map((item) => item.id), [
    validItem.id.toLowerCase(),
    second.id,
  ]);
});
