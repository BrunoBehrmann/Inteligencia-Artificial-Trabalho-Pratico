# estados/__init__.py

from .busca import executar as executar_busca
from .aproximacao import executar as executar_aproximacao
from .coleta import executar as executar_coleta
from .navegacao_caixa import executar as executar_navegacao_caixa
from .deposito import executar as executar_deposito

__all__ = [
    'executar_busca',
    'executar_aproximacao',
    'executar_coleta',
    'executar_navegacao_caixa',
    'executar_deposito'
]
