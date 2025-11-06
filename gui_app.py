# gui_app.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import datetime
import subprocess
import os
import logging
from api.export_service import run_export
from utils.logging_setup import get_logger
from core.version import __version__, PRODUCT_NAME

# Initialize logger with default INFO level
log = get_logger(__name__, level="INFO")

# App constants
APP_NAME = PRODUCT_NAME
WINDOW_TITLE = f"{APP_NAME} {__version__}"

class CalendarWindow:
    """Calendar window with clickable F1 schedule and direct export"""
    
    def __init__(self, parent_gui, season=2025):
        self.parent_gui = parent_gui
        self.season = season
        self.window = None
        self.schedule_data = []
        
        self.create_window()
        self.load_schedule()
        
    def create_window(self):
        """Create calendar window"""
        self.window = tk.Toplevel(self.parent_gui.root)
        self.window.title(f"F1 Calendar {self.season}")
        self.window.geometry("900x600")
        self.window.transient(self.parent_gui.root)
        
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(search_frame, text="Filter:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_schedule)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(0, 10))
        
        ttk.Button(search_frame, text="Refresh", command=self.load_schedule).pack(side="left")
        
        # Treeview for schedule - schlanke 4-Spalten Version
        cols = ("Round", "Date", "Grand Prix", "Circuit")
        self.tree = ttk.Treeview(main_frame, columns=cols, show="headings", height=16)
        
        # Configure columns with optimized widths
        for c, w in zip(cols, (70, 110, 300, 260)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")
            
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind events
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        
        # Context menu mit All Sessions Option
        self.context_menu = tk.Menu(self.window, tearoff=0)
        for label, code in [("Export Practice","Practice"),("Export Qualifying","Qualifying"),("Export Sprint","Sprint"),("Export Race","Race")]:
            self.context_menu.add_command(label=label, command=lambda c=code: self.export_session(c))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Export All Sessions", command=lambda: self.export_session("All Sessions"))
        
    def load_schedule(self):
        """Load F1 schedule data"""
        try:
            from api.providers.router import get_provider
            
            self.parent_gui.log_message(f"Loading F1 {self.season} calendar...", "INFO")
            provider = get_provider()  # Auto-Fallback Jolpica→FastF1
            self.schedule_data = provider.schedule(self.season)
            
            self.populate_tree()
            self.parent_gui.log_message(f"Calendar loaded: {len(self.schedule_data)} rounds", "INFO")
            
        except Exception as e:
            self.parent_gui.log_message(f"Failed to load calendar: {e}", "ERROR")
            
    def _fmt_date(self, iso_str: str) -> str:
        """Format date to DD.MM.YYYY"""
        try:
            from datetime import datetime
            d = datetime.fromisoformat(str(iso_str).split("T")[0])
            return d.strftime("%d.%m.%Y")
        except Exception:
            return str(iso_str)
    
    def populate_tree(self):
        """Populate treeview with schedule data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Build rows with sprint detection (keep internal)
        self._all_rows = []
        for event in self.schedule_data:
            rnd = event.get("round", "")
            date_formatted = self._fmt_date(event.get("date", ""))
            gp = event.get("raceName", "") or event.get("EventName", "")
            circuit = event.get("Circuit", {}).get("circuitName", "") or f"{event.get('Location','')} ({event.get('Country','')})"
            has_sprint = "sprint" in str(event.get("EventFormat","")).lower() or event.get("hasSprint", False)
            
            row = {
                "round": int(rnd) if str(rnd).isdigit() else 0,
                "date": date_formatted,
                "gp": gp,
                "circuit": circuit,
                "has_sprint": has_sprint
            }
            self._all_rows.append(row)
            
            # Insert only 4 columns into tree
            self.tree.insert("", "end", values=(row["round"], row["date"], row["gp"], row["circuit"]))
            
    def filter_schedule(self, *args):
        """Filter schedule based on search text"""
        search_text = self.search_var.get().lower()
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add filtered items from _all_rows
        for row in getattr(self, '_all_rows', []):
            # Check if search text matches any field
            searchable = f"{row.get('gp', '')} {row.get('circuit', '')}"
            if search_text in searchable.lower():
                self.tree.insert("", "end", values=(row["round"], row["date"], row["gp"], row["circuit"]))
                
    def on_double_click(self, event):
        """Handle double-click on schedule item"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            vals = item["values"]
            if vals:
                round_no = int(vals[0]) if str(vals[0]).isdigit() else 0
                row = next((r for r in getattr(self, '_all_rows', []) if r["round"] == round_no), None)
                if row:
                    self._open_picker(row)
            
    def on_right_click(self, event):
        """Handle right-click context menu"""
        selection = self.tree.selection()
        if selection:
            # Show context menu
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
                
    def show_export_dialog(self, values):
        """Show simple export session selection dialog"""
        if not values:
            return
            
        round_no = values[0]
        race_name = values[2]
        
        # Simple dialog for session selection
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Export {race_name} (Round {round_no})")
        dialog.geometry("300x200")
        dialog.transient(self.window)
        
        ttk.Label(dialog, text="Select session to export:", font=("Arial", 10, "bold")).pack(pady=10)
        ttk.Label(dialog, text=f"Round {round_no}: {race_name}").pack(pady=5)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        sessions = [
            ("Free Practice 1", "FP1"), ("Free Practice 2", "FP2"), ("Free Practice 3", "FP3"),
            ("Qualifying 1", "Q1"), ("Qualifying 2", "Q2"), ("Qualifying 3", "Q3"),
            ("Qualifying", "Q"), ("Sprint Qualifying", "SQ"), ("Sprint Shootout", "SS"), ("Sprint", "S"),
            ("Race", "R"), ("All Sessions", "ALL")
        ]
        for name, code in sessions:
            btn = ttk.Button(button_frame, text=name, width=18,
                           command=lambda s=code: self.export_from_dialog(round_no, s, dialog))
            btn.pack(pady=2, fill="x")
            
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(pady=10)
    
    def _open_picker(self, row):
        """Modern session picker dialog"""
        top = tk.Toplevel(self.window)
        top.title(f"Export {row['gp']} (Round {row['round']})")
        top.geometry("280x200")
        top.transient(self.window)
        top.resizable(False, False)
        
        ttk.Label(top, text="Select session to export:", font=("Arial", 10, "bold")).pack(padx=12, pady=(12,6))
        frm = ttk.Frame(top)
        frm.pack(padx=12, pady=8, fill="x")
        
        for label, code in [("Practice","Practice"),("Qualifying","Qualifying"),("Sprint","Sprint"),("Race","Race"),("All Sessions","All Sessions")]:
            ttk.Button(frm, text=label, width=18, 
                      command=lambda c=code: (top.destroy(), self._export_pick(c, row))).pack(pady=4)
        
        ttk.Button(frm, text="Cancel", command=top.destroy).pack(pady=8)
        
    def _export_pick(self, code, row=None):
        """Execute export for selected session"""
        if not row:
            selection = self.tree.selection()
            if not selection: return
            vals = self.tree.item(selection[0])["values"]
            round_no = int(vals[0]) if str(vals[0]).isdigit() else 0
            row = next((r for r in getattr(self, '_all_rows', []) if r["round"] == round_no), None)
            if not row: return
        
        # Call main GUI export with sprint info
        if hasattr(self.parent_gui, 'export_from_calendar'):
            self.parent_gui.export_from_calendar(self.season, row["round"], code, row.get("has_sprint"))
        
    def export_from_dialog(self, round_no, session, dialog):
        """Export session from dialog"""
        dialog.destroy()
        self.export_session(session, round_no)
        
    def export_session(self, session, round_no=None):
        """Export selected session - delegates to _export_pick"""
        if round_no is None:
            self._export_pick(session)
        else:
            row = next((r for r in getattr(self, '_all_rows', []) if r["round"] == round_no), None)
            if row:
                self._export_pick(session, row)

class LogView:
    """Enhanced log view with levels, colors, and toolbar"""
    
    def __init__(self, parent):
        self.parent = parent
        self.levels_visible = {
            "INFO": tk.BooleanVar(value=True),
            "STEP": tk.BooleanVar(value=True), 
            "WARN": tk.BooleanVar(value=True),
            "ERROR": tk.BooleanVar(value=True),
            "DONE": tk.BooleanVar(value=True)
        }
        
        self.create_widgets()
        self.setup_styles()
        
    def create_widgets(self):
        # Toolbar
        toolbar = ttk.Frame(self.parent)
        toolbar.pack(fill="x", pady=(0, 5))
        
        # Filter checkboxes
        ttk.Label(toolbar, text="Show:").pack(side="left", padx=(0, 5))
        
        for level, var in self.levels_visible.items():
            cb = ttk.Checkbutton(toolbar, text=level, variable=var, 
                                command=self.filter_log)
            cb.pack(side="left", padx=2)
        
        # Buttons
        ttk.Button(toolbar, text="Clear", command=self.clear_log).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Copy", command=self.copy_log).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Save...", command=self.save_log).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Open logs folder", command=self.open_logs_folder).pack(side="right", padx=2)
        
        # Text widget
        self.text = scrolledtext.ScrolledText(self.parent, height=15, state='disabled')
        self.text.pack(fill="both", expand=True)
        
    def setup_styles(self):
        """Configure text tags for different log levels"""
        self.text.tag_config("INFO", foreground="black")
        self.text.tag_config("STEP", foreground="blue", font=("Arial", 9, "bold"))
        self.text.tag_config("WARN", foreground="orange", background="lightyellow")
        self.text.tag_config("ERROR", foreground="red", background="mistyrose")
        self.text.tag_config("DONE", foreground="green", font=("Arial", 9, "bold"))
        
    def add(self, level, message):
        """Add log message with timestamp and level"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}\n"
        
        self.text.config(state='normal')
        self.text.insert(tk.END, formatted, level)
        self.text.config(state='disabled')
        self.text.see(tk.END)
        
        # Apply filter
        self.filter_log()
        
    def filter_log(self):
        """Show/hide lines based on level filters"""
        # Implementation would be complex - for now just refresh visibility
        pass
        
    def clear_log(self):
        """Clear all log content"""
        self.text.config(state='normal')
        self.text.delete(1.0, tk.END)
        self.text.config(state='disabled')
        
    def copy_log(self):
        """Copy log content to clipboard"""
        content = self.text.get(1.0, tk.END)
        self.text.clipboard_clear()
        self.text.clipboard_append(content)
        
    def save_log(self):
        """Save log to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.text.get(1.0, tk.END))
                
    def open_logs_folder(self):
        """Open logs folder in explorer"""
        logs_dir = Path.home() / "Documents" / "LooneyF1Tool" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            subprocess.Popen(f'explorer "{logs_dir}"')

