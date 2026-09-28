"""
CLI de análise em lote: percorre uma pasta de diagramas e gera um relatório
STRIDE em Markdown para cada um, sem precisar subir o servidor HTTP.

Uso:
    python scripts/analisar_lote.py images/ --saida relatorios/

Pensado para rodar em pipelines de CI/CD: a cada alteração de arquitetura
versionada no repositório, o relatório de ameaças é regenerado.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.deps import _construir_cliente_ia  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.services.report_renderer import renderizar_markdown  # noqa: E402
from app.services.stride_analyzer import StrideAnalyzer  # noqa: E402
from app.utils.image_utils import validar_e_codificar_imagem  # noqa: E402

_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


async def _processar(pasta: Path, saida: Path) -> int:
    settings = get_settings()
    analyzer = StrideAnalyzer(_construir_cliente_ia(settings.usar_cliente_mock))
    saida.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(p for p in pasta.iterdir() if p.suffix.lower() in _MIME)
    if not arquivos:
        print(f"Nenhuma imagem encontrada em {pasta}")
        return 1

    for arq in arquivos:
        mime = _MIME[arq.suffix.lower()]
        b64 = validar_e_codificar_imagem(arq.read_bytes(), mime, settings)
        relatorio, tempo = await analyzer.analisar(b64, mime)
        destino = saida / f"{arq.stem}.md"
        destino.write_text(renderizar_markdown(relatorio, f"Ameaças STRIDE — {arq.name}"), encoding="utf-8")
        print(f"[ok] {arq.name} -> {destino} ({len(relatorio.ameacas)} ameaças, {tempo} ms)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Gera relatórios STRIDE em lote a partir de diagramas.")
    ap.add_argument("pasta", type=Path)
    ap.add_argument("--saida", type=Path, default=Path("relatorios"))
    args = ap.parse_args()
    sys.exit(asyncio.run(_processar(args.pasta, args.saida)))
