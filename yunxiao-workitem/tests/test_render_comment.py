import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_comment.py"


class RenderCommentTests(unittest.TestCase):
    def run_script(self, *args: str) -> str:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def test_done_comment_contains_core_fields(self) -> None:
        output = self.run_script(
            "done",
            "--set",
            "project=后台",
            "--set",
            "trigger_path=后台 > 知识详情",
            "--list",
            "changes=修复跳转",
            "--set",
            "verification_result=已验证",
        )
        self.assertIn("AI: 已处理", output)
        self.assertIn("项目：后台", output)
        self.assertIn("路径：后台 > 知识详情", output)
        self.assertIn("- 修复跳转", output)
        self.assertIn("核验：已验证", output)

    def test_backend_gap_uses_plain_owner_fallback(self) -> None:
        output = self.run_script(
            "backend-gap",
            "--set",
            "backend_owner=陈聪",
            "--set",
            "work_item_key=DEMO-1",
        )
        self.assertIn("@陈聪 DEMO-1 需要后端补一下。", output)

    def test_backend_gap_uses_rich_mention_html(self) -> None:
        mention = (
            '<span class="sc-jJcwTH fUUHak"><span data-cangjie-key="1666" '
            'id="683db1680b1caf2a4e33da0a" data-type="mention" '
            'class="sc-cPyLVi jAgzPW">@陈聪</span></span>'
        )
        output = self.run_script(
            "backend-gap",
            "--set",
            f"backend_owner_mention_html={mention}",
            "--set",
            "work_item_key=DEMO-1",
        )
        self.assertIn(f"{mention} DEMO-1 需要后端补一下。", output)

    def test_backend_gap_builds_structured_rich_mention(self) -> None:
        config = {
            "backend_owner_mention": {
                "name": "陈聪",
                "id": "683db1680b1caf2a4e33da0a",
                "data_cangjie_key": "1666",
            },
            "work_item_key": "DEMO-1",
        }
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump(config, handle, ensure_ascii=False)
            config_path = handle.name

        try:
            output = self.run_script("backend-gap", "--config", config_path)
        finally:
            Path(config_path).unlink(missing_ok=True)

        self.assertIn('data-cangjie-key="1666"', output)
        self.assertIn('id="683db1680b1caf2a4e33da0a"', output)
        self.assertIn('data-type="mention"', output)
        self.assertIn("@陈聪</span></span> DEMO-1 需要后端补一下。", output)


if __name__ == "__main__":
    unittest.main()

