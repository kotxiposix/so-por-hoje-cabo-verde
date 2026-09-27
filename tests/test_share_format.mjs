import assert from "node:assert/strict";
import test from "node:test";

import { composeGroupMessage } from "../public/share-format.mjs";

test("formats the group message with the approved spacing and attribution", () => {
  const message = composeGroupMessage({
    date: "2026-04-30",
    weekday: "Quinta-feira",
    title: "DEUS FAZ POR NÓS",
    body: "Texto introdutório.\n\nSegundo parágrafo.",
    reflection: "Confio no próximo passo.",
  });

  assert.equal(message, [
    "BOM DIA GUERREIROS",
    "",
    "MEDITAÇÃO DO DIA",
    "",
    "Quinta, 30 de Abril de 2026",
    "",
    "",
    "DEUS FAZ POR NÓS",
    "",
    "",
    "Texto introdutório.",
    "",
    "",
    "Segundo parágrafo.",
    "",
    "",
    "SÓ POR HOJE:",
    "",
    "Confio no próximo passo.",
    "",
    "",
    "soporhoje.cv",
    "",
    "",
    "Fonte oficial: Narcóticos Anónimos Portugal",
    "© NA World Services, Inc. Reprinted by permission.",
  ].join("\n"));
  assert.doesNotMatch(message, /https?:\/\//);
  assert.doesNotMatch(message, /na-pt\.erlog\.pt/);
});
