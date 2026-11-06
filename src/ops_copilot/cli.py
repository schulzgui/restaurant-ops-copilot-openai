import argparse
import json
import os
from pathlib import Path
from .db import Store
from .engine import Engine
from .evaluation import evaluate
from .provider import OpenAIProvider, ProviderError
from .seed import export
from .server import make_server
from .config import load_local


def main():
    parser = argparse.ArgumentParser(description="Restaurant Ops Copilot — dados sintéticos")
    parser.add_argument("command", choices=["init", "serve", "run", "evaluate", "audit", "worker"])
    parser.add_argument("--db", default="runtime/copilot.sqlite")
    parser.add_argument("--port", type=int, default=8004)
    parser.add_argument("--host", choices=["127.0.0.1", "0.0.0.0"], default="127.0.0.1")
    parser.add_argument("--prompt", default="Prepare propostas para os pedidos urgentes")
    parser.add_argument("--cases", default="data/eval_cases.json")
    parser.add_argument("--output", default="artifacts/evaluation-live.json")
    args = parser.parse_args()
    try:
        load_local()
        provider = OpenAIProvider() if args.command in {"run", "serve", "evaluate"} else None
    except (ProviderError,ValueError) as exc:
        parser.error(str(exc))
    if args.command == "evaluate":
        report = evaluate(args.cases, args.output, provider)
        print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2, ensure_ascii=False))
        return
    store = Store(args.db)
    if args.command == "init":
        export("data")
        print("Base sintética criada ou preservada; nenhum estado existente foi apagado.")
    elif args.command == "run":
        print(json.dumps(Engine(store, provider).run(args.prompt), ensure_ascii=False, indent=2))
    elif args.command == "worker":
        print(json.dumps(store.dispatch(), ensure_ascii=False, indent=2))
    elif args.command == "audit":
        result = store.audit(); print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result["valid"]:
            raise SystemExit(1)
    else:
        server, operator, reviewer = make_server(store, provider, args.port, os.environ.get("OPS_OPERATOR_TOKEN"), os.environ.get("OPS_REVIEWER_TOKEN"), args.host)
        print(f"Abra http://127.0.0.1:{server.server_port}", flush=True)
        print(f"Token OPERADOR: {operator}", flush=True)
        print(f"Token REVISOR: {reviewer}", flush=True)
        print("Tokens são credenciais locais. Não compartilhe a saída do terminal.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()

if __name__ == "__main__":
    main()
