"""
ui_menu.py
Menu principal de seleção de sistema e fluxos (com persistência INI).
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Optional
from config import Config
from settings_manager import SettingsManager


class MenuPrincipal:
    """Menu principal para selecionar sistema e fluxos."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Automação Multi-Sistema - SGA e PDV")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Inicializar gerenciador de configurações
        self.settings = SettingsManager()
        
        self.sistema_selecionado = None
        self.fluxos_selecionados = {}
        self.resultado = None
        
        self.main_frame = None
        self.frame_sistema = None
        self.frame_fluxos = None
        self.frame_config = None
        self.canvas_config = None
        self.scrollbar_config = None
        self.frame_config_inner = None
        
        # Referências para widgets de entrada que precisam ser acessados depois
        self.entry_senha_pdv = None
        
        self._construir_ui()
        self._centralizar_janela()
    
    def _centralizar_janela(self):
        self.root.update_idletasks()
        largura = self.root.winfo_width()
        altura = self.root.winfo_height()
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        x = (largura_tela // 2) - (largura // 2)
        y = (altura_tela // 2) - (altura // 2)
        self.root.geometry(f'{largura}x{altura}+{x}+{y}')
    
    def _on_frame_configure(self, event=None):
        self.canvas_config.configure(scrollregion=self.canvas_config.bbox("all"))
    
    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas_config.itemconfig(self.canvas_config.find_all()[0], width=canvas_width)
    
    def _on_mousewheel(self, event):
        """Handler para rolagem do mouse no canvas."""
        self.canvas_config.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _construir_ui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(
            self.main_frame,
            text="🏢 SISTEMA DE AUTOMAÇÃO MULTI-SISTEMA",
            font=('Segoe UI', 16, 'bold'),
            foreground='#1a237e'
        ).pack(pady=(0, 10))
        
        ttk.Label(
            self.main_frame,
            text="Selecione o sistema e os fluxos que deseja automatizar",
            font=('Segoe UI', 10)
        ).pack(pady=(0, 20))
        
        self.frame_sistema = ttk.LabelFrame(self.main_frame, text="1. SELECIONE O SISTEMA", padding=15)
        self.frame_sistema.pack(fill='x', pady=(0, 20))
        
        cards_frame = ttk.Frame(self.frame_sistema)
        cards_frame.pack()
        
        self.cards = {}
        for sistema, info in Config.SISTEMAS_DISPONIVEIS.items():
            card = tk.Frame(cards_frame, relief='groove', borderwidth=2, bg=info['cor'])
            card.pack(side='left', padx=10)
            
            inner_card = tk.Frame(card, bg='white', padx=20, pady=20)
            inner_card.pack(padx=2, pady=2)
            
            tk.Label(
                inner_card,
                text=f"{info['icone']}",
                font=('Segoe UI', 24),
                bg='white'
            ).pack()
            
            tk.Label(
                inner_card,
                text=sistema,
                font=('Segoe UI', 12, 'bold'),
                bg='white'
            ).pack(pady=(5, 0))
            
            tk.Label(
                inner_card,
                text=info['nome_completo'],
                font=('Segoe UI', 9),
                bg='white',
                wraplength=150
            ).pack(pady=(0, 10))
            
            btn = ttk.Button(
                inner_card,
                text="Selecionar",
                command=lambda s=sistema: self._selecionar_sistema(s)
            )
            btn.pack()
            
            self.cards[sistema] = {
                'frame': card,
                'button': btn,
                'original_bg': info['cor']
            }
        
        self.frame_fluxos = ttk.LabelFrame(self.main_frame, text="2. SELECIONE OS FLUXOS", padding=15)
        self.frame_config = ttk.LabelFrame(self.main_frame, text="3. CONFIGURAÇÕES", padding=15)
        
        self.config_container = ttk.Frame(self.frame_config)
        self.config_container.pack(fill='both', expand=True)
        
        self.canvas_config = tk.Canvas(self.config_container, height=400)
        self.scrollbar_config = ttk.Scrollbar(self.config_container, orient="vertical", command=self.canvas_config.yview)
        self.canvas_config.configure(yscrollcommand=self.scrollbar_config.set)
        
        self.canvas_config.pack(side='left', fill='both', expand=True)
        self.scrollbar_config.pack(side='right', fill='y')
        
        # IMPORTANTE: Bind do mousewheel para funcionar em todo o canvas
        self.canvas_config.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.frame_config_inner = ttk.Frame(self.canvas_config)
        self.canvas_config.create_window((0, 0), window=self.frame_config_inner, anchor='nw', width=820)
        
        self.frame_config_inner.bind('<Configure>', self._on_frame_configure)
        self.canvas_config.bind('<Configure>', self._on_canvas_configure)
        
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(pady=20)
        
        self.btn_voltar = ttk.Button(
            self.btn_frame,
            text="← Voltar",
            command=self._voltar,
            state='disabled'
        )
        self.btn_voltar.pack(side='left', padx=5)
        
        self.btn_prosseguir = ttk.Button(
            self.btn_frame,
            text="Próximo →",
            command=self._mostrar_fluxos
        )
        self.btn_prosseguir.pack(side='left', padx=5)
        
        self.btn_iniciar = ttk.Button(
            self.btn_frame,
            text="🚀 Iniciar Automação",
            command=self._iniciar,
            state='disabled'
        )
        self.btn_iniciar.pack(side='left', padx=5)
        
        self.status_var = tk.StringVar(value="Selecione um sistema para começar")
        ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 9, 'italic'),
            foreground='#666'
        ).pack(pady=10)
    
    def _selecionar_sistema(self, sistema: str):
        for sys_name, card_info in self.cards.items():
            if sys_name == sistema:
                card_info['frame'].config(bg='#1e8449', relief='solid', borderwidth=3)
                card_info['button'].config(text="✓ Selecionado", state='disabled')
            else:
                card_info['frame'].config(bg=card_info['original_bg'], relief='groove', borderwidth=2)
                card_info['button'].config(text="Selecionar", state='normal')
        
        self.sistema_selecionado = sistema
        self.status_var.set(f"Sistema selecionado: {sistema}")
        self.btn_prosseguir.config(state='normal')
        self.fluxos_selecionados = {}
    
    def _mostrar_fluxos(self):
        if not self.sistema_selecionado:
            messagebox.showwarning("Atenção", "Selecione um sistema primeiro.")
            return
        
        self.frame_sistema.pack_forget()
        self.frame_fluxos.pack(fill='x', pady=(0, 20))
        
        for widget in self.frame_fluxos.winfo_children():
            widget.destroy()
        
        fluxos = Config.SISTEMAS_DISPONIVEIS[self.sistema_selecionado]['fluxos']
        
        ttk.Label(
            self.frame_fluxos,
            text=f"Fluxos disponíveis para {self.sistema_selecionado}:",
            font=('Segoe UI', 10, 'bold')
        ).pack(anchor='w', pady=(0, 10))
        
        check_frame = ttk.Frame(self.frame_fluxos)
        check_frame.pack(anchor='w', padx=20)
        
        self.fluxo_vars = {}
        
        for fluxo in fluxos:
            var = tk.BooleanVar(value=False)
            self.fluxo_vars[fluxo] = var
            
            cb = ttk.Checkbutton(
                check_frame,
                text=fluxo,
                variable=var,
                command=self._atualizar_status_fluxos
            )
            cb.pack(anchor='w', pady=5)
        
        self.todos_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            check_frame,
            text="📋 Selecionar Todos",
            variable=self.todos_var,
            command=self._selecionar_todos
        ).pack(anchor='w', pady=(10, 5))
        
        self.btn_voltar.config(state='normal')
        self.btn_prosseguir.config(command=self._mostrar_config)
        self.btn_prosseguir.config(state='disabled')
        self.btn_iniciar.config(state='disabled')
    
    def _selecionar_todos(self):
        for var in self.fluxo_vars.values():
            var.set(self.todos_var.get())
        self._atualizar_status_fluxos()
    
    def _atualizar_status_fluxos(self):
        selecionados = [nome for nome, var in self.fluxo_vars.items() if var.get()]
        
        if selecionados:
            self.status_var.set(f"{len(selecionados)} fluxo(s) selecionado(s) para {self.sistema_selecionado}")
            self.btn_prosseguir.config(state='normal')
        else:
            self.status_var.set("Selecione pelo menos um fluxo")
            self.btn_prosseguir.config(state='disabled')
    
    def _mostrar_config(self):
        self.fluxos_selecionados = {
            nome: {} for nome, var in self.fluxo_vars.items() if var.get()
        }
        
        if not self.fluxos_selecionados:
            messagebox.showwarning("Atenção", "Selecione pelo menos um fluxo.")
            return
        
        self.frame_fluxos.pack_forget()
        self.frame_config.pack(fill='both', expand=True, pady=(0, 20))
        
        for widget in self.frame_config_inner.winfo_children():
            widget.destroy()
        
        ttk.Label(
            self.frame_config_inner,
            text="Configurações Gerais:",
            font=('Segoe UI', 10, 'bold')
        ).pack(anchor='w', pady=(0, 10))
        
        log_frame = ttk.Frame(self.frame_config_inner)
        log_frame.pack(anchor='w', padx=20, pady=5)
        
        ttk.Label(log_frame, text="Formato do Log:").pack(side='left', padx=(0, 10))
        
        self.formato_log = tk.StringVar(value='TXT')
        for formato in Config.FORMATOS_LOG:
            ttk.Radiobutton(
                log_frame,
                text=formato,
                variable=self.formato_log,
                value=formato
            ).pack(side='left', padx=5)
        
        for fluxo in self.fluxos_selecionados.keys():
            if fluxo == "Entrada de Produtos":
                self._criar_config_sga()
            elif fluxo == "Vendas Simples":
                self._criar_config_pdv()
        
        self.btn_prosseguir.config(command=self._confirmar_config)
        self.status_var.set("Configure as opções e prossiga")
        
        self.frame_config_inner.update_idletasks()
        self.canvas_config.configure(scrollregion=self.canvas_config.bbox("all"))
    
    def _criar_config_sga(self):
        fluxo_frame = ttk.LabelFrame(
            self.frame_config_inner,
            text="⚙️ Entrada de Produtos - Configurações Específicas",
            padding=10
        )
        fluxo_frame.pack(fill='x', pady=10, padx=20)
        
        ttk.Label(fluxo_frame, text="Quantidade de Notas:").pack(anchor='w')
        self.quantidade_notas_sga = tk.IntVar(value=1)
        ttk.Spinbox(
            fluxo_frame,
            from_=1,
            to=Config.MAX_NOTAS_SGA,
            textvariable=self.quantidade_notas_sga,
            width=10
        ).pack(anchor='w', pady=5)
        
        ttk.Label(fluxo_frame, text="Banco de Dados (.fdb):").pack(anchor='w')
        
        db_frame = ttk.Frame(fluxo_frame)
        db_frame.pack(anchor='w', pady=5)
        
        # Carregar valor salvo do INI
        bd_sga_salvo = self.settings.get_sga_bd()
        self.caminho_bd_sga = tk.StringVar(value=bd_sga_salvo)
        
        ttk.Entry(db_frame, textvariable=self.caminho_bd_sga, width=40, state='readonly').pack(side='left', padx=(0, 5))
        ttk.Button(db_frame, text="Selecionar...", command=lambda: self._selecionar_arquivo('sga')).pack(side='left')
        
        self.usar_mock_sga = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            fluxo_frame,
            text="Usar dados de exemplo (modo teste - sem banco)",
            variable=self.usar_mock_sga
        ).pack(anchor='w', pady=5)
    
    def _criar_config_pdv(self):
        fluxo_frame = ttk.LabelFrame(
            self.frame_config_inner,
            text="⚙️ Vendas Simples - Configurações Específicas",
            padding=10
        )
        fluxo_frame.pack(fill='x', pady=10, padx=20)
        
        ttk.Label(fluxo_frame, text="Quantidade de Vendas:").pack(anchor='w')
        self.quantidade_vendas_pdv = tk.IntVar(value=1)
        ttk.Spinbox(
            fluxo_frame,
            from_=1,
            to=Config.MAX_VENDAS_PDV,
            textvariable=self.quantidade_vendas_pdv,
            width=10
        ).pack(anchor='w', pady=5)
        
        ttk.Separator(fluxo_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # BANCO DE DADOS
        bd_frame_outer = tk.LabelFrame(fluxo_frame, text="🔴 BANCO DE DADOS FIREBIRD (OBRIGATÓRIO)", 
                                       padx=10, pady=10, fg='#d9534f', font=('Segoe UI', 9, 'bold'))
        bd_frame_outer.pack(fill='x', pady=5)
        
        ttk.Label(bd_frame_outer, text="Arquivo do Banco (.fdb):", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        bd_frame = ttk.Frame(bd_frame_outer)
        bd_frame.pack(anchor='w', pady=5, fill='x')
        
        # Carregar valor salvo
        bd_pdv_salvo = self.settings.get_pdv_bd()
        self.caminho_bd_pdv = tk.StringVar(value=bd_pdv_salvo)
        
        ttk.Entry(bd_frame, textvariable=self.caminho_bd_pdv, width=50, state='readonly').pack(side='left', padx=(0, 5), fill='x', expand=True)
        ttk.Button(bd_frame, text="📁 Selecionar Banco...", command=lambda: self._selecionar_arquivo('pdv')).pack(side='left')
        
        ttk.Label(bd_frame_outer, text="⚠️  Obrigatório informar o caminho do banco de dados (.fdb)", 
                 foreground='#d9534f', font=('Segoe UI', 8)).pack(anchor='w', pady=(5,0))
        
        ttk.Separator(fluxo_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # EXECUTÁVEL - ALTERADO PARA OBRIGATÓRIO
        exe_frame_outer = tk.LabelFrame(fluxo_frame, text="🚀 EXECUTÁVEL DO PDV (OBRIGATÓRIO)", 
                                        padx=10, pady=10, fg='#d9534f', font=('Segoe UI', 9, 'bold'))
        exe_frame_outer.pack(fill='x', pady=5)
        
        ttk.Label(exe_frame_outer, text="Caminho do executável (.exe):").pack(anchor='w')
        
        exe_frame = ttk.Frame(exe_frame_outer)
        exe_frame.pack(anchor='w', pady=5, fill='x')
        
        # Carregar valor salvo
        exe_salvo = self.settings.get_pdv_exe()
        self.caminho_exe_pdv = tk.StringVar(value=exe_salvo)
        
        ttk.Entry(exe_frame, textvariable=self.caminho_exe_pdv, width=50, state='readonly').pack(side='left', padx=(0, 5), fill='x', expand=True)
        ttk.Button(exe_frame, text="📁 Selecionar EXE...", command=lambda: self._selecionar_executavel('pdv')).pack(side='left')
        
        ttk.Label(exe_frame_outer, text="⚠️  Obrigatório informar o executável do PDV", 
                 foreground='#d9534f', font=('Segoe UI', 8)).pack(anchor='w', pady=(5,0))
        
        # CREDENCIAIS DE LOGIN - COM VALIDAÇÃO
        cred_frame = tk.LabelFrame(fluxo_frame, text="🔐 Credenciais de Acesso (OBRIGATÓRIO)", 
                                  padx=10, pady=10, fg='#d9534f', font=('Segoe UI', 9, 'bold'))
        cred_frame.pack(fill='x', pady=10)
        
        # Usuário
        user_frame = ttk.Frame(cred_frame)
        user_frame.pack(fill='x', pady=2)
        ttk.Label(user_frame, text="Usuário:", width=10).pack(side='left')
        
        # Carregar valor salvo
        usuario_salvo = self.settings.get_pdv_usuario()
        self.usuario_pdv = tk.StringVar(value=usuario_salvo)
        
        ttk.Entry(user_frame, textvariable=self.usuario_pdv, width=20).pack(side='left', padx=5)
        
        # Senha com opção de mostrar/ocultar
        pass_frame = ttk.Frame(cred_frame)
        pass_frame.pack(fill='x', pady=2)
        ttk.Label(pass_frame, text="Senha:", width=10).pack(side='left')
        
        # Carregar valor salvo
        senha_salva = self.settings.get_pdv_senha()
        self.senha_pdv = tk.StringVar(value=senha_salva)
        
        self.entry_senha_pdv = ttk.Entry(pass_frame, textvariable=self.senha_pdv, width=20, show='*')
        self.entry_senha_pdv.pack(side='left', padx=5)
        
        # Checkbox para mostrar senha
        self.mostrar_senha_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            pass_frame, 
            text="👁 Mostrar senha", 
            variable=self.mostrar_senha_var,
            command=self._toggle_mostrar_senha
        ).pack(side='left', padx=5)
        
        ttk.Separator(fluxo_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # MODO DE TESTE
        test_frame = ttk.Frame(fluxo_frame)
        test_frame.pack(fill='x', pady=5)
        
        self.usar_mock_pdv = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            test_frame,
            text="✅ Usar dados de exemplo (Modo Teste - Não conecta ao banco real)",
            variable=self.usar_mock_pdv
        ).pack(anchor='w')
    
    def _toggle_mostrar_senha(self):
        """Alterna entre mostrar e ocultar a senha."""
        if self.mostrar_senha_var.get():
            self.entry_senha_pdv.config(show='')
        else:
            self.entry_senha_pdv.config(show='*')
    
    def _selecionar_arquivo(self, sistema: str):
        arquivo = filedialog.askopenfilename(
            title="Selecione o banco Firebird (.fdb)",
            filetypes=[("Firebird Database", "*.fdb"), ("Todos os arquivos", "*.*")]
        )
        if arquivo:
            if sistema == 'sga':
                self.caminho_bd_sga.set(arquivo)
            elif sistema == 'pdv':
                self.caminho_bd_pdv.set(arquivo)
    
    def _selecionar_executavel(self, sistema: str):
        arquivo = filedialog.askopenfilename(
            title="Selecione o executável do PDV (.exe)",
            filetypes=[("Executável Windows", "*.exe"), ("Todos os arquivos", "*.*")]
        )
        if arquivo:
            if sistema == 'pdv':
                self.caminho_exe_pdv.set(arquivo)
    
    def _confirmar_config(self):
        # Validações específicas
        for fluxo in self.fluxos_selecionados.keys():
            if fluxo == "Entrada de Produtos":
                if not self.usar_mock_sga.get() and not self.caminho_bd_sga.get():
                    messagebox.showwarning("Atenção", 
                        "Para 'Entrada de Produtos', selecione um banco de dados (.fdb) ou use modo de exemplo.")
                    return
                
                qtd = self.quantidade_notas_sga.get()
                if not (1 <= qtd <= Config.MAX_NOTAS_SGA):
                    messagebox.showerror("Erro", 
                        f"Quantidade deve estar entre 1 e {Config.MAX_NOTAS_SGA}")
                    return
            
            elif fluxo == "Vendas Simples":
                # Validações obrigatórias para PDV
                if not self.usar_mock_pdv.get():
                    # Validar Banco
                    if not self.caminho_bd_pdv.get():
                        messagebox.showerror("Erro", 
                            "Para 'Vendas Simples', o BANCO DE DADOS (.fdb) é OBRIGATÓRIO!")
                        return
                    
                    # Validar EXE (agora obrigatório)
                    if not self.caminho_exe_pdv.get():
                        messagebox.showerror("Erro", 
                            "O EXECUTÁVEL DO PDV (.exe) é OBRIGATÓRIO!\n\n"
                            "Clique em '📁 Selecionar EXE...' e informe o caminho.")
                        return
                    
                    # Validar Login
                    if not self.usuario_pdv.get().strip():
                        messagebox.showerror("Erro", 
                            "O campo USUÁRIO é OBRIGATÓRIO!")
                        return
                    
                    # Validar Senha
                    if not self.senha_pdv.get().strip():
                        messagebox.showerror("Erro", 
                            "O campo SENHA é OBRIGATÓRIO!")
                        return
                    
                    # Salvar configurações no INI para próxima vez
                    self.settings.set_pdv_config(
                        self.caminho_exe_pdv.get(),
                        self.caminho_bd_pdv.get(),
                        self.usuario_pdv.get(),
                        self.senha_pdv.get()
                    )
                    self.settings.save()
                
                qtd = self.quantidade_vendas_pdv.get()
                if not (1 <= qtd <= Config.MAX_VENDAS_PDV):
                    messagebox.showerror("Erro", 
                        f"Quantidade deve estar entre 1 e {Config.MAX_VENDAS_PDV}")
                    return
        
        # Salvar config SGA também se aplicável
        if "Entrada de Produtos" in self.fluxos_selecionados and self.caminho_bd_sga.get():
            self.settings.set('SGA', 'caminho_bd', self.caminho_bd_sga.get())
            self.settings.save()
        
        self.btn_iniciar.config(state='normal')
        self.status_var.set("✅ Pronto para iniciar a automação!")
        messagebox.showinfo("Configuração Concluída", "Todas as configurações estão válidas e foram salvas!\nClique em '🚀 Iniciar Automação' para começar.")
    
    def _voltar(self):
        self.frame_fluxos.pack_forget()
        self.frame_config.pack_forget()
        self.frame_sistema.pack(fill='x', pady=(0, 20))
        
        self.btn_voltar.config(state='disabled')
        self.btn_prosseguir.config(command=self._mostrar_fluxos)
        self.btn_prosseguir.config(state='normal' if self.sistema_selecionado else 'disabled')
        self.btn_iniciar.config(state='disabled')
        
        self.status_var.set("Selecione um sistema para começar")
    
    def _iniciar(self):
        self.resultado = {
            'sistema': self.sistema_selecionado,
            'fluxos': self.fluxos_selecionados,
            'config': {
                'formato_log': self.formato_log.get()
            }
        }
        
        if "Entrada de Produtos" in self.fluxos_selecionados:
            self.resultado['config'].update({
                'quantidade_notas_sga': self.quantidade_notas_sga.get(),
                'caminho_bd_sga': self.caminho_bd_sga.get(),
                'usar_mock_sga': self.usar_mock_sga.get()
            })
        
        if "Vendas Simples" in self.fluxos_selecionados:
            self.resultado['config'].update({
                'quantidade_vendas_pdv': self.quantidade_vendas_pdv.get(),
                'caminho_bd_pdv': self.caminho_bd_pdv.get(),
                'usar_mock_pdv': self.usar_mock_pdv.get(),
                'caminho_exe_pdv': self.caminho_exe_pdv.get(),
                'usuario_pdv': self.usuario_pdv.get(),
                'senha_pdv': self.senha_pdv.get()
            })
        
        self.root.destroy()
    
    def executar(self) -> Optional[Dict]:
        self.root.mainloop()
        return self.resultado