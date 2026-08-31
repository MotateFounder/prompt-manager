from __future__ import annotations
import json
import re
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from datetime import datetime

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

# Regex for finding {{variable_name}} in strings
VARIABLE = re.compile(r"{{\s*([^{}]+?)\s*}}")

# Default prompt structure
DEFAULT = {
    "name": "new_prompt",
    "category": "General",
    "tag": "draft",
    "description": "",
    "versions": [
        {
            "version": "1.0.0",
            "system": "You are a helpful assistant.",
            "user": "{{input}}",
            "variables": {"input": "Test input"},
            "rating": 0
        }
    ]
}

# UI Styling Constants
UI_FONTS = {
    "base_font": ("Segoe UI", 16),
    "button_font": ("Segoe UI", 15),
    "button_font_bold": ("Segoe UI", 15, "bold"),
    "heading_font": ("Segoe UI", 22, "bold"),
    "section_font": ("Segoe UI", 12, "bold"),
    "editor_font": ("Segoe UI", 14),
}

UI_PADDING = {
    "button_padding": (6, 3),
    "accent_button_padding": (10, 5),
    "entry_padding": 4,
    "window_padding": (7, 7),
    "panel_padding": 8,
    "editor_panel_padding": 8,
    "toolbar_gap": 4,
    "toolbar_group_gap": 4,
    "variables_height": 250,
}

COLORS = {
    "light": {
        "bg": "#edf2f7",
        "card": "#ffffff",
        "field": "#f8fafc",
        "text": "#17212b",
        "accent": "#1769aa",
        "accent_bg": "#d9edff",
        "border": "#cbd6e2",
    },
    "dark": {
        "bg": "#17212b",
        "card": "#22303d",
        "field": "#1b2835",
        "text": "#edf4fa",
        "accent": "#79c7ff",
        "accent_bg": "#28506b",
        "border": "#405466",
    },
}

# =============================================================================
# MAIN APPLICATION CLASS
# =============================================================================

