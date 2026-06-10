from funçoes import validar_nome, validar_quantidade, linha, menu, escolha, carregar_estoque, salvar_estoque, pedir_produto, pedir_preco, cadastrar_produto, remover_produto, atualizar_estoque,mostrar_estoque, atualizar_preco, repor_estoque, atualizar_estoque_minimo

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

    elif resposta ==4:
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
        print("\n   Saindo do sistema... ")
        linha()
        break