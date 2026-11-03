"""《麦麦的人类伪装计划》配置模型 (符合 MaiBot SDK 2.x 规范)

支持在 WebUI 中通过 json_schema_extra 渲染中文标签 (label)、输入框提示 (placeholder) 与通俗中文提示 (hint)。
支持群聊与私聊独立控制、黑白名单、彻底去句号、限长与做题家抑制。
"""

from __future__ import annotations

from typing import ClassVar, List
from maibot_sdk import Field, PluginConfigBase


class PluginSection(PluginConfigBase):
    """插件基础信息与全局开关"""

    __ui_label__: ClassVar[str] = "基础配置"
    __ui_icon__: ClassVar[str] = "package"
    __ui_order__: ClassVar[int] = 0

    name: str = Field(
        default="character_disguise",
        description="插件英文标识",
        json_schema_extra={
            "label": "插件标识",
            "hint": "插件内部唯一标识",
        },
    )
    version: str = Field(
        default="1.0.3",
        description="插件版本",
        json_schema_extra={
            "label": "插件版本",
            "hint": "当前安装的插件代码版本",
        },
    )
    config_version: str = Field(
        default="1.0.3",
        description="配置结构版本",
        json_schema_extra={
            "label": "配置版本",
            "hint": "用于配置结构升级与兼容性校验",
        },
    )
    enabled: bool = Field(
        default=True,
        description="是否启用人类伪装计划",
        json_schema_extra={
            "label": "启用伪装计划",
            "hint": "开启后，本插件的去 AI 味与真实聊天仿真规则将生效",
        },
    )


class ScopeSection(PluginConfigBase):
    """生效会话与作用域控制"""

    __ui_label__: ClassVar[str] = "生效范围"
    __ui_icon__: ClassVar[str] = "users"
    __ui_order__: ClassVar[int] = 1

    enable_group: bool = Field(
        default=True,
        description="是否在 QQ 群聊中启用真人群友伪装",
        json_schema_extra={
            "label": "群聊伪装生效",
            "hint": "开启后，群聊将应用极短回复、彻底去句号、做题家抑制等真实群友习惯",
        },
    )
    enable_private: bool = Field(
        default=True,
        description="是否在私聊中启用拟人化交流",
        json_schema_extra={
            "label": "私聊伪装生效",
            "hint": "开启后，私聊也会遵循自然朋友聊天节奏，去除 AI 客服腔调",
        },
    )
    target_groups: List[str] = Field(
        default_factory=list,
        description="指定生效群号列表，留空表示对所有群生效",
        json_schema_extra={
            "label": "生效群白名单",
            "placeholder": "例如 [\"12345678\"]，留空为全部群生效",
            "hint": "若只想在某几个群测试体验，可在此填入群号；留空则对所有群生效",
        },
    )
    ignored_groups: List[str] = Field(
        default_factory=list,
        description="忽略群号列表（黑名单）",
        json_schema_extra={
            "label": "群黑名单",
            "placeholder": "例如 [\"87654321\"]",
            "hint": "在此列表中的群聊将完全不应用本插件的伪装规则",
        },
    )
    target_users: List[str] = Field(
        default_factory=list,
        description="指定生效私聊用户 QQ 号列表，留空表示对所有用户生效",
        json_schema_extra={
            "label": "私聊白名单",
            "placeholder": "例如 [\"12345678\"]，留空为全部私聊生效",
            "hint": "仅在私聊生效时过滤用户；留空表示对所有私聊好友生效",
        },
    )
    ignored_users: List[str] = Field(
        default_factory=list,
        description="忽略私聊用户列表（黑名单）",
        json_schema_extra={
            "label": "私聊黑名单",
            "placeholder": "例如 [\"111222333\"]",
            "hint": "在此列表中的私聊用户不会被伪装规则拦截或处理",
        },
    )


