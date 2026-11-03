"""配置模型单元测试"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import maibot_sdk
except ImportError:
    from unittest.mock import MagicMock
    from pydantic import BaseModel, Field

    mock_sdk = MagicMock()
    mock_sdk.PluginConfigBase = BaseModel
    mock_sdk.Field = Field
    mock_sdk.MaiBotPlugin = type("MaiBotPlugin", (), {})
    mock_sdk.HomeCard = lambda *args, **kwargs: (lambda f: f)
    mock_sdk.HookHandler = lambda *args, **kwargs: (lambda f: f)
    mock_types = MagicMock()
    mock_types.HookMode = MagicMock()
    mock_types.HookOrder = MagicMock()
    mock_types.ErrorPolicy = MagicMock()
    mock_sdk.types = mock_types
    sys.modules["maibot_sdk"] = mock_sdk
    sys.modules["maibot_sdk.types"] = mock_types

import unittest
from config import CharacterDisguiseConfig


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = CharacterDisguiseConfig()
        self.assertTrue(cfg.plugin.enabled)
        self.assertEqual(cfg.plugin.config_version, "1.0.3")
        self.assertEqual(cfg.plugin.version, "1.0.3")
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
        self.assertEqual(cfg.rules.master_users, [])
        self.assertTrue(cfg.rules.filter_group_bot_noise)
        self.assertTrue(cfg.rules.block_model_safety_errors)
        self.assertTrue(cfg.simulation.simulate_typing)
        self.assertTrue(cfg.simulation.split_bubbles)


if __name__ == "__main__":
    unittest.main()
