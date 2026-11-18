"""T12: consolida medicoes locais; nao faz chamadas externas."""
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

CAMINHO = Path("resultados_t12/medicoes.csv")


def valor(row, campo):
    try:
        return float(row[campo])
    except (TypeError, ValueError, KeyError):
        return None


def main():
    if not CAMINHO.exists():
        raise SystemExit("Ainda nao existe resultados_t12/medicoes.csv")
    with CAMINHO.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    grupos = defaultdict(list)
    for row in rows:
        grupos[(row["modelo"], row["cenario"])].append(row)
    relatorio = {}
    for (modelo, cenario), registros in sorted(grupos.items()):
        ok = [r for r in registros if r["status"] == "ok"]
        def media(campo):
            dados = [v for r in ok if (v := valor(r, campo)) is not None]
            return round(mean(dados), 2) if dados else None
        relatorio[f"{modelo}/{cenario}"] = {
            "requisicoes": len(registros), "sucessos": len(ok),
            "erros": len(registros) - len(ok),
            "respostas_json_validas": sum(r["validacao"] == "valido" for r in ok),
            "latencia_media_s": media("duracao_s"),
            "tokens_entrada_medios": media("tokens_entrada"),
            "tokens_saida_medios": media("tokens_saida"),
            "tokens_pensamento_medios": media("tokens_pensamento"),
            "tokens_total_medios": media("tokens_total"),
        }
    print(json.dumps(relatorio, indent=2, ensure_ascii=False))
    print("\nNota: extrapolar 12 chamadas exige definir o mix de formatos, revisoes e novas tentativas.")
    print("RPM/RPD/TPM nao sao inferiveis com seguranca dessas medias; verificar no AI Studio.")


if __name__ == "__main__":
    main()
