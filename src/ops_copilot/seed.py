"""Reproducible, explicitly synthetic fixtures. No personal information."""
import json
import random
from pathlib import Path

POLICIES = [
    {"id": "P-DELAY", "title": "Atraso", "version": 1, "text": "Pedidos ativos com atraso positivo podem receber uma atualização de status. Nunca prometer novo prazo ou compensação sem confirmação. Atrasos de 20 minutos ou mais exigem escalonamento.", "templates": ["delay_update", "escalate"]},
    {"id": "P-SAFETY", "title": "Segurança alimentar", "version": 1, "text": "Relato de alergia, intoxicação ou alimento estragado exige escalonamento urgente para equipe humana. Não diagnosticar e não decidir reembolso.", "templates": ["escalate"]},
    {"id": "P-MISSING", "title": "Item ausente", "version": 1, "text": "Item faltante ou pedido incompleto exige conferência humana dos itens e do comprovante. Sem promessa automática de reembolso.", "templates": ["missing_review"]},
    {"id": "P-REVIEW", "title": "Revisão e execução", "version": 1, "text": "Toda proposta precisa de aprovação explícita de um operador. O modelo não aprova, não envia mensagens reais e não movimenta dinheiro. A execução deste laboratório grava apenas um recibo simulado.", "templates": []},
]

def fixtures():
    rng = random.Random(42)
    rows = []
    for i in range(1, 61):
        issue = rng.choice(["none", "none", "missing", "safety"])
        rows.append({"id": f"SYN-{i:03d}", "status": rng.choice(["preparing", "in_transit", "delivered", "cancelled"]), "delay_minutes": rng.randint(-10, 45), "issue": issue, "value_brl": round(rng.uniform(20, 150), 2), "version": 1, "synthetic": True})
    rows[:5] = [
        {"id": "SYN-001", "status": "in_transit", "delay_minutes": 12, "issue": "none", "value_brl": 48.9, "version": 1, "synthetic": True},
        {"id": "SYN-002", "status": "preparing", "delay_minutes": 32, "issue": "none", "value_brl": 75.0, "version": 1, "synthetic": True},
        {"id": "SYN-003", "status": "delivered", "delay_minutes": 0, "issue": "safety", "value_brl": 36.0, "version": 1, "synthetic": True},
        {"id": "SYN-004", "status": "delivered", "delay_minutes": 0, "issue": "missing", "value_brl": 25.0, "version": 1, "synthetic": True},
        {"id": "SYN-005", "status": "cancelled", "delay_minutes": 30, "issue": "none", "value_brl": 25.0, "version": 1, "synthetic": True},
    ]
    return rows

def export(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, obj in [("orders.json", fixtures()), ("policies.json", POLICIES)]:
        (directory / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
