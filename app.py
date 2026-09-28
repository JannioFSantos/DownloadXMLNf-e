import json
import os
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "Download XML NF-e - JannioFSantos"
BASE_DIR = Path(__file__).resolve().parent
PHP_SCRIPT = BASE_DIR / "php" / "distribuicao.php"

class NFeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("720x610")
        self.root.minsize(680, 560)

        self.cnpj = tk.StringVar()
        self.uf = tk.StringVar(value="CE")
        self.certificado = tk.StringVar()
        self.senha = tk.StringVar()
        self.destino = tk.StringVar(value=str(Path.home() / "Downloads" / "NFe"))
        self.status = tk.StringVar(value="Pronto para sincronizar.")
        self.progress = tk.DoubleVar(value=0)

        self._build()

    def _build(self):
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Download automático de NF-e 55", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Distribuição DF-e oficial • Certificado A1 • Controle automático de NSU").pack(anchor="w", pady=(2, 18))

        form = ttk.Frame(frame)
        form.pack(fill="x")
        self._field(form, "CNPJ", self.cnpj, 0)
        ttk.Label(form, text="UF").grid(row=1, column=0, sticky="w", pady=7)
        ttk.Combobox(form, textvariable=self.uf, values=[
            "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
            "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"
        ], width=8, state="readonly").grid(row=1, column=1, sticky="w", pady=7)

        ttk.Label(form, text="Certificado A1 (.pfx/.p12)").grid(row=2, column=0, sticky="w", pady=7)
        cert_row = ttk.Frame(form)
        cert_row.grid(row=2, column=1, sticky="ew", pady=7)
        ttk.Entry(cert_row, textvariable=self.certificado).pack(side="left", fill="x", expand=True)
        ttk.Button(cert_row, text="Selecionar", command=self.select_cert).pack(side="left", padx=(8,0))

        ttk.Label(form, text="Senha do certificado").grid(row=3, column=0, sticky="w", pady=7)
        ttk.Entry(form, textvariable=self.senha, show="•").grid(row=3, column=1, sticky="ew", pady=7)

        ttk.Label(form, text="Pasta dos XMLs").grid(row=4, column=0, sticky="w", pady=7)
        dest_row = ttk.Frame(form)
        dest_row.grid(row=4, column=1, sticky="ew", pady=7)
        ttk.Entry(dest_row, textvariable=self.destino).pack(side="left", fill="x", expand=True)
        ttk.Button(dest_row, text="Selecionar", command=self.select_dest).pack(side="left", padx=(8,0))

        form.columnconfigure(1, weight=1)

        self.sync_button = ttk.Button(frame, text="Sincronizar NF-e", command=self.start_sync)
        self.sync_button.pack(fill="x", pady=(18, 10), ipady=7)

        ttk.Progressbar(frame, variable=self.progress, maximum=100, mode="indeterminate").pack(fill="x")
        ttk.Label(frame, textvariable=self.status).pack(anchor="w", pady=(7, 8))

        ttk.Label(frame, text="Log").pack(anchor="w")
        self.log = tk.Text(frame, height=13, wrap="word", state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, pady=(4, 0))

    def _field(self, parent, label, variable, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=7)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=7)

    def select_cert(self):
        path = filedialog.askopenfilename(filetypes=[("Certificado A1", "*.pfx *.p12"), ("Todos os arquivos", "*.*")])
        if path:
            self.certificado.set(path)

    def select_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.destino.set(path)

    def append_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def validate(self):
        cnpj = "".join(ch for ch in self.cnpj.get() if ch.isdigit())
        if len(cnpj) != 14:
            raise ValueError("Informe um CNPJ com 14 dígitos.")
        cert = Path(self.certificado.get())
        if not cert.is_file():
            raise ValueError("Selecione um certificado A1 válido.")
        if not self.senha.get():
            raise ValueError("Informe a senha do certificado.")
        if not PHP_SCRIPT.is_file():
            raise ValueError("Backend PHP não encontrado.")
        return cnpj

    def start_sync(self):
        try:
            cnpj = self.validate()
        except ValueError as exc:
            messagebox.showerror("Validação", str(exc))
            return
        self.sync_button.configure(state="disabled")
        self.progress.start(12)
        self.status.set("Consultando Distribuição DF-e...")
        threading.Thread(target=self.run_sync, args=(cnpj,), daemon=True).start()

    def run_sync(self, cnpj):
        try:
            destino = Path(self.destino.get())
            destino.mkdir(parents=True, exist_ok=True)
            cmd = [
                "php", str(PHP_SCRIPT),
                "--cnpj", cnpj,
                "--uf", self.uf.get(),
                "--cert", self.certificado.get(),
                "--password", self.senha.get(),
                "--output", str(destino),
            ]
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", creationflags=creationflags
            )
            last = None
            for line in process.stdout:
                line = line.rstrip()
                self.root.after(0, self.append_log, line)
                try:
                    last = json.loads(line)
                except json.JSONDecodeError:
                    pass
            code = process.wait()
            if code != 0:
                raise RuntimeError("A sincronização terminou com erro. Consulte o log.")
            msg = "Sincronização concluída."
            if isinstance(last, dict):
                msg = f"Concluído. XML completos: {last.get('xml_completos', 0)} | Resumos: {last.get('resumos', 0)} | ultNSU: {last.get('ultNSU', '-')}"
            self.root.after(0, self.finish, msg, False)
        except FileNotFoundError:
            self.root.after(0, self.finish, "PHP não encontrado. Instale PHP 8.1+ e Composer.", True)
        except Exception as exc:
            self.root.after(0, self.finish, str(exc), True)

    def finish(self, msg, error):
        self.progress.stop()
        self.status.set(msg)
        self.sync_button.configure(state="normal")
        if error:
            messagebox.showerror("Erro", msg)
        else:
            messagebox.showinfo("NF-e", msg)

if __name__ == "__main__":
    root = tk.Tk()
    NFeDownloaderApp(root)
    root.mainloop()
