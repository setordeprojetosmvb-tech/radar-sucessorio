# -*- coding: utf-8 -*-
"""
Robô de busca diária de notícias sobre Direito Sucessório / ITCMD.

O QUE ESTE SCRIPT FAZ:
1. Monta uma busca no Google Notícias (RSS) para cada palavra-chave da lista
   abaixo, restringindo os resultados apenas aos sites confiáveis definidos
   em FONTES_CONFIAVEIS.
2. Baixa os resultados, remove duplicados e remove notícias já publicadas
   antes (guardadas em data/history.json).
3. Gera o arquivo index.html (a página do site) com as notícias organizadas
   por data, mais recentes primeiro.

Você não precisa entender o código para usar o projeto — ele já roda sozinho
todo dia via GitHub Actions (veja .github/workflows/daily.yml).

Se quiser ajustar palavras-chave ou fontes, edite apenas as duas listas
abaixo (KEYWORDS e FONTES_CONFIAVEIS) — o resto do arquivo não precisa ser
tocado.
"""

import json
import html
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO — edite aqui se quiser adicionar/remover termos ou fontes
# ---------------------------------------------------------------------------

KEYWORDS = [
    "ITCMD",
    "Direito das Sucessões",
    "Planejamento Sucessório",
    "Inventário extrajudicial",
    "Holding Familiar",
    "Reforma Tributária ITCMD",
    "STJ sucessões",
    "STF sucessões",
]

# Sites considerados confiáveis. As buscas SÓ trazem resultados desses
# domínios (usando o operador site: do Google).
FONTES_CONFIAVEIS = {
    "stj.jus.br": "STJ",
    "stf.jus.br": "STF",
    "cnj.jus.br": "CNJ",
    "cnbsp.org.br": "Colégio Notarial do Brasil - SP",
    "ibdfam.org.br": "IBDFAM",
    "conjur.com.br": "ConJur",
    "migalhas.com.br": "Migalhas",
    "jota.info": "JOTA",
    "valor.globo.com": "Valor Econômico",
}

# Quantos dias de notícia manter na página inicial
DIAS_NA_HOME = 30

TITULO_SITE = "Radar Sucessório"
SUBTITULO_SITE = "ITCMD, Direito das Sucessões, Planejamento Sucessório e Holding Familiar"

# ---------------------------------------------------------------------------
# Não é necessário editar nada abaixo desta linha
# ---------------------------------------------------------------------------

HISTORY_PATH = "data/history.json"
INDEX_PATH = "index.html"
USER_AGENT = "Mozilla/5.0 (compatible; RadarSucessorioBot/1.0)"


