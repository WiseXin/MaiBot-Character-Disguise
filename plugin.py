"""《麦麦的人类伪装计划》插件 (WiseXin.character-disguise)

核心特性：
1. 会话作用域智能感知与独立控制（群聊/私聊分别开闭、黑白名单）；
2. Planner / Replyer 阶段注入人类伪装法则（极短限长、彻底去句号、纯文本禁Markdown、做题家抑制、潜水许可）；
3. 后置硬规则守卫（剥除句末句号、清洗AI助手口癖、超长安全截断）；
4. 发送前拦截沉默意图（<silent> 物理已读不回/潜水）；
5. 模拟打字等待与多气泡断句陆续发送。
"""

from __future__ import annotations

import asyncio
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PLUGIN_DIR = Path(__file__).resolve().parent
PLUGIN_DIR_TEXT = str(PLUGIN_DIR)
if PLUGIN_DIR_TEXT not in sys.path:
    sys.path.insert(0, PLUGIN_DIR_TEXT)

from maibot_sdk import HomeCard, HookHandler, MaiBotPlugin
from maibot_sdk.types import ErrorPolicy, HookMode, HookOrder

from cleaner import TextCleaner
from config import CharacterDisguiseConfig
from prompt_builder import (
    PLANNER_MARKER,
    PROMPT_MARKER,
    build_group_prompt,
    build_planner_prompt,
    build_private_prompt,
)


