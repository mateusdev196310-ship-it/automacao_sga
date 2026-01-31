"""
automacao_pdv.py
Automação completa do PDV (Vendas Simples, abertura automática, etc.).
"""

import time
import random
import subprocess
import os
import datetime
import pyautogui
from typing import List, Dict
from config import Config
from models import Produto, ItemVenda, VendaPDV, EstatisticasExecucao
from database import RepositorioFirebird, RepositorioMockPDV
from logger import log
from ui_dashboard import DashboardExecucao


class GerenciadorPDV:
    """Gerencia a abertura e login automático do PDV."""
    
    @staticmethod
    def abrir_pdv(caminho_exe: str, caminho_bd: str, usuario: str, senha: str) -> bool:
        try:
            if not os.path.exists(caminho_exe):
                log.error(f"Executável não encontrado: {caminho_exe}")
                return False
            
            log.info(f"Abrindo PDV: {caminho_exe}")
            subprocess.Popen(caminho_exe, shell=True)
            
            log.info("Aguardando PDV abrir (10 segundos)...")
            time.sleep(10)
            
            janela_encontrada = False
            for tentativa in range(5):
                try:
                    possiveis_titulos = ["Login", "Acesso", "Entrar", "PDV", "Sistema", "SGAPDV", "FormLogin"]
                    
                    for titulo in possiveis_titulos:
                        try:
                            janelas = pyautogui.getWindowsWithTitle(titulo)
                            if janelas:
                                log.info(f"Janela encontrada: {titulo}")
                                janela = janelas[0]
                                janela.activate()
                                janela_encontrada = True
                                break
                        except:
                            continue
                    
                    if janela_encontrada:
                        break
                        
                except Exception as e:
                    log.debug(f"Tentativa {tentativa + 1} de encontrar janela: {e}")
                
                time.sleep(2)
            
            if not janela_encontrada:
                log.warning("Janela específica não encontrada, continuando com foco na tela atual...")
                try:
                    pyautogui.keyDown('alt')
                    pyautogui.keyDown('tab')
                    pyautogui.keyUp('tab')
                    pyautogui.keyUp('alt')
                    time.sleep(0.5)
                except:
                    pass
            
            log.info("Realizando login automático...")
            time.sleep(3)
            
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('a')
            pyautogui.keyUp('a')
            pyautogui.keyUp('ctrl')
            time.sleep(0.2)
            
            pyautogui.write(usuario)
            log.info(f"Usuário digitado: {usuario}")
            time.sleep(0.5)
            
            pyautogui.press('tab')
            time.sleep(0.3)
            
            pyautogui.write(senha)
            log.info("Senha digitada")
            time.sleep(0.5)
            
            pyautogui.press('enter')
            log.info("Login confirmado (Enter)")
            
            log.info("Aguardando sistema carregar (5 segundos)...")
            time.sleep(5)
            
            log.info("PDV aberto e logado com sucesso!")
            return True
            
        except Exception as e:
            log.error(f"Erro ao abrir PDV: {e}")
            return False


