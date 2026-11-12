"""Gera trilha.html: os notebooks executados da trilha num HTML dinâmico de arquivo único, com as cores preservadas.

Uso (na pasta AI_use_cases, depois de executar os notebooks):
    python gerar_trilha_html.py            # escreve trilha.html ao lado deste arquivo
    python gerar_trilha_html.py --saida /outro/caminho.html

O que o HTML tem:
    * saídas com as cores ANSI do prettifier e do logger (convertidas pelo rich), código com realce do pygments
    * índice agrupado por nível, com as seções do notebook atual; cupom de garantias (o que cada notebook garante e
      o que ainda quebra, riscado quando um notebook adiante resolve)
    * modo "só pegadinhas" (tecla s), código recolhível (c), tema claro/escuro (t), j/k entre seções, n/p entre notebooks
    * nenhum recurso externo: abre offline com duplo clique; links para outros notebooks viram âncoras na própria página

Dependências: nbformat, rich, pygments e markdown-it-py (as duas últimas já vêm com o rich).
"""
from __future__ import annotations

import argparse
import html
import io
import json
import posixpath
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import nbformat
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from rich.console import Console
from rich.terminal_theme import TerminalTheme
from rich.text import Text

RAIZ = Path(__file__).resolve().parent
NIVEIS = {"01_basico": "Básico", "02_intermediario": "Intermediário", "03_avancado": "Avançado"}

# O que cada notebook garante e o que deixa quebrado; o número diz qual notebook resolve (None: fica em aberto).
CUPOM = {
    "01": ("conversa com a API", [("quantidade vem como texto", "02")]),
    "02": ("contrato: campos e tipos", [("unidade aceita qualquer texto", "03")]),
    "03": ("vocabulário fechado e escopo", [("valores absurdos passam", "05"), ("modelo não sabe preços", "04")]),
    "04": ("dados reais, execução segura", [("dinheiro em float", "07")]),
    "05": ("regras de negócio e retry", [("regras fora do contrato", "07")]),
    "06": ("intenção vira rota", [("permissões por perfil", "08"), ("valor desconhecido derruba o pedido", "08")]),
    "07": ("regras no contrato, com contexto", [("quem pode o quê", "08")]),
    "08": ("permissões, negar por padrão", [("fluxo opaco: custo, tempo, histórico", "09")]),
    "09": ("custo, tempo e histórico com orçamento", [("configuração externa sem validação", "10")]),
    "10": ("pipeline testável, configuração validada",
           [("cache sem prazo de validade", None), ("testes simulados não medem o modelo", None)]),
}

TERMINAL = TerminalTheme(
    (24, 28, 32), (214, 218, 222),
    [(0, 0, 0), (205, 49, 49), (13, 188, 121), (229, 229, 16), (36, 114, 200), (188, 63, 188), (17, 168, 205), (229, 229, 229)],
    [(102, 102, 102), (241, 76, 76), (35, 209, 139), (245, 245, 67), (59, 142, 234), (214, 112, 214), (41, 184, 219), (229, 229, 229)],
)
LARGURA_TERMINAL = 112
MD = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
REALCE_CLARO = HtmlFormatter(style="xcode", nowrap=True)
REALCE_ESCURO = HtmlFormatter(style="github-dark", nowrap=True)
CABECALHO_MD = re.compile(r"^(#{1,3}) ", re.M)


@dataclass
class Notebook:
    numero: str
    nivel: str
    caminho: Path
    titulo: str = ""
    secoes: list[tuple[str, str]] = field(default_factory=list)   # (id, texto) dos h2/h3
    blocos: list[str] = field(default_factory=list)


def slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", "", texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-") or "secao"


def ansi_para_html(ansi: str) -> str:
    console = Console(record=True, file=io.StringIO(), width=LARGURA_TERMINAL, force_terminal=True,
                      color_system="256", markup=False, emoji=False, highlight=False)
    console.print(Text.from_ansi(ansi.rstrip("\n")), soft_wrap=True)
    return console.export_html(theme=TERMINAL, inline_styles=True, code_format="{code}")


def texto_da_saida(saida) -> str | None:
    if saida.output_type == "stream":
        return saida.text
    if saida.output_type in ("execute_result", "display_data"):
        return saida.data.get("text/plain")
    if saida.output_type == "error":
        return "\n".join(saida.traceback)
    return None


