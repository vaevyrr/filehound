from __future__ import annotations
import threading, tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from filehound import find_duplicates, write_report

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("FileHound"); self.geometry("1050x650"); self.minsize(800,500); self.build()
    def build(self):
        top=ttk.Frame(self,padding=12); top.pack(fill="x")
        ttk.Label(top,text="FileHound",font=("Segoe UI",16,"bold")).pack(anchor="w")
        ttk.Label(top,text="Find identical files using size + SHA-256. Nothing is deleted.").pack(anchor="w",pady=(2,8))
        row=ttk.Frame(top); row.pack(fill="x")
        self.folder=tk.StringVar()
        ttk.Entry(row,textvariable=self.folder).pack(side="left",fill="x",expand=True)
        ttk.Button(row,text="Choose folder",command=self.choose).pack(side="left",padx=6)
        ttk.Label(row,text="Min bytes").pack(side="left"); self.min=tk.StringVar(value="1"); ttk.Entry(row,textvariable=self.min,width=9).pack(side="left",padx=5)
        self.go=ttk.Button(row,text="Scan",command=self.run); self.go.pack(side="left")
        self.hidden=tk.BooleanVar(); ttk.Checkbutton(top,text="Include hidden files",variable=self.hidden).pack(anchor="w",pady=5)
        self.status=tk.StringVar(value="Ready"); ttk.Label(top,textvariable=self.status).pack(anchor="w")
        body=ttk.Frame(self,padding=12); body.pack(fill="both",expand=True)
        self.tree=ttk.Treeview(body,columns=("group","size","copies","saved","sha256","paths"),show="headings")
        for c,w in (("group",70),("size",120),("copies",70),("saved",120),("sha256",260),("paths",380)):
            self.tree.heading(c,text=c.title()); self.tree.column(c,width=w,anchor="w")
        self.tree.pack(side="left",fill="both",expand=True); sb=ttk.Scrollbar(body,command=self.tree.yview); sb.pack(side="right",fill="y"); self.tree.configure(yscrollcommand=sb.set)
        self.summary=tk.StringVar(value="No scan yet."); ttk.Label(self,textvariable=self.summary).pack(side="left",padx=12,pady=8)
        ttk.Button(self,text="Export CSV",command=self.export).pack(side="right",padx=12,pady=8)
    def choose(self):
        p=filedialog.askdirectory(title="Choose folder")
        if p:self.folder.set(p)
    def run(self):
        p=Path(self.folder.get())
        if not p.is_dir(): messagebox.showerror("Scan","Choose a folder."); return
        try:min_size=max(0,int(self.min.get()))
        except ValueError: messagebox.showerror("Scan","Min bytes must be a number."); return
        self.go.configure(state="disabled"); self.status.set("Scanning files...")
        def work():
            try:r=find_duplicates([p],min_size,self.hidden.get()); err=None
            except Exception as e:r=None; err=str(e)
            self.after(0,lambda:self.finish(r,err))
        threading.Thread(target=work,daemon=True).start()
    def finish(self,r,err):
        self.go.configure(state="normal")
        if err: self.status.set("Failed"); messagebox.showerror("Scan failed",err); return
        groups,errors=r
        for i in self.tree.get_children(): self.tree.delete(i)
        saved_total=0
        for n,g in enumerate(groups,1):
            saved=g["size"]*(len(g["paths"])-1); saved_total+=saved
            self.tree.insert("", "end", values=(n,f'{g["size"]:,}',len(g["paths"]),f'{saved:,}',g["sha256"]," | ".join(g["paths"])))
        self.last=groups; self.summary.set(f"{len(groups)} duplicate group(s) • {saved_total:,} redundant bytes • {len(errors)} read error(s)"); self.status.set("Complete")
    def export(self):
        if not hasattr(self,"last"): messagebox.showinfo("Export","Run a scan first."); return
        p=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if p:
            write_report(Path(p),self.last); self.status.set(f"Saved {p}")

if __name__=="__main__": App().mainloop()
