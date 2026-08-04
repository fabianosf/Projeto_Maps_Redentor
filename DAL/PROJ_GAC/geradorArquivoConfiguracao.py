# ----------------------
# Deus seja louvado!
# ----------------------

import json
import os
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DAL_ROOT = os.path.dirname(_MODULE_DIR)
_DEFAULT_CONF_DIR = os.path.join(_DAL_ROOT, "arquivos_crip")
_CHAVE_DIR = os.path.join(_DEFAULT_CONF_DIR, "chave")
_ARQ_DIR = os.path.join(_DEFAULT_CONF_DIR, "arq")


class ClGAC:
    """
    Gerenciador de arquivos de configuração criptografados (Fernet + arquivos_crip/chave/chave.key).

    Os arquivos .dat ficam em arquivos_crip/arq/. Compatível com DAL.py e CONFIGURACAO.py.
    """

    def __init__(self, nome_arquivo: str = "config.dat", pasta_conf: Optional[str] = None):
        self.arq = self._normalizar_nome_arquivo(nome_arquivo)
        self.path = os.path.abspath(pasta_conf) if pasta_conf else _DEFAULT_CONF_DIR
        self.path_chave = os.path.join(self.path, "chave")
        self.path_arq = os.path.join(self.path, "arq")
        self.key_path = os.path.join(self.path_chave, "chave.key")
        self.dados: Dict[str, Any] = {}

        self._setup()
        self.chave = self._gerarChave()
        self.cipher = Fernet(self.chave)

    @staticmethod
    def _normalizar_nome_arquivo(nome: str) -> str:
        nome = (nome or "").strip()
        if not nome:
            return ""
        if not nome.lower().endswith(".dat"):
            nome += ".dat"
        return nome

    def _setup(self):
        try:
            for pasta in (self.path, self.path_chave, self.path_arq):
                if not os.path.exists(pasta):
                    os.makedirs(pasta)
        except OSError as e:
            raise RuntimeError(
                f"ERRO: Falha ao criar diretório de configuração. Erro: {e}"
            ) from e

    def _gerarChave(self):
        try:
            if os.path.exists(self.key_path):
                with open(self.key_path, "rb") as key_file:
                    return key_file.read()
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as key_file:
                key_file.write(key)
            return key
        except IOError as e:
            raise RuntimeError(
                f"ERRO: Falha de I/O ao acessar o arquivo de chave '{self.key_path}'. Erro: {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"ERRO: Ocorreu um erro inesperado ao gerar/carregar a chave. Erro: {e}"
            ) from e

    def _crip(self, data: str, action: str = "decrypt") -> Optional[str]:
        if not data:
            return None

        try:
            if action == "encrypt":
                encrypted_bytes = self.cipher.encrypt(data.encode("utf-8"))
                return encrypted_bytes.decode("utf-8")
            if action == "decrypt":
                decrypted_bytes = self.cipher.decrypt(data.encode("utf-8"))
                return decrypted_bytes.decode("utf-8")
            print(f"ERRO: Ação '{action}' desconhecida. Use 'encrypt' ou 'decrypt'.")
            return None
        except Fernet.InvalidToken:
            print(
                "ERRO: Token de criptografia inválido. "
                "O arquivo pode estar corrompido ou a chave mudou."
            )
            return None
        except Exception as e:
            print(f"ERRO: Falha no processo de criptografia/descriptografia. Erro: {e}")
            return None

    def definir_dados(self, dados: Dict[str, Any]) -> None:
        """Define o dicionário de chaves/valores a ser gravado no arquivo."""
        self.dados = {str(k).strip(): v for k, v in dados.items() if str(k).strip()}

    def gerarArquivoConfiguracao(self) -> bool:
        if not self.arq:
            print("ERRO: O nome do arquivo não foi definido.")
            return False
        if not self.dados:
            print("ERRO: Nenhuma chave/valor foi informada.")
            return False

        try:
            config_path = os.path.join(self.path_arq, self.arq)
            json_data = json.dumps(self.dados, indent=4, ensure_ascii=False)
            encrypted_data = self._crip(json_data, action="encrypt")

            if encrypted_data is None:
                print("ERRO: Falha ao criptografar os dados. O arquivo não foi gerado.")
                return False

            with open(config_path, "w", encoding="utf-8") as file:
                file.write(encrypted_data)

            return True
        except Exception as e:
            print(f"ERRO: Falha ao gerar o arquivo de configuração. Erro: {e}")
            return False

    def lerArquivoConfiguracao(self) -> Optional[Dict[str, Any]]:
        if not self.arq:
            print("ERRO: O nome do arquivo não foi definido.")
            return None

        config_path = os.path.join(self.path_arq, self.arq)
        if not os.path.exists(config_path):
            print(
                f"ERRO: O arquivo '{self.arq}' não foi encontrado em '{self.path_arq}'."
            )
            return None

        try:
            with open(config_path, "r", encoding="utf-8") as file:
                encrypted_data = file.read()

            if not encrypted_data.strip():
                print("AVISO: O arquivo de configuração está vazio.")
                return None

            decrypted_json_data = self._crip(encrypted_data, action="decrypt")
            if decrypted_json_data is None:
                return None

            return json.loads(decrypted_json_data)
        except json.JSONDecodeError as json_err:
            print(f"ERRO: Falha ao decodificar JSON do arquivo '{self.arq}'. Erro: {json_err}")
            return None
        except Exception as e:
            print(f"ERRO: Exceção ao ler arquivo '{self.arq}'. Erro: {e}")
            return None

    @staticmethod
    def _formatar_valor(valor: Any) -> str:
        if valor is None:
            return ""
        if isinstance(valor, (dict, list)):
            return json.dumps(valor, ensure_ascii=False)
        return str(valor)

    def _exibir_tabela(self, config_dict: Dict[str, Any]) -> None:
        if not config_dict:
            print("AVISO: O arquivo não contém chaves.")
            return

        linhas = [(str(chave), self._formatar_valor(valor)) for chave, valor in config_dict.items()]
        largura_chave = max(len("Chave"), *(len(c) for c, _ in linhas))
        largura_valor = max(len("Valor"), *(len(v) for _, v in linhas))

        separador = f"+-{'-' * largura_chave}-+-{'-' * largura_valor}-+"
        print(separador)
        print(f"| {'Chave':<{largura_chave}} | {'Valor':<{largura_valor}} |")
        print(separador)
        for chave, valor in linhas:
            print(f"| {chave:<{largura_chave}} | {valor:<{largura_valor}} |")
        print(separador)

    def exibirArquivoConfiguracao(self) -> Optional[Dict[str, Any]]:
        config_dict = self.lerArquivoConfiguracao()
        if config_dict is None:
            return None

        print(f"\nArquivo: {self.arq}")
        print(f"Pasta:   {self.path_arq}\n")
        self._exibir_tabela(config_dict)
        return config_dict


def coletar_chaves_valores() -> Dict[str, Any]:
    """Solicita pares chave/valor ao usuário até o usuário responder N."""
    print("\nEspecifique os dados:\n")
    dados: Dict[str, Any] = {}
    indice = 1

    while True:
        chave = input(f"chave {indice:02d}: ").strip()
        if not chave:
            print("\nERRO: Informe ao menos uma chave.\n")
            continue

        valor = input("valor   : ").strip()
        if valor:
            if chave in dados:
                sobrescrever = input(
                    f"AVISO: A chave '{chave}' já existe. Sobrescrever? (s/n): "
                ).strip().lower()
                if sobrescrever == "s":
                    dados[chave] = valor
                else:
                    print("Chave mantida sem alteração.")
            else:
                dados[chave] = valor

        print()
        while True:
            resposta = input("Criar nova chave? ").strip().upper()
            if resposta == "S":
                indice += 1
                print()
                break
            if resposta == "N":
                print()
                return dados
            print("Resposta inválida. Informe S ou N.")
