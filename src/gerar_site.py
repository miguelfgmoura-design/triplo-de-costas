"""Gera o site em site/ a partir de dados/stats.json e dados/comentario.md.

Usar --dados-antigos quando a ESPN falhou: o site sai com os dados anteriores
e com o aviso "dados de ontem".
"""
import argparse
import json
import re
import shutil
import unicodedata
from datetime import date, timedelta

from comum import DADOS, FICHEIRO_STATS, RAIZ, ler_json
from desenho import Vista, data_longa, e, momento_longo
from seccoes import MENUS, SIMBOLOS, painel_equipa, peca

SITE = RAIZ / "site"
RECURSOS = RAIZ / "recursos"
FICHEIRO_COMENTARIO = DADOS / "comentario.md"
ARQUIVO_COMENTARIOS = DADOS / "comentarios"
SEM_COMENTARIO = '<p class="nota">O comentário não ficou disponível neste dia. Os números abaixo estão atualizados.</p>'
ICONES = ("icone-180.png", "icone-192.png", "icone-512.png")
NOME_CURTO = "Triplo Costas"

BOLA = (
    '<svg viewBox="-1 -1 2 2" aria-hidden="true"><circle r="1" fill="#eb6834"/>'
    '<g transform="rotate(20)" fill="none" stroke="#1a1a19" stroke-width=".09">'
    '<path d="M-1 0H1M0-1V1"/><path d="M-.72-.72a1.05 1.05 0 0 1 0 1.44M.72-.72a1.05 1.05 0 0 0 0 1.44"/>'
    "</g></svg>"
)


def sem_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower()


def linha_md(texto):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e(texto))


def corpo_md(texto):
    """Converte o pouco de Markdown que o comentário usa, sempre com o texto protegido."""
    html = []
    lista = []
    paragrafo = []

    def fechar():
        if paragrafo:
            html.append(f"<p>{linha_md(' '.join(paragrafo))}</p>")
            paragrafo.clear()
        if lista:
            html.append("<ul>" + "".join(f"<li>{linha_md(i)}</li>" for i in lista) + "</ul>")
            lista.clear()

    for linha in texto.splitlines():
        linha = linha.strip()
        if linha.startswith("- "):
            if paragrafo:
                fechar()
            lista.append(linha[2:])
        elif linha:
            if lista:
                fechar()
            paragrafo.append(linha)
        else:
            fechar()
    fechar()
    return "".join(html)


def ler_comentario(caminho):
    """Devolve as duas partes de um comentário, ou None se faltar ou vier incompleto."""
    if not caminho.exists():
        return None
    partes = re.split(r"^##\s+(.+?)\s*$", caminho.read_text(encoding="utf-8"), flags=re.M)
    seccoes = {sem_acentos(partes[i]): partes[i + 1].strip() for i in range(1, len(partes) - 1, 2)}
    analise = seccoes.get("a analise")
    balneario = seccoes.get("o balneario")
    return (analise, balneario) if analise and balneario else None


def cartoes_comentario(partes):
    return (
        f'<article class="cartao comentario"><h3>A análise</h3>{corpo_md(partes[0])}</article>'
        f'<article class="cartao balneario"><h3>O balneário</h3>{corpo_md(partes[1])}</article>'
    )


def arquivar_comentario(chave):
    """Guarda o comentário de hoje, para se poder voltar a ele nos dias seguintes."""
    if ler_comentario(FICHEIRO_COMENTARIO):
        ARQUIVO_COMENTARIOS.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(FICHEIRO_COMENTARIO, ARQUIVO_COMENTARIOS / f"{chave}.md")


def publicar_comentarios():
    """Escreve um ficheiro por dia, para a página só carregar o dia que se quer ler."""
    pasta = SITE / "comentarios"
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True)
    dias = []
    for ficheiro in sorted(ARQUIVO_COMENTARIOS.glob("*.md")):
        partes = ler_comentario(ficheiro)
        if partes:
            conteudo = json.dumps({"html": cartoes_comentario(partes)}, ensure_ascii=False)
            (pasta / f"{ficheiro.stem}.json").write_text(conteudo, encoding="utf-8", newline="\n")
            dias.append(ficheiro.stem)
    return dias


def rotulo_dia(chave):
    """O comentário sai na manhã a seguir ao último dia com as contas fechadas."""
    return data_longa((date.fromisoformat(chave) + timedelta(days=1)).isoformat())


