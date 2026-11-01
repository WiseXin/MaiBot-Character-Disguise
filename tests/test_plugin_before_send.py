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
from plugin import CharacterDisguisePlugin


class TestBeforeSendHook(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.plugin = CharacterDisguisePlugin()
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


if __name__ == "__main__":
    unittest.main()
