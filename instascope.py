#!/usr/bin/env python3
"""
InstaScope v2.0 — Instagram Account Analyzer
Drop your Instagram ZIP export and everything loads automatically.
100% offline. No API. No login.
"""

import sys, os, json, zipfile, webbrowser, csv, io, shutil, tempfile
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# ── tkinter ───────────────────────────────────────────────────────────────────
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    print("ERROR: tkinter not found.\n  Linux: sudo apt install python3-tk\n  Mac: brew install python-tk")
    input("Press Enter to exit.")
    sys.exit(1)

# ── tkinterdnd2 (drag & drop) — optional ─────────────────────────────────────
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# ── matplotlib — optional ─────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ═══════════════════════════ PALETTE ═════════════════════════════════════════
BG      = "#0d1117";  CARD    = "#161b22";  BORDER  = "#30363d"
ACCENT  = "#e1306c";  ACCENT2 = "#833ab4";  TEXT    = "#f0f6fc"
SUBTEXT = "#8b949e";  GREEN   = "#3fb950";  YELLOW  = "#d29922"
RED     = "#f85149";  BLUE    = "#58a6ff";  WHITE   = "#ffffff"
TEAL    = "#39d353"

FT  = ("Segoe UI", 10);        FT_B = ("Segoe UI", 10, "bold")
FT_H= ("Segoe UI", 13, "bold");FT_S = ("Segoe UI", 9)
FT_T= ("Segoe UI", 18, "bold");FT_BIG=("Segoe UI", 22, "bold")

# ═══════════════════════════ KNOWN FILE MAP ════════════════════════════════════
# Maps the logical key → all possible relative paths inside a Meta export ZIP
# Meta's folder structure has changed across versions — we cover all known ones.
FILE_MAP = {
    "followers": [
        "connections/followers_and_following/followers_1.json",
        "followers_and_following/followers_1.json",
        "followers_1.json",
        # some exports split into followers_2.json etc — handled separately
    ],
    "following": [
        "connections/followers_and_following/following.json",
        "followers_and_following/following.json",
        "following.json",
    ],
    "unfollowed": [
        "connections/followers_and_following/recently_unfollowed_profiles.json",
        "followers_and_following/recently_unfollowed_profiles.json",
        "recently_unfollowed_profiles.json",
    ],
    "hide_story": [
        "connections/followers_and_following/hide_story_from.json",
        "followers_and_following/hide_story_from.json",
        "hide_story_from.json",
    ],
    "pending_requests": [
        "connections/followers_and_following/pending_follow_requests.json",
        "followers_and_following/pending_follow_requests.json",
        "pending_follow_requests.json",
    ],
    "recent_requests": [
        "connections/followers_and_following/recent_follow_requests.json",
        "followers_and_following/recent_follow_requests.json",
        "recent_follow_requests.json",
    ],
    "removed_suggestions": [
        "connections/followers_and_following/removed_suggestions.json",
        "followers_and_following/removed_suggestions.json",
        "removed_suggestions.json",
    ],
}

FILE_LABELS = {
    "followers":          ("👥 Followers",          GREEN),
    "following":          ("➡️  Following",           ACCENT),
    "unfollowed":         ("🕐 Unfollowed",           YELLOW),
    "hide_story":         ("🙈 Story Hidden",         BLUE),
    "pending_requests":   ("⏳ Pending Sent",         ACCENT2),
    "recent_requests":    ("📨 Recent Requests",      TEAL),
    "removed_suggestions":("🚫 Removed Suggestions",  SUBTEXT),
}

# ═══════════════════════════ PARSER ═══════════════════════════════════════════
def parse_users(raw_json) -> list:
    """Parse any Instagram relationships JSON into [{username, href, timestamp}]."""
    if isinstance(raw_json, str):
        data = json.loads(raw_json)
    elif isinstance(raw_json, (bytes, bytearray)):
        data = json.loads(raw_json.decode("utf-8"))
    else:
        data = raw_json

    entries = []

    def extract(node):
        if isinstance(node, list):
            for item in node:
                extract(item)
        elif isinstance(node, dict):
            sld   = node.get("string_list_data", [])
            title = node.get("title", "")
            for s in sld:
                href  = s.get("href", "")
                value = s.get("value", "") or title or href.rstrip("/").split("/")[-1]
                ts    = s.get("timestamp", 0)
                if value or href:
                    entries.append({
                        "username":  value.strip(),
                        "href":      href,
                        "timestamp": ts,
                    })
            for v in node.values():
                if isinstance(v, (list, dict)):
                    extract(v)

    extract(data)

    seen, result = set(), []
    for e in entries:
        key = e["username"] or e["href"]
        if key and key not in seen:
            seen.add(key)
            result.append(e)
    return result


