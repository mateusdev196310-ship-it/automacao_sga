"""
models.py
Todos os modelos de dados (dataclasses) do sistema.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import datetime
import random


@dataclass
class Produto:
    codigo: str
    valor_avista: float
    unidade: str
    
    def calcular_valor_unitario(self) -> float:
        return max(0.01, self.valor_avista - 0.01)
    
    def gerar_quantidade(self) -> float:
        if self.unidade.upper() == 'KG':
            return round(random.uniform(0.5, 20.0), 3)
        return float(random.randint(1, 20))
    
    def formatar_quantidade(self, qtd: float) -> str:
        if self.unidade.upper() == 'KG':
            return f"{qtd:.3f}".replace('.', ',')
        return str(int(qtd))


@dataclass
class ItemVenda:
    produto: Produto
    quantidade: float
    valor_unitario: float
    timestamp_inicio: datetime.datetime = field(default_factory=datetime.datetime.now)
    timestamp_fim: Optional[datetime.datetime] = None
    status: str = "PENDENTE"
    
    @property
    def valor_total(self) -> float:
        return self.valor_unitario * self.quantidade
    
    @property
    def tempo_processamento(self) -> float:
        if self.timestamp_fim:
            return (self.timestamp_fim - self.timestamp_inicio).total_seconds()
        return 0.0
    
    def finalizar(self, status: str = "OK"):
        self.timestamp_fim = datetime.datetime.now()
        self.status = status


@dataclass
class VendaPDV:
    numero: int
    itens: List[ItemVenda] = field(default_factory=list)
    timestamp_inicio: datetime.datetime = field(default_factory=datetime.datetime.now)
    timestamp_fim: Optional[datetime.datetime] = None
    status: str = "PENDENTE"
    erro: Optional[str] = None
    
    @property
    def quantidade_total(self) -> float:
        return sum(item.quantidade for item in self.itens)
    
    @property
    def valor_total(self) -> float:
        return sum(item.valor_total for item in self.itens)
    
    @property
    def tempo_total(self) -> float:
        if self.timestamp_fim:
            return (self.timestamp_fim - self.timestamp_inicio).total_seconds()
        return (datetime.datetime.now() - self.timestamp_inicio).total_seconds()
    
    @property
    def itens_sucesso(self) -> int:
        return sum(1 for item in self.itens if item.status == "OK")
    
    @property
    def itens_falha(self) -> int:
        return sum(1 for item in self.itens if item.status == "FALHA")
    
    def finalizar(self, status: str = "OK", erro: str = None):
        self.timestamp_fim = datetime.datetime.now()
        self.status = status
        self.erro = erro


@dataclass
class ItemNota:
    produto: Produto
    quantidade: float
    valor_unitario: float
    timestamp_inicio: datetime.datetime = field(default_factory=datetime.datetime.now)
    timestamp_fim: Optional[datetime.datetime] = None
    status: str = "PENDENTE"
    
    @property
    def valor_total(self) -> float:
        return self.valor_unitario * self.quantidade
    
    @property
    def tempo_processamento(self) -> float:
        if self.timestamp_fim:
            return (self.timestamp_fim - self.timestamp_inicio).total_seconds()
        return 0.0
    
    def finalizar(self, status: str = "OK"):
        self.timestamp_fim = datetime.datetime.now()
        self.status = status


@dataclass
class ResumoNota:
    numero: int
    itens: List[ItemNota] = field(default_factory=list)
    timestamp_inicio: datetime.datetime = field(default_factory=datetime.datetime.now)
    timestamp_fim: Optional[datetime.datetime] = None
    status: str = "PENDENTE"
    erro: Optional[str] = None
    total_un: int = field(init=False)
    total_kg: int = field(init=False)
    
    def __post_init__(self):
        self.total_un = sum(1 for item in self.itens if item.produto.unidade.upper() == 'UN')
        self.total_kg = sum(1 for item in self.itens if item.produto.unidade.upper() == 'KG')
    
    @property
    def quantidade_total(self) -> float:
        return sum(item.quantidade for item in self.itens)
    
    @property
    def valor_total(self) -> float:
        return sum(item.valor_total for item in self.itens)
    
    @property
    def tempo_total(self) -> float:
        if self.timestamp_fim:
            return (self.timestamp_fim - self.timestamp_inicio).total_seconds()
        return (datetime.datetime.now() - self.timestamp_inicio).total_seconds()
    
    @property
    def itens_sucesso(self) -> int:
        return sum(1 for item in self.itens if item.status == "OK")
    
    @property
    def itens_falha(self) -> int:
        return sum(1 for item in self.itens if item.status == "FALHA")
    
    def finalizar(self, status: str = "OK", erro: str = None):
        self.timestamp_fim = datetime.datetime.now()
        self.status = status
        self.erro = erro


@dataclass
class EstatisticasExecucao:
    total_processos: int = 0
    processos_sucesso: int = 0
    processos_falha: int = 0
    total_itens: int = 0
    itens_sucesso: int = 0
    itens_falha: int = 0
    tempo_total: float = 0.0
    tempo_medio_processo: float = 0.0
    tempo_medio_item: float = 0.0
    valor_total: float = 0.0
    produtos_un: int = 0
    produtos_kg: int = 0
    inicio_execucao: datetime.datetime = field(default_factory=datetime.datetime.now)
    fim_execucao: Optional[datetime.datetime] = None
    
    def calcular_medias(self):
        if self.processos_sucesso > 0:
            self.tempo_medio_processo = self.tempo_total / self.processos_sucesso
        if self.itens_sucesso > 0:
            self.tempo_medio_item = self.tempo_total / self.itens_sucesso
    
    def finalizar(self):
        self.fim_execucao = datetime.datetime.now()
        self.tempo_total = (self.fim_execucao - self.inicio_execucao).total_seconds()
        self.calcular_medias()