"""Business constraints are enforced by code, independently of model output."""
import re
import unicodedata

class DomainError(ValueError):
    pass

TEMPLATES = {
    "delay_update": "Identificamos um atraso no pedido {id}. A equipe verificará o andamento e confirmará a previsão. Não há novo prazo confirmado neste momento.",
    "escalate": "O pedido {id} foi sinalizado para análise prioritária de uma pessoa da equipe. A mensagem não confirma compensação nem resolução do caso.",
    "missing_review": "Registramos a necessidade de conferir os itens do pedido {id}. Uma pessoa da equipe avaliará o caso antes de qualquer decisão sobre reembolso.",
}

def normalize(text):
    return unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()

def recommendation(order):
    if order["issue"] == "safety":
        return "escalate", "P-SAFETY", "urgent"
    if order["status"] in {"preparing", "in_transit"} and order["delay_minutes"] >= 20:
        return "escalate", "P-DELAY", "high"
    if order["issue"] == "missing":
        return "missing_review", "P-MISSING", "normal"
    if order["status"] in {"preparing", "in_transit"} and order["delay_minutes"] > 0:
        return "delay_update", "P-DELAY", "normal"
    return None

def validate_proposal(order, template, policy):
    expected = recommendation(order)
    if expected is None or (template, policy) != expected[:2]:
        raise DomainError("Proposta incompatível com o estado do pedido e a política")
    return {"template": template, "policy_id": policy, "priority": expected[2], "message": TEMPLATES[template].format(id=order["id"])}

def bounded_text(value, name, maximum=1000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise DomainError(f"Campo inválido: {name}")
    return value.strip()
