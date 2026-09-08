"""Testes de integração: persistência, integridade e contrato HTTP da interface."""

import concurrent.futures
import copy
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import erp_web
from erp_web import ERPError, ERPStore
from web_server import ERPServer


class ERPIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = ERPStore(self.temporary.name)

    def add_product(self, amount=10):
        return self.store.mutate("create", {"name": "Arroz Branco", "quantity": amount, "price": 6.49, "minimum": 5})

    def test_empty_legacy_files_and_registration_persist(self):
        self.assertEqual(self.store.snapshot()["summary"]["average"], 0)
        self.add_product()
        reopened = ERPStore(self.temporary.name).snapshot()
        self.assertEqual(reopened["summary"]["value"], 64.9)
        self.assertEqual(reopened["history"][0]["Operação"], "Cadastro")
        disk = json.loads(self.store.inventory_path.read_text())
        self.assertEqual(disk["arroz branco"], {"Qtde": 10, "Preço Unitário": 6.49, "Estoque Minimo": 5})

    def test_invalid_sale_changes_neither_stock_nor_history(self):
        self.add_product()
        before = (self.store.inventory_path.read_bytes(), self.store.history_path.read_bytes())
        with self.assertRaisesRegex(ERPError, "Estoque insuficiente"):
            self.store.mutate("movement", {"name": "arroz branco", "quantity": 11, "operation": "Venda"})
        self.assertEqual(before, (self.store.inventory_path.read_bytes(), self.store.history_path.read_bytes()))

    def test_sale_restock_and_rankings_recalculate(self):
        self.add_product()
        self.store.mutate("movement", {"name": "arroz branco", "quantity": 8, "operation": "Venda"})
        result = self.store.mutate("movement", {"name": "arroz branco", "quantity": 12, "operation": "Compra"})
        self.assertEqual(result["products"][0]["quantity"], 14)
        self.assertEqual(result["products"][0]["status"], "normal")
        self.assertEqual(result["rankings"]["sales"][0]["quantity"], 8)
        self.assertEqual(result["rankings"]["purchases"][0]["quantity"], 22)

    def test_concurrent_sales_do_not_oversell(self):
        self.add_product(amount=1)
        def buy():
            try:
                self.store.mutate("movement", {"name": "arroz branco", "quantity": 1, "operation": "Venda"})
                return True
            except ERPError:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: buy(), range(8)))
        self.assertEqual(sum(results), 1)
        self.assertEqual(self.store.snapshot()["products"][0]["quantity"], 0)
        self.assertEqual(len(self.store.snapshot()["history"]), 2)

    def test_duplicate_invalid_values_and_stale_edit_are_rejected(self):
        self.add_product()
        with self.assertRaisesRegex(ERPError, "já está cadastrado"):
            self.add_product()
        for invalid in (0, -1, float("nan"), float("inf"), True, 2.999):
            with self.subTest(price=invalid), self.assertRaises(ERPError):
                self.store.mutate("create", {"name": "feijão", "quantity": 5, "price": invalid, "minimum": 1})
        with self.assertRaises(ERPError):
            self.store.mutate("movement", {"name": "arroz branco", "quantity": True, "operation": "Venda"})
        previous = {"Qtde": 10, "Preço Unitário": 6.49, "Estoque Minimo": 5}
        self.store.mutate("movement", {"name": "arroz branco", "quantity": 1, "operation": "Venda"})
        with self.assertRaisesRegex(ERPError, "mudou desde"):
            self.store.mutate("update", {"name": "arroz branco", "quantity": 10, "price": 7.9, "minimum": 5, "expected": previous})
        self.assertEqual(self.store.snapshot()["products"][0]["quantity"], 9)

    def test_updates_are_audited_and_deletion_preserves_history(self):
        self.add_product()
        result = self.store.mutate("update", {"name": "arroz branco", "quantity": 0, "price": 7.99, "minimum": 3,
                                             "expected": {"Qtde": 10, "Preço Unitário": 6.49, "Estoque Minimo": 5}})
        self.assertEqual(result["history"][0]["Anterior"]["Qtde"], 10)
        self.assertEqual(result["history"][0]["Atual"]["Preço Unitário"], 7.99)
        result = self.store.mutate("delete", {"name": "arroz branco"})
        self.assertEqual(result["products"], [])
        self.assertEqual(len(result["history"]), 3)

    def test_damaged_json_is_not_replaced(self):
        self.store.inventory_path.write_text('{"dados":')
        with self.assertRaisesRegex(ERPError, "não foram substituídos"):
            self.add_product()
        self.assertEqual(self.store.inventory_path.read_text(), '{"dados":')

    def test_interrupted_two_file_write_recovers_consistently(self):
        self.add_product()
        real_write = erp_web.atomic_json
        def fail_history(path, value):
            if path == self.store.history_path:
                raise OSError("Simulated disk interruption")
            return real_write(path, value)
        with patch("erp_web.atomic_json", side_effect=fail_history), self.assertRaises(OSError):
            self.store.mutate("movement", {"name": "arroz branco", "quantity": 3, "operation": "Venda"})
        reopened = ERPStore(self.temporary.name).snapshot()
        self.assertEqual(reopened["products"][0]["quantity"], 7)
        self.assertEqual(reopened["history"][0]["Quantidade"], 3)
        self.assertFalse(self.store.journal_path.exists())

    def test_demo_ledger_matches_ending_stock(self):
        demo = ERPStore(Path(self.temporary.name) / "demo", demo=True).snapshot()
        for product in demo["products"]:
            balance = sum(item["Quantidade"] * (-1 if item["Operação"] == "Venda" else 1)
                          for item in demo["history"] if item["Produto"] == product["name"])
            self.assertEqual(balance, product["quantity"])
        self.assertFalse(self.store.inventory_path.exists())

    def test_http_static_api_csrf_and_path_boundaries(self):
        server = ERPServer(("127.0.0.1", 0), self.store)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        def request(path, data=None, token=None, host=None):
            headers = {"Content-Type": "application/json"}
            if token: headers["X-ERP-Token"] = token
            if host: headers["Host"] = host
            req = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
            try:
                with urllib.request.urlopen(req) as response:
                    return response.status, response.read(), response.headers
            except urllib.error.HTTPError as error:
                return error.code, error.read(), error.headers
        try:
            status, raw, headers = request("/")
            self.assertEqual(status, 200)
            self.assertIn(b'lang="pt-BR"', raw)
            self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
            self.assertEqual(request("/Estoque.json")[0], 404)
            self.assertEqual(request("/../erp_web.py")[0], 404)
            self.assertEqual(request("/api/state", host="untrusted.example")[0], 403)
            token = json.loads(request("/api/state")[1])["csrf"]
            data = {"name": "feijão", "quantity": 8, "price": 9.9, "minimum": 3}
            self.assertEqual(request("/api/products", data)[0], 403)
            self.assertEqual(request("/api/products", data, token)[0], 201)
            self.assertEqual(request("/api/products", data, token)[0], 409)
            self.assertEqual(request("/api/products", [], token)[0], 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