class ProcessadorVendasPDV:
    """Processador de vendas para o PDV - Usa apenas pyautogui."""
    
    def __init__(self, db, total_vendas: int, dashboard: DashboardExecucao = None):
        self.db = db
        self.total_vendas = total_vendas
        self.dashboard = dashboard
        self.vendas = []
        self.stats = EstatisticasExecucao(total_processos=total_vendas)
    
    def executar(self):
        inicio = time.time()
        
        try:
            if not self.db.conectar():
                raise RuntimeError("Falha na conexao")
            
            produtos = self.db.buscar_produtos()
            if not produtos:
                raise ValueError("Sem produtos")
            
            selecionados = self._selecionar_produtos(produtos)
            
            for num in range(1, self.total_vendas + 1):
                if self.dashboard:
                    pct = (num - 1) / self.total_vendas * 100
                    self.dashboard.atualizar('progresso', percentual=pct, 
                                           texto=f"Venda {num} de {self.total_vendas}")
                    self.dashboard.atualizar('status', texto=f"Processando venda {num}...")
                
                venda = self._processar_venda(num, selecionados)
                self.vendas.append(venda)
                
                self.stats.total_itens += len(venda.itens)
                self.stats.itens_sucesso += venda.itens_sucesso
                self.stats.itens_falha += venda.itens_falha
                self.stats.valor_total += venda.valor_total
                
                if venda.status == 'OK':
                    self.stats.processos_sucesso += 1
                else:
                    self.stats.processos_falha += 1
                
                if self.dashboard:
                    tempo_decorrido = int(time.time() - inicio)
                    mins, secs = divmod(tempo_decorrido, 60)
                    self.dashboard.atualizar('stats', 
                                           itens=self.stats.total_itens,
                                           valor=self.stats.valor_total,
                                           tempo=f"{mins:02d}:{secs:02d}")
                
                if num < self.total_vendas:
                    log.info(f"Aguardando {Config.DELAY_PDV_ENTRE_CUPONS}s antes da próxima venda...")
                    time.sleep(Config.DELAY_PDV_ENTRE_CUPONS)
            
            self.stats.finalizar()
            return self.vendas, self.stats
            
        finally:
            self.db.fechar()
    
    def _selecionar_produtos(self, produtos: List[Produto]) -> List[Produto]:
        n = min(random.randint(Config.MIN_PRODUTOS_SELECAO_PDV, 
                              min(Config.MAX_PRODUTOS_SELECAO_PDV, len(produtos))), 
                len(produtos))
        selecionados = random.sample(produtos, n)
        random.shuffle(selecionados)
        log.info(f"{len(selecionados)} produtos selecionados para vendas")
        return selecionados
    
    def _processar_venda(self, numero: int, produtos: List[Produto]) -> VendaPDV:
        log.info(f"\n{'='*50}")
        log.info(f"VENDA {numero}/{self.total_vendas}")
        log.info(f"{'='*50}")
        
        venda = VendaPDV(numero=numero)
        
        try:
            log.info("  Abrindo cupom (F10)...")
            pyautogui.press('f10')
            time.sleep(Config.DELAY_TRANSICAO_TELA)
            
            qtd_itens = random.randint(Config.MIN_ITENS_POR_VENDA_PDV, Config.MAX_ITENS_POR_VENDA_PDV)
            itens = []
            
            for i in range(qtd_itens):
                try:
                    prod = random.choice(produtos)
                    qtd = prod.gerar_quantidade()
                    valor_unit = prod.calcular_valor_unitario()
                    
                    item = ItemVenda(produto=prod, quantidade=qtd, valor_unitario=valor_unit)
                    
                    log.info(f"  Item {i+1}/{qtd_itens}: {prod.codigo} | {qtd} {prod.unidade} | R$ {valor_unit:.2f}")
                    
                    if self._adicionar_produto_ao_cupom(item):
                        itens.append(item)
                    else:
                        log.warning(f"  Item {i+1} adicionado com ressalvas")
                        itens.append(item)
                        
                except Exception as e:
                    log.error(f"  Erro ao processar item {i+1}: {e}")
            
            venda.itens = itens
            
            log.info("  Fechando cupom...")
            if not self._fechar_cupom():
                log.warning(f"Atenção ao fechar venda {numero}, mas continuando...")
            
            venda.finalizar('OK')
            log.info(f"Venda {numero} finalizada: {len(itens)} itens, R$ {venda.valor_total:.2f}")
            
        except Exception as e:
            log.error(f"Erro na venda {numero}: {e}")
            venda.finalizar('ERRO', str(e))
        
        return venda
    
    def _adicionar_produto_ao_cupom(self, item: ItemVenda) -> bool:
        produto = item.produto
        
        try:
            if produto.unidade.upper() == 'KG':
                qtd_str = f"{item.quantidade:.3f}".replace('.', ',')
            else:
                qtd_str = str(int(item.quantidade))
            
            pyautogui.write(qtd_str)
            time.sleep(Config.DELAY_DIGITACAO)
            
            pyautogui.write('*')
            time.sleep(0.1)
            
            pyautogui.write(produto.codigo)
            time.sleep(Config.DELAY_DIGITACAO)
            
            pyautogui.press('enter')
            time.sleep(1.0)
            
            item.finalizar("OK")
            return True
            
        except Exception as e:
            log.error(f"Erro ao adicionar produto {produto.codigo}: {e}")
            item.finalizar("FALHA")
            return False
    
    def _fechar_cupom(self) -> bool:
        try:
            pyautogui.press('f6')
            time.sleep(1.5)
            
            for _ in range(3):
                pyautogui.press('enter')
                time.sleep(0.5)
            
            log.info("Cupom fechado com sucesso")
            return True
            
        except Exception as e:
            log.error(f"Erro ao fechar cupom: {e}")
            return False


