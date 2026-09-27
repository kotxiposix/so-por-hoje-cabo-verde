from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class PlatformDocumentationTests(unittest.TestCase):
    def test_dossier_matches_the_current_product_map_and_gates(self) -> None:
        dossier = (DOCS / "PLATFORM_DOSSIER.md").read_text(encoding="utf-8")

        for area in ("Meditacao", "Jornada", "Viver Saudavel", "Ajuda", "Sobre"):
            self.assertIn(f"- {area}", dossier)
        for flag in (
            "ACCOUNT_READY=false",
            "AI_DELIVERY_READY=false",
            "COMMUNITY_READY=false",
            "EDITORIAL_CONTENT_READY=false",
            "HELP_DIRECTORY_READY=false",
            "PUSH_DELIVERY_READY=false",
        ):
            self.assertIn(flag, dossier)
        for filename in (
            "IMPLEMENTATION_MATRIX.md",
            "ACTIVATION_CHECKLIST.md",
            "OPERATIONS_DECISIONS.md",
        ):
            self.assertIn(filename, dossier)
            self.assertTrue((DOCS / filename).is_file())

        sharing = dossier.split("## 11. Partilha", 1)[1].split("## 12.", 1)[0]
        self.assertIn("soporhoje.cv", sharing)
        self.assertNotIn("https://na-pt.erlog.pt/sph.php", sharing)
        self.assertIn("© NA World Services, Inc. Reprinted by permission.", sharing)


if __name__ == "__main__":
    unittest.main()
