"""
config.py
Configurações centralizadas, enums e constantes do sistema.
"""

from enum import Enum, auto
from dataclasses import dataclass, field


class StatusExecucao(Enum):
    PENDENTE = auto()
    EM_EXECUCAO = auto()
    PAUSADO = auto()
    CONCLUIDO = auto()
    ERRO = auto()
    CANCELADO = auto()


class Config:
    """Configurações centralizadas do sistema."""
    DB_USER = 'SYSDBA'
    DB_PASSWORD = 'masterkey'
    
    # SGA
    MAX_NOTAS_SGA = 50
    MAX_ITENS_POR_NOTA_SGA = 19
    MIN_ITENS_POR_NOTA_SGA = 1
    MIN_PRODUTOS_SELECAO_SGA = 9
    MAX_PRODUTOS_SELECAO_SGA = 30
    
    # PDV
    MAX_VENDAS_PDV = 30
    MAX_ITENS_POR_VENDA_PDV = 15
    MIN_ITENS_POR_VENDA_PDV = 1
    MIN_PRODUTOS_SELECAO_PDV = 5
    MAX_PRODUTOS_SELECAO_PDV = 20
    
    # Delays
    DELAY_DIGITACAO = 0.3
    DELAY_ENTRE_CAMPOS = 0.2
    DELAY_CONFIRMACAO = 1.0
    DELAY_TRANSICAO_TELA = 2.0
    DELAY_PDV_ENTRE_CUPONS = 3.0
    
    # Janelas dos sistemas
    JANELA_SGA = "Entrada de produtos"
    JANELA_PDV = "FormPrincipal"
    JANELA_LOGIN_PDV = "Login"
    
    # Configurações padrão
    FORNECEDOR_PADRAO = "FORNECEDOR PADRAO"
    UNIDADES_VALIDAS = {'UN', 'KG'}
    FORMATOS_LOG = ['TXT', 'JSON', 'CSV']
    
    # Configurações do menu
    SISTEMAS_DISPONIVEIS = {
        "SGA": {
            "nome_completo": "SGA - Sistema de Gestão",
            "fluxos": ["Entrada de Produtos", "Saída de Produtos", "Inventário", "Relatórios"],
            "icone": "💻",
            "cor": "#2E86C1",
            "consultas": {
                "Entrada de Produtos": """
                    SELECT p.CODIGOPRODUTO, p.PR_AVISTA, p.UNIDADE
                    FROM PRODUTOS p
                    WHERE p.ATIVO = 0
                        AND p.UNIDADE IN ('UN', 'KG')
                        AND p.PR_AVISTA > 0
                        AND p.PR_APRAZO > 0
                        AND CHARACTER_LENGTH(p.CODIGOPRODUTO) >= 6
                        AND p.CFNCM != ''
                        AND p.CSTPRO = '000' 
                        AND p.CFOPPRO = '5102'
                    ORDER BY p.CODIGOPRODUTO
                """
            }
        },
        "PDV": {
            "nome_completo": "PDV - Ponto de Venda",
            "fluxos": ["Vendas Simples", "Abertura de Caixa", "Fechamento de Caixa", "Sangria", "Suprimento"],
            "icone": "📦",
            "cor": "#28B463",
            "consultas": {
                "Vendas Simples": """
                    SELECT p.CODIGOPRODUTO, p.PR_AVISTA, p.UNIDADE
                    FROM PRODUTOS p
                    WHERE p.ATIVO = 0
                        AND (p.UNIDADE = 'UN' OR p.UNIDADE = 'KG')
                        AND p.PR_AVISTA > 0
                        AND p.PR_APRAZO > 0
                        AND CHARACTER_LENGTH(p.CODIGOPRODUTO) >= 6
                        AND p.CFNCM != ''
                        AND (p.CSTPRO='000' and p.CFOPPRO='5102')
                    ORDER BY p.CODIGOPRODUTO
                """
            }
        }
    }