def reescrever_links(corpo: str, pasta_nb: str, ancoras: dict[str, str]) -> str:
    """Links relativos do notebook passam a valer a partir de AI_use_cases/; links para notebooks da trilha viram âncoras."""
    def trocar(m: re.Match) -> str:
        alvo = m.group(1)
        if re.match(r"(https?:|mailto:|#)", alvo):
            return m.group(0)
        caminho, _, fragmento = alvo.partition("#")
        relativo = posixpath.normpath(posixpath.join(pasta_nb, caminho))
        if relativo in ancoras:
            return f'href="#{ancoras[relativo]}"'
        return f'href="{relativo}{"#" + fragmento if fragmento else ""}"'
    return re.sub(r'href="([^"]+)"', trocar, corpo)


def pedacos_markdown(fonte: str) -> list[str]:
    """Quebra uma célula markdown nos cabeçalhos, para cada parte ser marcada (pegadinha ou não) por conta própria."""
    inicios = [m.start() for m in CABECALHO_MD.finditer(fonte)]
    if not inicios or inicios[0] != 0:
        inicios = [0, *inicios]
    return [fonte[a:b].strip("\n") for a, b in zip(inicios, [*inicios[1:], len(fonte)]) if fonte[a:b].strip()]


def montar_notebook(nb_info: Notebook, ancoras: dict[str, str]) -> None:
    nb = nbformat.read(nb_info.caminho, as_version=4)
    pasta_nb = nb_info.caminho.parent.name
    prefixo = f"nb-{nb_info.numero}"
    usados: set[str] = set()
    pegadinha = False
    for celula in nb.cells:
        if celula.cell_type == "markdown":
            for pedaco in pedacos_markdown(celula.source):
                cabecalho = CABECALHO_MD.match(pedaco)
                classes = ["md"]
                if cabecalho:
                    pegadinha = "O que ainda quebra" in pedaco.splitlines()[0]
                    if len(cabecalho.group(1)) == 1:
                        classes.append("titulo")
                if pegadinha:
                    classes.append("pegadinha")
                corpo = reescrever_links(MD.render(pedaco), pasta_nb, ancoras)

                def com_id(m: re.Match) -> str:
                    nivel, conteudo = int(m.group(1)), m.group(2)
                    if nivel == 1:
                        nb_info.titulo = re.sub(r"<[^>]+>", "", conteudo)
                        return f'<h1 id="{prefixo}">{conteudo}</h1>'
                    base = ident = f"{prefixo}-{slug(conteudo)}"
                    n = 2
                    while ident in usados:
                        ident, n = f"{base}-{n}", n + 1
                    usados.add(ident)
                    nb_info.secoes.append((ident, re.sub(r"<[^>]+>", "", conteudo)))
                    return f'<h{nivel} id="{ident}" class="secao">{conteudo}</h{nivel}>'

                corpo = re.sub(r"<h([1-3])>(.*?)</h\1>", com_id, corpo, flags=re.S)
                nb_info.blocos.append(f'<section class="{" ".join(classes)}">{corpo}</section>')
            continue
        if celula.cell_type != "code" or not celula.source.strip():
            continue
        api = "skip-execution" in celula.metadata.get("tags", [])
        contagem = celula.get("execution_count")
        if api:
            rotulo = f"[{contagem}] API, executada com o .env" if contagem else "API, não executada (precisa do .env)"
        else:
            rotulo = f"[{contagem}]" if contagem else ""
        saidas = "".join(f'<pre class="saida">{ansi_para_html(t)}</pre>'
                         for t in (texto_da_saida(s) for s in celula.get("outputs", [])) if t and t.strip())
        classes = ("celula" + (" api" if api else "") + (" nao-executada" if api and not contagem else "")
                   + (" pegadinha" if pegadinha else ""))
        nb_info.blocos.append(
            f'<div class="{classes}"><div class="cab">'
            f'<button class="dobrar" aria-expanded="true">código</button>'
            f'<span class="exec">{html.escape(rotulo)}</span>'
            f'<button class="copiar">copiar</button></div>'
            f'<pre class="codigo"><code>{highlight(celula.source, PythonLexer(), REALCE_CLARO)}</code></pre>'
            f'{saidas}</div>'
        )


