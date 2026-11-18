"""T12: lista modelos Gemini habilitados para generateContent, sem gerar texto."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from google import genai

CANDIDATOS = ("gemini-3.5-flash-lite", "gemini-3.8-flash")


def main() -> None:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise SystemExit("Defina GEMINI_API_KEY no terminal; nao inclua a chave no codigo.")
    client = genai.Client(api_key=key)
    try:
        modelos = {}
        for m in client.models.list():
            name = str(m.name or "").split("/")[-1]
            if name in CANDIDATOS:
                modelos[name] = {
                    "listado": True,
                    "acoes": list(m.supported_actions or []),
                    "entrada_limite": m.input_token_limit,
                    "saida_limite": m.output_token_limit,
                }
        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "observacao": "Listagem nao confirma cota gratuita nem acesso de geracao efetivo.",
            "modelos": {name: modelos.get(name, {"listado": False}) for name in CANDIDATOS},
        }
        out = Path("resultados_t12")
        out.mkdir(exist_ok=True)
        path = out / "modelos.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\nResultado: {path}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
