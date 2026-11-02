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

    def test_model_safety_error_detection(self):
        """测试上游大模型安全策略报错识别"""
        err1 = "The prompt could not be submitted. The prompt contains sensitive words that violate Google's Prohibited Use policy."
        err2 = "The prompt could not be submitted. The"
        err3 = "Try rephrasing the prompt."
        err4 = "violates safety policy and guidelines"
        normal = "今天单机游戏真好玩，生化危机通关了"
        self.assertTrue(TextCleaner.is_model_safety_error(err1))
        self.assertTrue(TextCleaner.is_model_safety_error(err2))
        self.assertTrue(TextCleaner.is_model_safety_error(err3))
        self.assertTrue(TextCleaner.is_model_safety_error(err4))
        self.assertFalse(TextCleaner.is_model_safety_error(normal))
        self.assertFalse(TextCleaner.is_model_safety_error(""))

    def test_toxic_and_bot_noise_filtering(self):
        """测试机器人指令、系统报错刷屏与注入过滤（主人豁免与防日常误杀）"""
        master_users = ["10001"]
        master_id = "10001"
        other_user = "20002"

        # 1. 主人发送指令：在配置名单中时放行；若未配置或清空则不设特殊豁免
        is_blocked, _ = TextCleaner.is_toxic_or_bot_noise("/reset", master_id, master_users)
        self.assertFalse(is_blocked)
        is_blocked, _ = TextCleaner.is_toxic_or_bot_noise("/status", master_id, master_users)
        self.assertFalse(is_blocked)
        is_blocked, _ = TextCleaner.is_toxic_or_bot_noise("/reset", master_id, [])
        self.assertTrue(is_blocked, "若配置名单为空，则尊重配置不设豁免")

        # 2. 群友发送机器人指令：精准拦截
        is_blocked, reason = TextCleaner.is_toxic_or_bot_noise("/reset", other_user, master_users)
        self.assertTrue(is_blocked)
        self.assertEqual(reason, "bot_command")

        is_blocked, reason = TextCleaner.is_toxic_or_bot_noise("/play 稻香", other_user, master_users)
        self.assertTrue(is_blocked)
        self.assertEqual(reason, "bot_command")

        is_blocked, reason = TextCleaner.is_toxic_or_bot_noise("!roll 100", other_user, master_users)
        self.assertTrue(is_blocked)
        self.assertEqual(reason, "bot_command")

        is_blocked, reason = TextCleaner.is_toxic_or_bot_noise(".help", other_user, master_users)
        self.assertTrue(is_blocked)
        self.assertEqual(reason, "bot_command")

        is_blocked, reason = TextCleaner.is_toxic_or_bot_noise("/签到", other_user, master_users)
        self.assertTrue(is_blocked)
        self.assertEqual(reason, "bot_command")

        # 3. 关键防误杀验证：群友正常日常水群交流必须 100% 放行！
        normal_cases = [
            ("！这也太离谱了吧", "中文全角感叹号开头表达震惊"),
            ("！卧槽", "短感叹"),
            ("、我觉得还行吧", "中文顿号开头"),
            ("#原神 今天抽到纳西妲了吗", "带话题标签的日常讨论"),
            ("You can select an option from the menu", "正常英文对话（包含 select 与 from）"),
            ("今天心情不错\n-- 小明", "带署名的换行文本"),
            ("老师今天讲了如何 drop table", "日常技术课业交流"),
            ("// 这是一行代码注释", "双斜杠注释文本"),
            ("...无语了", "省略号开头"),
            ("今天天气真好", "普通短句"),
        ]
        for text, desc in normal_cases:
            is_blocked, r = TextCleaner.is_toxic_or_bot_noise(text, other_user, master_users)
            self.assertFalse(is_blocked, f"正常交流内容不应被误杀: '{text}' ({desc}), 误报原因: {r}")

        # 4. 机器人系统报错与状态刷屏：拦截
        spam1 = "您(ID: 20002)的权限不足以使用此指令。通过 /sid 获取 ID 并请管理员添加。"
        is_blocked, reason = TextCleaner.is_toxic_or_bot_noise(spam1, other_user, master_users)
        self.assertTrue(is_blocked)
        self.assertEqual(reason, "bot_spam")

        spam2 = "Reset command requires admin permission in 群聊+会话隔离关闭 scenario"
        is_blocked, reason = TextCleaner.is_toxic_or_bot_noise(spam2, other_user, master_users)
        self.assertTrue(is_blocked)
        self.assertEqual(reason, "bot_spam")

        # 5. SQL 注入与恶意代码载荷：精准拦截
        inject_cases = [
            "Domain' OR '1'='1' --",
            "admin' or 1=1 --",
            "1' union select 1,2,3 --",
            "1; drop table users;",
            "<script>alert(1)</script>",
        ]
        for inj in inject_cases:
            is_blocked, reason = TextCleaner.is_toxic_or_bot_noise(inj, other_user, master_users)
            self.assertTrue(is_blocked, f"恶意攻击载荷必须被拦截: '{inj}'")
            self.assertEqual(reason, "code_injection")

        # 6. 禁言/闭嘴词拦截：精准拦截（物理静默机制）
        mute_cases = [
            "@小蓝 你妈的闭嘴",
            "人机全部闭嘴",
            "闭麦吧你",
            "别叫了烦死了",
            "快闭嘴行不行",
        ]
        for mute_text in mute_cases:
            is_blocked, reason = TextCleaner.is_toxic_or_bot_noise(mute_text, other_user, master_users)
            self.assertTrue(is_blocked, f"闭嘴禁言词必须被拦截: '{mute_text}'")
            self.assertEqual(reason, "mute_keyword")


if __name__ == "__main__":
    unittest.main()
