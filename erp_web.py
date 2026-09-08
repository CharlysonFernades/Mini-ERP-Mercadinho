"""Adaptador web do Mini ERP, compatível com os arquivos JSON do terminal.

Usa somente a biblioteca padrão. Execute um único processo por pasta de dados;
feche o programa de terminal antes de editar a mesma base pelo navegador.
"""

import copy
import json
import os
import tempfile
import threading
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path


class ERPError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def quantity(value, label="Quantidade", minimum=0):
    if type(value) is not int or not minimum <= value <= 1_000_000:
        raise ERPError(f"{label}: informe um número inteiro entre {minimum} e 1.000.000.")
    return value


def price(value):
    try:
        if isinstance(value, bool):
            raise InvalidOperation
        number = Decimal(str(value))
        if not number.is_finite() or not 0 < number <= 1_000_000:
            raise InvalidOperation
        if number != number.quantize(Decimal("0.01")):
            raise InvalidOperation
        return float(number)
    except (InvalidOperation, ValueError, TypeError):
        raise ERPError("Informe um preço maior que zero, com até duas casas decimais.") from None


def product_name(value):
    if not isinstance(value, str):
        raise ERPError("Informe o nome do produto.")
    name = " ".join(value.strip().lower().split())
    # Preserva a regra de nomes usada pelo programa de terminal.
    if not 2 <= len(name) <= 80 or not name.replace(" ", "").isalpha():
        raise ERPError("O nome deve ter de 2 a 80 caracteres, apenas letras e espaços.")
    return name


def stock_status(amount, minimum):
    # Mesmos limites de mostrar_status(), em funçoes.py.
    if amount >= 1.4 * minimum:
        return "normal"
    if amount >= minimum:
        return "low"
    return "critical"