def seccao_comentario(chave_hoje, dias):
    partes = ler_comentario(ARQUIVO_COMENTARIOS / f"{chave_hoje}.md")
    corpo = cartoes_comentario(partes) if partes else SEM_COMENTARIO
    todos = sorted(set(dias) | {chave_hoje})
    entradas = e(json.dumps([{"d": d, "r": rotulo_dia(d)} for d in todos], ensure_ascii=False, separators=(",", ":")))
    seta = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{}"/></svg>'
    return (
        '<section id="comentario"><h2>Comentário do dia</h2>'
        f'<div class="cn" id="comentario-navega" data-entradas="{entradas}" hidden>'
        f'<button type="button" class="cn-antes" aria-label="Dia anterior">{seta.format("M15 5l-7 7 7 7")}</button>'
        f'<div class="cn-dia" aria-live="polite">{e(rotulo_dia(chave_hoje))}</div>'
        f'<button type="button" class="cn-depois" aria-label="Dia seguinte">{seta.format("M9 5l7 7-7 7")}</button>'
        "</div>"
        '<button type="button" class="cn-recente" id="comentario-recente" hidden>Voltar ao mais recente</button>'
        f'<div id="comentario-texto">{corpo}</div></section>'
    )


def montar_paineis(stats, vista, dias_com_comentario):
    paineis = []
    for n, menu in enumerate(MENUS):
        corpo = "".join(peca(stats, vista, *p) for p in menu["pecas"])
        if menu["id"] == "hoje":
            corpo = seccao_comentario(stats["ultimo_dia_fechado"], dias_com_comentario) + corpo
        elif menu["id"] == "equipa":
            corpo = painel_equipa(stats, vista)
        ativo = " ativo" if n == 0 else ""
        paineis.append(f'<div class="painel{ativo}" id="{menu["id"]}">{corpo}</div>')
    return "".join(paineis)


def montar_pagina(stats, dias_com_comentario, dados_antigos):
    vista = Vista(stats)
    nome = stats["liga"]["nome"]
    menu = "".join(
        f'<a href="#{m["id"]}">{SIMBOLOS[m["id"]]}<span>{e(m["nome"])}</span></a>' for m in MENUS
    )
    paineis = montar_paineis(stats, vista, dias_com_comentario)
    aviso = (
        '<p class="aviso" role="status"><strong>Dados de ontem.</strong> '
        "A ESPN não respondeu esta manhã, por isso estes são os últimos números guardados.</p>"
        if dados_antigos else ""
    )
    estilo = (RECURSOS / "estilo.css").read_text(encoding="utf-8")
    codigo = "".join(
        (RECURSOS / nome_js).read_text(encoding="utf-8") for nome_js in ("graficos.js", "comentarios.js", "menus.js")
    )
    verificacao = stats.get("verificacao") or {}
    alerta_contas = (
        "<p>A soma dos dias ainda não bate certo com o total oficial da ESPN.</p>"
        if verificacao and not verificacao.get("bate_certo") else ""
    )
    return f"""<!doctype html>
<html lang="pt-PT">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(nome)}</title>
<meta name="robots" content="noindex, nofollow">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#f9f9f7">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0d0d0d">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{e(NOME_CURTO)}">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icone-192.png">
<link rel="apple-touch-icon" href="icone-180.png">
<script>document.documentElement.className='com-js'</script>
<style>{estilo}</style>
</head>
<body>
<div class="pagina">
<header class="topo">
<div class="marca">{BOLA}<h1>{e(nome)}</h1></div>
<p class="carimbo">Atualizado <strong>{e(momento_longo(stats["atualizado_em"]))}</strong></p>
<p class="fecho">Pontos fechados até {e(data_longa(stats["ultimo_dia_fechado"]))}</p>
{aviso}
</header>
<main>{paineis}</main>
<footer class="rodape">{alerta_contas}<p>Dados da ESPN Fantasy. Página atualizada automaticamente todas as manhãs.</p></footer>
</div>
<nav class="menus" aria-label="Menus">{menu}</nav>
<script>{codigo}</script>
</body>
</html>
"""


def escrever_manifesto(nome):
    manifesto = {
        "name": nome, "short_name": NOME_CURTO, "lang": "pt-PT",
        "description": "A nossa liga Fantasy NBA, atualizada todas as manhãs.",
        "start_url": "./", "scope": "./", "display": "standalone",
        "background_color": "#0d0d0d", "theme_color": "#0d0d0d",
        "icons": [
            {"src": "icone-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "icone-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "icone-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    (SITE / "manifest.webmanifest").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )


def principal():
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--dados-antigos", action="store_true")
    args = argumentos.parse_args()

    stats = ler_json(FICHEIRO_STATS)
    chave_hoje = stats["ultimo_dia_fechado"]
    arquivar_comentario(chave_hoje)
    SITE.mkdir(exist_ok=True)
    dias = publicar_comentarios()
    pagina = montar_pagina(stats, dias, args.dados_antigos)
    (SITE / "index.html").write_text(pagina, encoding="utf-8", newline="\n")
    escrever_manifesto(stats["liga"]["nome"])
    for icone in ICONES:
        shutil.copy2(RECURSOS / icone, SITE / icone)
    print(
        f"Site gerado: {len(pagina) // 1024} KB. Comentário de hoje: {'sim' if chave_hoje in dias else 'não'}. "
        f"Dias com comentário: {len(dias)}."
    )


if __name__ == "__main__":
    principal()