class RulesSection(PluginConfigBase):
    """人类拟真交流规范与硬规则守卫"""

    __ui_label__: ClassVar[str] = "伪装规则"
    __ui_icon__: ClassVar[str] = "sparkles"
    __ui_order__: ClassVar[int] = 2

    group_max_chars: int = Field(
        default=30,
        description="群聊建议最大字数（字）",
        json_schema_extra={
            "label": "群聊字数限制",
            "hint": "群聊单条发言建议上限，通常 15~30 字最像真人水群，强力抑制长篇小作文",
        },
    )
    private_max_chars: int = Field(
        default=60,
        description="私聊建议最大字数（字）",
        json_schema_extra={
            "label": "私聊字数限制",
            "hint": "私聊单条回复建议上限，默认 60 字，保持朋友随意畅谈感",
        },
    )
    hard_max_chars: int = Field(
        default=150,
        description="硬截断字数上限（字）",
        json_schema_extra={
            "label": "硬截断安全上限",
            "hint": "后置守卫安全红线：大模型若偶发输出失控的长文，将在此平滑截断，防止刷屏",
        },
    )
    strip_ending_periods: bool = Field(
        default=True,
        description="彻底去句号化（剥除末尾句号 。与 .）",
        json_schema_extra={
            "label": "彻底去句号",
            "hint": "真人打字极少以句号结尾。开启后自动剥除结尾句号，句中连续句号自动转为空格",
        },
    )
    strip_markdown: bool = Field(
        default=True,
        description="去除 Markdown 格式符号",
        json_schema_extra={
            "label": "纯文本净化",
            "hint": "自动清理粗体 **、标题 #、列表 - 等 Markdown 标记，让输出如手机打字般纯粹",
        },
    )
    clean_ai_tropes: bool = Field(
        default=True,
        description="清洗典型 AI 助手口癖",
        json_schema_extra={
            "label": "清洗 AI 口癖",
            "hint": "自动过滤“好的”、“希望对你有所帮助”、“作为一个单机玩家...”等机械式客套套话",
        },
    )
    suppress_know_it_all: bool = Field(
        default=True,
        description="抑制做题家模式（群聊禁止主动科普）",
        json_schema_extra={
            "label": "抑制好为人师",
            "hint": "在提示词中强力告诫：没人明确 @ 或提问时，绝不对截图、表情包或他人算式做题解答",
        },
    )
    allow_silent_reaction: bool = Field(
        default=True,
        description="允许沉默潜水（空回复拦截）",
        json_schema_extra={
            "label": "允许空回复潜水",
            "hint": "当模型输出 <silent> 或无话可说时，在发送前直接取消该消息，保持真实群友的潜水习惯",
        },
    )
    master_users: List[str] = Field(
        default_factory=list,
        description="主人账号白名单列表（支持 QQ 号或用户 ID）。此列表内的账号发送任何消息均不予拦截",
        json_schema_extra={
            "label": "主人账号白名单",
            "hint": "填入主人 QQ 或平台用户 ID。主人账号发送的指令与消息享有最高豁免权，绝不被拦截",
        },
    )
    filter_group_bot_noise: bool = Field(
        default=True,
        description="是否屏蔽群聊中第三方机器人系统报错刷屏与恶意代码注入（绝不拦截正常插件指令）",
        json_schema_extra={
            "label": "过滤机器人刷屏与恶意注入",
            "hint": "开启后，群内第三方机器人的系统报错刷屏、SQL注入代码将被直接屏蔽不进模型；正常插件指令（如 /dr、/help 等）不受任何影响，安全放行",
        },
    )
    block_model_safety_errors: bool = Field(
        default=True,
        description="是否在出站端拦截大模型安全报错（如 Google Policy 提示）",
        json_schema_extra={
            "label": "拦截大模型安全报错",
            "hint": "当模型因群友话题敏感触发 Google/平台安全策略返回英文报错时，静默拦截不发到聊天中",
        },
    )
    mute_keywords: List[str] = Field(
        default_factory=lambda: ["闭嘴", "闭麦", "别叫了", "别吵了", "给爷爬", "快闭嘴", "烦死了"],
        description="禁言与闭嘴触发词列表。群聊中命中此列表中词汇的消息将被底层直接拦截静默，绝不接嘴",
        json_schema_extra={
            "label": "闭嘴禁言词列表",
            "placeholder": "例如 [\"闭嘴\", \"闭麦\", \"别叫了\", \"别吵了\"]",
            "hint": "物理静默机制：群友发火或叫闭嘴时，底层直接丢弃消息，防止模型跳出来阴阳怪气",
        },
    )


class SimulationSection(PluginConfigBase):
    """物理行为仿真（打字状态与多气泡）"""

    __ui_label__: ClassVar[str] = "行为仿真"
    __ui_icon__: ClassVar[str] = "clock"
    __ui_order__: ClassVar[int] = 3

    simulate_typing: bool = Field(
        default=True,
        description="是否在发送前模拟打字耗时延迟",
        json_schema_extra={
            "label": "模拟打字耗时",
            "hint": "在后台模拟打字输入耗时，更贴合真人聊天节奏",
        },
    )
    split_bubbles: bool = Field(
        default=True,
        description="是否支持多气泡分段发送",
        json_schema_extra={
            "label": "多气泡分段",
            "hint": "识别 <message> 标签或长内容分段，拆为多条短消息陆续发出，模拟真实发微信/QQ节奏",
        },
    )
    bubble_delay_min: float = Field(
        default=0.8,
        description="气泡最小间隔延迟（秒）",
        json_schema_extra={
            "label": "气泡最小延迟",
            "hint": "多气泡依次发送时的随机等待下限",
        },
    )
    bubble_delay_max: float = Field(
        default=1.6,
        description="气泡最大间隔延迟（秒）",
        json_schema_extra={
            "label": "气泡最大延迟",
            "hint": "多气泡依次发送时的随机等待上限",
        },
    )


class LoggingSection(PluginConfigBase):
    """日志与审计"""

    __ui_label__: ClassVar[str] = "日志设置"
    __ui_icon__: ClassVar[str] = "file-text"
    __ui_order__: ClassVar[int] = 4

    enabled: bool = Field(
        default=True,
        description="是否记录伪装处理日志",
        json_schema_extra={
            "label": "启用日志",
            "hint": "在控制台输出命中过滤、去句号和防刷屏处理明细",
        },
    )
    log_rewrites: bool = Field(
        default=True,
        description="是否详细记录改写前后的文本对比",
        json_schema_extra={
            "label": "记录改写对比",
            "hint": "在日志中打印被剥离的句号、清洗的 AI 口癖和截断详情",
        },
    )


class CharacterDisguiseConfig(PluginConfigBase):
    """麦麦的人类伪装计划总配置模型"""

    plugin: PluginSection = Field(default_factory=PluginSection)
    scope: ScopeSection = Field(default_factory=ScopeSection)
    rules: RulesSection = Field(default_factory=RulesSection)
    simulation: SimulationSection = Field(default_factory=SimulationSection)
    logging: LoggingSection = Field(default_factory=LoggingSection)
