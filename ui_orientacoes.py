"""
ui_orientacoes.py
Tela de checklist e orientações pré-execução.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List
from config import Config


class TelaOrientacoes:
    """Tela de orientacoes com checkboxes funcionais."""
    
    def __init__(self, sistema: str, fluxos: List[str]):
        self.root = tk.Tk()
        self.root.title(f"Automação {sistema} - Verificação de Pré-Requisitos")
        self.root.geometry("750x650")
        self.root.resizable(True, True)
        
        self.sistema = sistema
        self.fluxos = fluxos
        self.check_vars = {}
        self.pronto = False
        
        self._construir_ui()
        self._centralizar_janela()
    
    def _centralizar_janela(self):
        self.root.update_idletasks()
        largura = self.root.winfo_width()
        altura = self.root.winfo_height()
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        x = (largura_tela // 2) - (largura // 2)
        y = (altura_tela // 2) - (altura // 2) - 50
        self.root.geometry(f'{largura}x{altura}+{x}+{y}')
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _construir_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        ttk.Label(
            self.scrollable_frame,
            text=f"CHECKLIST DE PRÉ-REQUISITOS - {self.sistema}",
            font=('Segoe UI', 14, 'bold'),
            foreground='#1a5490'
        ).pack(pady=(0, 10))
        
        ttk.Label(
            self.scrollable_frame,
            text=f"Fluxos selecionados: {', '.join(self.fluxos)}",
            font=('Segoe UI', 10, 'bold'),
            foreground='#2e86c1'
        ).pack(pady=(0, 10))
        
        ttk.Label(
            self.scrollable_frame,
            text="Antes de iniciar a automação, verifique se todos os itens abaixo estão OK:",
            font=('Segoe UI', 10),
            wraplength=700
        ).pack(pady=(0, 20))
        
        if self.sistema == "SGA":
            self._criar_secao("SISTEMA", [
                f"O sistema {self.sistema} está ABERTO e visível na tela",
                "A janela 'Entrada de produtos' está em primeiro plano",
                "Não há outros diálogos, pop-ups ou mensagens de erro abertas",
            ])
        else:
            self._criar_secao("SISTEMA", [
                f"O sistema {self.sistema} será aberto AUTOMATICAMENTE pelo programa (se informado o .exe)",
                "Se preferir abrir manualmente, certifique-se de que está na tela de login",
                "Nenhum cupom deve estar aberto (o programa abrirá na tela inicial)",
                "Lista de entrega está habilitada nas configurações do PDV",
            ])
        
        if "Entrada de Produtos" in self.fluxos:
            self._criar_secao("CADASTROS OBRIGATÓRIOS - SGA", [
                f"Existe um fornecedor cadastrado com o nome EXATO: '{Config.FORNECEDOR_PADRAO}'",
                "O fornecedor está ativo e sem restrições",
                "Existem produtos cadastrados com as unidades 'UN' ou 'KG'",
            ])
        
        if "Vendas Simples" in self.fluxos:
            self._criar_secao("CADASTROS OBRIGATÓRIOS - PDV", [
                "Existem produtos cadastrados com código >= 6 caracteres",
                "Produtos têm preços definidos (PR_AVISTA > 0) no banco selecionado",
                "Produtos estão ativos (ATIVO = 0) no banco .fdb selecionado",
                "O caminho do banco de dados (.fdb) foi verificado e está correto",
            ])
        
        self._criar_secao("USUÁRIO E PERMISSÕES", [
            "Você configurou o login e senha corretos nas configurações (se usar automação)",
            "O usuário tem permissão para abrir cupom no PDV",
            "O usuário pode acessar o banco de dados Firebird",
        ])
        
        self._criar_secao("AMBIENTE", [
            "O computador não será bloqueado por screensaver durante a execução",
            "Desativei o CAPS LOCK (deve estar desligado)",
            "O servidor Firebird está rodando (se usar banco real)",
        ])
        
        ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill='x', pady=20)
        
        instrucoes = ttk.LabelFrame(self.scrollable_frame, text="INSTRUÇÕES IMPORTANTES", padding=10)
        instrucoes.pack(fill='x', pady=10)
        
        if self.sistema == "SGA":
            texto = """
