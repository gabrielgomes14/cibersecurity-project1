from dataclasses import dataclass
from datetime import datetime

from data.controls import TEMAS
from logic.models import Avaliacao
from logic.scoring import resumo_tema, score_geral


@dataclass(frozen=True)
class Snapshot:
    timestamp: str
    rotulo: str
    score_geral: float
    scores_por_tema: dict[str, float]
    avaliados: int


def criar_snapshot(avaliacoes: dict[str, Avaliacao], rotulo: str = "") -> Snapshot:
    todos_ids = [c for grupo in TEMAS.values() for c in [x.id for x in grupo]]
    scores_por_tema = {
        tema_id: resumo_tema(avaliacoes, tema_id, [c.id for c in controles]).score
        for tema_id, controles in TEMAS.items()
    }
    ts = datetime.now().isoformat(timespec="seconds")
    return Snapshot(
        timestamp=ts,
        rotulo=rotulo or ts,
        score_geral=score_geral(avaliacoes, todos_ids),
        scores_por_tema=scores_por_tema,
        avaliados=sum(1 for cid in todos_ids if avaliacoes.get(cid, Avaliacao()).status),
    )


def snapshot_para_dict(s: Snapshot) -> dict[str, object]:
    return {
        "timestamp": s.timestamp,
        "rotulo": s.rotulo,
        "score_geral": s.score_geral,
        "scores_por_tema": dict(s.scores_por_tema),
        "avaliados": s.avaliados,
    }


def _to_float(v: object, default: float = 0.0) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v))
    except (TypeError, ValueError):
        return default


def _to_int(v: object, default: int = 0) -> int:
    if isinstance(v, int):
        return v
    try:
        return int(str(v))
    except (TypeError, ValueError):
        return default


def snapshot_de_dict(d: dict[str, object]) -> Snapshot:
    scores_raw = d.get("scores_por_tema", {})
    scores: dict[str, float] = {}
    if isinstance(scores_raw, dict):
        for k, v in scores_raw.items():
            scores[str(k)] = _to_float(v)
    return Snapshot(
        timestamp=str(d.get("timestamp", "")),
        rotulo=str(d.get("rotulo", "")),
        score_geral=_to_float(d.get("score_geral")),
        scores_por_tema=scores,
        avaliados=_to_int(d.get("avaliados")),
    )
