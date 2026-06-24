from funçoes import (
    validar_nome,
    validar_quantidade,
    linha,
    menu,
    escolha,
    carregar_estoque,
    salvar_estoque,
    pedir_produto,
    pedir_preco,
    cadastrar_produto,
    remover_produto,
    atualizar_estoque,
    mostrar_estoque,
    atualizar_preco,
    repor_estoque,
    atualizar_estoque_minimo,
    mostrar_relatorio_financeiro,
    mostrar_relatorio_situacional,
    mostrar_resumo,
    mostrar_historico,
    carregar_historico,
    salvar_historico,
    mostrar_mais_comprado,
    mostrar_mais_vendido
)

import os

while True:
    menu()
    resposta = escolha()
    linha()

    if resposta == 1:
        cadastrar_produto()
        salvar_estoque()
        continue

    elif resposta == 2:
        repor_estoque()
        salvar_estoque()
        continue

    elif resposta == 3:
        remover_produto()
        salvar_estoque()
        continue

    elif resposta == 4:
        atualizar_estoque()
        salvar_estoque()
        continue

    elif resposta == 5:
        atualizar_preco()
        salvar_estoque()
        continue

    elif resposta == 6:
        atualizar_estoque_minimo()
        salvar_estoque()

    elif resposta == 7:
        mostrar_estoque()
        continue

    elif resposta == 8:
        mostrar_relatorio_financeiro()
        continue

    elif resposta == 9:
        mostrar_relatorio_situacional()
        continue

    elif resposta == 10:
        mostrar_resumo()
        continue

    elif resposta == 11:
        mostrar_historico()
        continue

    elif resposta == 12:
        mostrar_mais_vendido()
        linha()
        mostrar_mais_comprado()
        continue
    
    elif resposta == 13:
        print("\n   Saindo do sistema... ")
        linha()
        break
