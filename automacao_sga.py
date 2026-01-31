"""
automacao_sga.py
Automação completa do SGA (Entrada de Produtos e outros fluxos).
"""

import time
import random
import pyautogui
from pywinauto import Application
from pywinauto.findwindows import WindowNotFoundError, ElementNotFoundError
from typing import List, Dict
from config import Config
from models import Produto, ItemNota, ResumoNota, EstatisticasExecucao
from database import RepositorioFirebird, RepositorioMockSGA
from logger import log
from ui_dashboard import DashboardExecucao
from reports import GeradorRelatorios


class AutomacaoEntradaProdutos:
    def __init__(self, app, janela, dashboard: DashboardExecucao = None):
        self.app = app
        self.janela = janela
        self.dashboard = dashboard
        self.tentativas_max = 3
    
    def _log_acao(self, msg: str):
        log.info(msg)
        if self.dashboard:
            self.dashboard.atualizar('log', texto=msg)
    
    def preencher_cabecalho(self) -> bool:
        self._log_acao("Preenchendo cabecalho...")
        
        try:
            pyautogui.press('space')
            time.sleep(0.3)
            
            for _ in range(5):
                pyautogui.press('enter')
                time.sleep(Config.DELAY_ENTRE_CAMPOS)
            
            pyautogui.write('UNICA')
            time.sleep(Config.DELAY_DIGITACAO)
            
            for _ in range(3):
                pyautogui.press('enter')
                time.sleep(Config.DELAY_ENTRE_CAMPOS)
            
            pyautogui.write(Config.FORNECEDOR_PADRAO)
            time.sleep(Config.DELAY_DIGITACAO)
            pyautogui.press('enter')
            time.sleep(0.5)
            
            return self._salvar_cabecalho()
            
        except Exception as e:
            log.error(f"Erro no cabecalho: {e}")
            return False
    
    def _salvar_cabecalho(self) -> bool:
        try:
            self.janela.Btn_Salvar.click()
            self._log_acao("Cabecalho salvo")
            return True
        except:
            pyautogui.press('f10')
            time.sleep(1)
            self._log_acao("Cabecalho salvo (F10)")
            return True
    
    def preencher_item(self, item: ItemNota) -> bool:
        produto = item.produto
        
        try:
            pyautogui.write(produto.codigo)
            time.sleep(Config.DELAY_DIGITACAO)
            pyautogui.press('enter')
            time.sleep(0.5)
            
            qtd_str = produto.formatar_quantidade(item.quantidade)
            pyautogui.write(qtd_str)
            time.sleep(Config.DELAY_DIGITACAO)
            
            for _ in range(3):
                pyautogui.press('enter')
                time.sleep(Config.DELAY_ENTRE_CAMPOS)
            
            valor_str = f"{item.valor_unitario:.2f}".replace('.', ',')
            pyautogui.write(valor_str)
            time.sleep(Config.DELAY_DIGITACAO)
            
            for _ in range(2):
                pyautogui.press('enter')
                time.sleep(1.5)
            
            for _ in range(2):
                pyautogui.press('enter')
                time.sleep(1)
            
            time.sleep(1)
            pyautogui.press('enter')
            
            item.finalizar("OK")
            return True
            
        except Exception as e:
            log.error(f"Erro no item {produto.codigo}: {e}")
            item.finalizar("FALHA")
            return False
    
    def concluir_nota(self) -> bool:
        self._log_acao("Concluindo nota...")
        
        try:
            try:
                self.janela.Btn_Concluir.click()
            except:
                botoes = self.janela.descendants(control_type="Button")
                for btn in botoes:
                    if "concluir" in btn.window_text().lower():
                        btn.click()
                        break
                else:
                    pyautogui.press('f9')
            
            time.sleep(Config.DELAY_CONFIRMACAO)
            pyautogui.press('s')
            time.sleep(Config.DELAY_TRANSICAO_TELA)
            
            self._log_acao("Nota concluida")
            return True
            
        except Exception as e:
            log.error(f"Erro ao concluir: {e}")
            return False