def montar_url_busca(keyword: str) -> str:
    """Monta a URL de busca do Google Notícias restrita às fontes confiáveis."""
    sites = " OR ".join(f"site:{dominio}" for dominio in FONTES_CONFIAVEIS)
    query = f'"{keyword}" ({sites})'
    query_codificada = urllib.parse.quote(query)
    return (
        f"https://news.google.com/rss/search?q={query_codificada}"
        f"&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    )


def identificar_fonte(link: str, titulo_fonte: str) -> str:
    """Tenta identificar de qual site confiável a notícia veio."""
    texto = (link or "") + " " + (titulo_fonte or "")
    for dominio, nome in FONTES_CONFIAVEIS.items():
        if dominio in texto:
            return nome
    return titulo_fonte or "Fonte não identificada"


def buscar_noticias_por_keyword(keyword: str) -> list:
    """Busca e faz o parse do feed RSS do Google Notícias para uma palavra-chave."""
    url = montar_url_busca(keyword)
    resultados = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            conteudo = resp.read()
        raiz = ET.fromstring(conteudo)
        for item in raiz.findall("./channel/item"):
            titulo = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            source_el = item.find("source")
            titulo_fonte = source_el.text if source_el is not None else ""

            if not titulo or not link:
                continue

            fonte = identificar_fonte(link, titulo_fonte or "")

            resultados.append(
                {
                    "titulo": html.unescape(titulo),
                    "link": link,
                    "fonte": fonte,
                    "pub_date_raw": pub_date,
                    "keyword": keyword,
                }
            )
    except Exception as erro:
        print(f"[aviso] Falha ao buscar '{keyword}': {erro}")
    return resultados


def parse_data(pub_date_raw: str) -> str:
    """Converte a data do RSS (RFC 822) para o formato AAAA-MM-DD. Usa hoje se falhar."""
    formatos = ["%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"]
    for fmt in formatos:
        try:
            dt = datetime.strptime(pub_date_raw, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def carregar_historico() -> dict:
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"links_publicados": [], "noticias": []}


def salvar_historico(historico: dict) -> None:
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def gerar_html(noticias: list) -> str:
    """Gera o HTML final do site a partir da lista de notícias (mais recentes primeiro)."""
    limite = (datetime.now(timezone.utc) - timedelta(days=DIAS_NA_HOME)).strftime("%Y-%m-%d")
    noticias_recentes = [n for n in noticias if n["data"] >= limite]
    noticias_recentes.sort(key=lambda n: n["data"], reverse=True)

    # Agrupa por data
    por_data = {}
    for n in noticias_recentes:
        por_data.setdefault(n["data"], []).append(n)

    blocos = []
    for data in sorted(por_data.keys(), reverse=True):
        data_fmt = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
        itens_html = []
        vistos_no_dia = set()
        for n in por_data[data]:
            if n["link"] in vistos_no_dia:
                continue
            vistos_no_dia.add(n["link"])
            itens_html.append(
                f"""
                <li class="noticia">
                  <a href="{html.escape(n['link'])}" target="_blank" rel="noopener noreferrer">
                    {html.escape(n['titulo'])}
                  </a>
                  <div class="meta">
                    <span class="fonte">{html.escape(n['fonte'])}</span>
                    <span class="tema">{html.escape(n['keyword'])}</span>
                  </div>
                </li>"""
            )
        blocos.append(
            f"""
            <section class="dia">
              <h2>{data_fmt}</h2>
              <ul>{''.join(itens_html)}</ul>
            </section>"""
        )

    agora = datetime.now(timezone.utc).strftime("%d/%m/%Y às %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(TITULO_SITE)}</title>
<meta name="description" content="{html.escape(SUBTITULO_SITE)}">
<style>
  :root {{
    --bg: #f7f6f2;
    --card: #ffffff;
    --ink: #1c2b3a;
    --muted: #6b7785;
    --accent: #8a6d3b;
    --accent-line: #0f2b46;
    --border: #e5e1d8;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: 'Georgia', 'Times New Roman', serif;
    line-height: 1.5;
  }}
  header {{
    background: var(--accent-line);
    color: #fff;
    padding: 2.5rem 1.5rem 2rem;
    text-align: center;
  }}
  header h1 {{
    margin: 0 0 .4rem;
    font-size: 1.9rem;
    letter-spacing: .5px;
  }}
  header p {{
    margin: 0;
    color: #cbd6e2;
    font-family: Arial, sans-serif;
    font-size: .95rem;
  }}
  main {{
    max-width: 780px;
    margin: 0 auto;
    padding: 2rem 1.2rem 4rem;
  }}
  .atualizado {{
    font-family: Arial, sans-serif;
    font-size: .8rem;
    color: var(--muted);
    text-align: center;
    margin-bottom: 2rem;
  }}
  .dia h2 {{
    font-size: 1.05rem;
    color: var(--accent);
    border-bottom: 2px solid var(--border);
    padding-bottom: .4rem;
    margin-top: 2.2rem;
    font-family: Arial, sans-serif;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  ul {{ list-style: none; margin: 0; padding: 0; }}
  .noticia {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem 1.1rem;
    margin: .7rem 0;
  }}
  .noticia a {{
    color: var(--ink);
    text-decoration: none;
    font-size: 1.05rem;
    font-weight: bold;
  }}
  .noticia a:hover {{ color: var(--accent); }}
  .meta {{
    margin-top: .5rem;
    font-family: Arial, sans-serif;
    font-size: .78rem;
    color: var(--muted);
  }}
  .fonte {{
    background: #eef1f5;
    padding: .15rem .5rem;
    border-radius: 3px;
    margin-right: .5rem;
  }}
  .tema {{
    color: var(--accent);
  }}
  .vazio {{
    text-align: center;
    color: var(--muted);
    font-family: Arial, sans-serif;
    margin-top: 3rem;
  }}
  footer {{
    text-align: center;
    font-family: Arial, sans-serif;
    font-size: .75rem;
    color: var(--muted);
    padding: 2rem 1rem;
  }}
</style>
</head>
<body>
<header>
  <h1>{html.escape(TITULO_SITE)}</h1>
  <p>{html.escape(SUBTITULO_SITE)}</p>
</header>
<main>
  <div class="atualizado">Atualizado automaticamente em {agora}</div>
  {''.join(blocos) if blocos else '<p class="vazio">Nenhuma notícia encontrada ainda. O robô roda todo dia — volte amanhã.</p>'}
</main>
<footer>
  Curadoria automática a partir de fontes públicas: STJ, STF, CNJ, IBDFAM, ConJur, Migalhas, JOTA, Valor Econômico e Colégio Notarial do Brasil.
</footer>
</body>
</html>
"""


def main():
    historico = carregar_historico()
    links_ja_publicados = set(historico.get("links_publicados", []))
    noticias_salvas = historico.get("noticias", [])

    novas_encontradas = 0
    for keyword in KEYWORDS:
        print(f"Buscando: {keyword}")
        resultados = buscar_noticias_por_keyword(keyword)
        for r in resultados:
            if r["link"] in links_ja_publicados:
                continue
            data = parse_data(r["pub_date_raw"])
            noticias_salvas.append(
                {
                    "titulo": r["titulo"],
                    "link": r["link"],
                    "fonte": r["fonte"],
                    "keyword": r["keyword"],
                    "data": data,
                }
            )
            links_ja_publicados.add(r["link"])
            novas_encontradas += 1

    historico["links_publicados"] = list(links_ja_publicados)
    historico["noticias"] = noticias_salvas
    salvar_historico(historico)

    html_final = gerar_html(noticias_salvas)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f"Concluído. {novas_encontradas} notícia(s) nova(s) adicionada(s).")


if __name__ == "__main__":
    main()
