import assert from "node:assert/strict";
import test from "node:test";

import {
  normalizePublishedHelpResource,
  normalizePublishedHelpResources,
} from "../public/help-resources.mjs";

const today = "2026-09-27";
const validResource = {
  id: "4948B21E-FACF-4BC8-A60E-8800B488DFEE",
  name: "  Grupo de apoio  ",
  island: "Santiago",
  municipality: "Praia",
  category: "meeting",
  description: "  Encontro confirmado pela entidade responsável. ",
  phone: "+238 262 31 29",
  email: "apoio@example.cv",
  website: "https://example.cv/apoio",
  schedule: [" Terça · 18h "],
  is_emergency: false,
  source_url: "https://example.cv/fonte",
  verified_at: "2026-09-20T10:00:00+00:00",
  review_due_at: "2026-10-27",
};

test("normalizes the verified public help contract", () => {
  assert.deepEqual(normalizePublishedHelpResource(validResource, today), {
    ...validResource,
    id: validResource.id.toLowerCase(),
    name: "Grupo de apoio",
    description: "Encontro confirmado pela entidade responsável.",
    schedule: ["Terça · 18h"],
  });
});

test("rejects expired, malformed and unsafe resources", () => {
  assert.equal(normalizePublishedHelpResource({ ...validResource, id: "resource-one" }, today), null);
  assert.equal(normalizePublishedHelpResource({ ...validResource, category: "unknown" }, today), null);
  assert.equal(normalizePublishedHelpResource({ ...validResource, source_url: "http://example.cv" }, today), null);
  assert.equal(normalizePublishedHelpResource({ ...validResource, review_due_at: "2026-09-26" }, today), null);
  assert.equal(normalizePublishedHelpResource({ ...validResource, review_due_at: "2026-02-30" }, today), null);
  assert.equal(normalizePublishedHelpResource({ ...validResource, is_emergency: "false" }, today), null);
});

test("requires actionable emergency, meeting and family details", () => {
  const emergency = {
    ...validResource,
    category: "emergency",
    is_emergency: true,
    phone: "",
  };
  assert.equal(normalizePublishedHelpResource(emergency, today), null);
  assert.equal(normalizePublishedHelpResource({ ...validResource, schedule: [] }, today), null);
  assert.equal(normalizePublishedHelpResource({
    ...validResource,
    phone: "",
    email: "",
    website: "",
  }, today), null);
});

test("filters duplicate identifiers and caps the public result", () => {
  const second = {
    ...validResource,
    id: "e00acccc-0f83-4132-8949-cd090a217c20",
    name: "Segundo grupo",
  };
  const result = normalizePublishedHelpResources([
    validResource,
    { ...validResource },
    { ...validResource, review_due_at: "2026-09-26" },
    second,
  ], today, 2);

  assert.deepEqual(result.map((resource) => resource.id), [
    validResource.id.toLowerCase(),
    second.id,
  ]);
  assert.deepEqual(normalizePublishedHelpResources([validResource], "2026-02-30"), []);
});
