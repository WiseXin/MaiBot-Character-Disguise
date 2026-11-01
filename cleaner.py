"""文本净化与仿真守卫模块 (Cleaner)

负责彻底去除 AI 味：
1. 识别沉默标签 (<silent>)，支持物理已读不回；
2. 彻底去句号化（句末绝无句号，句中句号转为空格）；
3. 剥离 Markdown 符号（粗体、列表、标题、代码块）；
4. 清洗典型 AI 助手口癖（好的、希望能帮到你、作为一个...）；
5. 长度安全截断与气泡提取。
"""

from __future__ import annotations

import re
from typing import List, Tuple


class TextCleaner:
    # 沉默/潜水标记
    SILENT_PATTERNS = [
        re.compile(r"<\s*silent\s*/?\s*>", re.IGNORECASE),
        re.compile(r"<\s*message\s*>\s*<\s*/\s*message\s*>", re.IGNORECASE),
        re.compile(r"^\[silent\]$", re.IGNORECASE),
        re.compile(r"^\(silent\)$", re.IGNORECASE),
        re.compile(r"^（沉默）$"),
        re.compile(r"^（潜水）$"),
    ]

    # AI 助手开头口癖
    AI_LEADING_PATTERNS = [
        re.compile(r"^(好的|好的呢|明白啦|了解啦|收到)[，,！!~ ]*", re.IGNORECASE),
        re.compile(r"^(作为|作为一个)[^，,。！？\n]{1,20}[，,]", re.IGNORECASE),
        re.compile(r"^(很高兴为你解答|关于这个问题|我来给你(解答|分析|说明)一下)[，,：:\s]*", re.IGNORECASE),
    ]

    # AI 助手结尾客套
    AI_TRAILING_PATTERNS = [
        re.compile(
            r"[，, ]*(希望(能|可以|对你)?(有(所)?)?帮(助|到)(你)?|有什么问题随时问我|祝你游戏愉快|祝你玩得开心|祝你生活愉快)[！!。.~]*$",
            re.IGNORECASE,
        ),
    ]

    # 上游大模型安全策略 / 敏感词拦截报错
    MODEL_SAFETY_ERROR_PATTERNS = [
        re.compile(r"the prompt could not be submitted", re.IGNORECASE),
        re.compile(r"prohibited use policy", re.IGNORECASE),
        re.compile(r"contains sensitive words that violate", re.IGNORECASE),
        re.compile(r"violate[s]? Google's", re.IGNORECASE),
        re.compile(r"generative ai prohibited use", re.IGNORECASE),
        re.compile(r"try rephrasing the prompt", re.IGNORECASE),
        re.compile(r"safety policy", re.IGNORECASE),
        re.compile(r"violate[s]? safety guidelines", re.IGNORECASE),
    ]

    # 机器人指令前缀（群友给机器人发指令时使用）
    BOT_COMMAND_PREFIXES = ("/", "#", "$", "!", "！", "、")

    # 机器人系统报错、状态打卡与刷屏套话
    BOT_SPAM_PATTERNS = [
        re.compile(r"权限不足以使用此指令"),
        re.compile(r"管理命令仅管理员可用"),
        re.compile(r"reset command requires admin permission", re.IGNORECASE),
        re.compile(r"运行中\s*={4,}status={4,}", re.IGNORECASE),
        re.compile(r"【.*?服务器机器人.*?状态报告.*?】"),
        re.compile(r"已恢复出厂默认的.*?人设规则"),
        re.compile(r"再发#napcat刷屏永久拉黑"),
        re.compile(r"Cookie\s*有效\s*\(UID:"),
    ]

    # SQL 注入与代码漏洞攻击载荷
    CODE_INJECTION_PATTERNS = [
        re.compile(r"'\s*or\s*'1'\s*=\s*'1", re.IGNORECASE),
        re.compile(r"'\s*or\s*1\s*=\s*1", re.IGNORECASE),
        re.compile(r"--\s*$", re.MULTILINE),
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        re.compile(r"\bselect\s+.*\bfrom\b", re.IGNORECASE),
    ]

    @classmethod
    def is_silent(cls, text: str) -> bool:
        """判断是否属于显式沉默/潜水意图（仅命中显式沉默标签才为 True，空文本不误判）"""
        if not text:
            return False
        s = text.strip()
        if not s:
            return False
        for pattern in cls.SILENT_PATTERNS:
            if pattern.search(s):
                return True
        return False

    @classmethod
    def is_model_safety_error(cls, text: str) -> bool:
        """检查文本是否属于大模型上游安全/敏感词拦截报错（如 Google Policy 提示）"""
        if not text:
            return False
        for pat in cls.MODEL_SAFETY_ERROR_PATTERNS:
            if pat.search(text):
                return True
        return False

    @classmethod
    def is_toxic_or_bot_noise(
        cls,
        text: str,
        user_id: str,
        master_users: List[str] | None = None,
    ) -> Tuple[bool, str]:
        """检查群消息是否属于群友发送的机器人指令、垃圾刷屏或代码注入

        Returns:
            (is_blocked, reason)
        """
        # 1. 主人白名单豁免：完全遵照用户配置的 master_users
        valid_masters = {str(u).strip() for u in (master_users or []) if u and str(u).strip()}

        uid = str(user_id).strip()
        if uid in valid_masters:
            return False, ""

        if not text:
            return False, ""

        s = text.strip()

        # 2. 机器人指令前缀检查
        # 排除单个标点符号或纯省略号 "..."
        if s.startswith(cls.BOT_COMMAND_PREFIXES):
            return True, "bot_command"
        if s.startswith(".") and len(s) > 1 and not s.startswith("..") and not s[1].isdigit():
            return True, "bot_command"

        # 3. 机器人系统报错/状态刷屏套话检查
        for pat in cls.BOT_SPAM_PATTERNS:
            if pat.search(s):
                return True, "bot_spam"

        # 4. 代码注入攻击与恶意载荷检查
        for pat in cls.CODE_INJECTION_PATTERNS:
            if pat.search(s):
                return True, "code_injection"

        return False, ""

    @classmethod
    def strip_markdown(cls, text: str) -> str:
        """剥离 Markdown 粗体、标题、列表等标记，回归纯文本交流"""
        t = text
        # 粗体与斜体
        t = re.sub(r"\*\*\*(.*?)\*\*\*", r"\1", t)
        t = re.sub(r"\*\*(.*?)\*\*", r"\1", t)
        t = re.sub(r"\*(.*?)\*", r"\1", t)
        t = re.sub(r"~~(.*?)~~", r"\1", t)
        # 代码块与行内代码
        t = re.sub(r"```[\w]*\n(.*?)```", r"\1", t, flags=re.DOTALL)
        t = re.sub(r"`([^`]+)`", r"\1", t)
        # 标题 #
        t = re.sub(r"#+\s*", "", t)
        # 无序列表与有序列表
        t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.MULTILINE)
        t = re.sub(r"^\s*\d+\.\s+", "", t, flags=re.MULTILINE)
        # 引用块 >
        t = re.sub(r"^\s*>\s*", "", t, flags=re.MULTILINE)
        return t

    @classmethod
    def clean_ai_tropes(cls, text: str) -> str:
        """清洗典型 AI 开头与结尾客套"""
        t = text.strip()
        for pat in cls.AI_LEADING_PATTERNS:
            t = pat.sub("", t).strip()
        for pat in cls.AI_TRAILING_PATTERNS:
            t = pat.sub("", t).strip()
        return t

    @classmethod
    def strip_periods(cls, text: str) -> str:
        """彻底去句号化：剥除句末句号，句中连续句号转为空格（保留省略号 ...）"""
        t = text.strip()
        # 剥除末尾全部连续的中文句号
        t = re.sub(r"。+$", "", t).strip()
        # 剥除末尾非省略号的英文单/双句点
        if not t.endswith("..."):
            t = re.sub(r"(?<!\.)\.{1,2}$", "", t).strip()
        # 句中出现的句号转为空格（符合手机输入法换行/打字习惯）
        t = re.sub(r"。", " ", t)
        # 去除多余连续空格，但保留单空格
        t = re.sub(r" {2,}", " ", t)
        return t.strip()

    @classmethod
    def truncate_smart(cls, text: str, max_chars: int) -> str:
        """智能限长截断：优先在标点或空格处截断，避免截半句话"""
        if len(text) <= max_chars:
            return text

        candidate = text[:max_chars]
        # 寻找最近的断句标点（逗号、感叹号、问号、空格、换行、波浪号）
        break_marks = "，, ！!？?~～ \n；;、"
        last_break = -1
        for mark in break_marks:
            pos = candidate.rfind(mark)
            if pos > last_break:
                last_break = pos

        # 只要断句点在长度的 55% 之后，就在此处截断
        if last_break >= int(max_chars * 0.55):
            truncated = candidate[:last_break]
        else:
            truncated = candidate

        # 剥除截断后可能残留的逗号或不完整标点
        truncated = re.sub(r"[，,、；; \-]+$", "", truncated).strip()
        return truncated

    @classmethod
    def extract_bubbles(cls, text: str) -> List[str]:
        """提取多气泡消息：若包含 <message> 标签则提取，否则返回单条"""
        msg_pattern = re.compile(r"<\s*message\s*>(.*?)<\s*/\s*message\s*>", re.DOTALL | re.IGNORECASE)
        matches = msg_pattern.findall(text)
        if matches:
            bubbles = [m.strip() for m in matches if m.strip()]
            if bubbles:
                return bubbles
        return [text.strip()] if text.strip() else []

    @classmethod
    def clean(
        cls,
        raw_text: str,
        is_group: bool,
        group_max_chars: int = 30,
        private_max_chars: int = 60,
        hard_max_chars: int = 150,
        strip_ending_periods: bool = True,
        strip_markdown: bool = True,
        clean_ai_tropes: bool = True,
        allow_silent: bool = True,
    ) -> Tuple[str, List[str], bool, bool]:
        """综合处理文本入口

        Returns:
            (cleaned_text, list_of_bubbles, is_changed, is_silent)
        """
        original = raw_text or ""
        trimmed = original.strip()

        # 1. 如果输入本身就是空文本，直接返回，不误标为沉默
        if not trimmed:
            return "", [], False, False

        # 2. 检查是否显式沉默
        if allow_silent and cls.is_silent(trimmed):
            return "", [], True, True

        # 3. 检查多气泡
        bubbles = cls.extract_bubbles(trimmed)
        is_multi = len(bubbles) > 1

        cleaned_bubbles: List[str] = []
        target_max = group_max_chars if is_group else private_max_chars

        for bubble in (bubbles if is_multi else [trimmed]):
            b = bubble
            if strip_markdown:
                b = cls.strip_markdown(b)
            if clean_ai_tropes:
                b = cls.clean_ai_tropes(b)
            if strip_ending_periods:
                b = cls.strip_periods(b)
            # 硬限制截断
            if len(b) > hard_max_chars:
                b = cls.truncate_smart(b, hard_max_chars)
            b = b.strip()
            if b and not cls.is_silent(b):
                cleaned_bubbles.append(b)

        if not cleaned_bubbles:
            return "", [], True, True

        if len(cleaned_bubbles) > 1:
            # 多气泡场景：保留 <message> 标签传递给 send_service 陆续发送
            combined_text = "".join(f"<message>{b}</message>" for b in cleaned_bubbles)
            return combined_text, cleaned_bubbles, True, False

        primary_text = cleaned_bubbles[0]
        # 如果不是多气泡，且单条依然超出建议长度过大，做温和修剪
        if not is_multi and len(primary_text) > target_max * 1.5:
            primary_text = cls.truncate_smart(primary_text, int(target_max * 1.5))
            if strip_ending_periods:
                primary_text = cls.strip_periods(primary_text)
            cleaned_bubbles = [primary_text]

        changed = (primary_text != original.strip()) or is_multi
        return primary_text, cleaned_bubbles, changed, False
