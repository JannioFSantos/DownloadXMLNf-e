import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import os
import time
import re
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


#interface gráfica com Tkinterecho "# DownloadXMLNf-e" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/JannioFSantos/DownloadXMLNf-e.git
git push -u origin main
class NFeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Downloader de NF-e")
        self.root.geometry("500x600")  # Aumentei a altura para acomodar nova funcionalidade

        # Cria abas
        self.notebook = tk.ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        # Frame para download normal
        self.download_frame = tk.Frame(self.notebook)
        self.notebook.add(self.download_frame, text="Download NF-e")

        # Variáveis
        self.nfe_keys = tk.StringVar()
        self.download_path = tk.StringVar(value="Downloads")  # Diretório padrão
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Pronto")

        # Interface
        # Componentes para download normal
        tk.Label(self.download_frame, text="Chaves de Acesso da NF-e (44 dígitos cada):").pack(pady=10)
        tk.Label(self.download_frame, text="Separe múltiplas chaves por vírgula ou quebra de linha").pack(pady=2)
        
        # Text area para múltiplas chaves
        self.keys_text = tk.Text(self.download_frame, height=10, width=50)
        self.keys_text.pack(pady=5)

        # Frame para seleção de diretório
        path_frame = tk.Frame(self.download_frame)
        path_frame.pack(pady=10)
        
        tk.Label(path_frame, text="Diretório para salvar XMLs:").pack(side=tk.LEFT)
        tk.Entry(path_frame, textvariable=self.download_path, width=30).pack(side=tk.LEFT, padx=5)
        tk.Button(path_frame, text="Selecionar", command=self.select_download_directory).pack(side=tk.LEFT)

        self.download_button = tk.Button(self.download_frame, text="Baixar XMLs", command=self.download_nfe, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.download_button.pack(pady=10)

        # Barra de progresso
        progress_frame = tk.Frame(self.download_frame)
        progress_frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Label(progress_frame, textvariable=self.status_var, font=("Arial", 10)).pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = tk.Label(progress_frame, text="0%", font=("Arial", 9))
        self.progress_label.pack(anchor=tk.E)

    def select_download_directory(self):
        """Abre uma caixa de diálogo para selecionar o diretório de download."""
        directory = filedialog.askdirectory(
            title="Selecionar diretório para salvar XMLs",
            initialdir=os.path.expanduser("~")
        )
        if directory:
            self.download_path.set(directory)

    def update_progress(self, progress, status):
        """Atualiza a barra de progresso e o status."""
        self.progress_var.set(progress)
        self.status_var.set(status)
        self.progress_label.config(text=f"{progress:.0f}%")
        self.root.update_idletasks()

    def update_download_progress(self, current, total, filename):
        """Atualiza o progresso durante o download."""
        progress = (current / total) * 100 if total > 0 else 0
        self.update_progress(progress, f"Baixando: {filename}")

    def download_nfe_meudanfe(self, nfe_key):
        """Faz o download da NF-e usando automação web com Selenium e XPaths específicos."""
        try:
            print(f"⚡ Iniciando automação para chave: {nfe_key}")
            
            # Configura o diretório de download
            download_dir = self.download_path.get()
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            # Configuração do Chrome WebDriver (modo normal maximizado - funcional)
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Configura o diretório de download padrão com caminho absoluto
            download_dir_abs = os.path.abspath(download_dir)
            prefs = {
                "download.default_directory": download_dir_abs,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "profile.default_content_settings.popups": 0,  # Desabilita popups de download
                "download.extensions_to_open": "",  # Não abre automaticamente nenhum arquivo
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Inicializa o WebDriver
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            try:
                # ETAPA 1: Acessa a página principal
                print("1. 🌐 Acessando www.meudanfe.com.br...")
                driver.get("https://www.meudanfe.com.br/")
                
                # Aguarda a página carregar
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@id='searchTxt']"))
                )
                
                # ETAPA 2: Preenche o campo de pesquisa com a chave NFE
                print("2. ⌨️  Preenchendo campo de pesquisa...")
                search_field = driver.find_element(By.XPATH, "//*[@id='searchTxt']")
                search_field.clear()
                search_field.send_keys(nfe_key)
                
                # ETAPA 3: Clica no botão de consulta
                print("3. 🔍 Clicando em consultar...")
                search_button = driver.find_element(By.XPATH, "//*[@id='searchBtn']")
                search_button.click()
                
                # ETAPA 4: Aguarda 10 segundos (como solicitado)
                print("4. ⏰ Aguardando 10 segundos...")
                for i in range(10, 0, -1):
                    print(f"   {i}...")
                    time.sleep(1)
                
                # ETAPA 5: Verifica se o botão de download está disponível e clica
                print("5. 💾 Verificando botão de download...")
                try:
                    # Aguarda o botão de download ficar disponível
                    download_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[@id='downloadXmlBtn']/span"))
                    )
                    print("✅ Botão de download encontrado, clicando...")
                    download_button.click()
                    
                    # Aguarda o download ser concluído
                    print("6. 📥 Aguardando download...")
                    time.sleep(3)  # Aguarda o download ser iniciado
                    
                    # Verifica se o arquivo foi baixado
                    expected_filename = f"nfe_{nfe_key}.xml"
                    expected_path = os.path.join(download_dir_abs, expected_filename)
                    
                    # Monitora o download por até 60 segundos
                    max_wait = 1
                    waited = 0
                    download_complete = False
                    
                    while waited < max_wait and not download_complete:
                        # Verifica se o arquivo existe e não está sendo escrito
                        if os.path.exists(expected_path):
                            # Verifica se o arquivo não está sendo escrito (tamanho estável)
                            size1 = os.path.getsize(expected_path)
                            time.sleep(1)
                            size2 = os.path.getsize(expected_path)
                            
                            if size1 == size2 and size1 > 0:
                                print(f"✅ Download concluído: {expected_path}")
                                # Não mostra popup para não interromper o fluxo automático
                                download_complete = True
                                break
                        
                        # Também verifica por arquivos .crdownload (downloads em andamento no Chrome)
                        temp_files = [f for f in os.listdir(download_dir_abs) if f.endswith('.crdownload')]
                        if not temp_files:
                            # Se não há arquivos temporários, verifica se o download já terminou
                            if os.path.exists(expected_path):
                                print(f"✅ Download concluído: {expected_path}")
                                # Não mostra popup para não interromper o fluxo automático
                                download_complete = True
                                break
                        
                        print(f"   Aguardando... ({waited}s)")
                        time.sleep(1)
                        waited += 1
                    
                    if not download_complete:
                        # Verifica se o arquivo foi baixado com nome diferente
                        xml_files = [f for f in os.listdir(download_dir_abs) if f.endswith('.xml') and nfe_key in f]
                        if xml_files:
                            actual_path = os.path.join(download_dir_abs, xml_files[0])
                            print(f"✅ Download concluído (nome diferente): {actual_path}")
                            # Não mostra popup para não interromper o fluxo automático
                        else:
                            raise Exception("Tempo limite excedido aguardando download")
                        
                except Exception as e:
                    print(f"❌ Erro ao tentar baixar: {str(e)}")
                    # Tenta fazer screenshot para debug
                    screenshot_path = os.path.join(download_dir, f"erro_{nfe_key}.png")
                    driver.save_screenshot(screenshot_path)
                    print(f"📸 Screenshot salvo em: {screenshot_path}")
                    raise Exception(f"Falha no download: {str(e)}")
                
                # ETAPA 6: Clica no botão de nova consulta
                print("7. 🔄 Clicando em nova consulta...")
                try:
                    new_search_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[@id='newSearchBtn']/span"))
                    )
                    new_search_button.click()
                    time.sleep(2)  # Pequena pausa após nova consulta
                except:
                    print("⚠️  Botão de nova consulta não encontrado, continuando...")
                
            finally:
                # Fecha o navegador
                driver.quit()
                print("✅ Navegador fechado")
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            messagebox.showerror("Erro", f"Falha no processo: {str(e)}")

    def download_nfe_threaded(self, valid_keys):
        """Executa o download em uma thread separada para não travar a interface."""
        try:
            total_keys = len(valid_keys)
            download_dir_abs = os.path.abspath(self.download_path.get())
            
            # Inicia monitoramento de progresso
            self.monitor_progress(valid_keys, download_dir_abs, total_keys)
            
            # Processa cada chave válida
            for i, key in enumerate(valid_keys):
                self.update_progress((i / total_keys) * 100, f"Iniciando download {i+1} de {total_keys}")
                self.download_nfe_meudanfe(key)
                time.sleep(1)  # Pequena pausa entre os downloads
            
            # Garante que o progresso final seja 100%
            self.update_progress(100, "Todos os downloads concluídos com sucesso!")
            messagebox.showinfo("Concluído", f"Download de {total_keys} NF-e(s) concluído com sucesso!")
            
        except Exception as e:
            self.update_progress(0, f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Falha no processo: {str(e)}")
        
        finally:
            # Reabilita o botão
            self.download_button.config(state=tk.NORMAL)

    def monitor_progress(self, valid_keys, download_dir, total_keys):
        """Monitora o progresso dos downloads verificando os arquivos na pasta."""
        def check_progress():
            downloaded_count = 0
            for key in valid_keys:
                # Verifica se o arquivo foi baixado (com diferentes padrões de nome)
                xml_files = [f for f in os.listdir(download_dir) if f.endswith('.xml') and key in f]
                if xml_files:
                    downloaded_count += 1
            
            progress = (downloaded_count / total_keys) * 100
            self.update_progress(progress, f"Baixados: {downloaded_count} de {total_keys}")
            
            # Se ainda não terminou, continua monitorando
            if downloaded_count < total_keys:
                self.root.after(1000, check_progress)  # Verifica a cada 1 segundo
        
        # Inicia o monitoramento
        self.root.after(100, check_progress)

    def download_nfe(self):
        """Faz o download de múltiplas NF-es."""
        # Obtém o texto da área de texto
        keys_text = self.keys_text.get("1.0", tk.END).strip()
        
        if not keys_text:
            messagebox.showerror("Erro", "Por favor, insira pelo menos uma chave de acesso.")
            return
        
        # Processa as chaves (separadas por vírgula, espaço ou quebra de linha)
        keys = []
        for line in keys_text.split('\n'):
            for key in line.split(','):
                key = key.strip()
                if key:
                    keys.append(key)
        
        if not keys:
            messagebox.showerror("Erro", "Nenhuma chave válida encontrada.")
            return
        
        # Valida cada chave
        valid_keys = []
        for key in keys:
            if len(key) == 44 and key.isdigit():
                valid_keys.append(key)
            else:
                messagebox.showwarning("Aviso", f"Chave inválida ignorada: {key}")
        
        if not valid_keys:
            messagebox.showerror("Erro", "Nenhuma chave válida encontrada.")
            return
        
        # Desabilita o botão durante o processo
        self.download_button.config(state=tk.DISABLED)
        self.update_progress(0, "Iniciando downloads...")
        
        # Executa o download em uma thread separada
        thread = threading.Thread(target=self.download_nfe_threaded, args=(valid_keys,))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = NFeDownloaderApp(root)
    root.mainloop()
