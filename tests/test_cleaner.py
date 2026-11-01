"""Cleaner 模块完整单元测试"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from cleaner import TextCleaner


class TestTextCleaner(unittest.TestCase):
    def test_silence_detection(self):
        # 显式沉默标记必须为 True
        self.assertTrue(TextCleaner.is_silent("<silent>"))
        self.assertTrue(TextCleaner.is_silent("<silent/>"))
        self.assertTrue(TextCleaner.is_silent("<SILENT>"))
        self.assertTrue(TextCleaner.is_silent("  <silent>  "))
        self.assertTrue(TextCleaner.is_silent("<message></message>"))
        self.assertTrue(TextCleaner.is_silent("[silent]"))
        self.assertTrue(TextCleaner.is_silent("（沉默）"))
        self.assertTrue(TextCleaner.is_silent("（潜水）"))
        # 空文本与纯空白绝不能误判为沉默（避免误伤图片等非文本消息）
        self.assertFalse(TextCleaner.is_silent(""))
        self.assertFalse(TextCleaner.is_silent("   "))
        self.assertFalse(TextCleaner.is_silent("我在玩生化危机"))

    def test_strip_markdown(self):
        raw = "**生化危机4**重制版是神作，# 推荐指数：\n- 画面棒\n- 动作流畅"
        cleaned = TextCleaner.strip_markdown(raw)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("#", cleaned)
        self.assertNotIn("- ", cleaned)
        self.assertIn("生化危机4重制版是神作", cleaned)

    def test_clean_ai_tropes(self):
        self.assertEqual(TextCleaner.clean_ai_tropes("好的，这关先去拿钥匙。"), "这关先去拿钥匙。")
        self.assertEqual(TextCleaner.clean_ai_tropes("明白啦！马上就去"), "马上就去")
        self.assertEqual(
            TextCleaner.clean_ai_tropes("作为一个单机玩家，我觉得挺难的，希望能帮到你！"),
            "我觉得挺难的",
        )
        self.assertEqual(
            TextCleaner.clean_ai_tropes("很高兴为你解答，这个 boss 弱火。"),
            "这个 boss 弱火。",
        )

    def test_strip_periods(self):
        self.assertEqual(TextCleaner.strip_periods("这关先去拿钥匙。"), "这关先去拿钥匙")
        self.assertEqual(TextCleaner.strip_periods("不知道啊...。"), "不知道啊...")
        self.assertEqual(TextCleaner.strip_periods("好耶！！！"), "好耶！！！")
        self.assertEqual(TextCleaner.strip_periods("今天好累。不想动。"), "今天好累 不想动")

    def test_truncate_smart(self):
        long_text = "生化危机4重制版真的太好玩了，里昂和碍事梨的互动特别有意思，尤其是城堡那段解谜！"
        truncated = TextCleaner.truncate_smart(long_text, 25)
        self.assertLessEqual(len(truncated), 25)
        self.assertTrue(truncated.endswith("特别有意思") or truncated.endswith("好玩了"))

    def test_extract_bubbles(self):
        raw = "<message>第一句</message><message>第二句</message>"
        bubbles = TextCleaner.extract_bubbles(raw)
        self.assertEqual(bubbles, ["第一句", "第二句"])

    def test_overall_clean(self):
        raw = "好的，**生化危机4**重制版真的很好玩。希望能帮到你！"
        cleaned, bubbles, changed, is_silent = TextCleaner.clean(
            raw, is_group=True, group_max_chars=30
        )
        self.assertFalse(is_silent)
        self.assertTrue(changed)
        self.assertNotIn("好的", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("希望能帮到你", cleaned)
        self.assertFalse(cleaned.endswith("。"))

    def test_multibubble_preservation(self):
        """测试多气泡在 clean 后正确保留 <message> 结构以便传递给 before_send"""
        raw = "<message>第一句好难。</message><message>第二句再试试。</message>"
        cleaned, bubbles, changed, is_silent = TextCleaner.clean(
            raw, is_group=True, group_max_chars=30
        )
        self.assertFalse(is_silent)
        self.assertTrue(changed)
        self.assertEqual(bubbles, ["第一句好难", "第二句再试试"])
        self.assertEqual(cleaned, "<message>第一句好难</message><message>第二句再试试</message>")

    def test_empty_input_not_silent(self):
        """测试空输入不误标为沉默"""
        cleaned, bubbles, changed, is_silent = TextCleaner.clean("", is_group=True)
        self.assertFalse(is_silent)
        self.assertEqual(cleaned, "")
        self.assertEqual(bubbles, [])


if __name__ == "__main__":
    unittest.main()
