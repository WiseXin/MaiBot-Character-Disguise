# 🎭 MaiBot Character Disguise (`WiseXin.character-disguise`)

> **"A true chatting pro never acts like a know-it-all."**  
> Say goodbye to preachiness, pedantic know-it-all answers, and robotic customer-service tones!  
> A native humanlike behavioral enhancement plugin for MaiBot designed to eliminate "AI vibes" and bring genuine conversational breathing room, social chill, and authentic human chatting soul.

---

## 💥 Traditional AI Bot vs. Character Disguise

| Realistic Chat Scenario | Traditional AI Bot 🤖 | With Character Disguise 🎭 |
| :--- | :--- | :--- |
| **Random game screenshot or casual complaint** | Dumps a 300-word tutorial & walkthrough (kills the room instantly) | "Ugh, this stage was awful, took me half an hour too" (natural relatable banter) |
| **Someone types 3-5 words** | Returns an essay with bold markdown headers and numbered lists | Replies in 10-20 words, casual and fast just like mobile texting |
| **Replying to a buried message** | Drops a disjointed reply with zero context, confusing everyone | Automatically quotes the original message, keeping thread context clear |
| **Group member vents or says "shut up"** | Argues back defensively: *"Sorry, as an AI..."* creating drama | Hits physical mute filter and drops message immediately without arguing |
| **Complex exam question or provocative test** | Tries to solve everything eagerly, often hallucinating | Sends a question mark, says "no idea", or outputs `<silent>` to lurk |
| **Sentence-ending punctuation** | Stiff and formal period `.` on every single casual line | Natural whitespace, conversational particles, or relaxed casual marks |
| **Prompt triggers upstream policy error** | Leaks raw English Google Policy violation errors into chat | Silently intercepted and dropped before dispatch, zero AI leak |
| **Plugin commands (/dr, /help, etc.)** | Commands blocked or intercepted by mistake | Seamlessly passes all plugin commands through, ensuring multi-plugin harmony |
| **Third-party bot error spam** | Echoes errors or pollutes conversation context | Inbound layer intercepts error spam ("permission denied", etc.) cleanly |
| **Chat mentions AI models or identity challenges** | Frantically defends "I am really a living human" causing drama | Eliminates self-reference; listens to tech chat casually without arguing |
| **LLM accidentally outputs internal markup** | Chat window displays raw `<message quote="...">` tags | Aggressively stripped and cleaned, guaranteeing pure clean text |

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

### 3. 🪞 Eliminate Self-Reference & Identity Defensiveness
- The harder an AI tries to prove it's human, the more robotic it sounds.
- Prompts completely remove words like "AI", "robot", "architecture", and "system prompt".
- Fosters a genuine group member mindset: treats technical talk as other people's gossip and avoids self-justification.

### 4. 🏷️ XML Pseudo Tag Terminator (Anti-Leak Guard)
- Strictly forbids the model from outputting XML/HTML tags (such as `<message>` or `quote=`) in reply text.
- Post-guard `strip_xml_tags` cleanly strips any residual, attributed, or unclosed tags, ensuring 100% clean plaintext output.

### 5. 🫧 Natural Flow (No Forced Over-Quoting)
- Real people in fast group chats rarely quote every single line.
- Avoids prompting that pushes quote reply rates toward 100%, letting quotes occur naturally via core probability rules.

### 6. 🤐 Social Relaxation (Graceful Lurking)
- Real humans do not reply to everything! If a message is hard to follow, awkward, or boring, the bot outputs `<silent>`.
- The plugin intercepts `<silent>` before transmission and silently discards it, achieving genuine "seen but didn't reply / lurking" behavior.

### 7. 🚫 Suppress Know-It-All Syndrome & Query Triage
- Enforces an unbendable rule: unless explicitly mentioned or directly asked, **never offer unsolicited tutorials or explanations** for random screenshots, memes, or chat math.
- **Smart Query Triage**:
  - Direct simple questions: short, casual answers without lecturing or step-by-step numbered guides.
  - Provocative test problems, complex exams, or spam: react casually with question marks, say you don't know, or simply output `<silent>` to stay quiet.

### 8. 🤫 Physical Mute & "Shut Up" Guard
- In group chats, members may occasionally vent or jokingly tell bots to "shut up" (*"闭嘴"*, *"别叫了"*, *"烦死了"*).
- Traditional AI tends to defensively argue back, escalating awkwardness.
- This plugin intercepts matching mute keywords at the inbound layer and drops the message entirely, letting the bot gracefully stay quiet without aggravating anyone.

### 9. 🛡️ Bot Noise Filtering, Outbound Shield & Multi-Plugin Harmony
- **Multi-Plugin Seamless Compatibility**: All valid command prefixes (`/dr`, `/help`, `/play`, `/xhh`, etc.) are passed through untouched, allowing MaiBot's plugin command pipeline to operate smoothly without interference.
- **Inbound Filter**: Intercepts third-party bot status error spam (*"permission denied to use this command"*, etc.) and malicious SQL injection/XSS payloads from regular members; master accounts (`master_users`) are exempt.
- **Outbound Safety Shield**: Catches and aborts upstream LLM policy errors (e.g., Google Prohibited Use policy rejections) before sending, preventing AI infrastructure details from leaking into the chat.

### 10. 🧼 Plaintext Cleanliness
- Strips markdown formatting (`**`, `#`, `- `, code blocks).
- Cleans typical AI clichés (*"Certainly"*, *"Hope this helps"*, *"As an AI..."*).
- Prevents repetitive catchphrases and forced memes.

### 11. 💬 Multi-Bubble Sequential Dispatch
- Recognizes `<message>` tags or multi-part thoughts, sending them as sequential bubbles with natural slight delays.

### 12. 🎭 Fully Decoupled Character Identity
- All behavioral guidelines focus strictly on universal human typing and chatting etiquette, without hardcoded character names or traits.
- Seamlessly fits any custom persona you define in MaiBot (tsundere girl, calm detective, cheerful companion, etc.).

### 13. 🎛️ Dual-Scope Independent Control
- Group chat disguise and private chat humanization can be toggled independently.
- Supports group and user whitelists and blacklists.
- Full WebUI visual card support with instant hot-reload (no restart required).

---

## ⚙️ Configuration (`config.toml.example`)

```toml
[plugin]
name = "character_disguise"
version = "1.0.3"
config_version = "1.0.3"
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
# Filter out third-party bot status spam and injection attempts (never intercepts valid plugin commands)
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
        │     ├─ Valid plugin commands (/dr, /help, /play) ──► 100% passthrough to target plugins!
        │     ├─ Third-party bot status spam / errors ──────► Silently abort
        │     ├─ Physical mute keywords ("闭嘴", "烦死了") ───► Silently abort
        │     └─ Malicious SQL injection payloads ───────────► Silently abort
        │     (Master accounts in master_users are always passed through)
        ▼
[Line 1: Humanlike Prompt Injection]
  ├─ Enforce concise brevity constraints (10~30 chars in group)
  ├─ Forbid trailing periods and markdown formatting
  ├─ Strictly forbid outputting XML/HTML tags in reply text
  ├─ Eliminate self-reference (treat tech/model topics as external talk)
  ├─ Suppress know-it-all impulses (react casually, dodge exams)
  └─ Grant lurking permission (allow outputting <silent>)
        │
        ▼
   [LLM Generation]
        │
        ▼
[Line 2: Replyer Hard Guardrails]
  ├─ Aggressively strip XML pseudo tags (<message>, <quote>, etc.)
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
