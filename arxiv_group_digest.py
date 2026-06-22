from __future__ import annotations

import json
from pathlib import Path
import re


DEFAULT_STATE_PATH = Path(".state/arxiv_group_state.json")


def select_group_papers(
    candidates,
    limit: int = 3,
    state_path: Path = DEFAULT_STATE_PATH,
):
    if not candidates:
        return []

    latest_id = _paper_id(candidates[0])
    state = _load_state(state_path)
    sent_ids = (
        set(state.get("sent_ids", []))
        if state.get("latest_id") == latest_id
        else set()
    )
    return [
        paper
        for paper in candidates
        if _paper_id(paper) not in sent_ids
    ][:limit]


def save_group_paper_state(
    candidates,
    sent_papers,
    state_path: Path = DEFAULT_STATE_PATH,
) -> None:
    if not candidates or not sent_papers:
        return

    latest_id = _paper_id(candidates[0])
    state = _load_state(state_path)
    sent_ids = (
        list(state.get("sent_ids", []))
        if state.get("latest_id") == latest_id
        else []
    )
    for paper in sent_papers:
        paper_id = _paper_id(paper)
        if paper_id and paper_id not in sent_ids:
            sent_ids.append(paper_id)

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"latest_id": latest_id, "sent_ids": sent_ids}, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_state(state_path: Path) -> dict:
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _paper_id(paper) -> str:
    match = re.search(r"/abs/([^/?#]+)", paper.link or "")
    if not match:
        return paper.title.casefold()
    return re.sub(r"v\d+$", "", match.group(1))


def build_arxiv_group_digest(settings, papers) -> str:
    if not settings.telegram_group_chat_id:
        return ""
    if not settings.openai_api_key:
        print("Group arXiv digest skipped: OPENAI_API_KEY is required.")
        return ""
    if not papers:
        return "🌌 Resumen diario de astro-ph.GA\n\nNo hay artículos disponibles hoy."

    sections = ["🌌 Resumen diario de astro-ph.GA"]
    for index, paper in enumerate(papers, start=1):
        try:
            summary = _summarize_paper_in_spanish(settings, paper)
        except Exception as exc:
            print(f"Could not summarize arXiv paper '{paper.title}': {exc}")
            summary = (
                "No se pudo generar el resumen en español de este artículo. "
                "Puedes consultar el trabajo completo en el enlace."
            )
        sections.append(
            "\n".join(
                [
                    f"{index}. {paper.title}",
                    summary,
                    f"(read more) {paper.link}",
                ]
            )
        )
    return "\n\n".join(sections)


def _summarize_paper_in_spanish(settings, paper) -> str:
    if not paper.summary:
        return (
            "No se pudo obtener el resumen original de este artículo. "
            "Puedes consultar el trabajo completo en el enlace."
        )

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un divulgador científico especializado en astronomía. "
                    "Explica artículos en español claro para lectores no especialistas. "
                    "No inventes resultados ni información que no aparezca en el resumen."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Resume el siguiente artículo en aproximadamente 200 palabras "
                    "(entre 180 y 220). Usa lenguaje sencillo y explica qué estudia, "
                    "cómo lo estudia, el resultado principal y por qué importa. "
                    "Devuelve solamente el resumen en español.\n\n"
                    f"Título: {paper.title}\n"
                    f"Resumen original: {paper.summary}"
                ),
            },
        ],
        temperature=0.2,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()