class LooneyF1GUI:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry("700x600")
        
        # Variables
        self.season_var = tk.StringVar(value="2025")
        self.round_var = tk.StringVar(value="1")
        self.session_var = tk.StringVar(value="Race")  
        self.output_dir_var = tk.StringVar()
        self.verbose_var = tk.BooleanVar()
        self.log_level_var = tk.StringVar(value="INFO")
        
        self.create_widgets()
        self.log_initial_message()
        
        log.info("GUI initialized")
        
    def create_widgets(self):
        # Title
        title_label = tk.Label(self.root, text="Looney F1 Tool — Exporter v1.7.2_beta", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Export Settings", padding=10)
        input_frame.pack(fill="x", pady=(0, 10))
        
        # Season
        ttk.Label(input_frame, text="Season:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.season_var, width=10).grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        # Round
        ttk.Label(input_frame, text="Round:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.round_var, width=10).grid(row=1, column=1, sticky="w", padx=(10, 0))
        
        # Session
        ttk.Label(input_frame, text="Session:").grid(row=2, column=0, sticky="w", pady=5)
        session_combo = ttk.Combobox(input_frame, textvariable=self.session_var, 
                                    values=["Practice", "Qualifying", "Sprint", "Race", "All Sessions"], state="readonly", width=12)
        session_combo.grid(row=2, column=1, sticky="w", padx=(10, 0))
        
        # Session info
        info_label = ttk.Label(input_frame, text="Practice = FP1+FP2+FP3 • Qualifying = Q1+Q2+Q3 • Sprint = SQ+SS+SR • Race = R • All Sessions = Everything", 
                              font=("Arial", 8))
        info_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=5)
        
        # Output directory
        ttk.Label(input_frame, text="Output folder:").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.output_dir_var, width=40).grid(row=4, column=1, sticky="ew", padx=(10, 5))
        ttk.Button(input_frame, text="Browse", command=self.browse_folder).grid(row=4, column=2)
        
        # Verbose checkbox
        ttk.Checkbutton(input_frame, text="Verbose log", variable=self.verbose_var).grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        
        # Log level selector
        ttk.Label(input_frame, text="Log level:").grid(row=6, column=0, sticky="w", pady=5)
        log_level_combo = ttk.Combobox(input_frame, textvariable=self.log_level_var,
                                      values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                      state="readonly", width=12)
        log_level_combo.grid(row=6, column=1, sticky="w", padx=(10, 0))
        log_level_combo.bind("<<ComboboxSelected>>", self.on_log_level_change)
        
        # Configure column weights
        input_frame.columnconfigure(1, weight=1)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Buttons
        self.export_button = tk.Button(button_frame, text="🚀 Start export", 
                                      command=self.start_export, bg="green", fg="white", 
                                      font=("Arial", 10, "bold"))
        self.export_button.pack(side="left", padx=(0, 10))
        
        calendar_button = tk.Button(button_frame, text="📅 Calendar", 
                                   command=self.open_calendar, bg="blue", fg="white")
        calendar_button.pack(side="left", padx=(0, 10))
        
        exit_button = tk.Button(button_frame, text="❌ Exit", 
                               command=self.root.quit, bg="red", fg="white")
        exit_button.pack(side="left")
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=10)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        # Result summary
        self.result_var = tk.StringVar(value="Ready to export...")
        result_label = ttk.Label(progress_frame, textvariable=self.result_var, 
                               font=("Arial", 8), foreground="gray")
        result_label.pack(fill="x")
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Activity log", padding=10)
        log_frame.pack(fill="both", expand=True)
        
        # Initialize log view
        self.log = LogView(log_frame)
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir_var.set(folder)
    
    def on_log_level_change(self, event=None):
        """Update logger level when user changes selection"""
        new_level = self.log_level_var.get()
        # Update all loggers to new level
        logging.getLogger().setLevel(getattr(logging, new_level))
        for handler in logging.getLogger().handlers:
            handler.setLevel(getattr(logging, new_level))
        log.info(f"Log level changed to {new_level}")
        self.log_message(f"Log level changed to {new_level}", "INFO")
            
    def log_message(self, message, level="INFO"):
        """Add log message with specified level"""
        self.log.add(level, message)
        self.root.update_idletasks()
        
    def log_initial_message(self):
        self.log_message("🐰 Bugs Bunny: 'Eh, what's up Doc? Ready to export some F1 data?'", "INFO")
        self.log_message("🐦 Road Runner: 'Meep Meep!' (Let's go fast!)", "INFO")
        self.log_message("💝 Support Formula Toons: https://github.com/sponsors/Tixer87", "INFO")
        self.log_message("=" * 80, "INFO")
        
    def start_export(self):
        try:
            season = int(self.season_var.get())
            round_no = int(self.round_var.get())
            session = self.session_var.get()
            out_dir = Path(self.output_dir_var.get() or (Path.home() / "Documents" / "LooneyExports"))
            verbose = self.verbose_var.get()
            
            self.export_button.config(state='disabled')
            self.progress_bar['value'] = 10
            
            self.log_message(f"Export started (season={season}, round={round_no}, session={session})", "STEP")
            self.log_message(f"Output folder: {out_dir}", "INFO")
            
            # Run export in separate thread
            thread = threading.Thread(target=self.run_export_thread, 
                                     args=(season, round_no, session, out_dir, verbose))
            thread.daemon = True
            thread.start()
            
        except ValueError as e:
            self.log_message(f"Input error: {e}", "ERROR")
            messagebox.showerror("Input Error", str(e))
            self.export_button.config(state='normal')
            self.progress_bar['value'] = 0
        except Exception as e:
            self.log_message(f"Export failed: {e}", "ERROR")
            messagebox.showerror("Error", str(e))
            self.export_button.config(state='normal')
            self.progress_bar['value'] = 0
            
    def run_export_thread(self, season, round_no, session, out_dir, verbose):
        """Background worker for Start export; supports grouped sessions."""
        try:
            from api.export_service import expand_session_group, SessionType as SessionCode
            from api.providers.router import get_provider
            from typing import cast

            # Determine if this is a grouped selection
            if session in ("All Sessions", "Practice", "Qualifying", "Sprint", "Race"):
                sessions_to_export = expand_session_group(session if session != "All Sessions" else "All Sessions")

                # Optional: filter sprint-related entries if the round has no sprint scheduled
                try:
                    provider = get_provider()  # Auto-Fallback Jolpica→FastF1
                    schedule_data = provider.schedule(season)
                    event = next((x for x in schedule_data if int(x.get("round", 0)) == round_no), None)
                    has_sprint = bool(event and (event.get("hasSprint", False) or "sprint" in str(event.get("EventFormat", "")).lower()))
                except Exception:
                    has_sprint = True  # don't block if schedule unavailable

                if not has_sprint:
                    sessions_to_export = [s for s in sessions_to_export if s not in ("SQ", "SS", "S", "SR")]

                total = len(sessions_to_export)
                success = 0
                last_path = None
                for idx, code in enumerate(sessions_to_export, start=1):
                    try:
                        self.log.add("INFO", f"Exporting {season} R{round_no} {code}...")
                        result_path = run_export(season, round_no, cast(SessionCode, code), out_dir, verbose)
                        if result_path:
                            success += 1
                            last_path = result_path
                            self.log.add("DONE", f"File written: {Path(result_path).name}")
                        else:
                            self.log.add("WARN", f"No data available for {code}")
                    except Exception as e:
                        self.log.add("ERROR", f"Export failed for {code}: {e}")
                    finally:
                        # Incremental progress
                        self.root.after(0, lambda v=int(10 + (idx/total)*80): self.progress_bar.config(value=v))

                # Update UI in main thread with grouped completion
                self.root.after(0, self.export_group_completed, total, success, out_dir, last_path)
                return

            # Single session path
            result_path = run_export(season, round_no, session, out_dir, verbose)

            # Update UI in main thread
            self.root.after(0, self.export_completed, result_path)

        except Exception as e:
            # Update UI in main thread
            self.root.after(0, self.export_failed, str(e))
            
    def export_completed(self, result_path):
        self.progress_bar['value'] = 100
        if result_path:
            file_size = Path(result_path).stat().st_size if Path(result_path).exists() else 0
            # Update result summary
            self.result_var.set(f"Result: file size={file_size} bytes")
            self.log_message("Export completed!", "DONE")
            self.log_message(f"File written: {result_path} ({file_size} bytes)", "INFO")
        else:
            self.result_var.set("Result: no data available")
            self.log_message("No data for this session/round. Nothing was exported.", "WARN")
        self.log_message("That's all folks! - Ready for next export.", "INFO")
        
        # Ask to open folder
        if result_path:
            choice = messagebox.askyesno("Export completed", 
                                       f"File successfully created:\n{result_path}\n\nOpen folder?")
            if choice:
                import subprocess
                import os
                if os.name == 'nt':  # Windows
                    subprocess.Popen(f'explorer /select,"{result_path}"')
        else:
            messagebox.showinfo("Export info", "No data available for this session/round.")
                
        self.export_button.config(state='normal')

    def export_group_completed(self, total: int, success: int, out_dir: Path, last_path: Path | None):
        """Finalize grouped export run with summary and optional folder prompt."""
        self.progress_bar['value'] = 100
        if total == 0:
            self.result_var.set("Result: no sessions selected")
            self.log_message("No sessions matched selection.", "WARN")
        else:
            self.result_var.set(f"Grouped export: {success}/{total} files created")
            self.log_message(f"Grouped export completed: {success}/{total} files", "DONE")
        self.log_message("That's all folks! - Ready for next export.", "INFO")

        # Ask to open folder when at least one file was created
        if success > 0:
            choice = messagebox.askyesno("Export completed", 
                                       f"Grouped export finished: {success}/{total} files created in:\n{out_dir}\n\nOpen folder?")
            if choice:
                import subprocess
                import os
                if os.name == 'nt':  # Windows
                    subprocess.Popen(f'explorer "{out_dir}"')
        else:
            messagebox.showinfo("Export info", "No data available for the selected sessions.")

        self.export_button.config(state='normal')
        
    def export_failed(self, error_msg):
        self.log_message(f"Export failed: {error_msg}", "ERROR")
        messagebox.showerror("Export Error", error_msg)
        self.export_button.config(state='normal')  
        self.progress_bar['value'] = 0
        
    def open_calendar(self):
        """Open F1 calendar window"""
        try:
            season = int(self.season_var.get())
            CalendarWindow(self, season)
            self.log_message("Calendar window opened", "INFO")
        except ValueError:
            self.log_message("Invalid season number", "ERROR")
            messagebox.showerror("Error", "Please enter a valid season number")
            
    def export_from_calendar(self, season: int, round_no: int, session_code: str, has_sprint=None):
        """Export session selected from calendar with group support (Practice/Qualifying/Sprint/Race/All Sessions)."""
        out_dir = self._resolve_out_dir()
        from api.export_service import expand_session_group

        # Determine list of sessions to export from group label or single code
        sessions_to_export = []
        if session_code in ("ALL", "All Sessions"):
            sessions_to_export = expand_session_group("All Sessions")
        elif session_code in ("Practice", "Qualifying", "Sprint", "Race"):
            sessions_to_export = expand_session_group(session_code)
        else:
            sessions_to_export = [session_code]

        # Filter sprint items if event has no sprint
        if has_sprint is False:
            sessions_to_export = [s for s in sessions_to_export if s not in ("SQ", "SS", "S", "SR")]

        if len(sessions_to_export) > 1:
            self.log.add("STEP", f"Exporting {len(sessions_to_export)} sessions for Season {season}, Round {round_no}")

        for code in sessions_to_export:
            try:
                self._export_one(season, round_no, code, out_dir)
            except Exception as e:
                self.log.add("WARN", f"Session {code} failed: {str(e)}")

        if len(sessions_to_export) > 1:
            self.log.add("DONE", "Grouped export completed")
    
    def _export_one(self, season: int, round_no: int, session: str, out_dir):
        """Export single session with dual-source aggregation"""
        try:
            from api.export_service import run_export, SessionType
            from typing import cast

            self.log.add("INFO", f"Exporting {season} R{round_no} {session}...")

            # Allow extended session codes; validation happens in run_export
            result_path = run_export(season, round_no, cast(SessionType, session), out_dir, verbose=False)

            if result_path:
                self.log.add("DONE", f"File written: {result_path.name}")
            else:
                self.log.add("WARN", f"No data available for {session}")

        except Exception as e:
            self.log.add("ERROR", f"Export failed for {session}: {e}")
    
    def _resolve_out_dir(self):
        """Get output directory from GUI settings"""
        # Use current working directory + exports as default
        return Path("./exports")

def main():
    root = tk.Tk()
    app = LooneyF1GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
