"""Funções auxiliares (ex.: feedback sonoro)."""

import winsound


def formatar_numero_br(valor, casas: int = 2, usar_milhar: bool = True) -> str:
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    
    if usar_milhar:
        texto = f"{valor:,.{casas}f}"
        return texto.replace(",", "_").replace(".", ",").replace("_", ".")
    
    return f"{valor:.{casas}f}".replace(".", ",")


def formatar_moeda_br(valor) -> str:
    return formatar_numero_br(valor, casas=2, usar_milhar=True)


def tocar_som_sucesso():
    try:
        winsound.Beep(800, 200)
        winsound.Beep(1000, 200)
        winsound.Beep(1200, 400)
    except:
        pass


def tocar_som_erro():
    try:
        winsound.Beep(400, 500)
        winsound.Beep(300, 500)
    except:
        pass