def gerar(saida: Path) -> list[Notebook]:
    notebooks = []
    for caminho in sorted(RAIZ.glob("0*/*.ipynb")):
        numero = caminho.name[:2]
        notebooks.append(Notebook(numero=numero, nivel=NIVEIS.get(caminho.parent.name, caminho.parent.name),
                                  caminho=caminho))
    ancoras = {f"{n.caminho.parent.name}/{n.caminho.name}": f"nb-{n.numero}" for n in notebooks}
    for nb_info in notebooks:
        montar_notebook(nb_info, ancoras)

    indice, nivel_atual = [], None
    for n in notebooks:
        if n.nivel != nivel_atual:
            if nivel_atual is not None:
                indice.append("</ol>")
            indice.append(f'<p class="nivel">{html.escape(n.nivel)}</p><ol>')
            nivel_atual = n.nivel
        secoes = "".join(f'<li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in n.secoes)
        indice.append(f'<li class="nb-item" data-nb="{n.numero}"><a class="nb-link" href="#nb-{n.numero}">'
                      f'{html.escape(n.titulo)}</a><ol class="secoes">{secoes}</ol></li>')
    indice.append("</ol>")

    artigos = "\n".join(f'<article class="nb" id="artigo-{n.numero}" data-nb="{n.numero}">' + "\n".join(n.blocos)
                        + "</article>" for n in notebooks)
    dados_cupom = {k: {"ganho": g, "quebras": [[t, r] for t, r in q]} for k, (g, q) in CUPOM.items()}
    nomes = {n.numero: n.titulo for n in notebooks}
    pagina = (MODELO
              .replace("{{estilo_codigo}}", REALCE_CLARO.get_style_defs(".codigo") + "\n"
                       + REALCE_ESCURO.get_style_defs(':root[data-tema="escuro"] .codigo'))
              .replace("{{indice}}", "\n".join(indice))
              .replace("{{artigos}}", artigos)
              .replace("{{total}}", str(len(notebooks)))
              .replace("{{cupom}}", json.dumps(dados_cupom, ensure_ascii=False))
              .replace("{{nomes}}", json.dumps(nomes, ensure_ascii=False)))
    saida.write_text(pagina, encoding="utf-8")
    return notebooks


MODELO = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trilha AI_use_cases — LLM com contrato</title>
<style>
:root {
  --papel: #F1F4EF; --papel-2: #E3E8E1; --tinta: #1E2A32; --tinta-suave: #52606A; --linha: #C9D1C6;
  --manjericao: #2E7A4E; --tomate: #C23B2A; --termica: #4A4D68; --cupom: #FCFCFA; --codigo-fundo: #FBFCFA; --terminal: #181C20;
  --texto: "Seravek", "Gill Sans Nova", "Segoe UI", "Ubuntu", "Helvetica Neue", Arial, sans-serif;
  --titulo: "Bahnschrift Condensed", "Bahnschrift", "Avenir Next Condensed", "Roboto Condensed", "Arial Narrow", sans-serif;
  --mono: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, "DejaVu Sans Mono", monospace;
}
:root[data-tema="escuro"] {
  --papel: #15191C; --papel-2: #1D2226; --tinta: #DDE3E0; --tinta-suave: #98A4A0; --linha: #2E363B;
  --manjericao: #5BBF85; --tomate: #F07A68; --termica: #B9BBD6; --cupom: #20262A; --codigo-fundo: #1E2428; --terminal: #0F1215;
}
* { box-sizing: border-box; }
html { scroll-padding-top: 1rem; }
body { margin: 0; background: var(--papel); color: var(--tinta); font: 16px/1.6 var(--texto); }
:focus-visible { outline: 3px solid var(--manjericao); outline-offset: 2px; }
.layout { display: grid; grid-template-columns: 19rem minmax(0, 1fr); }
aside.lateral { position: sticky; top: 0; height: 100vh; overflow-y: auto; padding: 1.2rem 1rem 2rem;
  background: var(--papel-2); border-right: 1px solid var(--linha); font-size: .85rem; }
.marca { font-family: var(--titulo); font-stretch: condensed; font-weight: 700; font-size: 1.35rem; line-height: 1.1; margin: 0 0 .2rem; }
.sub { color: var(--tinta-suave); font-size: .78rem; margin: 0 0 .9rem; }
.ferramentas { display: flex; flex-wrap: wrap; gap: .35rem; margin: 0 0 1rem; }
button { font: 600 .78rem var(--texto); color: var(--tinta); background: transparent; border: 1px solid var(--linha);
  border-radius: 4px; padding: .25rem .55rem; cursor: pointer; }
button:hover { border-color: var(--tinta-suave); }
button[aria-pressed="true"] { background: var(--tinta); color: var(--papel); border-color: var(--tinta); }
aside .nivel { font-family: var(--titulo); font-stretch: condensed; font-weight: 700; font-size: .95rem; margin: .9rem 0 .2rem; color: var(--tinta-suave); }
aside ol { list-style: none; margin: 0; padding: 0; }
aside a { color: var(--tinta-suave); text-decoration: none; display: block; padding: .15rem .45rem; border-left: 3px solid transparent; }
aside .nb-link { color: var(--tinta); font-weight: 600; }
aside .secoes { display: none; padding-left: .7rem; font-size: .78rem; }
aside .nb-item.atual .secoes { display: block; }
aside .nb-item.atual > .nb-link { border-left-color: var(--manjericao); }
aside .secoes a.ativo { color: var(--tinta); border-left-color: var(--manjericao); }
details.cupom { margin-top: 1.2rem; }
details.cupom summary { cursor: pointer; font-family: var(--titulo); font-stretch: condensed; font-weight: 700; font-size: .95rem; color: var(--tinta-suave); }
.fita { background: var(--cupom); color: var(--termica); font: 11.5px/1.45 var(--mono); padding: .8rem .75rem 1rem; margin-top: .5rem;
  border: 1px dashed var(--linha); }
.fita .item { margin: .4rem 0; }
.fita .nb { color: var(--tinta); font-weight: 700; }
.fita .ganho { color: var(--manjericao); }
.fita .quebra { color: var(--tomate); }
.fita .quebra.resolvida { color: var(--tinta-suave); text-decoration: line-through; }
.fita .quebra small { display: inline-block; margin-left: .3rem; text-decoration: none; color: var(--termica); }
.fita .totais { display: flex; justify-content: space-between; border-top: 1px dashed var(--termica); margin-top: .5rem; padding-top: .4rem; }
main { padding: 2rem clamp(1rem, 4vw, 3.5rem) 6rem; max-width: 66rem; }
article.nb { padding-bottom: 3rem; margin-bottom: 3rem; border-bottom: 2px solid var(--linha); }
section.md { max-width: 46rem; }
h1, h2, h3 { font-family: var(--titulo); font-stretch: condensed; line-height: 1.1; }
h1 { font-size: clamp(2rem, 4vw, 2.9rem); margin: 0 0 1rem; }
h2 { font-size: 1.7rem; margin: 2.2rem 0 .8rem; }
h3 { font-size: 1.25rem; margin: 1.6rem 0 .6rem; }
a { color: var(--manjericao); }
code { font-family: var(--mono); font-size: .88em; }
p code, li code, td code { background: var(--papel-2); padding: .05em .3em; border-radius: 3px; }
blockquote { margin: 1rem 0; padding: .2rem 1rem; border-left: 4px solid var(--linha); color: var(--tinta-suave); }
table { border-collapse: collapse; margin: 1rem 0; font-size: .92rem; }
th, td { text-align: left; padding: .4rem .8rem .4rem 0; border-bottom: 1px solid var(--linha); vertical-align: top; }
.celula { margin: 1rem 0 1.4rem; }
.pegadinha.celula, section.pegadinha { border-left: 3px solid var(--tomate); padding-left: .8rem; margin-left: -.95rem; }
.cab { display: flex; align-items: center; gap: .5rem; margin-bottom: .25rem; }
.cab .exec { font-family: var(--mono); font-size: .75rem; color: var(--tinta-suave); flex: 1; }
.celula.api .cab .exec { color: var(--manjericao); }
.celula.api.nao-executada .cab .exec { color: var(--tomate); }
.cab button { font-size: .72rem; padding: .1rem .5rem; }
pre { margin: 0; overflow-x: auto; font: 13px/1.45 var(--mono); }
pre.codigo { background: var(--codigo-fundo); border: 1px solid var(--linha); border-radius: 6px; padding: .8rem 1rem; }
.celula.oculta pre.codigo { display: none; }
pre.saida { background: var(--terminal); color: #D6DADE; border-radius: 6px; padding: .7rem 1rem; margin-top: .4rem; }
body.so-pegadinhas article.nb > :not(.pegadinha):not(.titulo) { display: none; }
body.so-pegadinhas section.titulo > :not(h1) { display: none; }
body.so-pegadinhas article.nb { padding-bottom: 1.5rem; margin-bottom: 1.5rem; }
.dica { font-size: .74rem; color: var(--tinta-suave); margin-top: 1rem; line-height: 1.8; }
kbd { font: .72rem var(--mono); border: 1px solid var(--linha); border-bottom-width: 2px; border-radius: 3px; padding: 0 .3em; }
@media (max-width: 900px) {
  .layout { display: block; }
  aside.lateral { position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--linha); }
  .pegadinha.celula, section.pegadinha { margin-left: 0; }
}
@media print {
  aside.lateral, .cab button { display: none; }
  .layout { display: block; }
  pre { white-space: pre-wrap; word-break: break-word; }
  .celula.oculta pre.codigo { display: block; }
  article.nb { break-before: page; }
}
{{estilo_codigo}}
</style>
</head>
<body>
<div class="layout">
<aside class="lateral" aria-label="Navegação da trilha">
  <p class="marca">Trilha AI_use_cases</p>
  <p class="sub">{{total}} notebooks executados, do JSON solto ao pipeline testável</p>
  <div class="ferramentas">
    <button id="bt-pegadinhas" aria-pressed="false">só pegadinhas</button>
    <button id="bt-codigo" aria-pressed="false">ocultar código</button>
    <button id="bt-tema">tema escuro</button>
  </div>
  <nav aria-label="Índice">{{indice}}</nav>
  <details class="cupom" open>
    <summary>Cupom de garantias</summary>
    <div class="fita" id="fita"></div>
  </details>
  <p class="dica"><kbd>n</kbd> <kbd>p</kbd> próximo e anterior notebook<br><kbd>j</kbd> <kbd>k</kbd> próxima e anterior seção<br>
  <kbd>s</kbd> só pegadinhas<br><kbd>c</kbd> mostra e oculta o código<br><kbd>t</kbd> alterna o tema<br>Ctrl+F busca na trilha inteira</p>
</aside>
<main>
{{artigos}}
</main>
</div>
<script>
"use strict";
const CUPOM = {{cupom}};
const NOMES = {{nomes}};
const raiz = document.documentElement;
const guardar = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
const ler = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };

/* ---------- tema ---------- */
function aplicarTema(escuro) {
  raiz.dataset.tema = escuro ? "escuro" : "claro";
  document.getElementById("bt-tema").textContent = escuro ? "tema claro" : "tema escuro";
  guardar("trilha-tema", escuro ? "escuro" : "claro");
}
aplicarTema(ler("trilha-tema") === "escuro");
document.getElementById("bt-tema").addEventListener("click", () => aplicarTema(raiz.dataset.tema !== "escuro"));

/* ---------- código ---------- */
const celulas = [...document.querySelectorAll(".celula")];
function dobrar(celula, ocultar) {
  celula.classList.toggle("oculta", ocultar);
  celula.querySelector(".dobrar").setAttribute("aria-expanded", String(!ocultar));
}
celulas.forEach(c => {
  c.querySelector(".dobrar").addEventListener("click", () => dobrar(c, !c.classList.contains("oculta")));
  c.querySelector(".copiar").addEventListener("click", async (e) => {
    const botao = e.currentTarget;
    try { await navigator.clipboard.writeText(c.querySelector("pre.codigo").innerText); botao.textContent = "copiado"; }
    catch (err) { botao.textContent = "sem permissão"; }
    setTimeout(() => { botao.textContent = "copiar"; }, 1400);
  });
});
const btCodigo = document.getElementById("bt-codigo");
btCodigo.addEventListener("click", () => {
  const ocultar = btCodigo.getAttribute("aria-pressed") !== "true";
  celulas.forEach(c => dobrar(c, ocultar));
  btCodigo.setAttribute("aria-pressed", String(ocultar));
  btCodigo.textContent = ocultar ? "mostrar código" : "ocultar código";
});

