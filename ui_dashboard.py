"""
ui_dashboard.py
Dashboard de acompanhamento em tempo real da execução.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
import threading
import time
import datetime


class DashboardExecucao:
    """Dashboard para acompanhar execucao em tempo real."""
    
    def __init__(self, sistema: str):
        self.sistema = sistema
        self.root = None
        self.queue = queue.Queue()
        self.running = False
        self.thread = None
    
    def iniciar(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        self.root = tk.Tk()
        self.root.title(f"Dashboard - Automação {self.sistema}")
        self.root.geometry("600x400")
        
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(
            header_frame,
            text=f"🏢 AUTOMAÇÃO {self.sistema}",
            font=('Segoe UI', 14, 'bold'),
            foreground='#1a237e'
        ).pack(side='left')
        
        self.lbl_status = ttk.Label(
            header_frame,
            text="Aguardando início...",
            font=('Segoe UI', 10),
            foreground='#666'
        )
        self.lbl_status.pack(side='right')
        
        self.frame_geral = ttk.LabelFrame(self.root, text="Progresso Geral", padding=10)
        self.frame_geral.pack(fill='x', padx=10, pady=5)
        
        self.progress_geral = ttk.Progressbar(self.frame_geral, length=500, mode='determinate')
        self.progress_geral.pack()
        
        self.lbl_progresso = ttk.Label(self.frame_geral, text="Processando...")
        self.lbl_progresso.pack()
        
        self.frame_stats = ttk.LabelFrame(self.root, text="Estatísticas em Tempo Real", padding=10)
        self.frame_stats.pack(fill='x', padx=10, pady=5)
        
        self.lbl_itens = ttk.Label(self.frame_stats, text="Itens processados: 0")
        self.lbl_itens.pack(anchor='w')
        
        self.lbl_valor = ttk.Label(self.frame_stats, text="Valor total: R$ 0,00")
        self.lbl_valor.pack(anchor='w')
        
        self.lbl_tempo = ttk.Label(self.frame_stats, text="Tempo decorrido: 00:00")
        self.lbl_tempo.pack(anchor='w')
        
        self.txt_log = scrolledtext.ScrolledText(self.root, height=10, state='disabled')
        self.txt_log.pack(fill='both', expand=True, padx=10, pady=5)
        
        self._atualizar()
        self.root.mainloop()
    
    def _atualizar(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                tipo = msg.get('tipo')
                
                if tipo == 'status':
                    self.lbl_status.config(text=msg['texto'])
                elif tipo == 'progresso':
                    self.progress_geral['value'] = msg['percentual']
                    self.lbl_progresso.config(text=msg['texto'])
                elif tipo == 'stats':
                    self.lbl_itens.config(text=f"Itens processados: {msg['itens']}")
                    self.lbl_valor.config(text=f"Valor total: R$ {msg['valor']:,.2f}")
                    self.lbl_tempo.config(text=f"Tempo decorrido: {msg['tempo']}")
                elif tipo == 'log':
                    self.txt_log.config(state='normal')
                    self.txt_log.insert('end', msg['texto'] + '\n')
                    self.txt_log.see('end')
                    self.txt_log.config(state='disabled')
        except queue.Empty:
            pass
        
        if self.running:
            self.root.after(100, self._atualizar)
    
    def atualizar(self, tipo: str, **kwargs):
        self.queue.put({'tipo': tipo, **kwargs})
    
    def fechar(self):
        self.running = False
        if self.root:
            self.root.quit()