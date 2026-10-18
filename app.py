import json, os, subprocess, threading, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from xml.etree import ElementTree as ET

APP_TITLE="Download XML NF-e - JannioFSantos"
BASE_DIR=Path(__file__).resolve().parent
DIST=BASE_DIR/"php"/"distribuicao.php"
MANIF=BASE_DIR/"php"/"manifestacao.php"

class App:
    def __init__(self,root):
        self.root=root; root.title(APP_TITLE); root.geometry("940x720")
        self.cnpj=tk.StringVar(); self.uf=tk.StringVar(value="CE"); self.cert=tk.StringVar()
        self.password=tk.StringVar(); self.output=tk.StringVar(value=str(Path.home()/"Downloads"/"NFe"))
        self.status=tk.StringVar(value="Pronto."); self.rows={}
        self.build()

    def build(self):
        f=ttk.Frame(self.root,padding=16); f.pack(fill="both",expand=True)
        ttk.Label(f,text="Download automático de NF-e 55",font=("Segoe UI",18,"bold")).pack(anchor="w")
        ttk.Label(f,text="Distribuição DF-e • Certificado A1 • NSU automático • Manifestação explícita").pack(anchor="w",pady=(2,12))
        form=ttk.Frame(f); form.pack(fill="x")
        self.field(form,"CNPJ",self.cnpj,0)
        ttk.Label(form,text="UF").grid(row=1,column=0,sticky="w",pady=5)
        ttk.Combobox(form,textvariable=self.uf,state="readonly",width=8,values="AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()).grid(row=1,column=1,sticky="w")
        ttk.Label(form,text="Certificado A1").grid(row=2,column=0,sticky="w",pady=5)
        r=ttk.Frame(form); r.grid(row=2,column=1,sticky="ew"); ttk.Entry(r,textvariable=self.cert).pack(side="left",fill="x",expand=True); ttk.Button(r,text="Selecionar",command=self.pick_cert).pack(side="left",padx=5)
        self.field(form,"Senha",self.password,3,show="•")
        ttk.Label(form,text="Pasta dos XMLs").grid(row=4,column=0,sticky="w",pady=5)
        r=ttk.Frame(form); r.grid(row=4,column=1,sticky="ew"); ttk.Entry(r,textvariable=self.output).pack(side="left",fill="x",expand=True); ttk.Button(r,text="Selecionar",command=self.pick_dir).pack(side="left",padx=5)
        form.columnconfigure(1,weight=1)
        bar=ttk.Frame(f); bar.pack(fill="x",pady=10)
        self.sync=ttk.Button(bar,text="Sincronizar NF-e",command=self.start_sync); self.sync.pack(side="left")
        ttk.Button(bar,text="Atualizar lista",command=self.load_documents).pack(side="left",padx=6)
        self.manifest=ttk.Button(bar,text="Ciência da Operação",command=self.start_manifest); self.manifest.pack(side="left")
        ttk.Label(f,textvariable=self.status).pack(anchor="w",pady=(0,7))
        cols=("data","numero","emitente","valor","tipo")
        self.tree=ttk.Treeview(f,columns=cols,show="headings",height=13,selectmode="browse")
        for c,t,w in [("data","Emissão",130),("numero","NF-e",80),("emitente","Emitente",300),("valor","Valor",100),("tipo","Situação",150)]:
            self.tree.heading(c,text=t); self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True)
        ttk.Label(f,text="Log").pack(anchor="w",pady=(8,0))
        self.log=tk.Text(f,height=8,state="disabled",font=("Consolas",9)); self.log.pack(fill="x")
        self.load_documents()

    def field(self,p,l,v,row,show=None):
        ttk.Label(p,text=l).grid(row=row,column=0,sticky="w",pady=5); ttk.Entry(p,textvariable=v,show=show).grid(row=row,column=1,sticky="ew",pady=5)
    def pick_cert(self):
        x=filedialog.askopenfilename(filetypes=[("Certificado A1","*.pfx *.p12")]); self.cert.set(x or self.cert.get())
    def pick_dir(self):
        x=filedialog.askdirectory(); self.output.set(x or self.output.get())
    def addlog(self,s):
        self.log.configure(state="normal"); self.log.insert("end",s.rstrip()+"\n"); self.log.see("end"); self.log.configure(state="disabled")
    def validate(self):
        c="".join(x for x in self.cnpj.get() if x.isdigit())
        if len(c)!=14: raise ValueError("Informe um CNPJ com 14 dígitos.")
        if not Path(self.cert.get()).is_file(): raise ValueError("Selecione o certificado A1.")
        if not self.password.get(): raise ValueError("Informe a senha do certificado.")
        return c
    def basecmd(self,script,cnpj):
        return ["php",str(script),"--cnpj",cnpj,"--uf",self.uf.get(),"--cert",self.cert.get(),"--password",self.password.get(),"--output",self.output.get()]
    def run(self,cmd):
        flags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0
        p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",creationflags=flags)
        last=None
        for line in p.stdout:
            line=line.rstrip(); self.root.after(0,self.addlog,line)
            try: last=json.loads(line)
            except: pass
        if p.wait()!=0: raise RuntimeError((last or {}).get("mensagem","Operação terminou com erro."))
        return last or {}
    def start_sync(self):
        try: c=self.validate()
        except Exception as e: messagebox.showerror("Validação",str(e)); return
        self.sync.configure(state="disabled"); self.status.set("Sincronizando...")
        threading.Thread(target=self.worker_sync,args=(c,),daemon=True).start()
    def worker_sync(self,c):
        try:
            Path(self.output.get()).mkdir(parents=True,exist_ok=True); x=self.run(self.basecmd(DIST,c))
            self.root.after(0,self.finish_sync,f"Concluído: {x.get('xml_completos',0)} XML completos, {x.get('resumos',0)} resumos. ultNSU {x.get('ultNSU','-')}")
        except Exception as e: self.root.after(0,self.finish_sync,str(e),True)
    def finish_sync(self,msg,error=False):
        self.sync.configure(state="normal"); self.status.set(msg); self.load_documents()
        (messagebox.showerror if error else messagebox.showinfo)("NF-e",msg)

    def parse_doc(self,path):
        try:
            root=ET.parse(path).getroot()
            def one(tag):
                n=root.find(".//{*}"+tag); return (n.text or "").strip() if n is not None else ""
            chave=one("chNFe")
            if not chave:
                inf=root.find(".//{*}infNFe")
                if inf is not None: chave=(inf.attrib.get("Id","").replace("NFe",""))
            return {"path":str(path),"chave":chave,"data":one("dhEmi") or one("dEmi"),"numero":one("nNF"),"emitente":one("xNome"),"valor":one("vNF")}
        except: return None
    def load_documents(self):
        for x in self.tree.get_children(): self.tree.delete(x)
        self.rows={}
        base=Path(self.output.get())
        for folder,label in [("resumos","Aguardando manifestação"),("xml","XML completo")]:
            d=base/folder
            if not d.exists(): continue
            for p in sorted(d.glob("*.xml"),reverse=True):
                x=self.parse_doc(p)
                if not x or not x["chave"]: continue
                iid=self.tree.insert("", "end", values=(x["data"][:19],x["numero"],x["emitente"],x["valor"],label))
                x["tipo"]=folder; self.rows[iid]=x

    def start_manifest(self):
        sel=self.tree.selection()
        if not sel: messagebox.showwarning("Manifestação","Selecione uma NF-e."); return
        doc=self.rows.get(sel[0])
        if not doc or doc["tipo"]!="resumos": messagebox.showinfo("Manifestação","A NF-e selecionada já possui XML completo."); return
        if not messagebox.askyesno("Confirmar Ciência da Operação","Registrar Ciência da Operação para esta NF-e?\n\nEsse é um evento fiscal transmitido à SEFAZ."): return
        try: c=self.validate()
        except Exception as e: messagebox.showerror("Validação",str(e)); return
        self.manifest.configure(state="disabled"); self.status.set("Registrando Ciência da Operação...")
        threading.Thread(target=self.worker_manifest,args=(c,doc["chave"]),daemon=True).start()
    def worker_manifest(self,c,chave):
        try:
            cmd=self.basecmd(MANIF,c)+["--chave",chave]
            x=self.run(cmd)
            self.root.after(0,self.finish_manifest,f"Manifestação enviada: {x.get('cStat','')} {x.get('xMotivo','')}")
        except Exception as e: self.root.after(0,self.finish_manifest,str(e),True)
    def finish_manifest(self,msg,error=False):
        self.manifest.configure(state="normal"); self.status.set(msg)
        (messagebox.showerror if error else messagebox.showinfo)("Manifestação",msg)
        if not error: messagebox.showinfo("Próximo passo","A manifestação foi registrada. Use 'Sincronizar NF-e' depois para consultar a disponibilização do XML completo.")

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()
