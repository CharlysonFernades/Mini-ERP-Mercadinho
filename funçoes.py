import os
import json
from datetime import datetime

CAMINHO_JSON = os.path.join(os.path.dirname(__file__), "Estoque.json")
CAMINHO_JS_HISTORICO = os.path.join(
    os.path.dirname(__file__), "Historico_de_movimentações.json"
)


def salvar_historico():
    with open(CAMINHO_JS_HISTORICO, "w") as arquivo:
        json.dump(historico, arquivo, indent=4, ensure_ascii=False)


def carregar_historico():
    try:
        with open(CAMINHO_JS_HISTORICO, "r") as arquivo:
            historico = json.load(arquivo)
        return historico
    except (FileNotFoundError, json.JSONDecodeError):
        return []


historico = carregar_historico()
# Para mostrar o menu:


def linha():
    print("-" * 50)


opcoes = {
    "Adicionar produto": 1,
    "Repor estoque": 2,
    "Remover produto (Venda)": 3,
    "Atualizar estoque do produto": 4,
    "Atualizar preço": 5,
    "Atualizar estoque mínimo": 6,
    "Mostrar estoque": 7,
    "Relatório financeiro": 8,
    "Relatório situacional": 9,
    "Resumo gerencial": 10,
    "Histórico de movimentações": 11,
    "Sair": 12,
}


def menu():
    print("\n- SISTEMA MINI ERP - MERCADINHO")
    linha()
    for opcao, numero in opcoes.items():
        print(f"{numero} - {opcao}")
    linha()


# Para validar os nomes dados ( cliente ou produto ).


def validar_nome(mensagem):
    while True:

        nome = input(mensagem)
        nome = nome.strip().lower()
        if nome:
            if not nome.replace(" ", "").isalpha():
                print("Você só pode digitar LETRAS e ESPAÇOS!")
                continue
        else:
            print(f"(Somente com LETRAS e ESPAÇOS!) - {mensagem} ")
            continue

        return nome


# Para validar a quantidade ( Vendida ou comprada )


def validar_quantidade(mensagem):
    while True:
        try:
            num_str = input(mensagem)
            num = int(num_str)
            if num > 0:
                return num
            else:
                print("Você PRECISA digitar um número MAIOR que ZERO!")
        except ValueError:
            print("Você deve digitar apenas números!")


def pedir_produto():
    nome = validar_nome("Digite o nome do produto: ")
    return nome


def pedir_preco(mensagem):
    while True:
        try:
            num_str = input(mensagem)
            num = float(num_str)
            if num > 0:
                return num
            else:
                print("Você PRECISA digitar um número MAIOR que ZERO!")
        except ValueError:
            print("Você deve digitar apenas números!")


def escolha():
    while True:
        escolha = validar_quantidade("Digite a opção: ")
        if escolha in opcoes.values():
            return escolha
        else:
            print("Você precisa escolher uma opção válida!")


def salvar_estoque():
    with open(CAMINHO_JSON, "w") as arquivo:
        json.dump(estoque, arquivo)


def carregar_estoque():
    try:
        with open(CAMINHO_JSON, "r") as arquivo:
            estoque = json.load(arquivo)
        return estoque
    except FileNotFoundError:
        return {}


estoque = carregar_estoque()


def cadastrar_produto():
    nome = pedir_produto()
    if nome in estoque:
        print("Este produto já está cadastrado!")
        return
    qde_compra = validar_quantidade("Informe a quantidade comprada: ")
    preco_unit = pedir_preco("Digite o preço unitário do produto:")
    estoque_minimo = validar_quantidade(
        "Digite a quantidade mínima em estoque para este produto: "
    )
    estoque[nome] = {
        "Qtde": qde_compra,
        "Preço Unitário": preco_unit,
        "Estoque Minimo": estoque_minimo,
    }

    registrar_movimentação("Cadastro", nome, qde_compra)


def repor_estoque():
    produto = pedir_produto()
    quantidade = validar_quantidade("Digite a quantidade comprada: ")
    if produto not in estoque:
        print("Este produto não está cadastrado!")
    else:
        estoque[produto]["Qtde"] += quantidade
        print(f"Novo estoque de {produto}: {estoque[produto]['Qtde']}")

        registrar_movimentação("Compra", produto, quantidade)


def remover_produto():
    produto = pedir_produto()
    if produto in estoque:
        qde_venda = validar_quantidade("Informe a quantidade vendida: ")

        registrar_movimentação("Venda", produto, qde_venda)

        if qde_venda <= estoque[produto]["Qtde"]:
            estoque[produto]["Qtde"] -= qde_venda
            if estoque[produto]["Qtde"] == 0:
                print(f"O estoque de {produto} chegou a ZERO!")
                print("Deseja remover o produto do estoque? (s/n)")
                resposta = validar_nome("Digite sua resposta: ")
                if resposta == "s":
                    del estoque[produto]

        else:

            print("\n Não há estoque suficiente!")
    else:
        print("O produto não se encontra no estoque!")


def atualizar_estoque():
    produto = validar_nome(
        "Digite o nome do produto que você deseja atualizar o estoque: "
    )
    if produto not in estoque:
        print("Este produto não encontra-se no estoque!")
    else:
        nova_qtde = validar_quantidade("Digite a quantidade em estoque atualizada: ")
        estoque[produto]["Qtde"] = nova_qtde
        print("A quantidade em estoque foi atualizada!")