• NÃO MOVA O MOUSE ou use o teclado durante a automação
• NÃO minimize ou altere o tamanho da janela do SGA
• NÃO abra outros programas durante a execução
• Mantenha o computador ligado e conectado à energia
• A automação pode levar vários minutos dependendo da quantidade
• Para CANCELAR a qualquer momento, pressione ESC rapidamente 3 vezes
            """
        else:
            texto = """
• O programa abrirá o PDV automaticamente (se informado o .exe) e fará login
• Se não informou o .exe, deixe o PDV aberto na tela de login
• NÃO MOVA O MOUSE ou use o teclado durante a automação
• NÃO abra outros programas durante a execução
• Mantenha o computador ligado e conectado à energia
• Aguarde o delay entre cupons para não travar o sistema
• Para CANCELAR a qualquer momento, pressione ESC rapidamente 3 vezes
• Já existe turno aberto(Certifique-se que o turno está aberto, pronto para fazer vendas)
            """
        
        ttk.Label(
            instrucoes,
            text=texto,
            font=('Consolas', 9),
            foreground='#d9534f',
            justify='left'
        ).pack(anchor='w')
        
        self.progress_frame = ttk.LabelFrame(self.scrollable_frame, text="Verificação de Itens", padding=10)
        self.progress_frame.pack(fill='x', pady=10)
        
        self.progress_label = ttk.Label(self.progress_frame, text="0/13 itens verificados")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(pady=5)
        
        btn_frame = ttk.Frame(self.scrollable_frame)
        btn_frame.pack(pady=20)
        
        self.btn_verificar = ttk.Button(
            btn_frame, 
            text="✅ Verificar e Prosseguir", 
            command=self._verificar_checklist,
            state='disabled'
        )
        self.btn_verificar.pack(side='left', padx=5)
        
        ttk.Button(
            btn_frame, 
            text="❌ Cancelar", 
            command=self._cancelar
        ).pack(side='left', padx=5)
        
        for var in self.check_vars.values():
            var.trace_add('write', self._atualizar_estado_botao)
    
    def _criar_secao(self, titulo: str, itens: List[str]):
        frame = ttk.LabelFrame(self.scrollable_frame, text=titulo, padding=10)
        frame.pack(fill='x', pady=5, padx=5)
        
        for texto in itens:
            var = tk.BooleanVar(value=False)
            key = texto[:20].replace(" ", "_").lower()
            self.check_vars[key] = var
            
            item_frame = ttk.Frame(frame)
            item_frame.pack(fill='x', pady=2)
            
            cb = tk.Checkbutton(
                item_frame,
                variable=var
            )
            cb.pack(side='left')
            
            lbl = ttk.Label(
                item_frame,
                text=texto,
                wraplength=600,
                justify='left'
            )
            lbl.pack(side='left', fill='x', expand=True)
    
    def _atualizar_estado_botao(self, *args):
        total = len(self.check_vars)
        marcados = sum(1 for v in self.check_vars.values() if v.get())
        
        self.progress_label.config(text=f"{marcados}/{total} itens verificados")
        self.progress_bar['value'] = (marcados / total) * 100
        
        if marcados == total:
            self.btn_verificar.config(state='normal')
            self.progress_label.config(text="Todos os itens verificados! Pronto para iniciar.")
        else:
            self.btn_verificar.config(state='disabled')
    
    def _verificar_checklist(self):
        faltantes = [k for k, v in self.check_vars.items() if not v.get()]
        
        if faltantes:
            messagebox.showwarning(
                "Atenção",
                f"Itens pendentes: {len(faltantes)}\n\nPor favor, verifique todos os pré-requisitos antes de continuar."
            )
            return
        
        resposta = messagebox.askyesno(
            "Confirmação Final",
            f"Todos os pré-requisitos para {self.sistema} foram verificados?\n\n"
            "Lembre-se: NÃO INTERFIRA no computador durante a automação!\n\n"
            "Deseja prosseguir com a execução?"
        )
        
        if resposta:
            self.pronto = True
            self.root.destroy()
    
    def _cancelar(self):
        if messagebox.askyesno("Confirmar", "Deseja realmente cancelar?"):
            self.pronto = False
            self.root.destroy()
    
    def executar(self) -> bool:
        self.root.mainloop()
        return self.pronto