class AutomacaoPDV:
    """Classe para automações do sistema PDV."""
    
    def __init__(self, dashboard: DashboardExecucao = None):
        self.dashboard = dashboard
    
    def executar_fluxo_vendas_simples(self, config: Dict):
        log.info("=" * 60)
        log.info("EXECUTANDO FLUXO: VENDAS SIMPLES - PDV")
        log.info("=" * 60)
        
        caminho_exe = config.get('caminho_exe_pdv', '')
        if caminho_exe and os.path.exists(caminho_exe) and not config.get('usar_mock_pdv', False):
            log.info("Modo automático: Abrindo PDV...")
            if self.dashboard:
                self.dashboard.atualizar('status', texto="Abrindo PDV automaticamente...")
            
            sucesso_abertura = GerenciadorPDV.abrir_pdv(
                caminho_exe=caminho_exe,
                caminho_bd=config.get('caminho_bd_pdv', ''),
                usuario=config.get('usuario_pdv', 'ADMIN'),
                senha=config.get('senha_pdv', '')
            )
            
            if not sucesso_abertura:
                log.warning("Falha ao abrir PDV automaticamente, tentando continuar...")
        else:
            log.info("Modo manual: PDV deve estar aberto")
            log.info("Preparando para iniciar em 7 segundos...")
            if self.dashboard:
                self.dashboard.atualizar('status', texto="Preparando... 7 segundos")
            
            for i in range(7, 0, -1):
                log.info(f"Iniciando em {i}...")
                if self.dashboard:
                    self.dashboard.atualizar('log', texto=f"Aguarde... {i} segundos")
                time.sleep(1)
        
        try:
            log.info("Iniciando automação do PDV agora!")
            if self.dashboard:
                self.dashboard.atualizar('status', texto="Executando vendas...")
            
            if config.get('usar_mock_pdv', False):
                db = RepositorioMockPDV()
            else:
                db = RepositorioFirebird(
                    caminho=config.get('caminho_bd_pdv', ''),
                    usuario=Config.DB_USER,
                    senha=Config.DB_PASSWORD,
                    consulta_sql=Config.SISTEMAS_DISPONIVEIS['PDV']['consultas']['Vendas Simples'],
                    host='localhost',
                    porta=3050
                )
            
            processador = ProcessadorVendasPDV(
                db=db,
                total_vendas=config.get('quantidade_vendas_pdv', 1),
                dashboard=self.dashboard
            )
            
            vendas, stats = processador.executar()
            
            if self.dashboard:
                self.dashboard.atualizar('status', texto="Gerando relatórios...")
            
            arquivos_gerados = []
            arquivos_gerados.append(self._gerar_relatorio_vendas_texto(vendas, stats))
            arquivos_gerados.append(log.exportar_csv_vendas(vendas))
            
            return {
                'sucesso': True,
                'vendas': vendas,
                'estatisticas': stats,
                'arquivos': arquivos_gerados
            }
            
        except Exception as e:
            log.error(f"Erro no fluxo de vendas simples: {e}")
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def _gerar_relatorio_vendas_texto(self, vendas: List[VendaPDV], stats: EstatisticasExecucao, filename: str = None) -> str:
        if not filename:
            filename = f"relatorio_vendas_pdv_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt"
        
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RELATÓRIO DE VENDAS - PDV\n")
            f.write("=" * 80 + "\n")
            f.write(f"Gerado em: {datetime.datetime.now():%d/%m/%Y %H:%M:%S}\n\n")
            
            f.write("ESTATÍSTICAS GERAIS\n")
            f.write("-" * 80 + "\n")
            f.write(f"  Total de vendas:     {stats.total_processos}\n")
            f.write(f"  Vendas com sucesso:  {stats.processos_sucesso}\n")
            f.write(f"  Vendas com falha:    {stats.processos_falha}\n")
            f.write(f"  Total de itens:      {stats.total_itens}\n")
            f.write(f"  Valor total:         R$ {stats.valor_total:,.2f}\n")
            f.write(f"  Tempo total:         {stats.tempo_total:.1f}s\n\n")
            
            for venda in vendas:
                status = "OK" if venda.status == "OK" else "FALHA"
                f.write(f"\n[{status}] VENDA {venda.numero}\n")
                f.write("-" * 80 + "\n")
                f.write(f"  Itens: {len(venda.itens)} (OK: {venda.itens_sucesso}, Falha: {venda.itens_falha})\n")
                f.write(f"  Valor: R$ {venda.valor_total:,.2f}\n")
                f.write(f"  Tempo: {venda.tempo_total:.1f}s\n")
        
        log.info(f"TXT Vendas: {filename}")
        return filename