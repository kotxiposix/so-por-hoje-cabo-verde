import assert from "node:assert/strict";
import test from "node:test";

import { selectDailySupport } from "../public/offline-support.mjs";

const catalog = [
  {
    month_day: "09-26",
    state: "standard",
    activity: "Atividade standard",
    phrase: "Frase standard",
    mental_challenge: "Desafio standard",
    safety_note: "Nota standard",
  },
  {
    month_day: "09-26",
    state: "risco",
    activity: "Pedir ajuda agora",
    phrase: "Não ficar sozinho",
    mental_challenge: "Escolher proteção",
    safety_note: "Procurar apoio humano",
  },
];

test("selects the state-specific offline support for the current day", () => {
  const support = selectDailySupport(catalog, "09-26", "risco");

  assert.equal(support.activity, "Pedir ajuda agora");
  assert.equal(support.mental_challenge, "Escolher proteção");
  assert.deepEqual(Object.keys(support), ["activity", "phrase", "mental_challenge", "safety_note"]);
});

test("falls back to the standard state without crossing into another day", () => {
  assert.equal(selectDailySupport(catalog, "09-26", "ansioso").phrase, "Frase standard");
  assert.equal(selectDailySupport(catalog, "09-27", "risco"), null);
  assert.equal(selectDailySupport(catalog, "not-a-date", "risco"), null);
});
