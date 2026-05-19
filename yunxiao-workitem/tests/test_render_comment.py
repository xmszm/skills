import subprocess
import sys
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


if __name__ == "__main__":
    unittest.main()