/* ---------- só pegadinhas ---------- */
const btPegadinhas = document.getElementById("bt-pegadinhas");
btPegadinhas.addEventListener("click", () => {
  const ligar = btPegadinhas.getAttribute("aria-pressed") !== "true";
  const ancora = artigos[notebookAtual()];
  document.body.classList.toggle("so-pegadinhas", ligar);
  btPegadinhas.setAttribute("aria-pressed", String(ligar));
  ancora?.scrollIntoView();
});

/* ---------- posição: notebook e seção atuais ---------- */
const artigos = [...document.querySelectorAll("article.nb")];
const titulosSecao = () => [...document.querySelectorAll("main h1[id], main h2.secao, main h3.secao")].filter(h => h.offsetParent);
const noFim = () => window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
function indiceNoTopo(elementos) {
  let atual = 0;
  elementos.forEach((el, i) => { if (el.getBoundingClientRect().top < 120) atual = i; });
  return noFim() ? elementos.length - 1 : atual;
}
const notebookAtual = () => indiceNoTopo(artigos);

function renderCupom(numeroAtual) {
  const fita = document.getElementById("fita");
  const atual = Number(numeroAtual);
  let html = "", garantias = 0, abertas = 0;
  // chaves "10" (inteiro) viriam antes de "01" num objeto JS: ordena explicitamente
  for (const nb of Object.keys(CUPOM).sort()) {
    const info = CUPOM[nb];
    if (Number(nb) > atual) continue;
    garantias++;
    html += `<div class="item"><div class="nb">${nb} ${NOMES[nb]?.replace(/^\d+\s*—\s*/, "") ?? ""}</div>`;
    html += `<div class="ganho">+ ${info.ganho}</div>`;
    for (const [texto, resolve] of info.quebras) {
      const resolvida = resolve !== null && Number(resolve) <= atual;
      if (!resolvida) abertas++;
      const nota = resolve === null ? "em aberto" : (resolvida ? `ok em ${resolve}` : `→ ${resolve}`);
      html += `<div class="quebra${resolvida ? " resolvida" : ""}">− ${texto}<small>${nota}</small></div>`;
    }
    html += "</div>";
  }
  html += `<div class="totais"><span>garantias</span><span>${garantias}</span></div>`;
  html += `<div class="totais"><span>em aberto</span><span>${abertas}</span></div>`;
  fita.innerHTML = html;
}

