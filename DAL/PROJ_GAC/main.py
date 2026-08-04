# ----------------------
# Deus seja louvado!
# ----------------------

import sys

from geradorArquivoConfiguracao import ClGAC, coletar_chaves_valores


def _perguntar_nome_arquivo() -> str:
    nome_base = input("Nome: ").strip()
    if not nome_base:
        print("\nERRO: O nome do arquivo é obrigatório.")
        return ""
    return nome_base


def gerar_arquivo_criptografado():
    print()
    nome_base = _perguntar_nome_arquivo()
    if not nome_base:
        return

    dados = coletar_chaves_valores()
    if not dados:
        return

    try:
        gac = ClGAC(nome_arquivo=nome_base)
        gac.definir_dados(dados)

        if gac.gerarArquivoConfiguracao():
            print("\nArquivo gerado com sucesso!")
            print()
            print(f"  Arquivo: {gac.arq}")
            print(f"  Local:   {gac.path_arq}")
            print(f"  Chaves:  {len(dados)}")
        else:
            print("\nFalha ao gerar o arquivo criptografado.")

    except RuntimeError as e:
        print(f"\nErro crítico: {e}")
    except Exception as e:
        print(f"\nErro inesperado: {e}")


def ler_arquivo_criptografado():
    nome_base = _perguntar_nome_arquivo()
    if not nome_base:
        return

    try:
        gac = ClGAC(nome_arquivo=nome_base)
        dados = gac.exibirArquivoConfiguracao()
        if dados is None:
            print("\nNão foi possível ler o arquivo informado.")
    except RuntimeError as e:
        print(f"\nErro crítico: {e}")
    except Exception as e:
        print(f"\nErro inesperado: {e}")


def main():
    while True:
        print("\nO que deseja realizar?\n")
        print("  1.) Gerar arquivo criptografado")
        print("  2.) Ler arquivo")
        print("  3.) Sair")
        print("")

        escolha = input("Opção: ").strip()

        if escolha == "1":
            gerar_arquivo_criptografado()
        elif escolha == "2":
            ler_arquivo_criptografado()
        elif escolha == "3":
            print("\nAté logo!\n")
            break
        else:
            print("\nOpção inválida. Informe 1, 2 ou 3.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        sys.exit(1)
