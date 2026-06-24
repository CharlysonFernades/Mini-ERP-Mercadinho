# Mini-ERP-Mercadinho
Sistema de gerenciamento de estoque desenvolvido em Python para pequenos comerciantes.

## Sobre o projeto
Este projeto foi desenvolvido para resolver um problema comum em pequenos comércios:

- controle manual de estoque
- dificuldade para acompanhar produtos
- falta de alertas de reposição

O sistema permite gerenciar produtos através de um terminal em Python.

## Funcionalidades

* Cadastro de produtos
* Controle de estoque
* Reposição de mercadorias
* Registro de vendas
* Atualização de preços
* Configuração de estoque mínimo
* Alertas automáticos de reposição
* Relatório financeiro

  * Valor total do estoque
  * Valor médio por produto
* Relatório situacional

  * Produtos em estoque baixo
  * Produtos em situação crítica
* Resumo gerencial

  * Total de produtos cadastrados
  * Quantidade de produtos em alerta
  * Quantidade de produtos com estoque baixo
  * Quantidade de produtos em situação normal
* Histórico de movimentações
  
  * Registro de compras
  * Registro de vendas
  * Registro de novos cadastros
  * Data e hora das operações
  * Ranking de produtos mais vendidos
  * Ranking de produtos mais comprados
* Persistência de dados em JSON


## Tecnologias utilizadas

- Python
- JSON

## Estrutura do projeto

funcoes.py
compras.py
Estoque.json
Historico_de_movimentações.json

## Arquivo de exemplo

O arquivo `Estoque.json` presente no repositório consta vazio para que o usuário consiga testar o sistema desde o início; validando, portanto, o histórico de movimentações de cada ação.
## Como executar

1. Baixe os arquivos do projeto
2. Certifique-se de ter Python instalado
3. Execute:

python compras.py

## Melhorias futuras

- Exportação para Excel
- Integração com Pandas
- Dashboard Gerencial
