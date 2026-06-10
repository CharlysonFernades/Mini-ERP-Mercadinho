import os
import json

CAMINHO_JSON = os.path.join(
    os.path.dirname(__file__),
    "Estoque.json"
)


# Para mostrar o menu:


def linha():
    print("-" * 50)


opcoes = {
    "Adicionar produto": 1,
    "Repor estoque":2,
    "Remover produto (Venda)": 3,
    "Atualizar estoque do produto": 4,
    "Atualizar preço": 5,
    "Atualizar estoque mínimo":6,
    "Mostrar estoque": 7,
    "Sair": 8,
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
        print('Este produto já está cadastrado!')
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

def repor_estoque():
    produto = pedir_produto()
    quantidade = validar_quantidade('Digite a quantidade comprada: ')
    if produto not in estoque:
        print('Este produto não está cadastrado!')
    else:
        estoque[produto]['Qtde'] += quantidade
        print(f"Novo estoque de {produto}: {estoque[produto]['Qtde']}")

def remover_produto():
    produto = pedir_produto()
    if produto in estoque:
        qde_venda = validar_quantidade("Informe a quantidade vendida: ")
        if qde_venda <= estoque[produto]["Qtde"]:
            estoque[produto]["Qtde"] -= qde_venda
            if estoque[produto]["Qtde"] == 0:
                print(f"O estoque de {produto} chegou a ZERO!")
                print('Deseja remover o produto do estoque? (s/n)')
                resposta = validar_nome('Digite sua resposta: ')
                if resposta == 's':
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
    estoque_minimo = estoque[produto]['Estoque Minimo']
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
            novo_minimo = validar_quantidade(f'Digite o novo estoque mínimo de {produto}: ')
            estoque[produto]["Estoque Minimo"] = novo_minimo
            print("Estoque mínimo atualizado!")
            break