def extract_zip_smart(zip_path: str) -> dict:
    """
    Open a Meta Instagram export ZIP and extract all known files.
    Returns {key: [user_list]} for every file found.
    Also handles multiple followers_N.json files.
    """
    result    = {k: [] for k in FILE_MAP}
    found_log = {}

    with zipfile.ZipFile(zip_path, "r") as zf:
        all_names = zf.namelist()

        for key, candidates in FILE_MAP.items():
            # try known paths first
            matched = None
            for candidate in candidates:
                # search with and without a top-level folder prefix
                for name in all_names:
                    norm = name.replace("\\", "/")
                    if norm == candidate or norm.endswith("/" + candidate) or norm.endswith("/" + candidate.split("/")[-1]):
                        # also verify it's the right filename
                        if Path(norm).name == Path(candidate).name:
                            matched = name
                            break
                if matched:
                    break

            if matched:
                raw = zf.read(matched)
                result[key] = parse_users(raw)
                found_log[key] = matched

        # ── handle followers_2.json, followers_3.json … ───────────────────────
        extra_followers = []
        for name in all_names:
            bn = Path(name).name
            if bn.startswith("followers_") and bn.endswith(".json") and bn != "followers_1.json":
                raw = zf.read(name)
                extra_followers.extend(parse_users(raw))
                found_log[f"extra:{bn}"] = name

        # merge, dedupe
        if extra_followers:
            existing = {u["username"] for u in result["followers"]}
            for u in extra_followers:
                if u["username"] not in existing:
                    result["followers"].append(u)
                    existing.add(u["username"])

    return result, found_log


def extract_folder_smart(folder_path: str) -> dict:
    """Walk a folder and find all known Instagram JSON files."""
    result    = {k: [] for k in FILE_MAP}
    found_log = {}

    folder = Path(folder_path)
    all_files = list(folder.rglob("*.json"))

    for key, candidates in FILE_MAP.items():
        for candidate in candidates:
            target_name = Path(candidate).name
            for f in all_files:
                if f.name == target_name:
                    result[key] = parse_users(json.loads(f.read_text("utf-8")))
                    found_log[key] = str(f)
                    break
            if found_log.get(key):
                break

    # extra followers
    extra_followers = []
    for f in all_files:
        if f.name.startswith("followers_") and f.name != "followers_1.json":
            extra = parse_users(json.loads(f.read_text("utf-8")))
            extra_followers.extend(extra)

    if extra_followers:
        existing = {u["username"] for u in result["followers"]}
        for u in extra_followers:
            if u["username"] not in existing:
                result["followers"].append(u)
                existing.add(u["username"])

    return result, found_log


def clean_url(username: str) -> str:
    u = username.lstrip("@").strip()
    return f"https://www.instagram.com/{u}" if u else ""


def fmt_ts(ts):
    if not ts:
        return "—"
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
    except Exception:
        return "—"


def ts_to_dt(ts):
    try:
        return datetime.fromtimestamp(int(ts))
    except Exception:
        return None


def days_ago(ts):
    dt = ts_to_dt(ts)
    if not dt:
        return "—"
    return str((datetime.now() - dt).days)

# ═══════════════════════════ TOOLTIP ══════════════════════════════════════════
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self.tip    = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + 28
            self.tip = tk.Toplevel(self.widget)
            self.tip.wm_overrideredirect(True)
            self.tip.wm_geometry(f"+{x}+{y}")
            tk.Label(self.tip, text=self.text, font=FT_S,
                     bg="#24292e", fg=TEXT, relief="flat",
                     padx=8, pady=4).pack()
        except Exception:
            pass

    def hide(self, _=None):
        if self.tip:
            try:
                self.tip.destroy()
            except Exception:
                pass
            self.tip = None

