"""配置模型单元测试"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from config import CharacterDisguiseConfig


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = CharacterDisguiseConfig()
        self.assertTrue(cfg.plugin.enabled)
        self.assertEqual(cfg.plugin.config_version, "1.0.0")
        self.assertEqual(cfg.plugin.version, "1.0.0")
        self.assertEqual(cfg.plugin.name, "character_disguise")
        self.assertTrue(cfg.scope.enable_group)
        self.assertTrue(cfg.scope.enable_private)
        self.assertEqual(cfg.rules.group_max_chars, 30)
        self.assertEqual(cfg.rules.private_max_chars, 60)
        self.assertEqual(cfg.rules.hard_max_chars, 150)
        self.assertTrue(cfg.rules.strip_ending_periods)
        self.assertTrue(cfg.rules.strip_markdown)
        self.assertTrue(cfg.rules.clean_ai_tropes)
        self.assertTrue(cfg.rules.suppress_know_it_all)
        self.assertTrue(cfg.rules.allow_silent_reaction)
        self.assertTrue(cfg.simulation.simulate_typing)
        self.assertTrue(cfg.simulation.split_bubbles)


if __name__ == "__main__":
    unittest.main()