class PromptManager(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Window Setup
        self.title("Prompt Manager")
        self.geometry("1380x900")
        self.minsize(1100, 700)
        
        # Paths and Data
        self.config_path = Path(__file__).with_name(".prompt_manager_config.json")
        self.root_dir = self.load_saved_folder() or Path.cwd() / "prompts"
        self.current_path = None
        self.current_data = None
        self.variable_entries = {}
        self.dark_mode = False
        
        # Initialization Sequence
        self.setup_style()
        self.build_ui()
        self.refresh()

    # --------------------------------------------------------------------------
    # Configuration & Theme Management
    # --------------------------------------------------------------------------

    def load_saved_folder(self) -> Path:
        try:
            saved = Path(json.loads(self.config_path.read_text(encoding="utf-8")).get("prompts_folder", ""))
            return saved if saved.is_dir() else None
        except (OSError, ValueError, TypeError):
            return None

    def remember_folder(self):
        try:
            self.config_path.write_text(json.dumps({"prompts_folder": str(self.root_dir)}, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass

    def setup_style(self):
        ttk.Style(self).theme_use("clam")
        self.apply_theme()

    def apply_theme(self):
        c = COLORS["dark" if self.dark_mode else "light"]
        ui = UI_FONTS
        
        self.configure(bg=c["bg"])
        s = ttk.Style(self)
        
        # Style configurations
        s.configure("TFrame", background=c["bg"])
        s.configure("Card.TFrame", background=c["card"], relief="solid", borderwidth=1)
        s.configure("TLabelframe", background=c["card"])
        s.configure("TLabelframe.Label", background=c["card"], foreground=c["accent"], font=ui["section_font"])
        s.configure("TLabel", background=c["bg"], foreground=c["text"], font=ui["base_font"])
        s.configure("Header.TLabel", background=c["bg"], foreground=c["accent"], font=ui["heading_font"])
        s.configure("TButton", font=ui["button_font"], padding=UI_PADDING["button_padding"])
        s.configure("Accent.TButton", background=c["accent_bg"], foreground=c["text"], font=ui["button_font_bold"], padding=UI_PADDING["accent_button_padding"])
        s.configure("TEntry", font=ui["base_font"], padding=UI_PADDING["entry_padding"])
        s.configure("TCombobox", font=ui["base_font"], padding=UI_PADDING["entry_padding"])
        s.configure("TSpinbox", font=ui["base_font"], padding=UI_PADDING["entry_padding"])

        # Update themed custom widgets
        for w in getattr(self, "_themed_widgets", []):
            try:
                w.configure(background=c["field"], foreground=c["text"], insertbackground=c["text"])
            except tk.TclError:
                pass
        
        if hasattr(self, "var_canvas"):
            self.var_canvas.configure(background=c["card"])
        if hasattr(self, "output"):
            self.output.configure(background=c["field"], foreground=c["text"], insertbackground=c["text"])
        if hasattr(self, "theme_button"):
            self.theme_button.configure(text="☀ Day mode" if self.dark_mode else "☾ Night mode")

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    # --------------------------------------------------------------------------
    # UI Layout Construction
    # --------------------------------------------------------------------------

    def build_ui(self):
        # --- Top Toolbar ---
        top = ttk.Frame(self, padding=UI_PADDING["window_padding"])
        top.pack(fill="x")

        ttk.Button(top, text="Folder", command=self.choose_folder).pack(side="left")
        ttk.Button(top, text="New", command=self.new_prompt).pack(side="left", padx=(18, 4))
        ttk.Button(top, text="Save", command=self.save_prompt).pack(side="left", padx=4)
        ttk.Button(top, text="Save as", command=self.save_as_version).pack(side="left")
        ttk.Button(top, text="Copy", style="Accent.TButton", command=self.copy_prompt).pack(side="left", padx=(18, 4))
        ttk.Button(top, text="Import", command=self.import_repo).pack(side="left", padx=(18, 4))
        ttk.Button(top, text="Commit", command=self.commit_repo).pack(side="left", padx=4)
        ttk.Button(top, text="Push", command=self.push_repo).pack(side="left")

        # --- Main Layout Container ---
        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=UI_PADDING["window_padding"][0], pady=(0, 12))

        left = ttk.Frame(body, style="Card.TFrame", padding=UI_PADDING["panel_padding"])
        right = ttk.Frame(body, style="Card.TFrame", padding=UI_PADDING["editor_panel_padding"])
        body.add(left, weight=1)
        body.add(right, weight=4)

        # --- Left Panel: File Browser ---
        ttk.Label(left, text="Prompt files", style="Header.TLabel").pack(anchor="w")
        
        filter_frame = ttk.Frame(left)
        filter_frame.pack(fill="x", pady=(14, 12))

        self.filter_var = tk.StringVar(value="all")
        self.filter_box = ttk.Combobox(
            filter_frame, textvariable=self.filter_var, state="readonly", 
            values=("all", "tags", "categories"), width=11
        )
        self.filter_box.pack(side="left")
        self.filter_box.bind("<<ComboboxSelected>>", lambda _: self.refresh())

        self.filter_text = ttk.Entry(filter_frame)
        self.filter_text.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.filter_text.bind("<KeyRelease>", lambda _: self.refresh())

        self.files = ttk.Treeview(left, show="tree", selectmode="browse")
        self.files.pack(fill="both", expand=True)
        self.files.bind("<<TreeviewSelect>>", self.load_selected)

        # --- Right Panel: Editor Tabs ---
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True)

        # --- Editor Tab ---
        editor_tab = ttk.Frame(self.tabs)
        self.tabs.add(editor_tab, text="Prompt")

        # Scrollable Canvas Setup
        editor_canvas = tk.Canvas(editor_tab, highlightthickness=0, borderwidth=0)
        editor_scrollbar = ttk.Scrollbar(editor_tab, orient="vertical", command=editor_canvas.yview)
        editor_canvas.configure(yscrollcommand=editor_scrollbar.set)
        editor_canvas.pack(side="left", fill="both", expand=True)
        editor_scrollbar.pack(side="right", fill="y")

        editor = ttk.Frame(editor_canvas, padding=UI_PADDING["editor_panel_padding"])
        editor_window = editor_canvas.create_window((0, 0), window=editor, anchor="nw")

        def update_editor_scroll_region(event=None):
            editor_canvas.configure(scrollregion=editor_canvas.bbox("all"))

        def resize_editor_width(event):
            editor_canvas.itemconfigure(editor_window, width=event.width)

        editor.bind("<Configure>", update_editor_scroll_region)
        editor_canvas.bind("<Configure>", resize_editor_width)

        # Custom Scroll Logic
        def scroll_editor(event):
            pointer_widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
            if pointer_widget is None: return
            
            widget = pointer_widget
            while widget is not None:
                if widget in (self.system, self.user, self.output, self.var_canvas):
                    return
                try:
                    widget = widget.master
                except AttributeError:
                    break
            
            editor_canvas.yview_scroll(
                -int(event.delta / 120) if event.delta else (-1 if event.num == 4 else 1),
                "units"
            )
            return "break"

        editor_canvas.bind("<MouseWheel>", scroll_editor, add="+")
        editor_canvas.bind("<Button-4>", scroll_editor, add="+")
        editor_canvas.bind("<Button-5>", scroll_editor, add="+")

        # --- Metadata Details ---
        meta = ttk.LabelFrame(editor, text="Prompt details", padding=UI_PADDING["panel_padding"])
        meta.pack(fill="x")

        self.name = self.field(meta, "Name", 0)
        self.category = self.field(meta, "Category", 1)
        self.tag = self.field(meta, "Tag", 2)
        self.description = self.field(meta, "Description", 3)

        ttk.Label(meta, text="Version").grid(row=0, column=2, sticky="w", padx=(18, 6))
        self.version_var = tk.StringVar()
        self.version_box = ttk.Combobox(meta, textvariable=self.version_var, state="readonly", width=18, height=20)
        self.version_box.grid(row=0, column=3, sticky="ew")
        self.version_box.bind("<<ComboboxSelected>>", self.change_version)

        ttk.Label(meta, text="Rating").grid(row=1, column=2, sticky="w", padx=(18, 6))
        self.rating_var = tk.IntVar(value=0)
        ttk.Spinbox(meta, from_=0, to=5, textvariable=self.rating_var, width=5).grid(row=1, column=3, sticky="w")

        meta.columnconfigure(1, weight=1)
        meta.columnconfigure(3, weight=1)

        # --- Templates Section ---
        templates = ttk.Frame(editor)
        templates.pack(fill="both", expand=True, pady=(12, 0))

        system_frame = ttk.LabelFrame(templates, text="System template", padding=UI_PADDING["panel_padding"])
        system_frame.pack(fill="both", expand=True)
        self.system = tk.Text(system_frame, height=3, wrap="word", font=UI_FONTS["editor_font"], bg="#ffffff", relief="flat", padx=10, pady=8)
        self.system.pack(fill="both", expand=True)

        user_frame = ttk.LabelFrame(templates, text="User template", padding=UI_PADDING["panel_padding"])
        user_frame.pack(fill="both", expand=True, pady=(12, 0))
        self.user = tk.Text(user_frame, height=7, wrap="word", font=UI_FONTS["editor_font"], bg="#ffffff", relief="flat", padx=10, pady=8)
        self.user.pack(fill="both", expand=True)
        self.user.bind("<KeyRelease>", lambda _: (self.rebuild_variables(), self.schedule_autosave()))

        # --- Template Variables Section ---
        self.varbox = ttk.LabelFrame(editor, text="Template variables", padding=UI_PADDING["panel_padding"])
        self.varbox.pack(fill="both", expand=True, pady=(12, 0))

        self.var_canvas = tk.Canvas(self.varbox, height=350, bg="#f8fafc", highlightthickness=0)
        self.var_canvas.pack(side="left", fill="both", expand=True)

        variable_scrollbar = ttk.Scrollbar(self.varbox, orient="vertical", command=self.var_canvas.yview)
        variable_scrollbar.pack(side="right", fill="y")
        self.var_canvas.configure(yscrollcommand=variable_scrollbar.set)

        self.var_frame = ttk.Frame(self.var_canvas)
        self.var_canvas.create_window((0, 0), window=self.var_frame, anchor="nw")
        self.var_scroll_active = False

        self.bind_variable_scroll(self.varbox)
        self.bind_variable_scroll(self.var_canvas)
        self.bind_variable_scroll(self.var_frame)

        # --- Preview Tab ---
        preview = ttk.Frame(self.tabs, padding=UI_PADDING["editor_panel_padding"])
        self.tabs.add(preview, text="Rendered preview")

        ttk.Label(preview, text="Rendered prompt", style="Header.TLabel").pack(anchor="w")
        self.output = tk.Text(preview, wrap="word", state="disabled", font=UI_FONTS["editor_font"], bg="#ffffff", relief="flat", padx=12, pady=12)
        self.output.pack(fill="both", expand=True, pady=(12, 0))

        # --- Status Bar ---
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w", padding=(12, 6)).pack(fill="x")

        # --- Bindings & Theme Registration ---
        for entry in (self.name, self.category, self.tag, self.description):
            entry.bind("<KeyRelease>", lambda _: self.schedule_autosave())

        self._themed_widgets = [self.system, self.user, self.output]
        self.system.bind("<KeyRelease>", lambda _: self.schedule_autosave())
        self.rating_var.trace_add("write", lambda *_: self.schedule_autosave())

    # --------------------------------------------------------------------------
    # Helper Methods
    # --------------------------------------------------------------------------

    def field(self, p, label, row):
        ttk.Label(p, text=label).grid(row=row, column=0, sticky="w", pady=3)
        e = ttk.Entry(p)
        e.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=3)
        return e

    # --------------------------------------------------------------------------
    # File & Folder Management
    # --------------------------------------------------------------------------

    def choose_folder(self):
        c = filedialog.askdirectory(initialdir=str(self.root_dir.parent))
        if c:
            self.root_dir = Path(c)
            self.remember_folder()
            self.refresh()

    def files_data(self):
        self.root_dir.mkdir(parents=True, exist_ok=True)
        out = []
        grouped = {}
        consolidated = set()

        # Identify unique prompts from existing files
        for p in self.root_dir.glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if "versions" in d: consolidated.add(d.get("name", p.stem))
            except Exception: pass

        # Group files into prompt objects
        for p in self.root_dir.glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            
            if "versions" in d:
                out.append((p, d))
                continue

            stem = p.stem
            match = re.match(r"^(.*)\.v([^.]*(?:\.[^.]+)*)$", stem)
            name = match.group(1) if match else d.get("name", stem)
            version = match.group(2) if match else d.get("version", "1.0.0")
            
            if name in consolidated: continue
            
            if name not in grouped:
                grouped[name] = (p, {
                    "name": name,
                    "category": d.get("category", "General"),
                    "tag": d.get("tag", "draft"),
                    "description": d.get("description", ""),
                    "versions": []
                })
                out.append(grouped[name])
            
            grouped[name][1]["versions"].append({**d, "version": version})
        
        return out

    def refresh(self):
        for x in self.files.get_children(): self.files.delete(x)
        
        mode = self.filter_var.get()
        q = self.filter_text.get().lower()
        self.entries = sorted(self.files_data(), key=lambda x: x[1].get("name", "").lower())
        
        groups = {}
        seen_groups = {}

        for _, d in self.entries:
            searchable = json.dumps(d, ensure_ascii=False).lower()
            raw_value = d.get("tag", "") if mode == "tags" else d.get("category", "")
            values = [x.strip() for x in str(raw_value).split(",") if x.strip()] or ["(uncategorized)"]
            
            if not q or q in searchable:
                if mode == "all":
                    self.files.insert("", "end", text=d.get("name", ""), values=(d.get("name", ""),))
                else:
                    for value in values:
                        if value not in groups:
                            groups[value] = self.files.insert("", "end", text=value, open=True)
                        group = groups[value]
                        seen = seen_groups.setdefault(value, set())
                        if d.get("name", "") not in seen:
                            self.files.insert(group, "end", text=d.get("name", ""), values=(d.get("name", ""),))
                            seen.add(d.get("name", ""))
        
        self.status.set(f"Folder: {self.root_dir}")

    # --------------------------------------------------------------------------
    # Content Manipulation
    # --------------------------------------------------------------------------

    def new_prompt(self):
        self.current_path = None
        self.current_data = json.loads(json.dumps(DEFAULT))
        self.put(self.current_data)

    def load_selected(self, _=None):
        sel = self.files.selection()
        if not sel: return
        
        n = self.files.item(sel[0], "values")
        n = n[0] if n else ""
        found = next(((p, d) for p, d in self.entries if d.get("name") == n), None)
        
        if found:
            self.current_path, self.current_data = found
            self.put(self.current_data)

    def put(self, d):
        # Keep the editor in a valid state even if a file was not loaded or
        # contains an empty/null JSON value.
        if not isinstance(d, dict):
            d = json.loads(json.dumps(DEFAULT))
            self.current_data = d

        for e in (self.name, self.category, self.tag, self.description):
            e.delete(0, tk.END)
        
        self.name.insert(0, d.get("name", ""))
        self.category.insert(0, d.get("category", "General"))
        self.tag.insert(0, d.get("tag", "draft"))
        self.description.insert(0, d.get("description", ""))
        
        versions = d.get("versions", [])
        if not isinstance(versions, list):
            versions = []

        versions = [v for v in versions if isinstance(v, dict)]
        if not versions:
            versions = json.loads(json.dumps(DEFAULT["versions"]))

        d["versions"] = versions
        self.current_data = d

        vs = sorted(versions, key=lambda x: x.get("version", ""))
        self.version_box["values"] = [v.get("version", "") for v in vs]
        self.version_var.set(vs[-1].get("version", "") if vs else "")
        self.show_version()

    def selected_version(self):
        """Return the selected version, or a safe empty version."""
        if not isinstance(self.current_data, dict):
            return {}

        versions = self.current_data.get("versions", [])
        if not isinstance(versions, list):
            return {}

        selected = self.version_var.get()
        version = next(
            (
                v for v in versions
                if isinstance(v, dict) and v.get("version") == selected
            ),
            None
        )
        return version if version is not None else (versions[0] if versions else {})

    def show_version(self):
        v = self.selected_version()
        self.system.delete("1.0", tk.END)
        self.user.delete("1.0", tk.END)
        self.system.insert("1.0", v.get("system", ""))
        self.user.insert("1.0", v.get("user", ""))
        self.rating_var.set(int(v.get("rating", 0)))
        self.rebuild_variables()

    def change_version(self, _=None):
        self.show_version()

    def rebuild_variables(self):
        old = {k: b.get("1.0", tk.END).rstrip() for k, b in self.variable_entries.items()}
        version = self.selected_version()
        stored_variables = version.get("variables", {})
        if not isinstance(stored_variables, dict):
            stored_variables = {}

        self.variable_entries.clear()
        
        # Destroy existing variable widgets
        for w in self.var_frame.winfo_children():
            w.destroy()

        keys = list(dict.fromkeys(VARIABLE.findall(self.user.get("1.0", tk.END))))
        
        for i, k in enumerate(keys):
            row = i * 2
            # Label
            label = ttk.Label(self.var_frame, text=k)
            label.grid(row=row, column=0, sticky="w", pady=(2, 0))
            self.bind_variable_scroll(label)
            
            # Text Box
            box = tk.Text(self.var_frame, height=2, wrap="word", font=UI_FONTS["editor_font"], bg="#fff", relief="solid", borderwidth=1)
            box.grid(row=row+1, column=0, sticky="ew")
            box.insert("1.0", old.get(k, stored_variables.get(k, "")))
            box.bind("<KeyRelease>", lambda _: (self.render_preview(), self.schedule_autosave()))
            
            # Resizable Grip
            grip = tk.Frame(self.var_frame, height=6, bg="#d5e5ef", cursor="sb_v_double_arrow")
            grip.grid(row=row+2, column=0, sticky="ew", pady=(0, 6))
            grip.bind("<Button-1>", lambda event, w=box: self.start_resize(event, w))
            grip.bind("<B1-Motion>", lambda event, w=box: self.resize_text(event, w))
            self.bind_variable_scroll(grip)
            
            self.variable_entries[k] = box
        
        self.var_frame.columnconfigure(0, weight=1)
        self.var_frame.update_idletasks()
        self.var_canvas.configure(scrollregion=self.var_canvas.bbox("all"))
        self.render_preview()

    # --------------------------------------------------------------------------
    # Interactivity & Scrolling
    # --------------------------------------------------------------------------

    def bind_variable_scroll(self, widget):
        widget.bind("<Enter>", lambda _: setattr(self, "var_scroll_active", True), add="+")
        widget.bind("<Leave>", lambda _: setattr(self, "var_scroll_active", False), add="+")
        widget.bind("<MouseWheel>", self.scroll_variables, add="+")
        widget.bind("<Button-4>", self.scroll_variables, add="+")
        widget.bind("<Button-5>", self.scroll_variables, add="+")

    def scroll_variables(self, event):
        if not getattr(self, "var_scroll_active", False): return
        if getattr(event, "num", None) == 4: units = -1
        elif getattr(event, "num", None) == 5: units = 1
        else: units = -int(event.delta/120) if event.delta else 0
        self.var_canvas.yview_scroll(units, "units")
        return "break"

    def start_resize(self, event, widget):
        widget._resize_start_y = event.y_root
        widget._resize_start_height = int(widget.cget("height"))

    def resize_text(self, event, widget):
        delta = event.y_root - widget._resize_start_y
        new_height = max(2, min(30, widget._resize_start_height + round(delta/16)))
        widget.configure(height=new_height)
        self.var_frame.update_idletasks()
        self.var_canvas.configure(scrollregion=self.var_canvas.bbox("all"))
        self.render_preview()
        self.schedule_autosave()

    # --------------------------------------------------------------------------
    # Persistence & Rendering
    # --------------------------------------------------------------------------

    def collect(self):
        if not self.name.get().strip(): raise ValueError("Name cannot be empty")
        if not isinstance(self.current_data, dict):
            self.current_data = json.loads(json.dumps(DEFAULT))

        if not self.current_data.get("versions"):
            self.current_data["versions"] = json.loads(json.dumps(DEFAULT["versions"]))

        v = self.selected_version()
        version_name = self.version_var.get().strip() or v.get("version", "1.0.0")
        self.version_var.set(version_name)
        v.update(
            version=version_name,
            system=self.system.get("1.0", tk.END).rstrip(),
            user=self.user.get("1.0", tk.END).rstrip(),
            variables={k: b.get("1.0", tk.END).rstrip() for k, b in self.variable_entries.items()},
            rating=int(self.rating_var.get())
        )
        self.current_data.update(
            name=self.name.get().strip(),
            category=self.category.get().strip(),
            tag=self.tag.get().strip(),
            description=self.description.get().strip()
        )

    def save_prompt(self):
        try:
            self.collect()
            p = self.current_path or self.root_dir / f"{self.current_data['name']}.json"
            p.write_text(json.dumps(self.current_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            self.current_path = p
            self.refresh()
            self.status.set(f"Saved {p.name}")
        except Exception as e:
            messagebox.showerror("Cannot save", str(e))

    def save_as_version(self):
        try:
            self.collect()
            nums = []
            for item in self.current_data["versions"]:
                try: nums.append(tuple(map(int, item.get("version", "0.0.0").split("."))))
                except ValueError: pass
            
            base = list(max(nums or [(0, 0, 0)]))
            base[-1] += 1
            suggested = ".".join(map(str, base))
            
            ver = simpledialog.askstring("Version", "New version:", initialvalue=suggested, parent=self)
            if ver:
                versions = [v.get("version") for v in self.current_data["versions"]]
                if ver in versions and not messagebox.askyesno("Version exists", f"Version {ver} already exists. Overwrite it?", parent=self):
                    return
                
                n = json.loads(json.dumps(self.selected_version()))
                n["version"] = ver
                self.current_data["versions"] = [v for v in self.current_data["versions"] if v.get("version") != ver] + [n]
                self.version_var.set(ver)
                self.save_prompt()
        except Exception as e:
            messagebox.showerror("Cannot save version", str(e))

    def rendered(self):
        v = self.selected_version()
        vals = {k: b.get("1.0", tk.END).rstrip() for k, b in self.variable_entries.items()}
        rep = lambda s: VARIABLE.sub(lambda m: vals.get(m.group(1).strip(), m.group(0)), s)
        return f"{rep(v.get('system', ''))}\n\n{rep(v.get('user', ''))}"

    def render_preview(self):
        if self.current_data:
            self.output.configure(state="normal")
            self.output.delete("1.0", tk.END)
            self.output.insert("1.0", self.rendered())
            self.output.configure(state="disabled")

    def copy_prompt(self):
        self.clipboard_clear()
        self.clipboard_append(self.rendered())
        self.update()
        self.status.set("Rendered prompt copied to clipboard")

    def schedule_autosave(self):
        if not self.current_path or not self.current_data: return
        if hasattr(self, "autosave_job"):
            self.after_cancel(self.autosave_job)
        self.autosave_job = self.after(700, self._autosave)

    def _autosave(self):
        try:
            self.collect()
            self.current_path.write_text(json.dumps(self.current_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            self.status.set("Automatically saved")
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Git / Repository Operations
    # --------------------------------------------------------------------------

    def repo_dir(self):
        return self.root_dir if (self.root_dir / ".git").exists() else \
               (self.root_dir.parent if (self.root_dir.parent / ".git").exists() else self.root_dir)

    def import_repo(self):
        url = simpledialog.askstring("Import repository", "Git repository URL:", parent=self)
        if not url: return
        destination = filedialog.askdirectory(title="Select clone destination", initialdir=str(self.root_dir.parent))
        if not destination: return
        
        name = url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git") or "prompt-repository"
        target = Path(destination) / name
        
        try:
            if target.exists() and any(target.iterdir()):
                raise ValueError(f"Destination already contains files: {target}")
            
            r = subprocess.run(["git", "clone", url, str(target)], capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(r.stderr.strip() or "Git clone failed")
            
            self.root_dir = target / "prompts" if (target / "prompts").is_dir() else target
            self.remember_folder()
            self.current_path = None
            self.current_data = None
            self.refresh()
            self.status.set(f"Imported and selected {self.root_dir}")
        except Exception as e:
            messagebox.showerror("Import failed", str(e))

    def commit_repo(self, silent=False):
        try:
            repo = self.repo_dir()
            repo.mkdir(parents=True, exist_ok=True)
            
            if not (repo / ".git").exists():
                subprocess.run(["git", "-C", str(repo), "init"], check=True, capture_output=True, text=True)
            
            subprocess.run(["git", "-C", str(repo), "add", str(self.root_dir)], check=True, capture_output=True, text=True)
            
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            r = subprocess.run(["git", "-C", str(repo), "commit", "-m", f"Update prompts {stamp}"], capture_output=True, text=True)
            
            if r.returncode and "nothing to commit" not in (r.stdout + r.stderr).lower():
                raise RuntimeError(r.stderr.strip() or r.stdout.strip())
            
            self.status.set("Committed successfully")
            return True
        except Exception as e:
            if not silent:
                messagebox.showerror("Commit failed", str(e))
            return False

    def push_repo(self):
        if not self.commit_repo(silent=True):
            messagebox.showerror("Push failed", "The prompts could not be committed first.")
            return
        
        try:
            repo = self.repo_dir()
            remote = subprocess.run(["git", "-C", str(repo), "remote", "get-url", "origin"], capture_output=True, text=True)
            
            if remote.returncode:
                try:
                    check = subprocess.run(["gh", "--version"], capture_output=True, text=True)
                except FileNotFoundError:
                    raise RuntimeError("No GitHub remote is configured, and GitHub CLI (gh.exe) was not found. Install GitHub CLI and run 'gh auth login', or import a repository that already has an origin remote.")
                
                if check.returncode:
                    raise RuntimeError("GitHub CLI is installed but not authenticated. Run 'gh auth login' and try again.")
                
                name = simpledialog.askstring("Private GitHub repository", "Repository name (for example: my-prompts):", parent=self)
                if not name: return
                
                r = subprocess.run(["gh", "repo", "create", name, "--private", "--source", str(repo), "--remote", "origin", "--push"], capture_output=True, text=True)
            else:
                r = subprocess.run(["git", "-C", str(repo), "push", "-u", "origin", "HEAD"], capture_output=True, text=True)
            
            if r.returncode:
                raise RuntimeError(r.stderr.strip() or r.stdout.strip() or "Push failed")
            
            self.status.set("Successful — changes pushed to GitHub")
        except Exception as e:
            messagebox.showerror("Push failed", str(e))

if __name__ == "__main__":
    PromptManager().mainloop()
