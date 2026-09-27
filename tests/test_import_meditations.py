from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.import_meditations import write_outputs


class MeditationImportTests(unittest.TestCase):
    def test_write_outputs_keeps_public_json_in_sync(self) -> None:
        records = [
            {
                "month_day": "01-01",
                "title": "Titulo",
                "body": "Corpo",
                "reflection": "Reflexao",
                "language": "pt-CV",
                "status": "published",
                "source": "teste.xlsx",
            }
        ]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            canonical = root / "data"
            public = root / "public" / "data"

            write_outputs(records, canonical, public)

            canonical_json = canonical / "meditations.json"
            public_json = public / "meditations.json"
            self.assertEqual(canonical_json.read_bytes(), public_json.read_bytes())
            self.assertEqual(json.loads(canonical_json.read_text(encoding="utf-8")), records)
            self.assertTrue((canonical / "meditations.csv").is_file())


if __name__ == "__main__":
    unittest.main()
