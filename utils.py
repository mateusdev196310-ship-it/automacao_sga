"""
utils.py
Funções auxiliares e utilitárias (sons, etc.).
"""

import winsound


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