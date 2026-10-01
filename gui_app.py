import datetime
import logging
import os
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog,messagebox,scrolledtext,ttk
from typing import cast
from api.export_service import SessionType,expand_session_group,run_export
from api.providers.router import get_provider
from core.version import PRODUCT_NAME,__version__
from utils.config_loader import get_default_export_dir
from utils.logging_setup import get_logger
log=get_logger(__name__,level="INFO")
APP_NAME=PRODUCT_NAME
WINDOW_TITLE=f"{APP_NAME} {__version__}"
class CalendarWindow:
    def __init__(self,parent_gui,season=2025):
        self.parent_gui=parent_gui
        self.season=season
        self.window=None
        self.schedule_data=[]
        self._all_rows=[]
        self.create_window()
        self.load_schedule()
    def create_window(self):
        self.window=tk.Toplevel(self.parent_gui.root)
        self.window.title(f"F1 Calendar {self.season}")
        self.window.geometry("900x600")
        self.window.transient(self.parent_gui.root)
        main=ttk.Frame(self.window)
        main.pack(fill="both",expand=True,padx=10,pady=10)
        search=ttk.Frame(main)
        search.pack(fill="x",pady=(0,10))
        ttk.Label(search,text="Filter:").pack(side="left",padx=(0,5))
        self.search_var=tk.StringVar()
        self.search_var.trace_add("write",self.filter_schedule)
        ttk.Entry(search,textvariable=self.search_var,width=30).pack(side="left",padx=(0,10))
        ttk.Button(search,text="Refresh",command=self.load_schedule).pack(side="left")
        tree_frame=ttk.Frame(main)
        tree_frame.pack(fill="both",expand=True)
        cols=("Round","Date","Grand Prix","Circuit")
        self.tree=ttk.Treeview(tree_frame,columns=cols,show="headings",height=16)
        for col,width in zip(cols,(70,110,300,260)):
            self.tree.heading(col,text=col)
            self.tree.column(col,width=width,anchor="w")
        scrollbar=ttk.Scrollbar(tree_frame,orient="vertical",command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left",fill="both",expand=True)
        scrollbar.pack(side="right",fill="y")
        self.tree.bind("<Double-1>",self.on_double_click)
        self.tree.bind("<Button-3>",self.on_right_click)
        self.context_menu=tk.Menu(self.window,tearoff=0)
        for label,code in [("Export Practice","Practice"),("Export Qualifying","Qualifying"),("Export Sprint","Sprint"),("Export Race","Race")]:
            self.context_menu.add_command(label=label,command=lambda c=code:self.export_session(c))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Export All Sessions",command=lambda:self.export_session("All Sessions"))
    def load_schedule(self):
        try:
            self.parent_gui.log_message(f"Loading F1 {self.season} calendar...","INFO")
            self.schedule_data=get_provider(year=self.season).schedule(self.season)
            self.populate_tree()
            self.parent_gui.log_message(f"Calendar loaded: {len(self.schedule_data)} rounds","INFO")
        except Exception as exc:
            self.parent_gui.log_message(f"Failed to load calendar: {exc}","ERROR")
    @staticmethod
    def _fmt_date(value):
        try:return datetime.datetime.fromisoformat(str(value).split("T")[0]).strftime("%d.%m.%Y")
        except Exception:return str(value)
    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._all_rows=[]
        for event in self.schedule_data:
            raw_round=event.get("round","")
            row={
                "round":int(raw_round) if str(raw_round).isdigit() else 0,
                "date":self._fmt_date(event.get("date","")),
                "gp":event.get("raceName") or event.get("EventName",""),
                "circuit":event.get("circuitFullName") or event.get("Circuit",{}).get("circuitName") or f"{event.get('Location','')} ({event.get('Country','')})".strip(),
                "has_sprint":bool(event.get("hasSprint",False) or "sprint" in str(event.get("EventFormat","")).lower())
            }
            self._all_rows.append(row)
            self.tree.insert("","end",values=(row["round"],row["date"],row["gp"],row["circuit"]))
    def filter_schedule(self,*_):
        search=self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for row in self._all_rows:
            if search in f"{row['gp']} {row['circuit']}".lower():
                self.tree.insert("","end",values=(row["round"],row["date"],row["gp"],row["circuit"]))
    def _selected_row(self):
        selection=self.tree.selection()
        if not selection:return None
        values=self.tree.item(selection[0])["values"]
        if not values:return None
        try:round_no=int(values[0])
        except (TypeError,ValueError):return None
        return next((row for row in self._all_rows if row["round"]==round_no),None)
    def on_double_click(self,_event):
        row=self._selected_row()
        if row:self._open_picker(row)
    def on_right_click(self,event):
        row_id=self.tree.identify_row(event.y)
        if row_id:self.tree.selection_set(row_id)
        if self.tree.selection():
            try:self.context_menu.tk_popup(event.x_root,event.y_root)
            finally:self.context_menu.grab_release()
    def _open_picker(self,row):
        top=tk.Toplevel(self.window)
        top.title(f"Export {row['gp']} (Round {row['round']})")
        top.geometry("280x260")
        top.transient(self.window)
        top.resizable(False,False)
        ttk.Label(top,text="Select session to export:",font=("Arial",10,"bold")).pack(padx=12,pady=(12,6))
        frame=ttk.Frame(top)
        frame.pack(padx=12,pady=8,fill="x")
        options=[("Practice","Practice"),("Qualifying","Qualifying"),("Sprint","Sprint"),("Race","Race"),("All Sessions","All Sessions")]
        for label,code in options:
            ttk.Button(frame,text=label,width=18,command=lambda c=code:(top.destroy(),self._export_pick(c,row))).pack(pady=4)
        ttk.Button(frame,text="Cancel",command=top.destroy).pack(pady=8)
    def _export_pick(self,code,row=None):
        row=row or self._selected_row()
        if row:self.parent_gui.export_from_calendar(self.season,row["round"],code,row.get("has_sprint"))
    def export_session(self,session,round_no=None):
        if round_no is None:self._export_pick(session)
        else:
            row=next((item for item in self._all_rows if item["round"]==round_no),None)
            if row:self._export_pick(session,row)
class LogView:
    def __init__(self,parent):
        self.parent=parent
        self.create_widgets()
        self.setup_styles()
    def create_widgets(self):
        toolbar=ttk.Frame(self.parent)
        toolbar.pack(fill="x",pady=(0,5))
        ttk.Button(toolbar,text="Clear",command=self.clear_log).pack(side="right",padx=2)
        ttk.Button(toolbar,text="Copy",command=self.copy_log).pack(side="right",padx=2)
        ttk.Button(toolbar,text="Save...",command=self.save_log).pack(side="right",padx=2)
        ttk.Button(toolbar,text="Open logs folder",command=self.open_logs_folder).pack(side="right",padx=2)
        self.text=scrolledtext.ScrolledText(self.parent,height=15,state="disabled")
        self.text.pack(fill="both",expand=True)
    def setup_styles(self):
        self.text.tag_config("INFO",foreground="black")
        self.text.tag_config("STEP",foreground="blue",font=("Arial",9,"bold"))
        self.text.tag_config("WARN",foreground="orange",background="lightyellow")
        self.text.tag_config("ERROR",foreground="red",background="mistyrose")
        self.text.tag_config("DONE",foreground="green",font=("Arial",9,"bold"))
    def add(self,level,message):
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.text.config(state="normal")
        self.text.insert(tk.END,f"[{timestamp}] [{level}] {message}\n",level)
        self.text.config(state="disabled")
        self.text.see(tk.END)
    def clear_log(self):
        self.text.config(state="normal")
        self.text.delete(1.0,tk.END)
        self.text.config(state="disabled")
    def copy_log(self):
        self.text.clipboard_clear()
        self.text.clipboard_append(self.text.get(1.0,tk.END))
    def save_log(self):
        filename=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text files","*.txt"),("All files","*.*")])
        if filename:
            with open(filename,"w",encoding="utf-8") as file:file.write(self.text.get(1.0,tk.END))
    def open_logs_folder(self):
        logs=Path("logs").resolve()
        logs.mkdir(parents=True,exist_ok=True)
        if os.name=="nt":subprocess.Popen(["explorer",str(logs)])
class LooneyF1GUI:
    def __init__(self,root):
        self.root=root
        self.root.title(WINDOW_TITLE)
        self.root.geometry("700x600")
        self.season_var=tk.StringVar(value=str(datetime.datetime.now().year))
        self.round_var=tk.StringVar(value="1")
        self.session_var=tk.StringVar(value="Race")
        self.output_dir_var=tk.StringVar(value=get_default_export_dir())
        self.verbose_var=tk.BooleanVar()
        self.log_level_var=tk.StringVar(value="INFO")
        self.create_widgets()
        self.log_initial_message()
        log.info("GUI initialized")
    def create_widgets(self):
        tk.Label(self.root,text=WINDOW_TITLE,font=("Arial",16,"bold")).pack(pady=10)
        main=ttk.Frame(self.root)
        main.pack(padx=20,pady=10,fill="both",expand=True)
        settings=ttk.LabelFrame(main,text="Export Settings",padding=10)
        settings.pack(fill="x",pady=(0,10))
        ttk.Label(settings,text="Season:").grid(row=0,column=0,sticky="w",pady=5)
        ttk.Entry(settings,textvariable=self.season_var,width=10).grid(row=0,column=1,sticky="w",padx=(10,0))
        ttk.Label(settings,text="Round:").grid(row=1,column=0,sticky="w",pady=5)
        ttk.Entry(settings,textvariable=self.round_var,width=10).grid(row=1,column=1,sticky="w",padx=(10,0))
        ttk.Label(settings,text="Session:").grid(row=2,column=0,sticky="w",pady=5)
        ttk.Combobox(settings,textvariable=self.session_var,values=["Practice","Qualifying","Sprint","Race","All Sessions"],state="readonly",width=14).grid(row=2,column=1,sticky="w",padx=(10,0))
        ttk.Label(settings,text="Practice = FP1 + FP2 + FP3   Qualifying = Q1 + Q2 + Q3   Sprint = SQ + S   Race = R",font=("Arial",8)).grid(row=3,column=0,columnspan=3,sticky="w",pady=5)
        ttk.Label(settings,text="Output folder:").grid(row=4,column=0,sticky="w",pady=5)
        ttk.Entry(settings,textvariable=self.output_dir_var,width=40).grid(row=4,column=1,sticky="ew",padx=(10,5))
        ttk.Button(settings,text="Browse",command=self.browse_folder).grid(row=4,column=2)
        ttk.Checkbutton(settings,text="Verbose log",variable=self.verbose_var).grid(row=5,column=0,columnspan=2,sticky="w",pady=5)
        ttk.Label(settings,text="Log level:").grid(row=6,column=0,sticky="w",pady=5)
        levels=ttk.Combobox(settings,textvariable=self.log_level_var,values=["DEBUG","INFO","WARNING","ERROR","CRITICAL"],state="readonly",width=12)
        levels.grid(row=6,column=1,sticky="w",padx=(10,0))
        levels.bind("<<ComboboxSelected>>",self.on_log_level_change)
        settings.columnconfigure(1,weight=1)
        buttons=ttk.Frame(main)
        buttons.pack(fill="x",pady=(0,10))
        self.export_button=ttk.Button(buttons,text="Start export",command=self.start_export)
        self.export_button.pack(side="left",padx=(0,10))
        ttk.Button(buttons,text="Calendar",command=self.open_calendar).pack(side="left",padx=(0,10))
        ttk.Button(buttons,text="Exit",command=self.root.quit).pack(side="left")
        progress=ttk.LabelFrame(main,text="Progress",padding=10)
        progress.pack(fill="x",pady=(0,10))
        self.progress_bar=ttk.Progressbar(progress,mode="determinate")
        self.progress_bar.pack(fill="x",pady=(0,5))
        self.result_var=tk.StringVar(value="Ready to export")
        ttk.Label(progress,textvariable=self.result_var,font=("Arial",8),foreground="gray").pack(fill="x")
        log_frame=ttk.LabelFrame(main,text="Activity log",padding=10)
        log_frame.pack(fill="both",expand=True)
        self.log=LogView(log_frame)
    def browse_folder(self):
        folder=filedialog.askdirectory()
        if folder:self.output_dir_var.set(folder)
    def on_log_level_change(self,_event=None):
        level=getattr(logging,self.log_level_var.get())
        log.setLevel(level)
        for handler in log.handlers:handler.setLevel(level)
        self.log_message(f"Log level changed to {self.log_level_var.get()}","INFO")
    def log_message(self,message,level="INFO"):
        self.log.add(level,message)
        self.root.update_idletasks()
    def log_initial_message(self):
        self.log_message(f"{PRODUCT_NAME} {__version__} ready","INFO")
    def start_export(self):
        try:
            season=int(self.season_var.get())
            round_no=int(self.round_var.get())
            session=self.session_var.get()
            out_dir=Path(self.output_dir_var.get() or get_default_export_dir())
            self.export_button.config(state="disabled")
            self.progress_bar["value"]=10
            self.log_message(f"Export started: {season} R{round_no} {session}","STEP")
            self.log_message(f"Output folder: {out_dir}","INFO")
            threading.Thread(target=self.run_export_thread,args=(season,round_no,session,out_dir,self.verbose_var.get()),daemon=True).start()
        except ValueError as exc:
            self.export_failed(str(exc))
        except Exception as exc:
            self.export_failed(str(exc))
    def run_export_thread(self,season,round_no,session,out_dir,verbose):
        try:
            codes=expand_session_group(session)
            if session in ("All Sessions","Sprint"):
                try:
                    event=next((item for item in get_provider(year=season).schedule(season) if int(item.get("round",0))==round_no),None)
                    has_sprint=bool(event and (event.get("hasSprint",False) or "sprint" in str(event.get("EventFormat","")).lower()))
                except Exception:
                    has_sprint=True
                if not has_sprint:codes=[code for code in codes if code not in ("SQ","SS","S","SR")]
            total=len(codes)
            success=0
            last_path=None
            for index,code in enumerate(codes,1):
                try:
                    self.root.after(0,lambda c=code:self.log.add("INFO",f"Exporting {season} R{round_no} {c}..."))
                    result=run_export(season,round_no,cast(SessionType,code),out_dir,verbose)
                    if result:
                        success+=1
                        last_path=result
                        self.root.after(0,lambda p=Path(result).name:self.log.add("DONE",f"File written: {p}"))
                    else:self.root.after(0,lambda c=code:self.log.add("WARN",f"No data available for {c}"))
                except Exception as exc:
                    self.root.after(0,lambda c=code,e=str(exc):self.log.add("ERROR",f"Export failed for {c}: {e}"))
                if total:self.root.after(0,lambda value=int(10+(index/total)*80):self.progress_bar.config(value=value))
            if len(codes)==1:self.root.after(0,self.export_completed,last_path)
            else:self.root.after(0,self.export_group_completed,total,success,out_dir,last_path)
        except Exception as exc:
            self.root.after(0,self.export_failed,str(exc))
    def export_completed(self,result_path):
        self.progress_bar["value"]=100
        if result_path:
            path=Path(result_path)
            size=path.stat().st_size if path.exists() else 0
            self.result_var.set(f"Result: {size} bytes")
            self.log_message("Export completed","DONE")
            self.log_message(f"File written: {path}","INFO")
            if messagebox.askyesno("Export completed",f"File created:\n{path}\n\nOpen folder?") and os.name=="nt":
                subprocess.Popen(["explorer","/select,",str(path)])
        else:
            self.result_var.set("Result: no data available")
            self.log_message("No data available for this session","WARN")
            messagebox.showinfo("Export info","No data available for this session or round.")
        self.export_button.config(state="normal")
    def export_group_completed(self,total:int,success:int,out_dir:Path,last_path:Path|None):
        self.progress_bar["value"]=100
        self.result_var.set(f"Grouped export: {success}/{total} sessions exported")
        level="DONE" if success==total else "ERROR" if success==0 else "WARN"
        self.log_message(f"Grouped export: {success}/{total} sessions exported",level)
        if success:
            if messagebox.askyesno("Export completed" if success==total else "Export incomplete",f"Exported {success}/{total} sessions to:\n{out_dir}\n\nOpen folder?") and os.name=="nt":
                subprocess.Popen(["explorer",str(out_dir)])
        else:messagebox.showwarning("No sessions exported","No files were created. See the log for details.")
        self.export_button.config(state="normal")
    def export_failed(self,error_msg):
        self.log_message(f"Export failed: {error_msg}","ERROR")
        messagebox.showerror("Export Error",error_msg)
        self.export_button.config(state="normal")
        self.progress_bar["value"]=0
    def open_calendar(self):
        try:
            CalendarWindow(self,int(self.season_var.get()))
            self.log_message("Calendar window opened","INFO")
        except ValueError:
            self.log_message("Invalid season number","ERROR")
            messagebox.showerror("Error","Please enter a valid season number")
    def export_from_calendar(self,season:int,round_no:int,session_code:str,has_sprint=None):
        if str(self.export_button["state"])=="disabled":
            self.log_message("An export is already running","WARN")
            return
        self.season_var.set(str(season))
        self.round_var.set(str(round_no))
        self.session_var.set("All Sessions" if session_code=="ALL" else session_code)
        self.start_export()
def main():
    root=tk.Tk()
    LooneyF1GUI(root)
    root.mainloop()
if __name__=="__main__":
    main()