class ProcessadorNotasFiscais:
    def __init__(self, db, automacao, total_notas: int, dashboard: DashboardExecucao = None):
        self.db = db
        self.automacao = automacao
        self.total_notas = total_notas
        self.dashboard = dashboard
        self.resumos = []
        self.stats = EstatisticasExecucao(total_processos=total_notas)
    
    def executar(self):
        inicio = time.time()
        
        try:
            if not self.db.conectar():
                raise RuntimeError("Falha na conexao")
            
            produtos = self.db.buscar_produtos()
            if not produtos:
                raise ValueError("Sem produtos")
            
            selecionados = self._selecionar_produtos(produtos)
            
            for num in range(1, self.total_notas + 1):
                if self.dashboard:
                    pct = (num - 1) / self.total_notas * 100
                    self.dashboard.atualizar('progresso', percentual=pct, 
                                           texto=f"Nota {num} de {self.total_notas}")
                    self.dashboard.atualizar('status', texto=f"Processando nota {num}...")
                
                resumo = self._processar_nota(num, selecionados)
                self.resumos.append(resumo)
                
                self.stats.total_itens += len(resumo.itens)
                self.stats.itens_sucesso += resumo.itens_sucesso
                self.stats.itens_falha += resumo.itens_falha
                self.stats.valor_total += resumo.valor_total
                self.stats.produtos_un += resumo.total_un
                self.stats.produtos_kg += resumo.total_kg
                
                if resumo.status == 'OK':
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
                
                if num < self.total_notas:
                    time.sleep(2)
            
            self.stats.finalizar()
            return self.resumos, self.stats
            
        finally:
            self.db.fechar()
    
    def _selecionar_produtos(self, produtos: List[Produto]) -> List[Produto]:
        n = min(random.randint(Config.MIN_PRODUTOS_SELECAO_SGA, 
                              min(Config.MAX_PRODUTOS_SELECAO_SGA, len(produtos))), 
                len(produtos))
        selecionados = random.sample(produtos, n)
        random.shuffle(selecionados)
        log.info(f"{len(selecionados)} produtos selecionados para uso")
        return selecionados
    
    def _processar_nota(self, numero: int, produtos: List[Produto]) -> ResumoNota:
        log.info(f"\n{'='*50}")
        log.info(f"NOTA {numero}/{self.total_notas}")
        log.info(f"{'='*50}")
        
        resumo = ResumoNota(numero=numero)
        
        if not self.automacao.preencher_cabecalho():
            resumo.finalizar('ERRO', 'Falha no cabecalho')
            return resumo
        
        time.sleep(Config.DELAY_TRANSICAO_TELA)
        
        qtd_itens = random.randint(Config.MIN_ITENS_POR_NOTA_SGA, Config.MAX_ITENS_POR_NOTA_SGA)
        itens = []
        
        for i in range(qtd_itens):
            prod = random.choice(produtos)
            qtd = prod.gerar_quantidade()
            valor_unit = prod.calcular_valor_unitario()
            
            item = ItemNota(produto=prod, quantidade=qtd, valor_unitario=valor_unit)
            
            log.info(f"  Item {i+1}/{qtd_itens}: {prod.codigo} | {qtd} {prod.unidade} | R$ {valor_unit:.2f}")
            
            if self.automacao.preencher_item(item):
                itens.append(item)
            else:
                log.error(f"  Falha no item {i+1}")
                itens.append(item)
        
        resumo.itens = itens
        
        if not self.automacao.concluir_nota():
            log.warning(f"Possivel falha ao concluir nota {numero}")
        
        resumo.finalizar('OK')
        log.info(f"Nota {numero} finalizada: {len(itens)} itens, R$ {resumo.valor_total:.2f}")
        
        return resumo


class AutomacaoSGA:
    """Classe para automações do sistema SGA."""
    
    def __init__(self, dashboard: DashboardExecucao = None):
        self.dashboard = dashboard
    
    def executar_fluxo_entrada_produtos(self, config: Dict):
        log.info("=" * 60)
        log.info("EXECUTANDO FLUXO: ENTRADA DE PRODUTOS - SGA")
        log.info("=" * 60)
        
        try:
            app, janela = self._conectar_aplicacao(Config.JANELA_SGA)
            automacao = AutomacaoEntradaProdutos(app, janela, self.dashboard)
            
            if config.get('usar_mock_sga', False):
                db = RepositorioMockSGA()
            else:
                db = RepositorioFirebird(
                    caminho=config.get('caminho_bd_sga', ''),
                    usuario=Config.DB_USER,
                    senha=Config.DB_PASSWORD,
                    consulta_sql=Config.SISTEMAS_DISPONIVEIS['SGA']['consultas']['Entrada de Produtos'],
                    host='localhost',
                    porta=3050
                )
            
            processador = ProcessadorNotasFiscais(
                db=db,
                automacao=automacao,
                total_notas=config.get('quantidade_notas_sga', 1),
                dashboard=self.dashboard
            )
            
            resumos, stats = processador.executar()
            
            if self.dashboard:
                self.dashboard.atualizar('status', texto="Gerando relatórios...")
            
            arquivos_gerados = []
            arquivos_gerados.append(GeradorRelatorios.gerar_relatorio_texto(resumos, stats))
            arquivos_gerados.append(log.exportar_csv(resumos))
            
            return {
                'sucesso': True,
                'resumos': resumos,
                'estatisticas': stats,
                'arquivos': arquivos_gerados
            }
            
        except Exception as e:
            log.error(f"Erro no fluxo de entrada de produtos: {e}")
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def _conectar_aplicacao(self, titulo_janela: str):
        log.info(f"Conectando a aplicacao: {titulo_janela}")
        time.sleep(3)
        
        tentativas = [
            lambda: Application(backend="uia").connect(title=titulo_janela),
            lambda: Application(backend="uia").connect(title_re=f".*{titulo_janela}.*"),
            lambda: Application(backend="win32").connect(title=titulo_janela),
            lambda: Application(backend="win32").connect(title_re=f".*{titulo_janela}.*"),
        ]
        
        app = None
        janela = None
        metodo_encontrado = None
        
        for i, tentativa in enumerate(tentativas):
            try:
                app = tentativa()
                
                try:
                    if i == 0 or i == 2:
                        janela = app.window(title=titulo_janela)
                    else:
                        janela = app.window(title_re=f".*{titulo_janela}.*")
                except:
                    janelas = app.windows()
                    if janelas:
                        janela = janelas[0]
                
                if janela:
                    try:
                        janela.set_focus()
                    except:
                        pass
                    metodo_encontrado = i
                    break
                    
            except (WindowNotFoundError, ElementNotFoundError, Exception) as e:
                log.debug(f"Tentativa {i} falhou: {e}")
                continue
        
        if not app or not janela:
            raise RuntimeError(
                f"Janela '{titulo_janela}' não encontrada.\n"
                f"Certifique-se de que a tela está aberta e visível."
            )
        
        log.info(f"Conectado com sucesso (método {metodo_encontrado + 1})")
        time.sleep(1)
        return app, janela