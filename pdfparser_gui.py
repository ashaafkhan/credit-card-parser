import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import threading
import os
import subprocess
import shutil
import json
import PdfParser

class PDFParserGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('PDF Parser')
        self.geometry('900x700')
       
        try:
            style = ttk.Style(self)
            style.theme_use('clam')
        except Exception:
            pass
       
        frm = ttk.Frame(self)
        frm.pack(fill='x', padx=12, pady=8)
        ttk.Label(frm, text='PDF file or folder:').pack(side='left')
        self.path_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.path_var, width=70).pack(side='left', padx=6)
        ttk.Button(frm, text='Browse', command=self.browse).pack(side='left')

        frm2 = ttk.Frame(self)
        frm2.pack(fill='x', padx=12, pady=4)
        ttk.Label(frm2, text='TESSERACT_CMD (optional):').pack(side='left')
        self.tess_var = tk.StringVar(value=os.environ.get('TESSERACT_CMD', ''))
        ttk.Entry(frm2, textvariable=self.tess_var, width=60).pack(side='left', padx=6)
        ttk.Button(frm2, text='Detect', command=self.detect_tesseract).pack(side='left')

        frm3 = ttk.Frame(self)
        frm3.pack(fill='x', padx=12, pady=6)
        self.run_btn = ttk.Button(frm3, text='Run Parser', command=self.run_parser)
        self.run_btn.pack(side='left')
        self.open_btn = ttk.Button(frm3, text='Open output JSON', command=self.open_output)
        self.open_btn.pack(side='left', padx=6)
       
        ttk.Label(frm3, text='Output JSON:').pack(side='left', padx=(12,0))
        self.out_json_var = tk.StringVar(value=os.path.join(os.getcwd(), 'parsed_credit_card_statements.json'))
        ttk.Entry(frm3, textvariable=self.out_json_var, width=32).pack(side='left', padx=6)
        self.save_json_btn = ttk.Button(frm3, text='Save JSON As', command=self.save_json_as)
        self.save_json_btn.pack(side='left', padx=6)
        ttk.Label(frm3, text='Output CSV:').pack(side='left', padx=(12,0))
        self.out_csv_var = tk.StringVar(value=os.path.join(os.getcwd(), 'parsed_credit_card_statements.csv'))
        ttk.Entry(frm3, textvariable=self.out_csv_var, width=32).pack(side='left', padx=6)
        self.save_csv_btn = ttk.Button(frm3, text='Save CSV As', command=self.save_csv_as)
        self.save_csv_btn.pack(side='left', padx=6)

        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=12, pady=8)

   
        log_frame = ttk.Frame(nb)
        nb.add(log_frame, text='Log')
        self.log = scrolledtext.ScrolledText(log_frame, height=20)
        self.log.pack(fill='both', expand=True, padx=6, pady=6)

        # Output tab
        out_frame = ttk.Frame(nb)
        nb.add(out_frame, text='Parsed Output')
        # Table preview (top)
        ttk.Label(out_frame, text='Table Preview:').pack(anchor='w', padx=6, pady=(6,0))
        self.output_tree = ttk.Treeview(out_frame, columns=(), show='headings', height=8)
        self.output_tree.pack(fill='x', expand=False, padx=6, pady=(0,6))

        ttk.Label(out_frame, text='JSON Preview:').pack(anchor='w', padx=6, pady=(6,0))
        self.output_text = scrolledtext.ScrolledText(out_frame, height=12, font=('Consolas', 10))
        self.output_text.pack(fill='both', expand=True, padx=6, pady=6)

        # Progress bar
        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.progress.pack(fill='x', padx=12, pady=(0,12))

    def browse(self):
        p = filedialog.askopenfilename(filetypes=[('PDF files','*.pdf')])
        if not p:
            p = filedialog.askdirectory()
        if p:
            self.path_var.set(p)

    def detect_tesseract(self):
        # Try common default location
        default = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.isfile(default):
            self.tess_var.set(default)
            messagebox.showinfo('Detected', f'Detected tesseract at {default}')
            return
        # Try calling 'tesseract' on PATH
        try:
            proc = subprocess.run(['tesseract','--version'], capture_output=True, text=True)
            if proc.returncode == 0:
                self.tess_var.set('tesseract')
                messagebox.showinfo('Detected', 'Detected tesseract on PATH')
                return
        except Exception:
            pass
        messagebox.showwarning('Not found', 'Tesseract not found. Please provide path or install it.')

    def append_log(self, msg):
        # Schedule GUI update on main thread
        def _append():
            self.log.insert('end', msg + '\n')
            self.log.see('end')
        try:
            self.after(0, _append)
        except Exception:
            # fallback if after not available
            _append()

    def safe_log(self, msg):
        self.append_log(msg)

    def set_running(self, running: bool):
        # Enable/disable controls and start/stop progress
        state = 'disabled' if running else 'normal'
        try:
            self.path_var_entry_state = state
        except Exception:
            pass
        # disable main interactive controls
        widgets = [getattr(self, 'run_btn', None), getattr(self, 'open_btn', None), getattr(self, 'save_json_btn', None), getattr(self, 'save_csv_btn', None)]
        for w in widgets:
            if w:
                try:
                    w.config(state=state)
                except Exception:
                    pass
        if running:
            try:
                self.progress.start(10)
            except Exception:
                pass
        else:
            try:
                self.progress.stop()
            except Exception:
                pass

    def run_parser(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror('Error', 'Please select a file or folder')
            return
        tess = self.tess_var.get().strip()
        if tess:
            os.environ['TESSERACT_CMD'] = tess

        # Run in background thread
        out_csv = self.out_csv_var.get().strip()
        out_json = self.out_json_var.get().strip()
        t = threading.Thread(target=self._run_thread, args=(path, out_csv, out_json))
        t.start()

    def _run_thread(self, path, out_csv, out_json):
        try:
            self.safe_log(f'Running parser on: {path}')
            # Disable controls and start progress
            self.after(0, lambda: self.set_running(True))
            # Validate path and call PdfParser.main with provided output paths
            if os.path.isdir(path) or (os.path.isfile(path) and path.lower().endswith('.pdf')):
                args = [path, '--out-csv', out_csv, '--out-json', out_json]
                PdfParser.main(args)
            else:
                self.safe_log('Path not found or unsupported')
                return
            self.safe_log('Parser finished. Outputs: parsed_credit_card_statements.csv/json')

            # Load and display JSON preview if available
            try:
                if os.path.isfile(out_json):
                    with open(out_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    pretty = json.dumps(data, indent=2)
                    # Update output_text on main thread
                    self.after(0, lambda: self.output_text.delete('1.0', 'end'))
                    self.after(0, lambda: self.output_text.insert('1.0', pretty))
                    # Populate table preview if data is a list of dicts
                    if isinstance(data, list) and data:
                        self.after(0, lambda d=data: self.populate_table(d))
                else:
                    self.safe_log(f'Output JSON not found: {out_json}')
            except Exception as e:
                self.safe_log('Failed to load output JSON: ' + str(e))
        except Exception as e:
            self.safe_log('Error: ' + str(e))
        finally:
            # Re-enable controls and stop progress
            self.after(0, lambda: self.set_running(False))

    def open_output(self):
        out = self.out_json_var.get().strip() or os.path.join(os.getcwd(), 'parsed_credit_card_statements.json')
        if os.path.isfile(out):
            os.startfile(out)
        else:
            messagebox.showwarning('No output', f'Output JSON not found: {out}')

    def save_json_as(self):
        src = self.out_json_var.get().strip() or os.path.join(os.getcwd(), 'parsed_credit_card_statements.json')
        if not os.path.isfile(src):
            messagebox.showwarning('No source', f'JSON output not found: {src}')
            return
        dest = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
        if dest:
            try:
                shutil.copy(src, dest)
                messagebox.showinfo('Saved', f'JSON saved to {dest}')
            except Exception as e:
                messagebox.showerror('Error', str(e))

    def save_csv_as(self):
        src = self.out_csv_var.get().strip() or os.path.join(os.getcwd(), 'parsed_credit_card_statements.csv')
        if not os.path.isfile(src):
            messagebox.showwarning('No source', f'CSV output not found: {src}')
            return
        dest = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if dest:
            try:
                shutil.copy(src, dest)
                messagebox.showinfo('Saved', f'CSV saved to {dest}')
            except Exception as e:
                messagebox.showerror('Error', str(e))

    def populate_table(self, data_list):
        # Clear existing
        for col in self.output_tree['columns']:
            self.output_tree.heading(col, text='')
        self.output_tree.delete(*self.output_tree.get_children())
        # Determine columns from keys of first item
        if not isinstance(data_list, list) or not data_list:
            return
        cols = list(data_list[0].keys())
        self.output_tree['columns'] = cols
        for c in cols:
            self.output_tree.heading(c, text=c)
            self.output_tree.column(c, width=120, anchor='w')
        # Insert rows
        for row in data_list:
            vals = [row.get(c, '') for c in cols]
            self.output_tree.insert('', 'end', values=vals)

if __name__ == '__main__':
    app = PDFParserGUI()
    app.mainloop()
