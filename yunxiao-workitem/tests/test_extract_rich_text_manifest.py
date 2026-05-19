import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract_rich_text_manifest.py"


class ExtractManifestTests(unittest.TestCase):
    def test_extracts_image_placeholder(self) -> None:
        payload = {
            "htmlValue": "<p>hello</p><img src=\"https://example.com/a.png?fileIdentifier=abc123\" />"
        }
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            json.dump(payload, handle, ensure_ascii=False)
            temp_path = handle.name
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    temp_path,
                    "--item-key",
                    "DEMO-1",
                    "--source-label",
                    "description",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            manifest = json.loads(result.stdout)
        finally:
            Path(temp_path).unlink(missing_ok=True)

        self.assertIn("{{image:description-1", manifest["annotatedText"])
        self.assertIn("description-1", manifest["images"])
        self.assertEqual(manifest["images"]["description-1"]["fileIdentifier"], "abc123")


if __name__ == "__main__":
    unittest.main()

