"""
logger.py
Sistema de logging, relatórios CSV e gestão de eventos.
"""

import logging
import sys
import queue
import threading
import datetime
import csv
import os
import json
from collections import defaultdict
from typing import List
from models import ResumoNota, VendaPDV, EstatisticasExecucao


class SistemaLogging:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._inicializar()
        return cls._instance
    
    def _inicializar(self):
        self.logger = logging.getLogger("AutomacaoNF")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        self.file_handler = None
        self.caminho_log = None
        self.queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._processar_fila, daemon=True)
        self.worker_thread.start()
        self.metricas = []
        self.eventos = []
    
    def criar_arquivo_log(self, formato: str = 'txt') -> str:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if formato.upper() == 'TXT':
            filename = f"log_automacao_nf_{timestamp}.txt"
            self.file_handler = logging.FileHandler(filename, encoding='utf-8')
            self.file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
                datefmt='%d/%m/%Y %H:%M:%S'
            )
            self.file_handler.setFormatter(file_format)
            self.logger.addHandler(self.file_handler)
        else:
            filename = f"log_automacao_nf_{timestamp}.{formato.lower()}"
        
        self.caminho_log = filename
        self.info(f"Log iniciado: {filename} (Formato: {formato})")
        return filename
    
    def _processar_fila(self):
        while True:
            try:
                level, msg, extra = self.queue.get(timeout=1)
                if level == 'info':
                    self.logger.info(msg)
                elif level == 'error':
                    self.logger.error(msg)
                elif level == 'warning':
                    self.logger.warning(msg)
                elif level == 'debug':
                    self.logger.debug(msg)
                
                self.eventos.append({
                    'timestamp': datetime.datetime.now().isoformat(),
                    'level': level,
                    'mensagem': msg,
                    'extra': extra
                })
            except queue.Empty:
                continue
    
    def info(self, msg: str, extra: dict = None):
        self.queue.put(('info', msg, extra))
    
    def error(self, msg: str, extra: dict = None):
        self.queue.put(('error', msg, extra))
    
    def warning(self, msg: str, extra: dict = None):
        self.queue.put(('warning', msg, extra))
    
    def debug(self, msg: str, extra: dict = None):
        self.queue.put(('debug', msg, extra))
    
    def exportar_csv_vendas(self, vendas: List[VendaPDV], filename: str = None) -> str:
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"relatorio_vendas_pdv_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            
            writer.writerow(['RELATORIO DE VENDAS - PDV'])
            writer.writerow(['Gerado em:', datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')])
            writer.writerow([])
            
            writer.writerow(['RESUMO EXECUTIVO'])
            writer.writerow(['Total de Vendas:', len(vendas)])
            writer.writerow(['Vendas com Sucesso:', sum(1 for v in vendas if v.status == 'OK')])
            writer.writerow(['Vendas com Falha:', sum(1 for v in vendas if v.status == 'ERRO')])
            writer.writerow(['Total de Itens:', sum(len(v.itens) for v in vendas)])
            writer.writerow(['Valor Total Geral:', f"R$ {sum(v.valor_total for v in vendas):,.2f}"])
            writer.writerow([])
            
            writer.writerow(['DETALHAMENTO POR VENDA'])
            writer.writerow([
                'N Venda', 'Status', 'Itens Totais', 'Itens OK', 'Itens Falha',
                'Qtd Total', 'Valor Total', 'Tempo (s)', 'Inicio', 'Fim'
            ])
            
            for venda in vendas:
                writer.writerow([
                    venda.numero,
                    venda.status,
                    len(venda.itens),
                    venda.itens_sucesso,
                    venda.itens_falha,
                    f"{venda.quantidade_total:.3f}",
                    f"{venda.valor_total:.2f}",
                    f"{venda.tempo_total:.2f}",
                    venda.timestamp_inicio.strftime('%H:%M:%S'),
                    venda.timestamp_fim.strftime('%H:%M:%S') if venda.timestamp_fim else 'N/A'
                ])
            
            writer.writerow([])
            
            writer.writerow(['DETALHAMENTO POR ITEM'])
            writer.writerow([
                'N Venda', 'Seq', 'Codigo Produto', 'Unidade', 'Quantidade',
                'Valor Unitario', 'Valor Total', 'Status', 'Tempo Proc (s)',
                'Inicio Item', 'Fim Item'
            ])
            
            for venda in vendas:
                for seq, item in enumerate(venda.itens, 1):
                    writer.writerow([
                        venda.numero,
                        seq,
                        item.produto.codigo,
                        item.produto.unidade,
                        f"{item.quantidade:.3f}" if item.produto.unidade == 'KG' else int(item.quantidade),
                        f"{item.valor_unitario:.2f}",
                        f"{item.valor_total:.2f}",
                        item.status,
                        f"{item.tempo_processamento:.2f}",
                        item.timestamp_inicio.strftime('%H:%M:%S.%f')[:-3],
                        item.timestamp_fim.strftime('%H:%M:%S.%f')[:-3] if item.timestamp_fim else 'N/A'
                    ])
        
        self.info(f"Relatorio CSV de vendas exportado: {filename}")
        return filename
    
    def exportar_csv(self, resumos: List[ResumoNota], filename: str = None) -> str:
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"relatorio_detalhado_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            
            writer.writerow(['RELATORIO DE AUTOMACAO - NOTAS FISCAIS DE ENTRADA'])
            writer.writerow(['Gerado em:', datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')])
            writer.writerow([])
            
            writer.writerow(['RESUMO EXECUTIVO'])
            writer.writerow(['Total de Notas:', len(resumos)])
            writer.writerow(['Notas com Sucesso:', sum(1 for r in resumos if r.status == 'OK')])
            writer.writerow(['Notas com Falha:', sum(1 for r in resumos if r.status == 'ERRO')])
            writer.writerow(['Total de Itens:', sum(len(r.itens) for r in resumos)])
            writer.writerow(['Valor Total Geral:', f"R$ {sum(r.valor_total for r in resumos):,.2f}"])
            writer.writerow([])
            
            writer.writerow(['DETALHAMENTO POR NOTA'])
            writer.writerow([
                'N Nota', 'Status', 'Itens Totais', 'Itens OK', 'Itens Falha',
                'Qtd UN', 'Qtd KG', 'Qtd Total', 'Valor Total', 'Tempo (s)', 
                'Inicio', 'Fim'
            ])
            
            for resumo in resumos:
                writer.writerow([
                    resumo.numero,
                    resumo.status,
                    len(resumo.itens),
                    resumo.itens_sucesso,
                    resumo.itens_falha,
                    resumo.total_un,
                    resumo.total_kg,
                    f"{resumo.quantidade_total:.3f}",
                    f"{resumo.valor_total:.2f}",
                    f"{resumo.tempo_total:.2f}",
                    resumo.timestamp_inicio.strftime('%H:%M:%S'),
                    resumo.timestamp_fim.strftime('%H:%M:%S') if resumo.timestamp_fim else 'N/A'
                ])
            
            writer.writerow([])
            
            writer.writerow(['DETALHAMENTO POR ITEM'])
            writer.writerow([
                'N Nota', 'Seq', 'Codigo Produto', 'Unidade', 'Quantidade',
                'Valor Unitario', 'Valor Total', 'Status', 'Tempo Proc (s)',
                'Inicio Item', 'Fim Item'
            ])
            
            for resumo in resumos:
                for seq, item in enumerate(resumo.itens, 1):
                    writer.writerow([
                        resumo.numero,
                        seq,
                        item.produto.codigo,
                        item.produto.unidade,
                        f"{item.quantidade:.3f}" if item.produto.unidade == 'KG' else int(item.quantidade),
                        f"{item.valor_unitario:.2f}",
                        f"{item.valor_total:.2f}",
                        item.status,
                        f"{item.tempo_processamento:.2f}",
                        item.timestamp_inicio.strftime('%H:%M:%S.%f')[:-3],
                        item.timestamp_fim.strftime('%H:%M:%S.%f')[:-3] if item.timestamp_fim else 'N/A'
                    ])
            
            writer.writerow([])
            
            writer.writerow(['FREQUENCIA DE PRODUTOS'])
            produto_freq = defaultdict(lambda: {'count': 0, 'unidade': '', 'valor_total': 0})
            for resumo in resumos:
                for item in resumo.itens:
                    cod = item.produto.codigo
                    produto_freq[cod]['count'] += 1
                    produto_freq[cod]['unidade'] = item.produto.unidade
                    produto_freq[cod]['valor_total'] += item.valor_total
            
            writer.writerow(['Codigo', 'Unidade', 'Vezes Usado', 'Valor Total Acumulado'])
            for cod, dados in sorted(produto_freq.items(), key=lambda x: x[1]['count'], reverse=True):
                writer.writerow([cod, dados['unidade'], dados['count'], f"{dados['valor_total']:.2f}"])
        
        self.info(f"Relatorio CSV exportado: {filename}")
        return filename


# Instância global do logger
log = SistemaLogging()