def atomic_json(path, value):
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".erp-", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class ERPStore:
    def __init__(self, directory, demo=False):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.inventory_path = self.directory / "Estoque.json"
        self.history_path = self.directory / "Historico_de_movimentações.json"
        self.journal_path = self.directory / ".erp-transaction.json"
        self.lock = threading.RLock()
        self.demo = demo
        self.recover()
        if demo and not self.inventory_path.exists() and not self.history_path.exists():
            self.seed_demo()

    def recover(self):
        # Um diário permite concluir as duas gravações após uma interrupção.
        if self.journal_path.exists():
            try:
                pending = json.loads(self.journal_path.read_text(encoding="utf-8"))
                self.validate(pending["inventory"], pending["history"])
            except (ValueError, KeyError, TypeError) as error:
                raise ERPError("O diário de gravação precisa ser revisado antes de continuar.", 500) from error
            atomic_json(self.inventory_path, pending["inventory"])
            atomic_json(self.history_path, pending["history"])
            self.journal_path.unlink()

    @staticmethod
    def read_json(path, fallback):
        if not path.exists():
            return copy.deepcopy(fallback)
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except (ValueError, UnicodeError) as error:
            raise ERPError(f"Não foi possível ler {path.name}. Revise o arquivo; seus dados não foram substituídos.", 500) from error

    @staticmethod
    def validate(inventory, history):
        try:
            if not isinstance(inventory, dict) or not isinstance(history, list):
                raise ValueError
            for name, item in inventory.items():
                product_name(name)
                quantity(item["Qtde"])
                quantity(item["Estoque Minimo"], "Estoque mínimo", 1)
                price(item["Preço Unitário"])
            for item in history:
                if not all(isinstance(item[key], str) for key in ("Data", "Hora", "Operação", "Produto")):
                    raise ValueError
                if type(item["Quantidade"]) is not int:
                    raise ValueError
                datetime.strptime(item["Data"] + " " + item["Hora"], "%d/%m/%Y %H:%M:%S")
        except (ValueError, KeyError, TypeError):
            raise ERPError("Há um registro inválido nos arquivos JSON. Revise os dados antes de continuar.", 500) from None

    def read(self):
        self.recover()
        inventory = self.read_json(self.inventory_path, {})
        history = self.read_json(self.history_path, [])
        self.validate(inventory, history)
        return inventory, history

    def save(self, inventory, history):
        self.validate(inventory, history)
        atomic_json(self.journal_path, {"inventory": inventory, "history": history})
        self.recover()

    @staticmethod
    def record(history, operation, name, amount, **extra):
        now = datetime.now()
        history.append({"Data": now.strftime("%d/%m/%Y"), "Hora": now.strftime("%H:%M:%S"),
                        "Operação": operation, "Produto": name, "Quantidade": amount, **extra})

    def mutate(self, action, data):
        if not isinstance(data, dict):
            raise ERPError("Envie os campos da operação em um objeto JSON.")
        with self.lock:
            inventory, history = self.read()
            name = product_name(data.get("name"))
            if action == "create":
                if name in inventory:
                    raise ERPError("Este produto já está cadastrado.", 409)
                amount = quantity(data.get("quantity"), minimum=1)
                inventory[name] = {"Qtde": amount, "Preço Unitário": price(data.get("price")),
                                   "Estoque Minimo": quantity(data.get("minimum"), "Estoque mínimo", 1)}
                self.record(history, "Cadastro", name, amount)
            elif action in ("movement", "update", "delete"):
                if name not in inventory:
                    raise ERPError("Produto não encontrado. Atualize a lista.", 404)
                item = inventory[name]
                if action == "movement":
                    operation = data.get("operation")
                    if operation not in ("Compra", "Venda"):
                        raise ERPError("Escolha uma entrada ou uma venda.")
                    amount = quantity(data.get("quantity"), minimum=1)
                    if operation == "Venda" and amount > item["Qtde"]:
                        raise ERPError(f"Estoque insuficiente: há apenas {item['Qtde']} unidade(s) disponível(is).", 409)
                    item["Qtde"] = quantity(item["Qtde"] + (amount if operation == "Compra" else -amount))
                    # Só registra depois que a operação inteira foi validada.
                    self.record(history, operation, name, amount)
                elif action == "update":
                    # Impede que um formulário antigo sobrescreva uma venda recente.
                    if data.get("expected") != item:
                        raise ERPError("Este produto mudou desde a abertura. Feche e abra a edição novamente.", 409)
                    replacement = {"Qtde": quantity(data.get("quantity")), "Preço Unitário": price(data.get("price")),
                                   "Estoque Minimo": quantity(data.get("minimum"), "Estoque mínimo", 1)}
                    if replacement != item:
                        self.record(history, "Ajuste", name, replacement["Qtde"] - item["Qtde"],
                                    Anterior=copy.deepcopy(item), Atual=copy.deepcopy(replacement))
                    inventory[name] = replacement
                else:
                    if item["Qtde"] != 0:
                        raise ERPError("Só é possível excluir um produto com estoque zerado.", 409)
                    del inventory[name]
                    self.record(history, "Exclusão", name, 0)
            else:
                raise ERPError("Operação não encontrada.", 404)
            self.save(inventory, history)
            return self.snapshot()

    def snapshot(self):
        with self.lock:
            inventory, history = self.read()
            products = [{"name": name, "quantity": item["Qtde"], "price": item["Preço Unitário"],
                         "minimum": item["Estoque Minimo"], "status": stock_status(item["Qtde"], item["Estoque Minimo"]),
                         "value": round(item["Qtde"] * item["Preço Unitário"], 2)}
                        for name, item in sorted(inventory.items())]
            total = sum(Decimal(str(item["Preço Unitário"])) * item["Qtde"] for item in inventory.values())
            today = datetime.now().date()
            days = []
            for ago in range(6, -1, -1):
                day = today - timedelta(days=ago)
                records = [item for item in history if item["Data"] == day.strftime("%d/%m/%Y")]
                days.append({"date": day.isoformat(),
                             "in": sum(item["Quantidade"] for item in records if item["Operação"] in ("Compra", "Cadastro")),
                             "out": sum(item["Quantidade"] for item in records if item["Operação"] == "Venda")})
            rankings = {}
            for key, operations in (("sales", ("Venda",)), ("purchases", ("Compra", "Cadastro"))):
                counts = {}
                for item in history:
                    if item["Operação"] in operations:
                        counts[item["Produto"]] = counts.get(item["Produto"], 0) + item["Quantidade"]
                rankings[key] = [{"name": name, "quantity": amount} for name, amount in
                                 sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:5]]
            return {"demo": self.demo, "today": today.isoformat(), "updatedAt": datetime.now().isoformat(),
                    "products": products, "history": list(reversed(history)), "week": days, "rankings": rankings,
                    "summary": {"products": len(products), "units": sum(p["quantity"] for p in products),
                                "value": float(total), "average": float(total / len(products)) if products else 0,
                                "normal": sum(p["status"] == "normal" for p in products),
                                "low": sum(p["status"] == "low" for p in products),
                                "critical": sum(p["status"] == "critical" for p in products),
                                "todayIn": days[-1]["in"], "todayOut": days[-1]["out"]}}

    def seed_demo(self):
        samples = [("arroz branco", 84, 6.49, 20), ("feijão carioca", 36, 8.90, 15),
                   ("açúcar cristal", 8, 4.59, 12), ("café torrado", 6, 18.90, 10),
                   ("leite integral", 54, 5.79, 24), ("óleo de soja", 22, 7.99, 18),
                   ("macarrão espaguete", 42, 4.29, 15), ("farinha de trigo", 0, 5.49, 10),
                   ("biscoito cream cracker", 28, 5.99, 12), ("sabão em barra", 32, 3.49, 12),
                   ("detergente neutro", 46, 2.89, 20), ("papel higiênico", 13, 8.99, 10)]
        inventory, history = {}, []
        for index, (name, final, unit_price, minimum) in enumerate(samples):
            daily_sales = [(index * 2 + day * 3) % 8 + 1 for day in range(7)]
            restock = 12 if index % 3 == 0 else 0
            initial = final + sum(daily_sales) - restock
            inventory[name] = {"Qtde": final, "Preço Unitário": unit_price, "Estoque Minimo": minimum}
            start = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0) - timedelta(days=7)
            history.append({"Data": start.strftime("%d/%m/%Y"), "Hora": "08:00:00", "Operação": "Cadastro", "Produto": name, "Quantidade": initial})
            for day, amount in enumerate(daily_sales):
                date = start + timedelta(days=day + 1)
                if day == 2 and restock:
                    history.append({"Data": date.strftime("%d/%m/%Y"), "Hora": "08:30:00", "Operação": "Compra", "Produto": name, "Quantidade": restock})
                history.append({"Data": date.strftime("%d/%m/%Y"), "Hora": f"{9 + index % 8:02d}:{index * 4:02d}:00", "Operação": "Venda", "Produto": name, "Quantidade": amount})
        history.sort(key=lambda item: datetime.strptime(item["Data"] + " " + item["Hora"], "%d/%m/%Y %H:%M:%S"))
        self.save(inventory, history)
