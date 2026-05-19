import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "profile_lint.py"


class ProfileLintTests(unittest.TestCase):
    def test_valid_config_passes(self) -> None:
        payload = {
            "version": 1,
            "organization_id": "org-1",
            "project_id": "proj-1",
            "project_code": "DEMO",
            "owners": {
                "backend": "A",
                "ui_product": "B",
                "qa": "C",
            },
            "statuses": [
                {"type": "Bug", "status": "待处理", "id": "1", "meaning": "unfinished"},
                {"type": "Bug", "status": "处理中", "id": "2", "meaning": "active"},
                {"type": "Bug", "status": "已关闭", "id": "3", "meaning": "terminal"},
            ],
            "production_targets": ["admin/src"],
            "validations": [["admin", "pnpm -C admin lint"]],
        }
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            json.dump(payload, handle, ensure_ascii=False)
            temp_path = handle.name
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--config-path", temp_path],
                capture_output=True,
                text=True,
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ok: true", result.stdout)

    def test_missing_active_status_errors_when_no_active_meaning_exists(self) -> None:
        payload = {
            "version": 1,
            "organization_id": "org-1",
            "project_id": "proj-1",
            "project_code": "DEMO",
            "statuses": [
                {"type": "Bug", "status": "待处理", "id": "1", "meaning": "unfinished"},
                {"type": "Bug", "status": "已关闭", "id": "3", "meaning": "terminal"},
            ],
            "status_policy": "Statuses may be updated during handling.",
        }
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            json.dump(payload, handle, ensure_ascii=False)
            temp_path = handle.name
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--config-path", temp_path],
                capture_output=True,
                text=True,
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("status updates appear enabled", result.stdout)


if __name__ == "__main__":
    unittest.main()
