"""
settings_manager.py
Gerenciamento de configurações em arquivo INI para persistência.
"""

import configparser
import os


class SettingsManager:
    def __init__(self, filename='config.ini'):
        self.filename = filename
        self.config = configparser.ConfigParser()
        self._load()
    
    def _load(self):
        """Carrega o arquivo INI ou cria estrutura padrão se não existir."""
        if os.path.exists(self.filename):
            self.config.read(self.filename, encoding='utf-8')
        else:
            self.config['PDV'] = {}
            self.config['SGA'] = {}
    
    def save(self):
        """Salva as configurações no arquivo INI."""
        with open(self.filename, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)
    
    def get(self, section, key, default=''):
        """Obtém valor de uma seção/chave."""
        return self.config.get(section, key, fallback=default)
    
    def set(self, section, key, value):
        """Define valor em uma seção/chave."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = str(value)
    
    # === Métodos específicos PDV ===
    def get_pdv_exe(self):
        return self.get('PDV', 'caminho_exe', '')
    
    def get_pdv_bd(self):
        return self.get('PDV', 'caminho_bd', '')
    
    def get_pdv_usuario(self):
        return self.get('PDV', 'usuario', 'ADMIN')
    
    def get_pdv_senha(self):
        return self.get('PDV', 'senha', '')
    
    def set_pdv_config(self, exe, bd, usuario, senha):
        self.set('PDV', 'caminho_exe', exe)
        self.set('PDV', 'caminho_bd', bd)
        self.set('PDV', 'usuario', usuario)
        self.set('PDV', 'senha', senha)
    
    # === Métodos específicos SGA ===
    def get_sga_bd(self):
        return self.get('SGA', 'caminho_bd', '')
    
    def set_sga_config(self, bd):
        self.set('SGA', 'caminho_bd', bd)
        self.settings.save()