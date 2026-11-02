# 🎭 MaiBot Character Disguise (`WiseXin.character-disguise`)

> **"A true chatting pro never acts like a know-it-all."**  
> Say goodbye to preachiness, pedantic know-it-all answers, and robotic customer-service tones!  
> A native humanlike behavioral enhancement plugin for MaiBot designed to eliminate "AI vibes" and bring genuine conversational breathing room, social chill, and authentic human chatting soul.

---

## 💥 Common AI Chatting Blunders

- 📉 **The Know-It-All Reflex**: A group member shares a game screenshot or casual complaint, and the bot immediately outputs a 300-word academic analysis and walkthrough... killing the room instantly.
- 📏 **Period Obsession**: Every single casual message ends with a strict period `.` or `。`, looking like a formal corporate report.
- 🤖 **Eager Service Drone**: People are bantering or joking, yet the bot responds: *"Certainly! I am happy to assist you..."*
- 📜 **Essay Bombing**: Someone typed three words, but the bot returns paragraphs of bold markdown `**`, numbered lists, and headers.

**MaiBot Character Disguise** solves these issues across three solid defensive lines: **Prompt Engineering**, **Replyer Output Guard**, and **SendService Interception**.

---

## 🌟 Key Features

### 1. 🙅‍♀️ The Period Crusher
- Ruthlessly strips trailing periods (`。` and `.`) from casual replies.
- Preserves natural emotional marks (`~`, `?`, `!`, `...`).
- Converts in-sentence periods into spaces, mimicking natural mobile keypad typing.

### 2. 📱 Mobile Chat Flow (No Long Essays)
- **Group chats**: Strict brevity (suggested 10 ~ 30 characters), quick and casual.
- **Private chats**: Relaxed conversational replies (suggested 20 ~ 60 characters).
- **Safety cutoff**: Hard truncation at 150 characters to prevent runaway LLM outputs.

### 3. 💬 Prioritize Quoting Non-Latest Messages (Contextual Continuity)
- **Say goodbye to disjointed group messages!** In fast-paced group chats, if the target message was already buried under multiple subsequent messages, replying without quoting feels jarring and disconnected.
- The prompt strongly instructs the model to **prefer quote replies (reply quotes)** when responding to non-latest messages, keeping conversation threads clean and natural just like real people do.

### 4. 🤐 Social Relaxation (Graceful Lurking)
- Real humans do not reply to everything! If a message is hard to follow, awkward, or boring, the bot outputs `<silent>`.
- The plugin intercepts `<silent>` before transmission and silently discards it, achieving genuine "seen but didn't reply / lurking" behavior.

### 5. 🚫 Suppress Know-It-All Syndrome & Query Triage
- Enforces an unbendable rule: unless explicitly mentioned or directly asked, **never offer unsolicited tutorials or explanations** for random screenshots, memes, or chat math.
- **Smart Query Triage**:
  - Direct simple questions: short, casual answers without lecturing or step-by-step numbered guides.
  - Provocative test problems, complex exams, or spam: react casually with question marks, say you don't know, or simply output `<silent>` to stay quiet.

### 6. 🤫 Physical Mute & "Shut Up" Guard
- In group chats, members may occasionally vent or jokingly tell bots to "shut up" (*"闭嘴"*, *"别叫了"*, *"烦死了"*).
- Traditional AI tends to defensively argue back, escalating awkwardness.
- This plugin intercepts matching mute keywords at the inbound layer and drops the message entirely, letting the bot gracefully stay quiet without aggravating anyone.

### 7. 🛡️ Inbound Bot Noise Filtering & Outbound Safety Shield
- **Inbound Filter**: Intercepts external CLI bot commands (`/play`, `/help`), third-party bot status spam, and SQL injection payloads from regular members; master accounts (`master_users`) are exempt.
- **Outbound Safety Shield**: Catches and aborts upstream LLM policy errors (e.g., Google Prohibited Use policy rejections) before sending, preventing AI infrastructure details from leaking into the chat.

### 8. 🧼 Plaintext Cleanliness
- Strips markdown formatting (`**`, `#`, `- `, code blocks).
- Cleans typical AI clichés (*"Certainly"*, *"Hope this helps"*, *"As an AI..."*).
- Prevents repetitive catchphrases and forced memes.

