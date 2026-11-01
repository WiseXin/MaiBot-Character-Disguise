"""before_send 钩子防御性回归测试

重点测试：
1. 纯图片、表情包、语音、合并转发等非文本消息绝不被误判沉默而丢弃（返回 continue）；
2. 显式沉默标记 (<silent>) 准确拦截丢弃（返回 abort）；
3. 普通文本消息正常去句号；
4. 多气泡消息准确提取首气泡并放行。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import unittest
from config import CharacterDisguiseConfig
from plugin import CharacterDisguisePlugin


class TestBeforeSendHook(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.plugin = CharacterDisguisePlugin()
        self.plugin._test_config = CharacterDisguiseConfig()
        # 模拟插件已载入
        self.plugin._sessions["test_group_session"] = {
            "chat_type": "group",
            "group_id": "123456",
            "user_id": "789",
            "platform": "qq",
        }

    async def test_pure_image_message_never_aborted(self):
        """测试纯图片消息绝对不被 abort 丢弃"""
        msg = {
            "session_id": "test_group_session",
            "message_id": "msg_img_1",
            "processed_plain_text": "",
            "raw_message": [
                {"type": "image", "data": {"file": "https://example.com/art.png"}}
            ],
        }
        res = await self.plugin.handle_before_send(message=msg)
        self.assertEqual(res.get("action"), "continue", "纯图片消息必须直接放行，不可 abort")

    async def test_pure_record_voice_message_never_aborted(self):
        """测试纯语音消息绝对不被 abort 丢弃"""
        msg = {
            "session_id": "test_group_session",
            "message_id": "msg_voice_1",
            "processed_plain_text": "",
            "raw_message": [
                {"type": "record", "data": {"file": "test.silk"}}
            ],
        }
        res = await self.plugin.handle_before_send(message=msg)
        self.assertEqual(res.get("action"), "continue", "纯语音消息必须直接放行")

    async def test_empty_nontext_message_never_aborted(self):
        """测试没有任何 text 段的空内容消息直接放行"""
        msg = {
            "session_id": "test_group_session",
            "message_id": "msg_empty_1",
            "processed_plain_text": "",
            "raw_message": [],
        }
        res = await self.plugin.handle_before_send(message=msg)
        self.assertEqual(res.get("action"), "continue")

    async def test_explicit_silent_text_is_aborted(self):
        """测试显式包含 <silent> 的文本消息被 abort 拦截"""
        msg = {
            "session_id": "test_group_session",
            "message_id": "msg_silent_1",
            "processed_plain_text": "<silent>",
            "raw_message": [
                {"type": "text", "data": {"text": "<silent>"}}
            ],
        }
        res = await self.plugin.handle_before_send(message=msg)
        self.assertEqual(res.get("action"), "abort", "显式 <silent> 必须触发 abort 潜水")

    async def test_normal_text_strips_period(self):
        """测试正常文本消息剥除末尾句号"""
        msg = {
            "session_id": "test_group_session",
            "message_id": "msg_text_1",
            "processed_plain_text": "今天去打生化危机。",
            "raw_message": [
                {"type": "text", "data": {"text": "今天去打生化危机。"}}
            ],
        }
        res = await self.plugin.handle_before_send(message=msg)
        self.assertEqual(res.get("action"), "continue")
        modified_msg = res.get("modified_kwargs", {}).get("message", {})
        self.assertEqual(modified_msg.get("processed_plain_text"), "今天去打生化危机")
        self.assertEqual(
            modified_msg.get("raw_message", [])[0]["data"]["text"], "今天去打生化危机"
        )

    async def test_string_data_part_does_not_crash(self):
        """测试当 raw_message 中 part['data'] 为字符串时不会 AttributeError"""
        msg = {
            "session_id": "test_group_session",
            "message_id": "msg_str_data_1",
            "processed_plain_text": "开一把游戏吧。",
            "raw_message": [
                {"type": "text", "data": "开一把游戏吧。"}
            ],
        }
        res = await self.plugin.handle_before_send(message=msg)
        self.assertEqual(res.get("action"), "continue")
        modified_msg = res.get("modified_kwargs", {}).get("message", {})
        self.assertEqual(modified_msg.get("processed_plain_text"), "开一把游戏吧")

    async def test_flat_text_part_does_not_crash(self):
        """测试当 raw_message 中 part 直接包含 text 字段时的处理"""
        msg = {
            "session_id": "test_group_session",
            "message_id": "msg_flat_1",
            "processed_plain_text": "今天天气真好。",
            "raw_message": [
                {"type": "text", "text": "今天天气真好。"}
            ],
        }
        res = await self.plugin.handle_before_send(message=msg)
        self.assertEqual(res.get("action"), "continue")
        modified_msg = res.get("modified_kwargs", {}).get("message", {})
        self.assertEqual(modified_msg.get("processed_plain_text"), "今天天气真好")
        self.assertEqual(modified_msg.get("raw_message", [])[0].get("text"), "今天天气真好")

    async def test_video_and_gif_messages_safely_passed(self):
        """测试视频(video)、GIF动图(image)与动态表情(mface/face)绝对安全放行"""
        # 1. 纯视频消息
        msg_video = {
            "session_id": "test_group_session",
            "message_id": "msg_video_1",
            "processed_plain_text": "",
            "raw_message": [{"type": "video", "data": {"file": "short_clip.mp4"}}],
        }
        res_v = await self.plugin.handle_before_send(message=msg_video)
        self.assertEqual(res_v.get("action"), "continue", "纯视频消息必须直接放行")

        # 2. 纯 GIF 动图消息
        msg_gif = {
            "session_id": "test_group_session",
            "message_id": "msg_gif_1",
            "processed_plain_text": "",
            "raw_message": [{"type": "image", "data": {"file": "funny_meme.gif", "subType": 1}}],
        }
        res_g = await self.plugin.handle_before_send(message=msg_gif)
        self.assertEqual(res_g.get("action"), "continue", "纯 GIF 动图必须直接放行")

        # 3. 动态商城表情 (mface) 与 QQ 原生表情 (face)
        msg_mface = {
            "session_id": "test_group_session",
            "message_id": "msg_mface_1",
            "processed_plain_text": "",
            "raw_message": [{"type": "mface", "data": {"id": "12345"}}],
        }
        res_mf = await self.plugin.handle_before_send(message=msg_mface)
        self.assertEqual(res_mf.get("action"), "continue", "动态表情必须直接放行")

        # 4. 视频/GIF 带文案混排消息
        msg_mixed = {
            "session_id": "test_group_session",
            "message_id": "msg_mixed_1",
            "processed_plain_text": "这个搞笑动图笑死我了。",
            "raw_message": [
                {"type": "image", "data": {"file": "laugh.gif"}},
                {"type": "text", "data": {"text": "这个搞笑动图笑死我了。"}}
            ],
        }
        res_m = await self.plugin.handle_before_send(message=msg_mixed)
        self.assertEqual(res_m.get("action"), "continue", "图文/视文混排必须正常放行")
        new_raw = res_m.get("modified_kwargs", {}).get("message", {}).get("raw_message", [])
        self.assertEqual(len(new_raw), 2)
        self.assertEqual(new_raw[0]["type"], "image")
        self.assertEqual(new_raw[1]["data"]["text"], "这个搞笑动图笑死我了")

    async def test_capture_receive_blocks_bot_commands_for_normal_users_but_allows_master(self):
        """测试入站拦截：群友发机器人指令/报错直接 abort 拦截，主人不受任何限制，正常交流不误杀"""
        self.plugin._test_config.rules.master_users = ["10001"]

        # 1. 普通群友发 /reset 指令 -> 必须被 abort 拦截，不进入后续链路
        msg_group_user = {
            "session_id": "test_group_sid_1",
            "scope": "group",
            "message_info": {
                "group_info": {"group_id": "1014708337"},
                "user_info": {"user_id": "20002", "user_nickname": "普通群友"},
            },
            "processed_plain_text": "/reset",
        }
        res1 = await self.plugin.capture_receive(message=msg_group_user)
        self.assertEqual(res1.get("action"), "abort", "普通群友发送的机器人指令必须被静默拦截 abort")

        # 2. 主人发 /reset 指令 -> 必须 continue 放行
        msg_group_master = {
            "session_id": "test_group_sid_2",
            "scope": "group",
            "message_info": {
                "group_info": {"group_id": "1014708337"},
                "user_info": {"user_id": "10001", "user_nickname": "老大"},
            },
            "processed_plain_text": "/reset",
        }
        res2 = await self.plugin.capture_receive(message=msg_group_master)
        self.assertEqual(res2.get("action"), "continue", "主人发送的指令绝不受限，必须放行 continue")

        # 3. 普通群友发送正常日常交流（中文感叹句、正常英文句子） -> 必须 100% 放行 continue，绝不误杀！
        msg_normal_exclaim = {
            "session_id": "test_group_sid_normal_1",
            "scope": "group",
            "message_info": {
                "group_info": {"group_id": "1014708337"},
                "user_info": {"user_id": "20002", "user_nickname": "普通群友"},
            },
            "processed_plain_text": "！这也太离谱了吧",
        }
        res_norm1 = await self.plugin.capture_receive(message=msg_normal_exclaim)
        self.assertEqual(res_norm1.get("action"), "continue", "日常中文感叹句绝不能被误杀")

        msg_normal_en = {
            "session_id": "test_group_sid_normal_2",
            "scope": "group",
            "message_info": {
                "group_info": {"group_id": "1014708337"},
                "user_info": {"user_id": "20002", "user_nickname": "普通群友"},
            },
            "processed_plain_text": "You can select an option from the menu",
        }
        res_norm2 = await self.plugin.capture_receive(message=msg_normal_en)
        self.assertEqual(res_norm2.get("action"), "continue", "正常英文对话（含 select/from）绝不能被误杀为 SQL 注入")

        # 4. 普通群友发送 SQL 注入攻击代码 -> 必须被 abort 拦截
        msg_group_inject = {
            "session_id": "test_group_sid_3",
            "scope": "group",
            "message_info": {
                "group_info": {"group_id": "1014708337"},
                "user_info": {"user_id": "1284219057", "user_nickname": "Hacker"},
            },
            "processed_plain_text": "Domain' OR '1'='1' --",
        }
        res3 = await self.plugin.capture_receive(message=msg_group_inject)
        self.assertEqual(res3.get("action"), "abort", "群友发送的代码注入攻击必须被 abort 拦截")

    async def test_before_send_aborts_model_safety_errors(self):
        """测试出站拦截：捕获到模型输出包含 Google 安全策略报错时静默掐死"""
        error_msg = {
            "session_id": "test_group_session",
            "message_id": "msg_err_1",
            "processed_plain_text": "The prompt could not be submitted. The prompt contains sensitive words that violate Google's Prohibited Use policy.",
            "raw_message": [
                {"type": "text", "data": {"text": "The prompt could not be submitted. The prompt contains sensitive words that violate Google's Prohibited Use policy."}}
            ],
        }
        res = await self.plugin.handle_before_send(message=error_msg)
        self.assertEqual(res.get("action"), "abort", "大模型安全策略报错必须被出站拦截 abort，防止露馅")


if __name__ == "__main__":
    unittest.main()
