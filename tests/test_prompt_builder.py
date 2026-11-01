"""提示词构建器单元测试"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from prompt_builder import (
    PLANNER_MARKER,
    PROMPT_MARKER,
    build_group_prompt,
    build_planner_prompt,
    build_private_prompt,
)


class TestPromptBuilder(unittest.TestCase):
    def test_group_prompt(self):
        p = build_group_prompt(25)
        self.assertIn(PROMPT_MARKER, p)
        self.assertIn("群聊·人类伪装法则", p)
        self.assertIn("25", p)
        self.assertIn("做题家抑制", p)
        self.assertIn("<silent>", p)

    def test_private_prompt(self):
        p = build_private_prompt(50)
        self.assertIn(PROMPT_MARKER, p)
        self.assertIn("私聊·人类伪装法则", p)
        self.assertIn("50", p)

    def test_planner_prompt(self):
        p_group = build_planner_prompt(True, 30)
        self.assertIn(PLANNER_MARKER, p_group)
        self.assertIn("QQ群聊水群", p_group)

        p_private = build_planner_prompt(False, 60)
        self.assertIn(PLANNER_MARKER, p_private)
        self.assertIn("私聊好友日常交流", p_private)


if __name__ == "__main__":
    unittest.main()