### 9. 🫧 Multi-Bubble Sequential Dispatch
- Recognizes `<message>` tags or multi-part thoughts, sending them as sequential bubbles with natural slight delays.

### 10. 🎭 Fully Decoupled Character Identity
- All behavioral guidelines focus strictly on universal human typing and chatting etiquette, without hardcoded character names or traits.
- Seamlessly fits any custom persona you define in MaiBot (tsundere girl, calm detective, cheerful companion, etc.).

### 11. 🎛️ Dual-Scope Independent Control
- Group chat disguise and private chat humanization can be toggled independently.
- Supports group and user whitelists and blacklists.
- Full WebUI visual card support with instant hot-reload (no restart required).

---

## ⚙️ Configuration (`config.toml.example`)

```toml
[plugin]
name = "character_disguise"
version = "1.0.1"
config_version = "1.0.1"
enabled = true

[scope]
enable_group = true      # Enable disguise in group chats
enable_private = true    # Enable humanlike tone in private chats
target_groups = []       # Whitelist of groups (empty = all)
ignored_groups = []      # Blacklist of groups
target_users = []        # Whitelist of private users (empty = all)
ignored_users = []       # Blacklist of private users

[rules]
group_max_chars = 30     # Suggested max characters for group replies
private_max_chars = 60   # Suggested max characters for private replies
hard_max_chars = 150     # Hard safety cutoff limit
strip_ending_periods = true
strip_markdown = true
clean_ai_tropes = true
suppress_know_it_all = true
allow_silent_reaction = true
# Whitelist of master accounts (exempt from all command / noise filters)
master_users = []
# Filter out external bot commands, spam, and injection attempts from regular members
filter_group_bot_noise = true
# Intercept upstream LLM safety/policy errors before sending to chat
block_model_safety_errors = true
# Mute keywords: when matched, the bot drops the message immediately and stays quiet
mute_keywords = ["闭嘴", "闭麦", "别叫了", "别吵了", "给爷爬", "快闭嘴", "烦死了"]

[simulation]
simulate_typing = true   # Simulate background typing delay
split_bubbles = true     # Split into multiple sequential bubbles
bubble_delay_min = 0.8
bubble_delay_max = 1.6

[logging]
enabled = true
log_rewrites = true
```

---

## 🛠️ Complete Defense Pipeline

```
[Inbound Group/Private Message]
        │
        ├─►【Frontline Guard: Inbound Filtering (chat.receive)】
        │     ├─ External CLI bot commands (/play, /help) ──► Silently abort
        │     ├─ Third-party bot status spam / errors ──────► Silently abort
        │     ├─ Physical mute keywords ("闭嘴", "烦死了") ───► Silently abort
        │     └─ Malicious SQL injection payloads ───────────► Silently abort
        │     (Master accounts in master_users are always passed through)
        ▼
[Line 1: Humanlike Prompt Injection]
  ├─ Enforce concise brevity constraints (10~30 chars in group)
  ├─ Forbid trailing periods and markdown formatting
  ├─ Prioritize quoting buried/non-latest messages
  ├─ Suppress know-it-all impulses (react casually, dodge exams)
  └─ Grant lurking permission (allow outputting <silent>)
        │
        ▼
   [LLM Generation]
        │
        ▼
[Line 2: Replyer Hard Guardrails]
  ├─ Strip trailing periods (。 and .)
  ├─ Remove bold (**), headers (#), lists
  ├─ Clean customer-service clichés
  └─ Smooth sentence-boundary cutoff if runaway
        │
        ▼
[Line 3: SendService Outbound Guard]
  ├─ Catch upstream LLM safety/policy errors ──► Silently abort (no leaks!)
  ├─ Recognize <silent> / empty replies ──────► Silently abort (lurking!)
  ├─ Pure media (images, videos, GIFs) ────────► 100% untouched passthrough
  ├─ Multi-bubble sequential dispatch
  └─ Natural typing delay simulation
        │
        ▼
  [Sent to Chat Platform / QQ]
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
