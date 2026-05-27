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
            "runtime_limits": {
                "query_page_size": 5,
                "max_enrich_per_round": 3,
                "max_implement_per_round": 1,
                "max_trellis_tasks_per_round": 5,
                "stop_after_code_change": True,
                "full_requires_explicit_confirmation": True,
            },
            "trellis_intake": {
                "enabled": True,
                "image_root": "system-cache",
                "create_parent_task_for_full": True,
                "leave_yunxiao_unchanged": True,
                "full_drain_until_no_creatable": True,
                "full_execute_after_intake": True,
                "writeback_after_task_done": True,
            },
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

    def test_invalid_runtime_limits_fail(self) -> None:
        payload = {
            "version": 1,
            "organization_id": "org-1",
            "project_id": "proj-1",
            "project_code": "DEMO",
            "statuses": [
                {"type": "Bug", "status": "待处理", "id": "1", "meaning": "unfinished"},
                {"type": "Bug", "status": "处理中", "id": "2", "meaning": "active"},
                {"type": "Bug", "status": "已关闭", "id": "3", "meaning": "terminal"},
            ],
            "runtime_limits": {
                "query_page_size": 0,
                "stop_after_code_change": "yes",
            },
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
        self.assertIn("runtime_limits.query_page_size", result.stdout)
        self.assertIn("runtime_limits.stop_after_code_change", result.stdout)

    def test_versioned_trellis_image_root_warns(self) -> None:
        payload = {
            "version": 1,
            "organization_id": "org-1",
            "project_id": "proj-1",
            "project_code": "DEMO",
            "statuses": [
                {"type": "Bug", "status": "待处理", "id": "1", "meaning": "unfinished"},
                {"type": "Bug", "status": "处理中", "id": "2", "meaning": "active"},
                {"type": "Bug", "status": "已关闭", "id": "3", "meaning": "terminal"},
            ],
            "trellis_intake": {
                "image_root": ".trellis/workspace/yunxiao-images",
            },
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
        self.assertIn("versioned Trellis paths", result.stdout)

    def test_project_relative_image_root_warns(self) -> None:
        payload = {
            "version": 1,
            "organization_id": "org-1",
            "project_id": "proj-1",
            "project_code": "DEMO",
            "statuses": [
                {"type": "Bug", "status": "待处理", "id": "1", "meaning": "unfinished"},
                {"type": "Bug", "status": "处理中", "id": "2", "meaning": "active"},
                {"type": "Bug", "status": "已关闭", "id": "3", "meaning": "terminal"},
            ],
            "trellis_intake": {
                "image_root": "yunxiao-images",
            },
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
        self.assertIn("project-relative path", result.stdout)


if __name__ == "__main__":
    unittest.main()
