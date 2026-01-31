"""
database.py
Repositórios de dados: Firebird e Mocks para testes.
"""

import fdb
import random
import os
from typing import List
from models import Produto
from config import Config
from logger import log


class RepositorioFirebird:
    """Repositório para conexão com banco Firebird."""
    
    def __init__(self, caminho: str, usuario: str, senha: str, consulta_sql: str, 
                 host: str = None, porta: int = 3050):
        self.caminho = caminho
        self.usuario = usuario
        self.senha = senha
        self.consulta_sql = consulta_sql
        self.host = host
        self.porta = porta
        self.conexao = None
        self.cursor = None
    
    def conectar(self) -> bool:
        try:
            if self.host:
                dsn = f"{self.host}/{self.porta}:{self.caminho}"
                self.conexao = fdb.connect(
                    dsn=dsn,
                    user=self.usuario,
                    password=self.senha
                )
                modo = f"via rede ({self.host}:{self.porta})"
            else:
                self.conexao = fdb.connect(
                    database=self.caminho,
                    user=self.usuario,
                    password=self.senha
                )
                modo = "direto (embedded)"
            
            self.cursor = self.conexao.cursor()
            log.info(f"Conectado ao banco ({modo}): {os.path.basename(self.caminho)}")
            return True
            
        except fdb.Error as e:
            erro_str = str(e)
            if "already in use" in erro_str.lower() or "sendo usado" in erro_str.lower() or "335544344" in erro_str:
                log.error("=" * 60)
                log.error("ERRO: O banco está sendo usado exclusivamente por outro programa!")
                log.error("O sistema tentará abrir o PDV automaticamente se configurado.")
                log.error("=" * 60)
            else:
                log.error(f"Erro ao conectar ao Firebird: {e}")
            return False
    
    def buscar_produtos(self) -> List[Produto]:
        if not self.conexao:
            raise RuntimeError("Conexao nao estabelecida")
        
        self.cursor.execute(self.consulta_sql)
        registros = self.cursor.fetchall()
        
        produtos = []
        for row in registros:
            try:
                produto = Produto(
                    codigo=str(row[0]).strip(),
                    valor_avista=float(row[1]),
                    unidade=str(row[2]).strip().upper()
                )
                if produto.unidade in Config.UNIDADES_VALIDAS:
                    produtos.append(produto)
            except (ValueError, TypeError) as e:
                log.warning(f"Registro ignorado: {row} - {e}")
        
        log.info(f"{len(produtos)} produtos carregados")
        return produtos
    
    def fechar(self):
        if self.cursor:
            self.cursor.close()
        if self.conexao:
            self.conexao.close()
            log.info("Conexao com banco fechada")


class RepositorioMockSGA:
    """Repositório mock para SGA."""
    
    def __init__(self):
        random.seed(42)
        self.produtos_mock = [
            Produto(f"{100000 + i:06d}", 
                   round(random.uniform(5.0, 100.0), 2), 
                   'UN' if i % 3 != 0 else 'KG')
            for i in range(1, 31)
        ]
    
    def conectar(self) -> bool:
        log.info("Modo TESTE ativado para SGA (sem banco real)")
        return True
    
    def buscar_produtos(self) -> List[Produto]:
        return self.produtos_mock.copy()
    
    def fechar(self):
        pass


class RepositorioMockPDV:
    """Repositório mock para PDV."""
    
    def __init__(self):
        random.seed(43)
        self.produtos_mock = [
            Produto(f"{200000 + i:06d}", 
                   round(random.uniform(1.0, 50.0), 2), 
                   'UN' if i % 2 != 0 else 'KG')
            for i in range(1, 26)
        ]
    
    def conectar(self) -> bool:
        log.info("Modo TESTE ativado para PDV (sem banco real)")
        return True
    
    def buscar_produtos(self) -> List[Produto]:
        return self.produtos_mock.copy()
    
    def fechar(self):
        pass