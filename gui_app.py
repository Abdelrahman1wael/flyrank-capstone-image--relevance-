"""
Tkinter Graphical User Interface for AI Image Understanding & Content Matching Engine.
Allows real-time visual testing of image candidate ranking, vector similarity scores,
Mismatch Guard threshold enforcement, and human-in-the-loop audit logging.

Supports dual execution modes:
1. Direct Local Engine (if sentence-transformers & sqlite dependencies are installed).
2. Live Docker REST API Client (falls back automatically to http://localhost:8000).
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Dict, Any, Optional

# Reconfigure stdout for UTF-8 safety
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Attempt importing local engine components; fallback to Docker REST API if missing
USE_LOCAL_ENGINE = True
try:
    from engine.services import MatchingService
    from engine.database import (
        init_db,
        update_review_status,
        fetch_review_ledger,
        fetch_cost_telemetry
    )
except ImportError:
    USE_LOCAL_ENGINE = False

# API Base URL for Docker fallback mode
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Sample post templates for quick testing
SAMPLE_POSTS = {
    "p_01: Red Fox Behaviors": {
        "id": "p_01",
        "title": "Red Fox Behaviors",
        "text": "The nocturnal hunting behavior and territorial range of wild red foxes."
    },
    "p_02: Vulpes Vulpes Research": {
        "id": "p_02",
        "title": "Vulpes Vulpes Research",
        "text": "Research papers documenting the migratory trends, pelt colors, and diet of Vulpes vulpes."
    },
    "p_03: Fox Foraging Habits": {
        "id": "p_03",
        "title": "Fox Foraging Habits",
        "text": "The secretive foraging habits of red foxes in woodland edges and open fields."
    },
    "p_04: Grey Wolf Conservation (Taxonomic Trap)": {
        "id": "p_04",
        "title": "Grey Wolf Conservation",
        "text": "Conservation efforts and pack dynamics for wild grey wolves in Wyoming."
    },
    "p_05: Mechanical Turbocharger Engine (Negative Control)": {
        "id": "p_05",
        "title": "Mechanical Engine Performance",
        "text": "A technical breakdown of mechanical automotive engine performance, turbochargers, and horsepower."
    }
}

# Color palette (Dark Modern Aesthetics)
BG_DARK = "#111827"        # Dark slate background
CARD_BG = "#1f2937"        # Card background
HEADER_BG = "#1e293b"      # Header toolbar background
TEXT_MAIN = "#f9fafb"      # Main text color
TEXT_MUTED = "#9ca3af"     # Muted text
ACCENT_BLUE = "#3b82f6"    # Accent blue
ACCENT_GREEN = "#10b981"   # Success green
ACCENT_RED = "#ef4444"     # Rejection red
ACCENT_AMBER = "#f59e0b"   # Amber warning
BORDER_COLOR = "#374151"   # Border lines


class ImageMatchingGUI:
    def __init__(self, root: tk.Tk):
        global USE_LOCAL_ENGINE
        self.root = root
        mode_str = "Local Engine" if USE_LOCAL_ENGINE else f"Docker REST API ({API_BASE_URL})"
        self.root.title(f"AI Image Understanding & Content Matching Engine — GUI [{mode_str}]")
        self.root.geometry("1100x820")
        self.root.minsize(950, 700)
        self.root.configure(bg=BG_DARK)

        # Initialize local engine if available
        if USE_LOCAL_ENGINE:
            try:
                init_db()
                self.matching_service = MatchingService()
            except Exception:
                USE_LOCAL_ENGINE = False

        # State variables
        self.selected_post_key = tk.StringVar(value=list(SAMPLE_POSTS.keys())[0])
        self.threshold_var = tk.DoubleVar(value=0.54)
        self.current_match_results: Optional[Dict[str, Any]] = None

        self._apply_theme()
        self._build_ui()

        # Load initial template content & run evaluation
        self._on_post_selected()
        self.evaluate_matching()

    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=BG_DARK)
        style.configure("Header.TFrame", background=HEADER_BG)
        style.configure("Card.TFrame", background=CARD_BG, relief="flat")

        style.configure("TLabel", background=BG_DARK, foreground=TEXT_MAIN, font=("Segoe UI", 10))
        style.configure("HeaderTitle.TLabel", background=HEADER_BG, foreground="#38bdf8", font=("Segoe UI", 15, "bold"))
        style.configure("HeaderSub.TLabel", background=HEADER_BG, foreground=TEXT_MUTED, font=("Segoe UI", 9))

        style.configure("TLabelframe", background=BG_DARK, foreground=ACCENT_BLUE, bordercolor=BORDER_COLOR)
        style.configure("TLabelframe.Label", background=BG_DARK, foreground=ACCENT_BLUE, font=("Segoe UI", 10, "bold"))

        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background=ACCENT_BLUE, foreground="#ffffff", borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#2563eb")])

        style.configure("Approve.TButton", font=("Segoe UI", 9, "bold"), background=ACCENT_GREEN, foreground="#ffffff")
        style.map("Approve.TButton", background=[("active", "#059669")])

        style.configure("Reject.TButton", font=("Segoe UI", 9, "bold"), background=ACCENT_RED, foreground="#ffffff")
        style.map("Reject.TButton", background=[("active", "#dc2626")])

    def _build_ui(self):
        # 1. Header Bar
        header = ttk.Frame(self.root, style="Header.TFrame", padding=15)
        header.pack(fill="x", side="top")

        mode_badge = "🟢 Local PyTorch Engine" if USE_LOCAL_ENGINE else f"🌐 Connected to Docker API ({API_BASE_URL})"
        title_lbl = ttk.Label(
            header,
            text=f"🦊 AI Image Understanding & Content Matching Engine  [{mode_badge}]",
            style="HeaderTitle.TLabel"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ttk.Label(
            header,
            text="Interactive Real-Time Visual Asset Matching, Cosine Vector Ranking & Mismatch Guard Safety Gate",
            style="HeaderSub.TLabel"
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        # 2. Main Layout (Notebook Tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Image Candidate Matcher
        tab_matcher = ttk.Frame(notebook, padding=10)
        notebook.add(tab_matcher, text=" 🔍 Visual Candidate Matcher ")

        # Tab 2: Audit Ledger & Telemetry
        tab_ledger = ttk.Frame(notebook, padding=10)
        notebook.add(tab_ledger, text=" 📊 Audit Ledger & Cost Telemetry ")

        self._build_matcher_tab(tab_matcher)
        self._build_ledger_tab(tab_ledger)

    def _build_matcher_tab(self, parent: ttk.Frame):
        paned = ttk.PanedWindow(parent, orient="vertical")
        paned.pack(fill="both", expand=True)

        # Top Control Box
        control_frame = ttk.LabelFrame(paned, text=" Input Query & Mismatch Guard Configuration ", padding=10)
        paned.add(control_frame, weight=1)

        # Row 1: Template selector & Threshold slider
        r1 = ttk.Frame(control_frame)
        r1.pack(fill="x", pady=5)

        ttk.Label(r1, text="Sample Article Template:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 5))
        combo = ttk.Combobox(
            r1,
            textvariable=self.selected_post_key,
            values=list(SAMPLE_POSTS.keys()),
            state="readonly",
            width=45,
            font=("Segoe UI", 9)
        )
        combo.pack(side="left", padx=5)
        combo.bind("<<ComboboxSelected>>", lambda e: self._on_post_selected())

        # Mismatch Guard Slider
        ttk.Label(r1, text="  Mismatch Guard Threshold:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(15, 5))
        self.slider_label = ttk.Label(r1, text=f"{self.threshold_var.get():.2f}", font=("Segoe UI", 10, "bold"), foreground="#fbbf24")
        
        slider = ttk.Scale(
            r1,
            from_=0.30,
            to=0.80,
            variable=self.threshold_var,
            command=self._on_threshold_slide,
            orient="horizontal",
            length=140
        )
        slider.pack(side="left", padx=5)
        self.slider_label.pack(side="left")

        # Row 2: Text Query Box
        r2 = ttk.Frame(control_frame)
        r2.pack(fill="both", expand=True, pady=5)

        ttk.Label(r2, text="Post Article Content / Search Query:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.txt_query = scrolledtext.ScrolledText(
            r2,
            height=3,
            wrap="word",
            bg="#1f2937",
            fg="#f9fafb",
            insertbackground="#ffffff",
            font=("Consolas", 10),
            bd=1,
            relief="solid"
        )
        self.txt_query.pack(fill="both", expand=True, pady=3)

        # Action Buttons Row
        r3 = ttk.Frame(control_frame)
        r3.pack(fill="x", pady=(5, 0))

        btn_run = ttk.Button(
            r3,
            text=" 🔍 Run AI Image Relevance Matching ",
            style="Primary.TButton",
            command=self.evaluate_matching
        )
        btn_run.pack(side="left", padx=(0, 10))

        self.lbl_status = ttk.Label(r3, text="Ready.", font=("Segoe UI", 9, "italic"), foreground=TEXT_MUTED)
        self.lbl_status.pack(side="left")

        # Bottom Results Box: Scrollable Candidate Canvas
        results_frame = ttk.LabelFrame(paned, text=" Image Candidate Ranking & Mismatch Guard Verdicts ", padding=10)
        paned.add(results_frame, weight=3)

        # Summary Bar inside results
        self.summary_bar = ttk.Frame(results_frame)
        self.summary_bar.pack(fill="x", side="top", pady=(0, 5))

        self.lbl_summary = ttk.Label(self.summary_bar, text="", font=("Segoe UI", 10, "bold"), foreground=TEXT_MAIN)
        self.lbl_summary.pack(side="left")

        # Scrollable area for candidate cards
        canvas_container = ttk.Frame(results_frame)
        canvas_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_container, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)

        self.cards_inner_frame = ttk.Frame(self.canvas)
        self.cards_inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_post_selected(self):
        key = self.selected_post_key.get()
        if key in SAMPLE_POSTS:
            text = SAMPLE_POSTS[key]["text"]
            self.txt_query.delete("1.0", tk.END)
            self.txt_query.insert("1.0", text)

    def _on_threshold_slide(self, val):
        t_val = float(val)
        self.slider_label.config(text=f"{t_val:.2f}")
        os.environ["MISMATCH_GUARD_THRESHOLD"] = str(t_val)
        if USE_LOCAL_ENGINE and hasattr(self, "matching_service"):
            self.matching_service.mismatch_guard_threshold = t_val

    def evaluate_matching(self):
        query_text = self.txt_query.get("1.0", tk.END).strip()
        if not query_text:
            messagebox.showwarning("Empty Query", "Please enter post article text or a search query.")
            return

        post_key = self.selected_post_key.get()
        post_id = SAMPLE_POSTS.get(post_key, {}).get("id", "p_01")

        self.lbl_status.config(text="Evaluating Mismatch Guard & candidate ranking...", foreground="#fbbf24")
        self.root.update_idletasks()

        cur_t = self.threshold_var.get()

        if USE_LOCAL_ENGINE:
            self.matching_service.mismatch_guard_threshold = cur_t
            response = self.matching_service.evaluate_candidates(post_id=post_id, post_text=query_text)
            self.current_match_results = response.model_dump()
        else:
            # REST API Fallback (Docker)
            try:
                encoded_q = urllib.parse.quote(query_text)
                url = f"{API_BASE_URL}/posts/{post_id}/images?query={encoded_q}"
                req = urllib.request.Request(url, headers={"User-Agent": "MatchingEngineGUI/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw_data = resp.read().decode("utf-8")
                    self.current_match_results = json.loads(raw_data)
            except Exception as err:
                messagebox.showerror(
                    "API Connection Error",
                    f"Unable to connect to matching server at {API_BASE_URL}.\nEnsure Docker container is running.\n\nError: {err}"
                )
                self.lbl_status.config(text="Connection failed.", foreground=ACCENT_RED)
                return

        self._render_results(self.current_match_results)
        self.lbl_status.config(text="Evaluation complete.", foreground=ACCENT_GREEN)

    def _render_results(self, data: Dict[str, Any]):
        for widget in self.cards_inner_frame.winfo_children():
            widget.destroy()

        candidates = data.get("candidates", [])
        total = len(candidates)
        approved_count = sum(1 for c in candidates if c.get("mismatch_guard", {}).get("status") == "APPROVED")
        rejected_count = total - approved_count

        top_score = data.get("top_score", 0.0)
        self.lbl_summary.config(
            text=f"Total Candidates: {total}  |  🟢 Approved: {approved_count}  |  🔴 Blocked by Guard: {rejected_count}  |  Top Similarity Score: {top_score:.4f}"
        )

        if not candidates:
            lbl_empty = ttk.Label(
                self.cards_inner_frame,
                text="No matching candidates found in database corpus. Verify database seeder or API service.",
                font=("Segoe UI", 11, "italic"),
                foreground=ACCENT_AMBER
            )
            lbl_empty.pack(pady=20)
            return

        for idx, cand in enumerate(candidates, 1):
            self._create_image_candidate_card(self.cards_inner_frame, cand, idx, data)

    def _create_image_candidate_card(self, parent: ttk.Frame, cand: Dict[str, Any], rank: int, data: Dict[str, Any]):
        image_id = cand.get("image_id", "unknown")
        subject = cand.get("subject", "Asset")
        category = cand.get("category", "general")
        caption = cand.get("caption", "No description available.")
        attributes = cand.get("attributes", [])
        score = cand.get("score", 0.0)
        guard_info = cand.get("mismatch_guard", {})
        guard_status = guard_info.get("status", "REJECTED")
        explanation = guard_info.get("explanation", "")

        is_approved = (guard_status == "APPROVED")
        border_col = ACCENT_GREEN if is_approved else ACCENT_RED

        # Outer card frame
        card = tk.Frame(parent, bg=CARD_BG, bd=1, relief="solid", highlightbackground=border_col, highlightthickness=1)
        card.pack(fill="x", expand=True, padx=5, pady=6)

        # Left thumbnail canvas
        left_frame = tk.Frame(card, bg=CARD_BG, width=150, height=110)
        left_frame.pack(side="left", padx=10, pady=10)
        left_frame.pack_propagate(False)

        self._draw_asset_thumbnail(left_frame, category, subject, rank)

        # Center details
        center_frame = tk.Frame(card, bg=CARD_BG)
        center_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        header_line = tk.Frame(center_frame, bg=CARD_BG)
        header_line.pack(anchor="w")

        lbl_rank = tk.Label(header_line, text=f"#{rank}", font=("Segoe UI", 11, "bold"), fg="#fbbf24", bg=CARD_BG)
        lbl_rank.pack(side="left", padx=(0, 6))

        lbl_title = tk.Label(header_line, text=f"{subject} [{image_id}]", font=("Segoe UI", 11, "bold"), fg=TEXT_MAIN, bg=CARD_BG)
        lbl_title.pack(side="left")

        lbl_cat = tk.Label(header_line, text=f" {category.upper()} ", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#4b5563")
        lbl_cat.pack(side="left", padx=8)

        lbl_cap = tk.Label(center_frame, text=caption, font=("Segoe UI", 9, "italic"), fg=TEXT_MUTED, bg=CARD_BG, wraplength=450, justify="left")
        lbl_cap.pack(anchor="w", pady=(3, 3))

        attr_line = tk.Frame(center_frame, bg=CARD_BG)
        attr_line.pack(anchor="w")

        for attr in attributes[:4]:
            tag = tk.Label(attr_line, text=f"• {attr}", font=("Segoe UI", 8), fg="#93c5fd", bg="#1e3a8a", padx=4, pady=1)
            tag.pack(side="left", padx=(0, 4))

        # Right side: Score & Mismatch Guard Verdict
        right_frame = tk.Frame(card, bg=CARD_BG, width=240)
        right_frame.pack(side="right", fill="y", padx=10, pady=8)

        score_frame = tk.Frame(right_frame, bg=CARD_BG)
        score_frame.pack(anchor="e")

        tk.Label(score_frame, text="Similarity Cosine:", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=CARD_BG).pack(side="left", padx=(0, 4))
        score_val_lbl = tk.Label(score_frame, text=f"{score:.4f}", font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg=CARD_BG)
        score_val_lbl.pack(side="left")

        # Score progress bar
        bar_canvas = tk.Canvas(right_frame, width=160, height=12, bg="#374151", highlightthickness=0)
        bar_canvas.pack(anchor="e", pady=(4, 6))

        bar_width = int(min(1.0, max(0.0, score)) * 160)
        bar_color = ACCENT_GREEN if is_approved else (ACCENT_AMBER if score >= 0.40 else ACCENT_RED)
        bar_canvas.create_rectangle(0, 0, bar_width, 12, fill=bar_color, width=0)

        # Guard Status Badge
        badge_bg = ACCENT_GREEN if is_approved else ACCENT_RED
        badge_text = "🟢 APPROVED MATCH" if is_approved else "🔴 REJECTED BY GUARD"

        badge = tk.Label(
            right_frame,
            text=f" {badge_text} ",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg=badge_bg,
            padx=6,
            pady=3
        )
        badge.pack(anchor="e")

        lbl_exp = tk.Label(
            right_frame,
            text=explanation,
            font=("Segoe UI", 8),
            fg=ACCENT_GREEN if is_approved else "#fca5a5",
            bg=CARD_BG,
            wraplength=230,
            justify="right"
        )
        lbl_exp.pack(anchor="e", pady=(3, 4))

        # Human Review Action Buttons
        btn_frame = tk.Frame(right_frame, bg=CARD_BG)
        btn_frame.pack(anchor="e")

        post_id = data.get("post_id", "p_01")
        btn_approve = ttk.Button(
            btn_frame,
            text="👍 Approve",
            style="Approve.TButton",
            command=lambda: self._on_human_review(post_id, image_id, "APPROVED")
        )
        btn_approve.pack(side="left", padx=2)

        btn_reject = ttk.Button(
            btn_frame,
            text="👎 Reject",
            style="Reject.TButton",
            command=lambda: self._on_human_review(post_id, image_id, "REJECTED")
        )
        btn_reject.pack(side="left", padx=2)

    def _draw_asset_thumbnail(self, parent: tk.Frame, category: str, subject: str, rank: int):
        canvas = tk.Canvas(parent, width=150, height=110, bg="#111827", highlightthickness=1, highlightbackground="#374151")
        canvas.pack(fill="both", expand=True)

        category_colors = {
            "fox": ("#d97706", "#78350f", "🦊"),
            "wolf": ("#475569", "#0f172a", "🐺"),
            "bear": ("#854d0e", "#451a03", "🐻"),
            "eagle": ("#1e40af", "#1e1b4b", "🦅"),
            "engine": ("#0284c7", "#0c4a6e", "⚙️")
        }

        top_color, btm_color, icon = category_colors.get(category.lower(), ("#374151", "#111827", "🖼️"))

        for i in range(110):
            r1, g1, b1 = int(top_color[1:3], 16), int(top_color[3:5], 16), int(top_color[5:7], 16)
            r2, g2, b2 = int(btm_color[1:3], 16), int(btm_color[3:5], 16), int(btm_color[5:7], 16)
            ratio = i / 110.0
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color_hex = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(0, i, 150, i, fill=color_hex)

        canvas.create_text(75, 45, text=icon, font=("Segoe UI Emoji", 26))
        canvas.create_text(75, 82, text=subject, font=("Segoe UI", 9, "bold"), fill="#ffffff")
        canvas.create_text(75, 96, text=f"Asset #{rank}", font=("Segoe UI", 8), fill="#cbd5e1")

    def _on_human_review(self, post_id: str, image_id: str, action: str):
        if USE_LOCAL_ENGINE:
            success = update_review_status(post_id=post_id, image_id=image_id, action=action)
        else:
            try:
                url = f"{API_BASE_URL}/review/action"
                payload = json.dumps({"post_id": post_id, "image_id": image_id, "action": action}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    success = (res_json.get("status") == "SUCCESS")
            except Exception as e:
                success = False

        if success:
            messagebox.showinfo("Audit Logged", f"Human review state resolved to [{action}] for post '{post_id}' and asset '{image_id}'.")
            self.refresh_ledger()
        else:
            messagebox.showerror("Error", f"Failed to record review action for {image_id}.")

    def _build_ledger_tab(self, parent: ttk.Frame):
        lbl = ttk.Label(parent, text="📋 Human Audit Review Ledger & Financial Token Telemetry", font=("Segoe UI", 12, "bold"))
        lbl.pack(anchor="w", pady=(0, 10))

        btn_refresh = ttk.Button(parent, text=" 🔄 Refresh Ledger Data ", style="Primary.TButton", command=self.refresh_ledger)
        btn_refresh.pack(anchor="w", pady=(0, 10))

        columns = ("id", "post_id", "image_id", "score", "guard_status", "status", "timestamp")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        self.tree.heading("id", text="ID")
        self.tree.heading("post_id", text="Post ID")
        self.tree.heading("image_id", text="Image ID")
        self.tree.heading("score", text="Similarity Score")
        self.tree.heading("guard_status", text="Guard Status")
        self.tree.heading("status", text="Human Audit Action")
        self.tree.heading("timestamp", text="Timestamp")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("post_id", width=90, anchor="center")
        self.tree.column("image_id", width=90, anchor="center")
        self.tree.column("score", width=110, anchor="center")
        self.tree.column("guard_status", width=130, anchor="center")
        self.tree.column("status", width=140, anchor="center")
        self.tree.column("timestamp", width=220, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.refresh_ledger()

    def refresh_ledger(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if USE_LOCAL_ENGINE:
            entries = fetch_review_ledger()
        else:
            try:
                url = f"{API_BASE_URL}/review/ledger"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    entries = data.get("review_ledger", [])
            except Exception:
                entries = []

        for row in entries:
            self.tree.insert("", "end", values=(
                row.get("id"),
                row.get("post_id"),
                row.get("image_id"),
                f"{row.get('score', 0.0):.4f}",
                row.get("guard_status"),
                row.get("status"),
                row.get("timestamp")
            ))


def main():
    root = tk.Tk()
    app = ImageMatchingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