const itensIndice = [...document.querySelectorAll("aside .nb-item")];
const linksSecao = new Map([...document.querySelectorAll("aside .secoes a")].map(a => [a.getAttribute("href").slice(1), a]));
let ultimoNb = null, agendado = false;
function atualizarPosicao() {
  agendado = false;
  const nb = artigos[notebookAtual()]?.dataset.nb;
  if (nb !== ultimoNb) {
    itensIndice.forEach(li => li.classList.toggle("atual", li.dataset.nb === nb));
    renderCupom(nb);
    ultimoNb = nb;
  }
  const titulos = titulosSecao();
  const id = titulos[indiceNoTopo(titulos)]?.id;
  linksSecao.forEach((a, chave) => a.classList.toggle("ativo", chave === id));
}
window.addEventListener("scroll", () => { if (!agendado) { agendado = true; requestAnimationFrame(atualizarPosicao); } }, { passive: true });
atualizarPosicao();
if (window.matchMedia("(max-width: 900px)").matches) document.querySelector("details.cupom").removeAttribute("open");

/* ---------- teclado ---------- */
function irPara(lista, delta) {
  const alvo = lista[Math.max(0, Math.min(lista.length - 1, indiceNoTopo(lista) + delta))];
  alvo?.scrollIntoView();
}
document.addEventListener("keydown", (e) => {
  if (e.target.matches("input, textarea, select") || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.target.matches("button") && (e.key === " " || e.key === "Enter")) return;
  const acoes = {
    n: () => irPara(artigos, 1), p: () => irPara(artigos, -1),
    j: () => irPara(titulosSecao(), 1), k: () => irPara(titulosSecao(), -1),
    s: () => btPegadinhas.click(), c: () => btCodigo.click(), t: () => document.getElementById("bt-tema").click(),
  };
  if (!(e.key in acoes)) return;
  acoes[e.key]();
  e.preventDefault();
});
</script>
</body>
</html>
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera trilha.html a partir dos notebooks executados da trilha")
    parser.add_argument("--saida", type=Path, default=RAIZ / "trilha.html")
    args = parser.parse_args()
    gerados = gerar(args.saida)
    print(f"trilha.html: {len(gerados)} notebooks -> {args.saida}")
