import json
from datetime import datetime

from logic.models import Avaliacao, avaliacao_de_dict, avaliacao_para_dict

VERSAO_SCHEMA = 1


def serializar(avaliacoes: dict[str, Avaliacao], historico: list[dict[str, object]] | None = None) -> bytes:
    payload = {
        "schema": VERSAO_SCHEMA,
        "exportado_em": datetime.now().isoformat(timespec="seconds"),
        "avaliacoes": {cid: avaliacao_para_dict(a) for cid, a in avaliacoes.items()},
        "historico": historico or [],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def deserializar(data: bytes) -> tuple[dict[str, Avaliacao], list[dict[str, object]]]:
    raw = json.loads(data.decode("utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Arquivo inválido: raiz não é objeto JSON.")
    schema = raw.get("schema")
    if schema != VERSAO_SCHEMA:
        raise ValueError(f"Schema incompatível: esperado {VERSAO_SCHEMA}, recebido {schema}.")
    avaliacoes_raw = raw.get("avaliacoes", {})
    if not isinstance(avaliacoes_raw, dict):
        raise ValueError("Campo 'avaliacoes' inválido.")
    avaliacoes = {str(cid): avaliacao_de_dict(d) for cid, d in avaliacoes_raw.items() if isinstance(d, dict)}
    historico = raw.get("historico", []) or []
    if not isinstance(historico, list):
        historico = []
    return avaliacoes, historico
