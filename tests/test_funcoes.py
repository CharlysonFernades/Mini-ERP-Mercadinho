import tempfile 
import unittest
from pathlib import Path
from unittest.mock import patch
import io
from contextlib import redirect_stdout


import funçoes as funcoes
# Criando a classe que utiliza os recursos de teste automatizados do python

class TestFuncoes(unittest.TestCase):
    # setUp permite que o ambiente seja preparado N vezes para N testes diferentes, prepara o ambiente de testes,  e o cleanup limpa os dados entre um teste e outro.

    def setUp(self):
        # 1. cria a pasta temporaria
        self.pasta_temporaria = tempfile.TemporaryDirectory()
        # limpa a pasta ao final
        self.addCleanup(self.pasta_temporaria.cleanup)
        # define o caminho da pasta, .name fornece o caminho da pasta criada. Path() transforma em objeto que facilita trabalhar com caminhos de arquivos.
        self.caminho = Path(self.pasta_temporaria.name)

        # 2. Substitui o caminho original do estoque
        patch_estoque = patch.object(funcoes, "CAMINHO_JSON", self.caminho/"Estoque.json")
        # Ativando a substituição
        patch_estoque.start()
        self.addCleanup(patch_estoque.stop)
        # 2.1 Substitui o caminho original do historico
        patch_historico = patch.object(funcoes, "CAMINHO_JS_HISTORICO", self.caminho / "Historico_de_movimentações.json")
        # Ativando a substituição
        patch_historico.start()
        self.addCleanup(patch_historico.stop)
        # 3. Substituir estoque em memoria
        patch_estoque_memoria = patch.object(funcoes, "estoque", {"arroz": {"Qtde": 10, "Preço Unitário": 5.00, "Estoque Minimo": 2}})
        patch_estoque_memoria.start()
        self.addCleanup(patch_estoque_memoria.stop)

        # 4. Substituir o histórico em memória - Isso cria uma memoria para que cada teste seja executado a partir daqui.
        patch_historico_memoria = patch.object(funcoes, "historico", [])
        patch_historico_memoria.start()
        self.addCleanup(patch_historico_memoria.stop)

    def test_venda_maior_que_estoque(self):
        # 1. Simular as respostas do usuário
        with patch("builtins.input", side_effect=["arroz", "50"]):

            # 2. Executar a função que queremos testar
            funcoes.remover_produto()

        # 3. Conferir se o estoque permaneceu em 10
        # self.assertEqual(Resultado esperado, resultado obtido.)
        
        self.assertEqual(10, funcoes.estoque["arroz"]["Qtde"])

        # 4. Conferir se o histórico continua vazio
        # self.assertEqual(Resultado esperado, resultado obtido.)
        self.assertEqual([], funcoes.historico)
        
    def test_mensagem_de_erro(self):
        with patch("builtins.input", side_effect=["arroz", "50"]):
            # guarda o print da mensagem de erro
            saida = io.StringIO()
            # Redireciona a mensagem de erro pra um getvalue
            with redirect_stdout(saida):
                # Executa a função
                funcoes.remover_produto()
            # Compara se tem "texto desejado" na mensagem de erro
            self.assertIn("estoque suficiente", saida.getvalue())