# ═══════════════════════════ MAIN APP ═════════════════════════════════════════
class InstaScope(tk.Tk if not HAS_DND else TkinterDnD.Tk):

    def __init__(self):
        super().__init__()
        self.title("InstaScope v2.0 — Instagram Account Analyzer")
        self.geometry("1220x780")
        self.minsize(980, 640)
        self.configure(bg=BG)

        self.data        = {k: [] for k in FILE_MAP}
        self.found_log   = {}
        self.current_tab = "not_following_back"
        self._sort_col   = None
        self._sort_rev   = False

        self._apply_style()
        self._build_ui()

        if HAS_DND:
            self._setup_dnd()

    # ── Style ──────────────────────────────────────────────────────────────────
    def _apply_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("IS.Treeview",
                        background=CARD, fieldbackground=CARD,
                        foreground=TEXT, rowheight=28, borderwidth=0, font=FT)
        style.configure("IS.Treeview.Heading",
                        background="#1c2128", foreground=SUBTEXT,
                        relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("IS.Treeview",
                  background=[("selected", "#1f6feb")],
                  foreground=[("selected", WHITE)])
        style.configure("IS.Vertical.TScrollbar",
                        background=BORDER, troughcolor=CARD,
                        arrowcolor=SUBTEXT, borderwidth=0)

    # ── UI build ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_drop_zone()
        self._build_stats_row()
        self._build_tab_bar()
        self._build_toolbar()
        self._build_table()
        self._build_footer()
        self._refresh_table()

    # ── Header ─────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=CARD, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📸  InstaScope",
                 font=FT_T, fg=WHITE, bg=CARD).pack(side="left", padx=22, pady=10)
        tk.Label(hdr, text="v2.0  •  Instagram Account Analyzer",
                 font=FT_S, fg=SUBTEXT, bg=CARD).pack(side="left", pady=10)
        self.status_lbl = tk.Label(hdr,
                                   text="Drop your Instagram ZIP or click Browse",
                                   font=FT_S, fg=SUBTEXT, bg=CARD)
        self.status_lbl.pack(side="right", padx=22)

    # ── Drop Zone ──────────────────────────────────────────────────────────────
    def _build_drop_zone(self):
        outer = tk.Frame(self, bg=CARD)
        outer.pack(fill="x")
        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x")

        # Drop area
        self.drop_frame = tk.Frame(outer, bg="#0d1f12", pady=0)
        self.drop_frame.pack(fill="x", padx=16, pady=10)

        dz = tk.Frame(self.drop_frame, bg="#0d1f12",
                      highlightthickness=2, highlightbackground=GREEN,
                      pady=16)
        dz.pack(fill="x")
        self.dz = dz

        dz_inner = tk.Frame(dz, bg="#0d1f12")
        dz_inner.pack()

        self.dz_icon  = tk.Label(dz_inner, text="📂", font=("Segoe UI", 26),
                                  bg="#0d1f12", fg=GREEN)
        self.dz_icon.pack(side="left", padx=(0,12))

        txt_frame = tk.Frame(dz_inner, bg="#0d1f12")
        txt_frame.pack(side="left")

        self.dz_title = tk.Label(txt_frame,
                                  text="Drop your Instagram ZIP here",
                                  font=FT_B, fg=TEXT, bg="#0d1f12")
        self.dz_title.pack(anchor="w")
        self.dz_sub   = tk.Label(txt_frame,
                                  text="or select a ZIP file / extracted folder manually",
                                  font=FT_S, fg=SUBTEXT, bg="#0d1f12")
        self.dz_sub.pack(anchor="w")

        btn_frame = tk.Frame(dz, bg="#0d1f12")
        btn_frame.pack(pady=(10,4))

        self._ibtn(btn_frame, "📦  Browse ZIP File", GREEN,
                   self._browse_zip).pack(side="left", padx=6)
        self._ibtn(btn_frame, "📁  Browse Folder", BLUE,
                   self._browse_folder).pack(side="left", padx=6)
        self._ibtn(btn_frame, "📊  Charts", "#21262d",
                   self._show_charts).pack(side="left", padx=6)
        self._ibtn(btn_frame, "💾  Export CSV", "#21262d",
                   self._export_csv).pack(side="left", padx=6)
        self._ibtn(btn_frame, "📋  Copy All", "#21262d",
                   self._copy_all).pack(side="left", padx=6)
        self._ibtn(btn_frame, "📋  View Load Log", "#21262d",
                   self._show_log).pack(side="left", padx=6)

        # file status pills
        self.pill_frame = tk.Frame(outer, bg=CARD)
        self.pill_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.pills = {}
        for key, (label, color) in FILE_LABELS.items():
            pill = tk.Label(self.pill_frame,
                            text=f"○  {label}",
                            font=FT_S, fg=SUBTEXT, bg="#21262d",
                            padx=8, pady=3, relief="flat")
            pill.pack(side="left", padx=3)
            self.pills[key] = pill

    # ── Stats ──────────────────────────────────────────────────────────────────
    def _build_stats_row(self):
        row = tk.Frame(self, bg=BG, pady=8)
        row.pack(fill="x", padx=16)
        self.stat_labels = {}
        defs = [
            ("followers_count", "Followers",          "—", ACCENT2),
            ("following_count", "Following",           "—", ACCENT),
            ("nfb_count",       "Not Following Back",  "—", RED),
            ("fans_count",      "Your Fans",           "—", GREEN),
            ("mutual_count",    "Mutual",              "—", YELLOW),
            ("ratio",           "Follow-back Ratio",   "—", BLUE),
            ("ghost_count",     "Ghost Followers",     "—", SUBTEXT),
            ("pending_count",   "Pending Sent",        "—", ACCENT2),
        ]
        for key, title, val, color in defs:
            f = tk.Frame(row, bg=CARD, padx=14, pady=8)
            f.pack(side="left", fill="y", padx=(0,7))
            lbl = tk.Label(f, text=val, font=FT_BIG, fg=color, bg=CARD)
            lbl.pack(anchor="w")
            tk.Label(f, text=title, font=FT_S, fg=SUBTEXT, bg=CARD).pack(anchor="w")
            self.stat_labels[key] = lbl

    # ── Tab bar ────────────────────────────────────────────────────────────────
    def _build_tab_bar(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=16, pady=(4,0))
        self.tab_btns = {}
        tabs = [
            ("not_following_back", "❌  Not Following Back"),
            ("fans",               "💛  Your Fans"),
            ("mutual",             "✅  Mutual"),
            ("ghost_followers",    "👻  Ghost Followers"),
            ("story_hiders",       "🙈  Story Hiders"),
            ("recently_unfollowed","🕐  Recently Unfollowed"),
            ("pending_requests",   "⏳  Pending Sent"),
            ("recent_requests",    "📨  Recent Requests"),
            ("removed_suggestions","🚫  Removed Suggestions"),
            ("all_followers",      "👥  All Followers"),
            ("all_following",      "➡️   All Following"),
        ]
        for key, label in tabs:
            btn = tk.Button(bar, text=label, font=FT_S,
                            bg=BG, fg=SUBTEXT, relief="flat",
                            padx=11, pady=6, cursor="hand2",
                            command=lambda k=key: self._switch_tab(k))
            btn.pack(side="left")
            self.tab_btns[key] = btn
        self._highlight_tab("not_following_back")

    # ── Toolbar ────────────────────────────────────────────────────────────────
    def _build_toolbar(self):
        bar = tk.Frame(self, bg=BG, pady=5)
        bar.pack(fill="x", padx=16)
        tk.Label(bar, text="🔎", font=FT, fg=SUBTEXT, bg=BG).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_table())
        ent = tk.Entry(bar, textvariable=self.search_var, font=FT,
                       bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat",
                       highlightthickness=1,
                       highlightbackground=BORDER, highlightcolor=ACCENT)
        ent.pack(side="left", fill="x", expand=True, ipady=5, padx=6)
        self.count_lbl = tk.Label(bar, text="", font=FT_S, fg=SUBTEXT, bg=BG)
        self.count_lbl.pack(side="right", padx=8)

    # ── Table ──────────────────────────────────────────────────────────────────
    def _build_table(self):
        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=16, pady=(2,10))
        cols = ("#", "Username", "Profile Link", "Date", "Days Ago")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                 style="IS.Treeview", selectmode="browse")
        for col, w in zip(cols, [36, 190, 320, 95, 75]):
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._col_sort(c))
            self.tree.column(col, width=w, minwidth=30, anchor="w")
        vsb = ttk.Scrollbar(frame, orient="vertical",
                            style="IS.Vertical.TScrollbar",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self._open_profile)
        self.tree.bind("<Return>",   self._open_profile)
        self.tree.bind("<Button-3>", self._right_click)
        # context menu
        self.ctx = tk.Menu(self, tearoff=0, bg=CARD, fg=TEXT,
                           activebackground="#1f6feb", activeforeground=WHITE,
                           font=FT_S, bd=0)
        self.ctx.add_command(label="🌐  Open Profile",  command=self._open_profile)
        self.ctx.add_command(label="📋  Copy Username", command=self._copy_username)
        self.ctx.add_command(label="🔗  Copy Link",     command=self._copy_link)

    # ── Footer ─────────────────────────────────────────────────────────────────
    def _build_footer(self):
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        foot = tk.Frame(self, bg=CARD)
        foot.pack(fill="x")
        tk.Label(foot,
                 text="Double-click → open profile  •  Right-click → more options  •  "
                      "All data stays on your device  •  Made with ❤ by InstaScope",
                 font=FT_S, fg=SUBTEXT, bg=CARD).pack(pady=5)

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _ibtn(self, parent, text, bg, cmd):
        b = tk.Button(parent, text=text, font=FT_S,
                      bg=bg, fg=WHITE, activebackground=BORDER,
                      relief="flat", padx=12, pady=5,
                      cursor="hand2", command=cmd)
        return b

    def _highlight_tab(self, key):
        for k, btn in self.tab_btns.items():
            btn.configure(bg=ACCENT if k == key else BG,
                          fg=WHITE  if k == key else SUBTEXT)

    def _switch_tab(self, key):
        self.current_tab = key
        self._highlight_tab(key)
        self.search_var.set("")
        self._refresh_table()

    def _set_status(self, msg):
        self.status_lbl.configure(text=msg)

    # ── Drag & Drop ────────────────────────────────────────────────────────────
    def _setup_dnd(self):
        self.dz.drop_target_register(DND_FILES)
        self.dz.dnd_bind("<<Drop>>", self._on_drop)
        self.dz_title.configure(text="Drop your Instagram ZIP here ↓")

    def _on_drop(self, event):
        path = event.data.strip().strip("{}")
        self._load_path(path)

    # ── File loading ───────────────────────────────────────────────────────────
    def _browse_zip(self):
        path = filedialog.askopenfilename(
            title="Select Instagram Export ZIP",
            filetypes=[("ZIP files", "*.zip"), ("All", "*.*")])
        if path:
            self._load_path(path)

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Select Extracted Instagram Export Folder")
        if path:
            self._load_path(path)

    def _load_path(self, path: str):
        path = path.strip()
        self._set_status(f"Loading: {os.path.basename(path)} ...")
        self.update_idletasks()
        try:
            if os.path.isfile(path) and path.lower().endswith(".zip"):
                self.data, self.found_log = extract_zip_smart(path)
            elif os.path.isdir(path):
                self.data, self.found_log = extract_folder_smart(path)
            else:
                messagebox.showerror("Unsupported", "Please select a .zip file or a folder.")
                return
        except Exception as e:
            messagebox.showerror("Error loading file", str(e))
            return

        self._update_pills()
        self._run_analysis()
        self._refresh_table()

        loaded = sum(1 for v in self.data.values() if v)
        total_users = sum(len(v) for v in self.data.values())
        self._set_status(
            f"✅  Loaded {loaded} files · {total_users} total entries — "
            f"{os.path.basename(path)}")
        # flash the drop zone green
        self.dz.configure(highlightbackground=GREEN)
        self.dz_icon.configure(text="✅")
        self.dz_title.configure(text=f"Loaded: {os.path.basename(path)}")
        self.dz_sub.configure(
            text=f"{len(self.data['followers'])} followers · "
                 f"{len(self.data['following'])} following · "
                 f"{loaded} files found")

    def _update_pills(self):
        for key, pill in self.pills.items():
            users = self.data.get(key, [])
            label, color = FILE_LABELS[key]
            if users:
                pill.configure(text=f"✅ {label} ({len(users)})", fg=color)
            else:
                pill.configure(text=f"○  {label}", fg=SUBTEXT)

    # ── Analysis ───────────────────────────────────────────────────────────────
    def _run_analysis(self):
        frs  = {u["username"] for u in self.data["followers"]}
        fing = {u["username"] for u in self.data["following"]}
        now  = datetime.now()
        cutoff = now.timestamp() - (180 * 86400)

        nfb_c    = len(fing - frs)
        fans_c   = len(frs - fing)
        mutual_c = len(frs & fing)
        ghost_c  = sum(1 for u in self.data["followers"]
                       if u.get("timestamp", now.timestamp()) < cutoff)
        pending_c= len(self.data["pending_requests"])
        ratio    = round(len(frs) / max(len(fing), 1), 2)

        self.stat_labels["followers_count"].configure(text=str(len(frs)))
        self.stat_labels["following_count"].configure(text=str(len(fing)))
        self.stat_labels["nfb_count"].configure(text=str(nfb_c))
        self.stat_labels["fans_count"].configure(text=str(fans_c))
        self.stat_labels["mutual_count"].configure(text=str(mutual_c))
        self.stat_labels["ratio"].configure(text=str(ratio))
        self.stat_labels["ghost_count"].configure(text=str(ghost_c))
        self.stat_labels["pending_count"].configure(text=str(pending_c))

    # ── Table population ───────────────────────────────────────────────────────
    def _get_current_data(self) -> list:
        frs  = {u["username"] for u in self.data["followers"]}
        fing = {u["username"] for u in self.data["following"]}
        now  = datetime.now()
        cutoff = now.timestamp() - (180 * 86400)
        tab  = self.current_tab

        if   tab == "not_following_back":
            return [u for u in self.data["following"]  if u["username"] not in frs]
        elif tab == "fans":
            return [u for u in self.data["followers"]  if u["username"] not in fing]
        elif tab == "mutual":
            return [u for u in self.data["followers"]  if u["username"] in fing]
        elif tab == "ghost_followers":
            return [u for u in self.data["followers"]
                    if u.get("timestamp", now.timestamp()) < cutoff]
        elif tab == "story_hiders":
            return list(self.data["hide_story"])
        elif tab == "recently_unfollowed":
            return list(self.data["unfollowed"])
        elif tab == "pending_requests":
            return list(self.data["pending_requests"])
        elif tab == "recent_requests":
            return list(self.data["recent_requests"])
        elif tab == "removed_suggestions":
            return list(self.data["removed_suggestions"])
        elif tab == "all_followers":
            return list(self.data["followers"])
        elif tab == "all_following":
            return list(self.data["following"])
        return []

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        data  = self._get_current_data()
        query = self.search_var.get().strip().lower()
        if query:
            data = [u for u in data if query in u["username"].lower()]

        for i, u in enumerate(data, 1):
            uname = u["username"] or "—"
            link  = clean_url(uname)
            date  = fmt_ts(u.get("timestamp", 0))
            da    = days_ago(u.get("timestamp", 0))
            tag   = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end",
                             values=(i, uname, link, date, da),
                             tags=(tag,))

        self.tree.tag_configure("even", background="#1c2128")
        self.tree.tag_configure("odd",  background=CARD)
        self.count_lbl.configure(text=f"{len(data)} users")

    # ── Sort ───────────────────────────────────────────────────────────────────
    def _col_sort(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children()]
        rev   = (self._sort_col == col and not self._sort_rev)
        items.sort(
            key=lambda x: (x[0] in ("—",""), x[0].lower()),
            reverse=rev)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)
        self._sort_col = col
        self._sort_rev = rev

    # ── Actions ────────────────────────────────────────────────────────────────
    def _sel(self):
        s = self.tree.selection()
        return self.tree.item(s[0], "values") if s else None

    def _open_profile(self, _=None):
        v = self._sel()
        if v:
            url = clean_url(v[1])
            if url:
                webbrowser.open(url)

    def _copy_username(self, _=None):
        v = self._sel()
        if v:
            self.clipboard_clear(); self.clipboard_append(v[1])
            self._set_status(f"Copied: @{v[1]}")

    def _copy_link(self, _=None):
        v = self._sel()
        if v:
            url = clean_url(v[1])
            self.clipboard_clear(); self.clipboard_append(url)
            self._set_status(f"Copied: {url}")

    def _copy_all(self):
        data = self._get_current_data()
        if not data:
            messagebox.showinfo("Nothing to copy", "No data in current tab.")
            return
        text = "\n".join(u["username"] for u in data if u["username"])
        self.clipboard_clear(); self.clipboard_append(text)
        self._set_status(f"Copied {len(data)} usernames to clipboard ✅")

    def _right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.ctx.tk_popup(event.x_root, event.y_root)

    # ── Export CSV ─────────────────────────────────────────────────────────────
    def _export_csv(self):
        data = self._get_current_data()
        if not data:
            messagebox.showinfo("Nothing to export", "No data in current tab.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"instascope_{self.current_tab}.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Username", "Profile Link", "Date", "Days Ago"])
            for u in data:
                uname = u["username"] or ""
                w.writerow([uname, clean_url(uname),
                            fmt_ts(u.get("timestamp",0)),
                            days_ago(u.get("timestamp",0))])
        messagebox.showinfo("Exported ✅", f"Saved {len(data)} records to:\n{path}")

    # ── Load log ───────────────────────────────────────────────────────────────
    def _show_log(self):
        win = tk.Toplevel(self)
        win.title("File Load Log")
        win.configure(bg=BG)
        win.geometry("700x420")
        tk.Label(win, text="Files Found in Your Export",
                 font=FT_H, fg=TEXT, bg=BG).pack(padx=20, pady=(14,6), anchor="w")

        txt = tk.Text(win, bg=CARD, fg=TEXT, font=FT_S,
                      relief="flat", padx=12, pady=8, wrap="word")
        txt.pack(fill="both", expand=True, padx=14, pady=(0,14))

        if not self.found_log:
            txt.insert("end", "No export loaded yet.")
        else:
            for key, path in self.found_log.items():
                users = self.data.get(key, [])
                count = len(users) if isinstance(users, list) else "?"
                txt.insert("end", f"✅  {key:25s}  →  {count:>4} entries\n")
                txt.insert("end", f"     {path}\n\n")
            not_found = [k for k in FILE_MAP if k not in self.found_log]
            if not_found:
                txt.insert("end", "\n── Not found in export ──\n")
                for k in not_found:
                    txt.insert("end", f"○  {k}\n")
        txt.configure(state="disabled")

    # ── Charts ─────────────────────────────────────────────────────────────────
    def _show_charts(self):
        if not HAS_MPL:
            messagebox.showinfo("matplotlib missing",
                "Run InstaScope.bat again — it will install matplotlib automatically.")
            return
        if not any(self.data.values()):
            messagebox.showinfo("No data", "Load your Instagram export first.")
            return

        win = tk.Toplevel(self)
        win.title("InstaScope — Charts")
        win.configure(bg=BG)
        win.geometry("960x580")

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        frs  = {u["username"] for u in self.data["followers"]}
        fing = {u["username"] for u in self.data["following"]}

        # ── Overview pie ──────────────────────────────────────────────────────
        if frs or fing:
            f1 = tk.Frame(nb, bg=BG); nb.add(f1, text="Overview")
            nfb_c  = len(fing - frs)
            fans_c = len(frs  - fing)
            mut_c  = len(frs  & fing)
            vals   = [(nfb_c,"Not Following Back",RED),
                      (fans_c,"Your Fans",GREEN),
                      (mut_c, "Mutual",YELLOW)]
            vals   = [(v,l,c) for v,l,c in vals if v > 0]
            if vals:
                v2,l2,c2 = zip(*vals)
                fig = Figure(figsize=(8,4.5), facecolor=BG)
                ax  = fig.add_subplot(111, facecolor=CARD)
                ax.pie(v2, labels=l2, colors=c2, autopct="%1.1f%%",
                       textprops={"color":TEXT,"fontsize":9})
                ax.set_title("Account Relationship Overview", color=TEXT, fontsize=12)
                FigureCanvasTkAgg(fig, f1).get_tk_widget().pack(fill="both", expand=True)
                FigureCanvasTkAgg(fig, f1).draw()

        # ── Unfollow timeline ─────────────────────────────────────────────────
        uf = self.data["unfollowed"]
        if uf:
            f2 = tk.Frame(nb, bg=BG); nb.add(f2, text="Unfollow Timeline")
            counts = defaultdict(int)
            for u in uf:
                dt = ts_to_dt(u.get("timestamp",0))
                if dt:
                    counts[dt.strftime("%Y-%m-%d")] += 1
            dates  = sorted(counts)[-30:]
            values = [counts[d] for d in dates]
            fig2 = Figure(figsize=(8,4.5), facecolor=BG)
            ax2  = fig2.add_subplot(111, facecolor=CARD)
            ax2.bar(range(len(dates)), values, color=ACCENT, width=0.7)
            ax2.set_xticks(range(len(dates)))
            ax2.set_xticklabels(dates, rotation=45, ha="right",
                                color=SUBTEXT, fontsize=7)
            ax2.set_ylabel("Unfollows", color=SUBTEXT)
            ax2.set_title("Unfollow Activity (last 30 days)", color=TEXT)
            ax2.tick_params(colors=SUBTEXT)
            for sp in ax2.spines.values(): sp.set_edgecolor(BORDER)
            fig2.tight_layout()
            c2 = FigureCanvasTkAgg(fig2, f2)
            c2.draw(); c2.get_tk_widget().pack(fill="both", expand=True)

        # ── Follower join timeline ────────────────────────────────────────────
        if self.data["followers"]:
            f3 = tk.Frame(nb, bg=BG); nb.add(f3, text="Follower Growth")
            monthly = defaultdict(int)
            for u in self.data["followers"]:
                dt = ts_to_dt(u.get("timestamp",0))
                if dt:
                    monthly[dt.strftime("%Y-%m")] += 1
            months = sorted(monthly)
            vals3  = [monthly[m] for m in months]
            fig3 = Figure(figsize=(8,4.5), facecolor=BG)
            ax3  = fig3.add_subplot(111, facecolor=CARD)
            ax3.fill_between(range(len(months)), vals3, color=ACCENT2, alpha=0.5)
            ax3.plot(range(len(months)), vals3, color=ACCENT2, linewidth=2)
            ax3.set_xticks(range(len(months)))
            ax3.set_xticklabels(months, rotation=45, ha="right",
                                color=SUBTEXT, fontsize=7)
            ax3.set_ylabel("New Followers", color=SUBTEXT)
            ax3.set_title("Followers Gained Over Time", color=TEXT)
            ax3.tick_params(colors=SUBTEXT)
            for sp in ax3.spines.values(): sp.set_edgecolor(BORDER)
            fig3.tight_layout()
            c3 = FigureCanvasTkAgg(fig3, f3)
            c3.draw(); c3.get_tk_widget().pack(fill="both", expand=True)

        # ── Following vs Follower ratio bar ───────────────────────────────────
        if frs or fing:
            f4 = tk.Frame(nb, bg=BG); nb.add(f4, text="Ratio")
            fig4 = Figure(figsize=(6,4.5), facecolor=BG)
            ax4  = fig4.add_subplot(111, facecolor=CARD)
            cats   = ["Followers", "Following", "Mutual", "Not Following Back", "Your Fans"]
            values4= [len(frs), len(fing),
                      len(frs&fing), len(fing-frs), len(frs-fing)]
            colors4= [ACCENT2, ACCENT, YELLOW, RED, GREEN]
            bars   = ax4.bar(cats, values4, color=colors4, width=0.5)
            for bar, val in zip(bars, values4):
                ax4.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1,
                         str(val), ha="center", color=TEXT, fontsize=9)
            ax4.set_ylabel("Count", color=SUBTEXT)
            ax4.set_title("Account Breakdown", color=TEXT)
            ax4.tick_params(colors=SUBTEXT)
            ax4.set_xticklabels(cats, color=SUBTEXT, fontsize=8, rotation=15)
            for sp in ax4.spines.values(): sp.set_edgecolor(BORDER)
            fig4.tight_layout()
            c4 = FigureCanvasTkAgg(fig4, f4)
            c4.draw(); c4.get_tk_widget().pack(fill="both", expand=True)


# ═══════════════════════════ ENTRY POINT ══════════════════════════════════════
if __name__ == "__main__":
    app = InstaScope()
    app.mainloop()
