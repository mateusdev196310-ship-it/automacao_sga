"""Ponto de entrada: seleção de fluxos, execução e relatório final."""

import os
import sys
import time
import datetime
from tkinter import messagebox
import pyautogui

# Importações dos módulos locais
from config import Config
from logger import log
from ui_menu import MenuPrincipal
from ui_orientacoes import TelaOrientacoes
from ui_dashboard import DashboardExecucao
from automacao_sga import AutomacaoSGA
from automacao_pdv import AutomacaoPDV
from utils import tocar_som_sucesso, tocar_som_erro


class SistemaAutomacaoMultiSistema:
    """Sistema principal que gerencia múltiplos sistemas e fluxos."""
    
    def __init__(self):
        self.log = log
        self.resultados = {}
    
    def executar(self):
        print("=" * 60)
        print("SISTEMA DE AUTOMAÇÃO MULTI-SISTEMA - SGA e PDV")
        print("=" * 60)
        
        try:
            print("\nAbrindo menu principal...")
            menu = MenuPrincipal()
            selecoes = menu.executar()
            
            if not selecoes:
                print("Operação cancelada pelo usuário.")
                return
            
            sistema = selecoes['sistema']
            fluxos = selecoes['fluxos']
            config = selecoes['config']
            
            print(f"\nSistema selecionado: {sistema}")
            print(f"Fluxos selecionados: {', '.join(fluxos.keys())}")
            
            print("\nAbrindo checklist de pré-requisitos...")
            tela_orientacoes = TelaOrientacoes(sistema, list(fluxos.keys()))
            if not tela_orientacoes.executar():
                print("Cancelado pelo usuário na fase de orientações.")
                return
            
            self.log.criar_arquivo_log(config['formato_log'])
            self.log.info("=" * 60)
            self.log.info(f"AUTOMAÇÃO {sistema} - INICIANDO")
            self.log.info("=" * 60)
            self.log.info(f"Data: {datetime.datetime.now():%d/%m/%Y %H:%M:%S}")
            self.log.info(f"Sistema: {sistema}")
            self.log.info(f"Fluxos: {list(fluxos.keys())}")
            self.log.info(f"Configurações: {config}")
            
            dashboard = DashboardExecucao(sistema)
            dashboard.iniciar()
            time.sleep(1)
            
            try:
                if sistema == "SGA":
                    resultados = self._executar_sga(fluxos, config, dashboard)
                elif sistema == "PDV":
                    resultados = self._executar_pdv(fluxos, config, dashboard)
                else:
                    raise ValueError(f"Sistema não suportado: {sistema}")
                
                self._processar_resultados(resultados, sistema, fluxos, dashboard)
                
            except Exception as e:
                self.log.error(f"ERRO NA EXECUÇÃO: {e}")
                tocar_som_erro()
                
                try:
                    screenshot = pyautogui.screenshot()
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot.save(f"erro_automacao_{sistema}_{timestamp}.png")
                    self.log.info(f"Screenshot do erro salvo: erro_automacao_{sistema}_{timestamp}.png")
                except:
                    pass
                
                messagebox.showerror("Erro", f"Falha na automação:\n\n{str(e)}")
                raise
                
            finally:
                try:
                    dashboard.fechar()
                except:
                    pass
                    
        except Exception as e:
            self.log.error(f"Erro geral: {e}")
            raise
    
    def _executar_sga(self, fluxos, config, dashboard):
        automacao = AutomacaoSGA(dashboard)
        resultados = {}
        
        for fluxo in fluxos.keys():
            try:
                dashboard.atualizar('status', texto=f"Executando: {fluxo}")
                self.log.info(f"\n{'='*60}")
                self.log.info(f"INICIANDO FLUXO: {fluxo}")
                self.log.info(f"{'='*60}")
                
                if fluxo == "Entrada de Produtos":
                    resultado = automacao.executar_fluxo_entrada_produtos(config)
                else:
                    resultado = {'sucesso': True, 'mensagem': f"Fluxo {fluxo} executado (simulação)"}
                
                resultados[fluxo] = resultado
                dashboard.atualizar('log', texto=f"Fluxo {fluxo}: {'✓ Sucesso' if resultado.get('sucesso') else '✗ Falha'}")
                
            except Exception as e:
                resultados[fluxo] = {'sucesso': False, 'erro': str(e)}
                self.log.error(f"Erro no fluxo {fluxo}: {e}")
                dashboard.atualizar('log', texto=f"Erro no fluxo {fluxo}: {e}")
        
        return resultados
    
    def _executar_pdv(self, fluxos, config, dashboard):
        automacao = AutomacaoPDV(dashboard)
        resultados = {}
        
        for fluxo in fluxos.keys():
            try:
                dashboard.atualizar('status', texto=f"Executando: {fluxo}")
                self.log.info(f"\n{'='*60}")
                self.log.info(f"INICIANDO FLUXO: {fluxo}")
                self.log.info(f"{'='*60}")
                
                if fluxo == "Vendas Simples":
                    resultado = automacao.executar_fluxo_vendas_simples(config)
                else:
                    resultado = {'sucesso': True, 'mensagem': f"Fluxo {fluxo} executado (simulação)"}
                
                resultados[fluxo] = resultado
                dashboard.atualizar('log', texto=f"Fluxo {fluxo}: {'✓ Sucesso' if resultado.get('sucesso') else '✗ Falha'}")
                
            except Exception as e:
                resultados[fluxo] = {'sucesso': False, 'erro': str(e)}
                self.log.error(f"Erro no fluxo {fluxo}: {e}")
                dashboard.atualizar('log', texto=f"Erro no fluxo {fluxo}: {e}")
        
        return resultados
    
    def _processar_resultados(self, resultados, sistema, fluxos, dashboard):
        sucessos = sum(1 for r in resultados.values() if r.get('sucesso'))
        totais = len(resultados)
        
        dashboard.atualizar('status', texto="Processando resultados...")
        dashboard.atualizar('progresso', percentual=100, texto=f"Concluído: {sucessos}/{totais} fluxos")
        
        relatorio = self._gerar_relatorio_consolidado(resultados, sistema, fluxos)
        
        mensagem = f"""
🏢 AUTOMAÇÃO {sistema} CONCLUÍDA!

Fluxos executados: {totais}
Fluxos com sucesso: {sucessos}
Fluxos com falha: {totais - sucessos}

Relatórios gerados:
"""
        
        for fluxo, resultado in resultados.items():
            if resultado.get('sucesso') and 'arquivos' in resultado:
                for arquivo in resultado['arquivos']:
                    mensagem += f"• {os.path.basename(arquivo)}\n"
                    if os.path.exists(arquivo):
                        try:
                            os.startfile(arquivo)
                        except:
                            os.system(f'start "" "{arquivo}"')
        
        mensagem += f"• {os.path.basename(relatorio)}\n"
        if os.path.exists(relatorio):
            try:
                os.startfile(relatorio)
            except:
                os.system(f'start "" "{relatorio}"')
        
        dashboard.atualizar('log', texto="Automação concluída com sucesso!")
        tocar_som_sucesso()
        
        messagebox.showinfo("🎉 Concluído!", mensagem)
    
    def _gerar_relatorio_consolidado(self, resultados, sistema, fluxos):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_consolidado_{sistema}_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"RELATÓRIO CONSOLIDADO - AUTOMAÇÃO {sistema}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Gerado em: {datetime.datetime.now():%d/%m/%Y %H:%M:%S}\n\n")
            
            f.write("RESUMO DA EXECUÇÃO\n")
            f.write("-" * 80 + "\n")
            
            sucessos = sum(1 for r in resultados.values() if r.get('sucesso'))
            f.write(f"Sistema: {sistema}\n")
            f.write(f"Total de fluxos: {len(resultados)}\n")
            f.write(f"Fluxos com sucesso: {sucessos}\n")
            f.write(f"Fluxos com falha: {len(resultados) - sucessos}\n\n")
            
            f.write("DETALHAMENTO POR FLUXO\n")
            f.write("-" * 80 + "\n")
            
            for fluxo, resultado in resultados.items():
                status = "✓ SUCESSO" if resultado.get('sucesso') else "✗ FALHA"
                f.write(f"\n{status} - {fluxo}\n")
                
                if resultado.get('sucesso'):
                    if 'mensagem' in resultado:
                        f.write(f"  Mensagem: {resultado['mensagem']}\n")
                    if 'arquivos' in resultado:
                        f.write(f"  Arquivos gerados: {len(resultado['arquivos'])}\n")
                else:
                    f.write(f"  Erro: {resultado.get('erro', 'Erro desconhecido')}\n")
            
            if sistema == "SGA" and "Entrada de Produtos" in resultados and resultados["Entrada de Produtos"].get('sucesso'):
                entrada_result = resultados["Entrada de Produtos"]
                if 'estatisticas' in entrada_result:
                    stats = entrada_result['estatisticas']
                    f.write("\n" + "-" * 80 + "\n")
                    f.write("ESTATÍSTICAS DETALHADAS - ENTRADA DE PRODUTOS\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"  Notas processadas: {stats.processos_sucesso}/{stats.total_processos}\n")
                    f.write(f"  Itens processados: {stats.itens_sucesso}\n")
                    f.write(f"  Valor total: R$ {stats.valor_total:,.2f}\n")
                    f.write(f"  Tempo total: {stats.tempo_total/60:.1f} minutos\n")
            
            if sistema == "PDV" and "Vendas Simples" in resultados and resultados["Vendas Simples"].get('sucesso'):
                vendas_result = resultados["Vendas Simples"]
                if 'estatisticas' in vendas_result:
                    stats = vendas_result['estatisticas']
                    f.write("\n" + "-" * 80 + "\n")
                    f.write("ESTATÍSTICAS DETALHADAS - VENDAS SIMPLES\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"  Vendas processadas: {stats.processos_sucesso}/{stats.total_processos}\n")
                    f.write(f"  Itens processados: {stats.itens_sucesso}\n")
                    f.write(f"  Valor total: R$ {stats.valor_total:,.2f}\n")
                    f.write(f"  Tempo total: {stats.tempo_total/60:.1f} minutos\n")
        
        self.log.info(f"Relatório consolidado: {filename}")
        return filename


if __name__ == "__main__":
    sistema = SistemaAutomacaoMultiSistema()
    sistema.executar()
