import assert from "node:assert/strict";
import test from "node:test";

import { getPrivacyCopy } from "../public/privacy-copy.mjs";


test("privacy copy keeps unconfigured environments local", () => {
  const copy = getPrivacyCopy();

  assert.match(copy.summary, /armazenamento do navegador/);
  assert.match(copy.summary, /Não são enviados para uma conta/);
  assert.match(copy.gratitudeNote, /apenas neste dispositivo/);
});

test("privacy copy explains that an available account remains optional", () => {
  const copy = getPrivacyCopy({ accountEnabled: true });

  assert.match(copy.summary, /nenhum dado da Jornada é enviado/);
  assert.match(copy.detail, /modo local e anónimo/);
  assert.match(copy.faqAnswer, /permanecem neste dispositivo/);
});

test("privacy copy does not claim synchronization before the user chooses", () => {
  const copy = getPrivacyCopy({ accountEnabled: true, signedIn: true });

  assert.match(copy.summary, /sincronização ainda não começou/);
  assert.match(copy.principle, /continua local/);
  assert.match(copy.journeyIntro, /continuam neste navegador/);
});

test("privacy copy distinguishes synchronized and device-only data", () => {
  const copy = getPrivacyCopy({
    accountEnabled: true,
    signedIn: true,
    syncEnabled: true,
  });

  assert.match(copy.summary, /podem ser guardados na tua conta/);
  assert.match(copy.detail, /Sala Anónima/);
  assert.match(copy.detail, /apenas neste dispositivo/);
  assert.match(copy.gratitudeNote, /guardada na tua conta/);
  assert.match(copy.faqAnswer, /Sala Anónima.*continuam locais/);
});
