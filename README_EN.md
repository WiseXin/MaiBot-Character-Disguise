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
- **Group chats**: Strict brevity (10 ~ 30 characters), quick and casual.
- **Private chats**: Relaxed conversational replies (20 ~ 60 characters).
- **Safety cutoff**: Hard truncation at 150 characters to prevent runaway LLM outputs.

### 3. 🤐 Social Relaxation (Graceful Lurking)
- Real humans do not reply to everything! If a message is hard to follow, awkward, or boring, the bot outputs `<silent>`.
- The plugin intercepts `<silent>` before transmission and silently discards it, achieving genuine "seen but didn't reply / lurking" behavior.

### 4. 🚫 Suppress Know-It-All Syndrome
- Enforces an unbendable rule: unless explicitly mentioned or directly asked, **never offer unsolicited tutorials or explanations** for random screenshots, memes, or chat math.
- Authentic group members joke, react, send question marks, or play along—they don't act like serious textbook tutors.

### 5. 🧼 Plaintext Cleanliness
- Strips markdown formatting (`**`, `#`, `- `, code blocks).
- Cleans typical AI clichés (*"Certainly"*, *"Hope this helps"*, *"As a gamer..."*).

### 6. 💬 Multi-Bubble Simulation
- Recognizes `<message>` tags or multi-part thoughts, sending them as sequential bubbles with natural slight delays.

### 7. 🎛️ Dual-Scope Independent Control
- Group chat disguise and private chat humanization can be toggled independently.
- Supports group and user whitelists and blacklists.
- Full WebUI visual card support with instant hot-reload (no restart required).

---

## ⚙️ Configuration (`config.toml.example`)

```toml
[plugin]
name = "character_disguise"
version = "1.0.0"
config_version = "1.0.0"
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

## 📄 License

This project is licensed under the [MIT License](LICENSE).
