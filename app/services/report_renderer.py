"""
Renderiza um `RelatorioSTRIDE` como documento Markdown pronto para ser
anexado a um pull request, wiki ou ticket de segurança.

Transformar a saída estruturada (JSON) em um artefato legível por humanos é
o que fecha o ciclo de automação: o time de segurança não precisa consumir
a API manualmente — pode gerar o relatório em CI a cada mudança de
arquitetura (ver scripts/analisar_lote.py).
"""

from app.schemas.threat_model import RelatorioSTRIDE

_ICONE = {"Crítica": "🔴", "Alta": "🟠", "Média": "🟡", "Baixa": "🟢"}


def renderizar_markdown(relatorio: RelatorioSTRIDE, titulo: str = "Relatório de Ameaças STRIDE") -> str:
    linhas = [f"# {titulo}", "", "## Resumo da arquitetura", "", relatorio.resumo_arquitetura, ""]

    if relatorio.componentes:
        linhas += ["## Componentes identificados", "", "| Componente | Tipo | Descrição |", "|---|---|---|"]
        for c in relatorio.componentes:
            linhas.append(f"| {c.nome} | {c.tipo} | {c.descricao or '-'} |")
        linhas.append("")

    linhas += ["## Visão geral", "", "| Categoria STRIDE | Ameaças |", "|---|:-:|"]
    for categoria, qtd in relatorio.contagem_por_categoria().items():
        linhas.append(f"| {categoria} | {qtd} |")
    linhas += ["", "| Severidade | Ameaças |", "|---|:-:|"]
    for sev, qtd in relatorio.contagem_por_severidade().items():
        linhas.append(f"| {_ICONE[sev]} {sev} | {qtd} |")
    linhas += ["", "## Ameaças (da mais crítica para a menos crítica)", ""]

    for i, a in enumerate(relatorio.ameacas_ordenadas_por_severidade(), start=1):
        linhas += [
            f"### {i}. {_ICONE[a.severidade.value]} {a.titulo}",
            "",
            f"- **Categoria:** {a.categoria.value}",
            f"- **Componente afetado:** {a.componente_afetado}",
            f"- **Severidade:** {a.severidade.value}",
            "",
            a.descricao,
            "",
        ]
        if a.mitigacoes:
            linhas.append("**Mitigações recomendadas:**")
            linhas += [f"- {m}" for m in a.mitigacoes]
            linhas.append("")

    return "\n".join(linhas)