def atualizar_preco():
    produto = validar_nome("Informe o produto que você deseja atualizar o preço: ")
    if produto not in estoque:
        print("Este produto não encontra-se no estoque!")
    else:
        novo_preco = pedir_preco("Digite o novo preço unitário do produto: ")
        preco_antigo = estoque[produto]["Preço Unitário"]
        estoque[produto]["Preço Unitário"] = novo_preco
        print(
            f"O preço de {produto} foi atualizado de R$ {preco_antigo:.2f} para R$ {novo_preco:.2f}"
        )


def mostrar_estoque():
    for produto, dados in estoque.items():
        print(f"\n Produto: {produto.title()}")
        print(f"- Estoque Mínimo: {estoque[produto]['Estoque Minimo']}")
        print(f"- Quantidade: {dados['Qtde']}")
        print(f"- Preço Unitário: R$ {dados['Preço Unitário']}")
        total = dados["Qtde"] * dados["Preço Unitário"]

        print(f"- Total em Estoque: R$ {total:.2f}")
        status = mostrar_status(produto)
        print(f"- Situação: {status}")
        linha()


def mostrar_status(produto):
    estoque_minimo = estoque[produto]["Estoque Minimo"]
    if estoque[produto]["Qtde"] >= (1.4 * estoque_minimo):
        return "Em estoque"
    elif estoque[produto]["Qtde"] >= estoque_minimo:
        return "Estoque Baixo"
    else:
        return "Alerta!!!"


def atualizar_estoque_minimo():
    while True:
        produto = pedir_produto()
        if produto not in estoque:
            print("Este produto não encontra-se no estoque!")
            continue
        else:
            novo_minimo = validar_quantidade(
                f"Digite o novo estoque mínimo de {produto}: "
            )
            estoque[produto]["Estoque Minimo"] = novo_minimo
            print("Estoque mínimo atualizado!")
            break


def somar_valores_estoque():
    total = 0
    for dados in estoque.values():
        total += dados["Qtde"] * dados["Preço Unitário"]

    return total


def mostrar_relatorio_financeiro():
    total_estoque = somar_valores_estoque()
    print(f"\n- O Valor Total do Estoque encontra-se em: R$ {total_estoque:.2f}")


def mostrar_relatorio_situacional():
    print("\nProdutos em situações críticas:")
    linha()
    for produto, dados in estoque.items():
        status = mostrar_status(produto)
        qde = dados["Qtde"]
        minimo = dados["Estoque Minimo"]
        qde_pendente = minimo - qde
        qde_acima_do_minimo = qde - minimo
        if status != "Em estoque":
            print(f"Produto: {produto.title()}")
            print()
            if qde == minimo:
                print(f"Quantidade atual: {qde} ")
                print(f"Estoque mínimo: {minimo} ")
                print()
                print("ATENÇÃO:")
                print(
                    f"A quantidade em estoque atingiu o limite MÍNIMO para este produto"
                )
            elif qde < minimo:
                print(f"Quantidade atual: {qde} ")
                print(f"Estoque mínimo: {minimo} ")
                print()
                print("ATENÇÃO:")
                print(f"Necessário repor: {qde_pendente} unidades.")
            else:
                print(f"Quantidade em estoque: {qde}")
                print(f"Estoque mínimo: {minimo} ")
                print()
                print("ATENÇÃO:")
                print(
                    f"Restam apenas {qde_acima_do_minimo} unidades para chegar no nível MÍNIMO de estoque! "
                )
            print()
            print(f"Situação: {status}")
            linha()


def mostrar_resumo():
    prod_em_alerta = 0
    prod_estoque_baixo = 0
    total_produtos = len(estoque)
    financeiro = somar_valores_estoque()
    valor_medio = financeiro / total_produtos
    for produto, dados in estoque.items():
        status = mostrar_status(produto)
        if status == "Alerta!!!":
            prod_em_alerta += 1
        elif status == "Estoque Baixo":
            prod_estoque_baixo += 1

    print("\nRESUMO GERAL")
    linha()
    print(f"\n- Produtos cadastrados: {total_produtos}")
    print(f"\n- Produtos em alerta: {prod_em_alerta}")
    print(f"\n- Produtos com estoque baixo: {prod_estoque_baixo}")
    print(
        f"\n- Produtos em situação normal: {total_produtos - prod_em_alerta - prod_estoque_baixo}"
    )
    mostrar_relatorio_financeiro()
    print(f"\n- Valor médio por produto: R$ {valor_medio}")
    linha()


def registrar_movimentação(tipo, produto, quantidade):
    registro = {
        "Data": datetime.now().strftime("%d/%m/%Y"),
        "Hora": datetime.now().strftime("%H:%M:%S"),
        "Operação": tipo,
        "Produto": produto,
        "Quantidade": quantidade,
    }

    historico.append(registro)
    salvar_historico()


def mostrar_historico():
    for registro in historico:
        print(
            f"{registro['Data']} | "
            f"{registro['Hora']} | "
            f"{registro['Operação']} | "
            f"{registro['Produto']} | "
            f"{registro['Quantidade']} | "
        )
