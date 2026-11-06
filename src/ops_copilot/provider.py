"""Minimal Responses API client. No SDK, hidden credentials or silent fallback."""
import json
import os
import time
import urllib.error
import urllib.request
from .privacy import FINAL_SCHEMA, check_outbound

class ProviderError(RuntimeError):
    pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderError("Redirecionamento do endpoint bloqueado")

class OpenAIProvider:
    mode = "live"
    def __init__(self, key=None, model=None, opener=None, sleep=time.sleep):
        self.key = key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL")
        if not self.key or not self.model:
            raise ProviderError("Modo live exige OPENAI_API_KEY e OPENAI_MODEL")
        self.opener = opener or urllib.request.build_opener(NoRedirect()).open
        self.sleep = sleep

    def respond(self, history, tools, instructions):
        check_outbound(history)
        body = json.dumps({"model": self.model, "input": history, "instructions": instructions, "tools": tools, "parallel_tool_calls": False, "store": False, "max_output_tokens": 1800, "text": {"format": {"type": "json_schema", "name": "operations_summary", "strict": True, "schema": FINAL_SCHEMA}}}).encode()
        req = urllib.request.Request("https://api.openai.com/v1/responses", data=body, headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with self.opener(req, timeout=30) as response:
                    result = json.loads(response.read(2_000_000))
                if result.get("status") != "completed" or not isinstance(result.get("output"), list):
                    raise ProviderError("Resposta incompleta ou incompatível do provedor")
                return result
            except urllib.error.HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise ProviderError(f"Falha HTTP {exc.code} no provedor; nenhuma aprovação foi executada") from None
                self.sleep(2 ** attempt)
            except (urllib.error.URLError, TimeoutError, ValueError):
                raise ProviderError("Falha de rede ou resposta inválida do provedor") from None
        raise ProviderError("Limite de tentativas atingido")
