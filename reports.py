"""
reports.py
Geradores de relatórios em diferentes formatos (TXT, JSON, CSV).
"""

import json
import csv
import datetime
import os
from collections import defaultdict
from dataclasses import asdict
from typing import List
from models import ResumoNota, EstatisticasExecucao, VendaPDV
from logger import log


class GeradorRelatorios:
    @staticmethod
    def gerar_relatorio_json(resumos, stats, filename=None):
        if not filename:
            filename = f"relatorio_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
        
        dados = {
            'metadata': {
                'data_geracao': datetime.datetime.now().isoformat(),
                'versao_sistema': '2.0',
                'total_notas': len(resumos),
                'estatisticas': asdict(stats)
            },
            'notas': []
        }
        
        for resumo in resumos:
            nota_dict = {
                'numero': resumo.numero,
                'status': resumo.status,
                'timestamps': {
                    'inicio': resumo.timestamp_inicio.isoformat(),
                    'fim': resumo.timestamp_fim.isoformat() if resumo.timestamp_fim else None
                },
                'totais': {
                    'itens': len(resumo.itens),
                    'un': resumo.total_un,
                    'kg': resumo.total_kg,
                    'quantidade': round(resumo.quantidade_total, 3),
                    'valor': round(resumo.valor_total, 2)
                },
                'itens': [{
                    'codigo': item.produto.codigo,
                    'unidade': item.produto.unidade,
                    'quantidade': item.quantidade,
                    'valor_unitario': item.valor_unitario,
                    'valor_total': item.valor_total,
                    'status': item.status,
                    'tempo_processamento': item.tempo_processamento
                } for item in resumo.itens]
            }
            dados['notas'].append(nota_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        
        log.info(f"JSON: {filename}")
        return filename
    
    @staticmethod
    def gerar_relatorio_texto(resumos, stats, filename=None):
        if not filename:
            filename = f"relatorio_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RELATORIO DE AUTOMACAO - NOTAS FISCAIS DE ENTRADA\n")
            f.write("=" * 80 + "\n")
            f.write(f"Gerado em: {datetime.datetime.now():%d/%m/%Y %H:%M:%S}\n\n")
            
            f.write("ESTATISTICAS GERAIS\n")
            f.write("-" * 80 + "\n")
            f.write(f"  Total de notas:      {stats.total_processos}\n")
            f.write(f"  Notas com sucesso:   {stats.processos_sucesso}\n")
            f.write(f"  Notas com falha:     {stats.processos_falha}\n")
            f.write(f"  Total de itens:      {stats.total_itens}\n")
            f.write(f"  Valor total:         R$ {stats.valor_total:,.2f}\n")
            f.write(f"  Tempo total:         {stats.tempo_total:.1f}s\n\n")
            
            for resumo in resumos:
                status = "OK" if resumo.status == "OK" else "FALHA"
                f.write(f"\n[{status}] NOTA {resumo.numero}\n")
                f.write("-" * 80 + "\n")
                f.write(f"  Itens: {len(resumo.itens)} (OK: {resumo.itens_sucesso}, Falha: {resumo.itens_falha})\n")
                f.write(f"  Valor: R$ {resumo.valor_total:,.2f}\n")
                f.write(f"  Tempo: {resumo.tempo_total:.1f}s\n")
        
        log.info(f"TXT: {filename}")
        return filename
    
    @staticmethod
    def gerar_csv_detalhado(resumos, stats, filename=None):
        return log.exportar_csv(resumos, filename)