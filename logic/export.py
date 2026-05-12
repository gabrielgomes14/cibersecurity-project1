import csv
import io
from dataclasses import dataclass

from data.controls import TEMA_LABELS, Controle
from logic.models import Avaliacao
from logic.scoring import status_individual


@dataclass(frozen=True)
class LinhaRelatorio:
    controle_id: str
    tema: str
    titulo: str
    status: str
    criticidade: str
    responsavel: str
    prazo: str
    observacao: str
    descricao: str


def montar_linhas(controles: list[Controle], avaliacoes: dict[str, Avaliacao]) -> list[LinhaRelatorio]:
    linhas: list[LinhaRelatorio] = []
    for c in controles:
        a = avaliacoes.get(c.id, Avaliacao())
        linhas.append(
            LinhaRelatorio(
                controle_id=c.id,
                tema=TEMA_LABELS[c.tema_id],
                titulo=c.titulo,
                status=status_individual(a if a.status else None),
                criticidade=a.criticidade,
                responsavel=a.responsavel,
                prazo=a.prazo,
                observacao=a.observacao,
                descricao=c.descricao,
            )
        )
    return linhas


def gerar_csv(controles: list[Controle], avaliacoes: dict[str, Avaliacao]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow(["Controle", "Tema", "Título", "Status", "Criticidade", "Responsável", "Prazo", "Observação", "Descrição"])
    for linha in montar_linhas(controles, avaliacoes):
        writer.writerow([
            linha.controle_id,
            linha.tema,
            linha.titulo,
            linha.status,
            linha.criticidade,
            linha.responsavel,
            linha.prazo,
            linha.observacao,
            linha.descricao,
        ])
    return buffer.getvalue().encode("utf-8-sig")