class CharacterDisguisePlugin(MaiBotPlugin):
    config_model = CharacterDisguiseConfig

    def __init__(self) -> None:
        super().__init__()
        # 会话状态缓存：sid -> {chat_type, group_id, user_id, platform, updated_at}
        self._sessions: Dict[str, Dict[str, Any]] = {}

    async def on_load(self) -> None:
        """插件加载初始化"""
        cfg = self._config()
        self.info(
            f"[人类伪装计划] 麦麦的人类伪装计划已启动 (v1.0.0): "
            f"群聊={cfg.scope.enable_group} 私聊={cfg.scope.enable_private} "
            f"去句号={cfg.rules.strip_ending_periods} 限长={cfg.rules.group_max_chars}字"
        )

    async def on_unload(self) -> None:
        """插件卸载清理"""
        self._sessions.clear()
        self.info("[人类伪装计划] 麦麦的人类伪装计划已卸载")

    async def on_config_update(self, scope: str, config_data: dict, version: str) -> None:
        """热更新配置"""
        if scope == "self":
            cfg = self._config()
            self.info(
                f"[人类伪装计划] 配置已热更新: 群聊={cfg.scope.enable_group} 私聊={cfg.scope.enable_private}"
            )

    @property
    def logger(self):
        try:
            return getattr(self.ctx, "logger", None)
        except Exception:
            return None

    def debug(self, msg: str, *args):
        if self.logger:
            try:
                self.logger.debug(msg, *args)
            except Exception:
                pass

    def info(self, msg: str, *args):
        if self.logger:
            try:
                self.logger.info(msg, *args)
            except Exception:
                pass

    def warning(self, msg: str, *args):
        if self.logger:
            try:
                self.logger.warning(msg, *args)
            except Exception:
                pass

    # =========================================================================
    # 配置读取与会话判定
    # =========================================================================

    def _config(self) -> CharacterDisguiseConfig:
        if hasattr(self, "_test_config") and self._test_config is not None:
            return self._test_config
        try:
            config = self.config
            if isinstance(config, CharacterDisguiseConfig):
                return config
            if hasattr(config, "model_dump"):
                return CharacterDisguiseConfig(**config.model_dump())
            if isinstance(config, dict):
                return CharacterDisguiseConfig(**config)
        except Exception:
            pass
        return CharacterDisguiseConfig()

    def _get_session_info(self, sid: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """获取或启发式推断会话信息"""
        if sid and sid in self._sessions:
            return self._sessions[sid]

        # 启发式推断
        chat_type = "private"
        group_id = ""
        user_id = ""
        platform = str(kwargs.get("platform", "") or "")

        # 从 kwargs 推断
        if kwargs.get("is_group_chat") or kwargs.get("group_id"):
            chat_type = "group"
            group_id = str(kwargs.get("group_id", "") or "")
        else:
            mi = kwargs.get("message", {}) if isinstance(kwargs.get("message"), dict) else {}
            minfo = mi.get("message_info", {}) if isinstance(mi.get("message_info"), dict) else {}
            gi = minfo.get("group_info", {}) if isinstance(minfo.get("group_info"), dict) else {}
            ui = minfo.get("user_info", {}) if isinstance(minfo.get("user_info"), dict) else {}
            if gi.get("group_id") or mi.get("scope") == "group":
                chat_type = "group"
                group_id = str(gi.get("group_id", "") or "")
            if ui.get("user_id"):
                user_id = str(ui.get("user_id", "") or "")

        info = {
            "chat_type": chat_type,
            "group_id": group_id,
            "user_id": user_id,
            "platform": platform,
            "updated_at": time.time(),
        }
        if sid:
            self._sessions[sid] = info
        return info

    def _is_enabled_for_session(self, session_info: Dict[str, Any]) -> Tuple[bool, str]:
        """根据当前配置判定此会话是否启用伪装"""
        cfg = self._config()
        if not cfg.plugin.enabled:
            return False, "plugin_disabled"

        chat_type = session_info.get("chat_type", "group")
        group_id = str(session_info.get("group_id", "") or "")
        user_id = str(session_info.get("user_id", "") or "")

        if chat_type == "group":
            if not cfg.scope.enable_group:
                return False, "group_disabled"
            if cfg.scope.ignored_groups and group_id in cfg.scope.ignored_groups:
                return False, "group_in_ignored_list"
            if cfg.scope.target_groups and group_id not in cfg.scope.target_groups:
                return False, "group_not_in_target_list"
            return True, "group"
        else:
            if not cfg.scope.enable_private:
                return False, "private_disabled"
            if cfg.scope.ignored_users and user_id in cfg.scope.ignored_users:
                return False, "user_in_ignored_list"
            if cfg.scope.target_users and user_id not in cfg.scope.target_users:
                return False, "user_not_in_target_list"
            return True, "private"

    # =========================================================================
    # 钩子 1: 消息接收时捕获会话环境
    # =========================================================================

    @HookHandler(
        "chat.receive.after_process",
        name="character_disguise_capture_receive",
        description="Capture session_id, chat_type, group_id, user_id from incoming message.",
        mode=HookMode.BLOCKING,
        order=HookOrder.EARLY,
        error_policy=ErrorPolicy.SKIP,
    )
    async def capture_receive(self, message: Any = None, **kwargs: Any) -> Dict[str, Any]:
        if isinstance(message, dict):
            sid = str(message.get("session_id", "") or "")
            if not sid:
                mi = message.get("message_info", {}) or {}
                if isinstance(mi, dict):
                    ac = mi.get("additional_config", {}) or {}
                    if isinstance(ac, dict):
                        sid = str(ac.get("session_id", "") or ac.get("stream_id", "") or "")
            if sid:
                message_info = message.get("message_info", {}) or {}
                user_info = message_info.get("user_info", {}) or {}
                group_info = message_info.get("group_info", {}) or {}
                user_id = str(user_info.get("user_id", "") or "") if isinstance(user_info, dict) else ""
                group_id = str(group_info.get("group_id", "") or "") if isinstance(group_info, dict) else ""
                platform = str(message.get("platform", "") or "")
                chat_type = "group" if (group_id or message.get("scope") == "group") else "private"

                self._sessions[sid] = {
                    "chat_type": chat_type,
                    "group_id": group_id,
                    "user_id": user_id,
                    "platform": platform,
                    "updated_at": time.time(),
                }
                self.debug(f"[人类伪装计划] 捕获会话: sid={sid} type={chat_type} group={group_id} user={user_id}")

                # 检查群聊垃圾过滤：仅对群聊中的普通群友生效，主人绝不受限
                cfg = self._config()
                if cfg.plugin.enabled and chat_type == "group" and cfg.rules.filter_group_bot_noise:
                    text_content = str(message.get("processed_plain_text", "") or "")
                    if not text_content:
                        raw_msg = message.get("raw_message")
                        if isinstance(raw_msg, list):
                            parts = []
                            for p in raw_msg:
                                if isinstance(p, dict) and p.get("type") == "text":
                                    pd = p.get("data")
                                    if isinstance(pd, dict):
                                        parts.append(str(pd.get("text", "")))
                                    elif isinstance(pd, str):
                                        parts.append(pd)
                            text_content = "".join(parts)

                    is_blocked, reason = TextCleaner.is_toxic_or_bot_noise(
                        text_content,
                        user_id=user_id,
                        master_users=cfg.rules.master_users,
                        mute_keywords=getattr(cfg.rules, "mute_keywords", None),
                    )
                    if is_blocked:
                        nickname = str(user_info.get("user_nickname", "") or user_info.get("user_name", "") or "")
                        self.info(
                            f"[人类伪装计划] 🛡️ 静默拦截群友({user_id}|{nickname})的垃圾刷屏/恶意注入消息: "
                            f"'{text_content[:60]}' (原因: {reason})，不予入库与送入模型"
                        )
                        return {"action": "abort"}
        return {"action": "continue"}

    # =========================================================================
    # 钩子 2: Planner 阶段提示词注入
    # =========================================================================

    @HookHandler(
        "maisaka.planner.before_request",
        name="character_disguise_planner_prompt",
        description="Inject compact disguise rules into Planner messages.",
        mode=HookMode.BLOCKING,
        order=HookOrder.NORMAL,
        error_policy=ErrorPolicy.SKIP,
    )
    async def handle_planner_prompt(self, **kwargs: Any) -> Dict[str, Any]:
        cfg = self._config()
        if not cfg.plugin.enabled:
            return {"action": "continue"}

        sid = str(kwargs.get("session_id", "") or kwargs.get("stream_id", "") or "")
        session_info = self._get_session_info(sid, kwargs)
        enabled, mode = self._is_enabled_for_session(session_info)
        if not enabled:
            return {"action": "continue"}

        is_group = session_info.get("chat_type") == "group"
        max_chars = cfg.rules.group_max_chars if is_group else cfg.rules.private_max_chars
        prompt = build_planner_prompt(is_group, max_chars)

        modified: Dict[str, Any] = {}
        # 针对 v1.2.x+ items 载荷注入
        raw_items = kwargs.get("items")
        if isinstance(raw_items, list):
            items = self._inject_items(raw_items, prompt, PLANNER_MARKER)
            if items is not None:
                modified["items"] = items

        # 针对旧版 messages 载荷兼容
        raw_msgs = kwargs.get("messages")
        if isinstance(raw_msgs, list):
            messages = self._inject_messages(raw_msgs, prompt, PLANNER_MARKER)
            if messages is not None:
                modified["messages"] = messages

        if modified:
            merged = dict(kwargs)
            merged.update(modified)
            return {"action": "continue", "modified_kwargs": merged}
        return {"action": "continue"}

    # =========================================================================
    # 钩子 3: Replyer 阶段提示词注入 (before_request + before_model_request)
    # =========================================================================

    @HookHandler(
        "maisaka.replyer.before_request",
        name="character_disguise_replyer_prompt",
        description="Inject disguise extra prompt before replyer builds request.",
        mode=HookMode.BLOCKING,
        order=HookOrder.NORMAL,
        error_policy=ErrorPolicy.SKIP,
    )
    async def handle_replyer_before_request(self, **kwargs: Any) -> Dict[str, Any]:
        cfg = self._config()
        if not cfg.plugin.enabled:
            return {"action": "continue"}

        sid = str(kwargs.get("session_id", "") or kwargs.get("stream_id", "") or "")
        session_info = self._get_session_info(sid, kwargs)
        enabled, mode = self._is_enabled_for_session(session_info)
        if not enabled:
            return {"action": "continue"}

        is_group = session_info.get("chat_type") == "group"
        prompt = (
            build_group_prompt(cfg.rules.group_max_chars)
            if is_group
            else build_private_prompt(cfg.rules.private_max_chars)
        )

        extra = kwargs.get("extra_prompt", "")
        if isinstance(extra, str):
            modified = dict(kwargs)
            modified["extra_prompt"] = f"{extra}\n\n{prompt}".strip() if extra.strip() else prompt
            return {"action": "continue", "modified_kwargs": modified}
        return {"action": "continue"}

    @HookHandler(
        "maisaka.replyer.before_model_request",
        name="character_disguise_replyer_model_prompt",
        description="Inject disguise constraints into final replyer system items.",
        mode=HookMode.BLOCKING,
        order=HookOrder.NORMAL,
        error_policy=ErrorPolicy.SKIP,
    )
    async def handle_replyer_before_model(self, **kwargs: Any) -> Dict[str, Any]:
        cfg = self._config()
        if not cfg.plugin.enabled:
            return {"action": "continue"}

        sid = str(kwargs.get("session_id", "") or kwargs.get("stream_id", "") or "")
        session_info = self._get_session_info(sid, kwargs)
        enabled, mode = self._is_enabled_for_session(session_info)
        if not enabled:
            return {"action": "continue"}

        is_group = session_info.get("chat_type") == "group"
        prompt = (
            build_group_prompt(cfg.rules.group_max_chars)
            if is_group
            else build_private_prompt(cfg.rules.private_max_chars)
        )

        modified: Dict[str, Any] = {}
        raw_items = kwargs.get("items")
        if isinstance(raw_items, list):
            items = self._inject_items(raw_items, prompt, PROMPT_MARKER)
            if items is not None:
                modified["items"] = items

        raw_msgs = kwargs.get("messages")
        if isinstance(raw_msgs, list):
            messages = self._inject_messages(raw_msgs, prompt, PROMPT_MARKER)
            if messages is not None:
                modified["messages"] = messages

        if modified:
            merged = dict(kwargs)
            merged.update(modified)
            return {"action": "continue", "modified_kwargs": merged}
        return {"action": "continue"}

    # =========================================================================
    # 钩子 4: Replyer 响应后置硬规则守卫 (去句号/清洗AI口癖/限长)
    # =========================================================================

    @HookHandler(
        "maisaka.replyer.after_response",
        name="character_disguise_reply_guard",
        description="Clean AI tropes, strip ending periods, enforce casual chat rules.",
        mode=HookMode.BLOCKING,
        order=HookOrder.NORMAL,
        error_policy=ErrorPolicy.SKIP,
    )
    async def handle_replyer_after_response(self, **kwargs: Any) -> Dict[str, Any]:
        cfg = self._config()
        if not cfg.plugin.enabled:
            return {"action": "continue"}

        sid = str(kwargs.get("session_id", "") or kwargs.get("stream_id", "") or "")
        session_info = self._get_session_info(sid, kwargs)
        enabled, mode = self._is_enabled_for_session(session_info)
        if not enabled:
            return {"action": "continue"}

        path, raw_text = self._find_reply_text(kwargs)
        if not raw_text:
            return {"action": "continue"}

        is_group = session_info.get("chat_type") == "group"
        cleaned_text, bubbles, changed, is_silent = TextCleaner.clean(
            raw_text,
            is_group=is_group,
            group_max_chars=cfg.rules.group_max_chars,
            private_max_chars=cfg.rules.private_max_chars,
            hard_max_chars=cfg.rules.hard_max_chars,
            strip_ending_periods=cfg.rules.strip_ending_periods,
            strip_markdown=cfg.rules.strip_markdown,
            clean_ai_tropes=cfg.rules.clean_ai_tropes,
            allow_silent=cfg.rules.allow_silent_reaction,
        )

        # 若判定为潜水，保留 <silent> 供 before_send 统一拦截
        final_text = "<silent>" if is_silent else cleaned_text

        if changed or is_silent:
            if cfg.logging.enabled and cfg.logging.log_rewrites:
                self.info(
                    f"[人类伪装计划] 回复净化 ({'群聊' if is_group else '私聊'}): 原文='{raw_text}' -> 处理后='{final_text}'"
                )

            modified = dict(kwargs)
            target = modified
            for key in path[:-1]:
                target[key] = dict(target.get(key, {}))
                target = target[key]
            target[path[-1]] = final_text
            return {"action": "continue", "modified_kwargs": modified}
        return {"action": "continue"}

    # =========================================================================
    # 钩子 5: 发送服务前置守卫 (物理潜水拦截 / 打字等待 / 气泡拆分)
    # =========================================================================

    @HookHandler(
        "send_service.before_send",
        name="character_disguise_before_send",
        description="Filter silence, strip trailing periods, simulate typing wait, split bubbles.",
        mode=HookMode.BLOCKING,
        order=HookOrder.LATE,
        error_policy=ErrorPolicy.SKIP,
    )
    async def handle_before_send(self, **kwargs: Any) -> Dict[str, Any]:
        cfg = self._config()
        if not cfg.plugin.enabled:
            return {"action": "continue"}

        message = kwargs.get("message")
        if not isinstance(message, dict):
            return {"action": "continue"}

        sid = str(message.get("session_id", "") or "")
        session_info = self._get_session_info(sid, kwargs)
        enabled, mode = self._is_enabled_for_session(session_info)
        if not enabled:
            return {"action": "continue"}

        is_group = session_info.get("chat_type") == "group"

        # 提取当前待发文本中的所有 text 组件
        raw_msg = message.get("raw_message")
        has_text_segment = False
        text_parts = []
        if isinstance(raw_msg, list):
            for part in raw_msg:
                if isinstance(part, dict) and part.get("type") == "text":
                    has_text_segment = True
                    part_data = part.get("data")
                    if isinstance(part_data, dict):
                        text_parts.append(str(part_data.get("text", "")))
                    elif isinstance(part_data, str):
                        text_parts.append(part_data)
                    elif "text" in part:
                        text_parts.append(str(part.get("text", "")))
        text_from_raw = "".join(text_parts)

        plain_text = str(message.get("processed_plain_text", "") or "")
        text = text_from_raw if has_text_segment else plain_text

        # 核心防护：如果不含任何 text 段且无有效纯文本（纯图片、纯表情、语音、合并转发、戳一戳等），直接放行
        if not has_text_segment and not text.strip():
            return {"action": "continue"}

        # 0. 上游大模型安全策略 / 敏感词拦截报错检查：静默拦截掐死，避免在聊天中暴露
        if cfg.rules.block_model_safety_errors and TextCleaner.is_model_safety_error(text):
            self.warning(
                f"[人类伪装计划] 🛑 捕获到模型生成的平台安全/敏感词报错: '{text[:80]}'，已静默拦截掐死，避免在群聊中暴露！"
            )
            return {"action": "abort"}

        # 1. 沉默潜水检查：仅在存在文本且包含显式沉默标记时，才在物理发出前 abort
        if cfg.rules.allow_silent_reaction and TextCleaner.is_silent(text):
            self.info(
                f"[人类伪装计划] 会话 {sid} ({'群聊' if is_group else '私聊'}) 命中显式沉默潜水标记，取消本次消息发送"
            )
            return {"action": "abort"}

        modified_kwargs = dict(kwargs)
        mutated_message = dict(message)
        changed = False

        # 2. 模拟打字等待
        if cfg.simulation.simulate_typing:
            modified_kwargs["typing"] = True

        # 3. 多气泡拆分支持
        bubbles = TextCleaner.extract_bubbles(text)
        if cfg.simulation.split_bubbles and len(bubbles) > 1:
            first_bubble = bubbles[0]
            text = first_bubble
            changed = True
            # 后续气泡异步依次发送
            remaining_bubbles = bubbles[1:]
            asyncio.create_task(
                self._send_followup_bubbles(
                    remaining_bubbles,
                    sid,
                    cfg.simulation.bubble_delay_min,
                    cfg.simulation.bubble_delay_max,
                )
            )

        # 4. 彻底去句号化（做底线防御）
        if cfg.rules.strip_ending_periods and text:
            cleaned_text = TextCleaner.strip_periods(text)
            if cleaned_text != text:
                text = cleaned_text
                changed = True

        if changed:
            mutated_message["processed_plain_text"] = text
            if isinstance(raw_msg, list):
                new_raw = []
                replaced = False
                for part in raw_msg:
                    if isinstance(part, dict) and part.get("type") == "text":
                        if not replaced:
                            new_part = dict(part)
                            part_data = part.get("data")
                            if isinstance(part_data, dict):
                                new_data = dict(part_data)
                                new_data["text"] = text
                                new_part["data"] = new_data
                            elif isinstance(part_data, str):
                                new_part["data"] = text
                            else:
                                new_part["data"] = {"text": text}
                            if "text" in new_part:
                                new_part["text"] = text
                            new_raw.append(new_part)
                            replaced = True
                        else:
                            continue
                    else:
                        new_raw.append(part)
                mutated_message["raw_message"] = new_raw
            modified_kwargs["message"] = mutated_message

        return {"action": "continue", "modified_kwargs": modified_kwargs}

    # =========================================================================
    # 异步多气泡分段发送辅助任务
    # =========================================================================

    async def _send_followup_bubbles(
        self, bubbles: List[str], session_id: str, delay_min: float, delay_max: float
    ) -> None:
        """模拟真人群聊打字停顿，陆续发送后续气泡"""
        for bubble in bubbles:
            clean_b = TextCleaner.strip_periods(bubble) if bubble else ""
            if not clean_b or TextCleaner.is_silent(clean_b):
                continue
            delay = random.uniform(delay_min, delay_max)
            await asyncio.sleep(delay)
            try:
                if hasattr(self.ctx, "send") and hasattr(self.ctx.send, "text"):
                    await self.ctx.send.text(clean_b, session_id)
                    self.debug(f"[人类伪装计划] 多气泡后续消息已发送: sid={session_id} text={clean_b}")
            except Exception as exc:
                self.warning(f"[人类伪装计划] 多气泡后续消息发送失败: {exc}")

    # =========================================================================
    # 内部工具函数
    # =========================================================================

    def _find_reply_text(self, data: Dict[str, Any]) -> Tuple[List[Any], str]:
        direct_keys = ("response", "reply", "content", "text", "message", "result")
        for key in direct_keys:
            value = data.get(key)
            if isinstance(value, str):
                return [key], value
            if isinstance(value, dict):
                nested_path, nested_text = self._find_reply_text(value)
                if nested_text:
                    return [key, *nested_path], nested_text
        return [], ""

    def _inject_items(self, items: List[Any], prompt: str, marker: str) -> Optional[List[Dict[str, Any]]]:
        if not isinstance(items, list):
            return None
        updated: List[Dict[str, Any]] = []
        injected = False
        for item in items:
            if not injected and isinstance(item, dict) and item.get("item_type") == "SystemMessageItem":
                parts = item.get("parts")
                if isinstance(parts, list):
                    texts = [
                        str(part.get("text", ""))
                        for part in parts
                        if isinstance(part, dict) and str(part.get("type", "")).lower() == "text"
                    ]
                    if any(marker in text for text in texts):
                        injected = True
                    else:
                        item = dict(item)
                        item["parts"] = [*parts, {"type": "text", "text": prompt}]
                        injected = True
            updated.append(item)
        if not injected:
            updated.insert(
                0,
                {
                    "item_type": "SystemMessageItem",
                    "meta": {
                        "item_id": uuid.uuid4().hex,
                        "logical_turn_id": None,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    "parts": [{"type": "text", "text": prompt}],
                },
            )
        return updated

    def _inject_messages(self, messages: List[Any], prompt: str, marker: str) -> Optional[List[Dict[str, Any]]]:
        if not isinstance(messages, list):
            return None
        updated: List[Dict[str, Any]] = []
        inserted = False
        for item in messages:
            if not isinstance(item, dict):
                updated.append(item)
                continue
            msg = dict(item)
            role = str(msg.get("role") or "").lower()
            content = str(msg.get("content") or msg.get("content_text") or "")
            if role == "system" and not inserted:
                if marker not in content:
                    msg["content"] = f"{content.rstrip()}\n\n{prompt}" if content.strip() else prompt
                    msg["content_text"] = msg["content"]
                inserted = True
            updated.append(msg)
        if not inserted:
            updated.insert(0, {"role": "system", "content": prompt, "content_text": prompt})
        return updated

    # =========================================================================
    # WebUI 仪表盘卡片
    # =========================================================================

    @HomeCard(
        "character_disguise",
        "麦麦的人类伪装计划",
        content=(
            "告别做题家说教与客服腔，粉碎 AI 味！\n\n"
            "✨ 彻底去句号 | 极短随性断句 | 纯文本零Markdown | 抑制做题家科普 | 允许空回复潜水"
        ),
        icon="user-check",
        order=35,
    )
    async def handle_home_card(self, **kwargs: Any) -> Dict[str, Any]:
        cfg = self._config()
        group_status = "已开启" if cfg.scope.enable_group else "已关闭"
        private_status = "已开启" if cfg.scope.enable_private else "已关闭"
        return {
            "title": "麦麦的人类伪装计划",
            "content": f"群聊伪装: {group_status} | 私聊拟人: {private_status}\n字数限制: 群聊 ≤{cfg.rules.group_max_chars}字 / 私聊 ≤{cfg.rules.private_max_chars}字\n去句号: {'开启' if cfg.rules.strip_ending_periods else '关闭'} | 潜水拦截: {'开启' if cfg.rules.allow_silent_reaction else '关闭'}",
        }


def create_plugin() -> CharacterDisguisePlugin:
    """工厂函数：MaiBot 实例化入口"""
    return CharacterDisguisePlugin()
