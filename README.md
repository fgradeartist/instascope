# 📸 InstaScope
## 🚀 Try It Instantly (No Download)

👉 https://fgradeartist.github.io/instascope/

Just open and drop your Instagram ZIP file.
> **Instagram Account Analyzer** — 100% offline. No API key. No login. Just drop your Instagram ZIP.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![HTML](https://img.shields.io/badge/Web-HTML5-orange?logo=html5)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20Offline-brightgreen)

---

## 🌐 Use in Browser (No Install Needed)

**Just download [`instascope.html`](instascope.html) and open it in Chrome/Firefox/Edge.**

- No Python needed
- No installation
- Works on any device with a browser
- Drop your Instagram ZIP directly into the page

---

## ✨ Features

| Feature | Desktop App | Browser Version |
|---|:---:|:---:|
| Auto-load from ZIP | ✅ | ✅ |
| Drag & Drop ZIP | ✅ | ✅ |
| Not Following Back | ✅ | ✅ |
| Your Fans | ✅ | ✅ |
| Mutual Followers | ✅ | ✅ |
| Ghost Followers (180d+) | ✅ | ✅ |
| Story Hiders | ✅ | ✅ |
| Recently Unfollowed | ✅ | ✅ |
| Pending Requests | ✅ | ✅ |
| Recent Follow Requests | ✅ | ✅ |
| Removed Suggestions | ✅ | ✅ |
| Charts (Pie, Bar, Timeline) | ✅ | ✅ |
| Export CSV | ✅ | ✅ |
| Copy All Usernames | ✅ | ✅ |
| Search/Filter | ✅ | ✅ |
| Sort Columns | ✅ | ✅ |
| Right-click menu | ✅ | — |
| Load Log | ✅ | ✅ |

---

## 🚀 Quick Start

### Option A — Browser (Easiest)
1. Download [`instascope.html`](instascope.html)
2. Open it in Chrome, Firefox, or Edge
3. Drop your Instagram ZIP on the page

### Option B — Desktop App (Windows)
1. Download and extract the ZIP
2. Double-click **`InstaScope.bat`**
3. It will install all dependencies automatically

### Option C — Desktop App (macOS / Linux)
```bash
chmod +x instascope.sh
./instascope.sh
```

---

## 📁 How to Export Your Instagram Data

1. Open Instagram → **Settings → Account Center → Your Information and Permissions**
2. Tap **Download Your Information**
3. Select **"Some of your information"**
4. Under **Connections**, check **Followers and Following**
5. Set format to **JSON** (important!)
6. Request download → wait for the email (up to 48 hours)
7. Download the ZIP — **drop it directly into InstaScope**

---

## 📂 Files InstaScope Reads

| File | What it contains |
|---|---|
| `followers_1.json` | Everyone who follows you |
| `following.json` | Everyone you follow |
| `recently_unfollowed_profiles.json` | Your recent unfollow history |
| `hide_story_from.json` | Accounts hidden from your stories |
| `pending_follow_requests.json` | Follow requests you've sent (not accepted) |
| `recent_follow_requests.json` | All follow requests you've sent |
| `removed_suggestions.json` | Suggested accounts you dismissed |

All these files are inside the `connections/followers_and_following/` folder in your ZIP — **InstaScope finds them automatically.**

---

## 📂 File Structure

```
InstaScope/
├── instascope.py       ← Desktop app (Python)
├── instascope.html     ← Browser version (no install)
├── InstaScope.bat      ← Windows launcher
├── instascope.sh       ← macOS/Linux launcher
└── README.md
```

---

## 🔒 Privacy

- **No internet required** (except to open profile links in browser)
- **No data sent anywhere** — everything runs locally on your device
- **No login, no API key, no tokens**
- The HTML version runs entirely in your browser tab

---

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| "Python not found" | Install from [python.org](https://www.python.org/downloads/), check "Add to PATH" |
| "tkinter not found" on Linux | `sudo apt install python3-tk` |
| "tkinter not found" on Mac | `brew install python-tk` |
| Drag & drop not working | Run the launcher again — it installs `tkinterdnd2` |
| Charts not showing | Run the launcher again — it installs `matplotlib` |
| App closes instantly | Open terminal, run `python3 instascope.py` to see the error |
| ZIP not loading in browser | Make sure you're using Chrome/Firefox/Edge (not Safari on older iOS) |

---

## 📄 License

MIT License — free to use, modify, and share.

---

*Made with ❤ for the Instagram community*
