"""Peças do avançado (07–09) reunidas para o pipeline do notebook 10. Mesma lógica dos notebooks, sem os exemplos."""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import Flag, StrEnum, auto
from types import MappingProxyType
from typing import Annotated, Mapping

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PrivateAttr, ValidationInfo, model_validator

from contrato import ListaDeCompras, Unidade

# ---------------------------------------------------------------- 07: contrato com contexto
FATOR = {
    (Unidade.G, Unidade.KG): Decimal("0.001"), (Unidade.KG, Unidade.G): Decimal(1000),
    (Unidade.ML, Unidade.L): Decimal("0.001"), (Unidade.L, Unidade.ML): Decimal(1000),
}


def converter(quantidade: Decimal, de: Unidade, para: Unidade) -> Decimal:
    if de is para:
        return quantidade
    try:
        return quantidade * FATOR[(de, para)]
    except KeyError:
        raise ValueError(f"não dá para converter {de} em {para}") from None


@dataclass(frozen=True)
class ContextoPedido:
    orcamento: Decimal
    precos: Mapping[str, tuple[Decimal, Unidade]]
    despensa: Mapping[str, tuple[Decimal, Unidade]] = field(default_factory=dict)
    limite_por_pessoa: Mapping[Unidade, Decimal] = field(default_factory=lambda: {
        Unidade.G: Decimal(400), Unidade.KG: Decimal("0.4"), Unidade.ML: Decimal(300),
        Unidade.L: Decimal("0.3"), Unidade.UN: Decimal(4),
    })

    def __post_init__(self):
        for nome in ("precos", "despensa", "limite_por_pessoa"):
            object.__setattr__(self, nome, MappingProxyType(dict(getattr(self, nome))))


class ListaComContexto(ListaDeCompras):
    _custo: Decimal | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def regras_com_contexto(self, info: ValidationInfo):
        ctx = info.context
        if not isinstance(ctx, ContextoPedido):
            raise ValueError("contexto obrigatório: valide com context=ContextoPedido(...)")
        problemas, total = [], Decimal(0)
        for item in self.ingredientes:
            quantidade = Decimal(str(item.quantidade))
            limite = ctx.limite_por_pessoa[item.unidade] * self.porcoes
            if quantidade > limite:
                problemas.append(f"{item.nome}: {quantidade} {item.unidade} passa do limite de {limite} {item.unidade}")
                continue
            falta = quantidade
            if item.nome in ctx.despensa:
                tem, unidade_casa = ctx.despensa[item.nome]
                falta = max(Decimal(0), quantidade - converter(tem, unidade_casa, item.unidade))
            if falta == 0:
                continue
            if item.nome not in ctx.precos:
                problemas.append(f"{item.nome}: sem preço na tabela")
                continue
            preco, unidade_venda = ctx.precos[item.nome]
            try:
                total += preco * converter(falta, item.unidade, unidade_venda)
            except ValueError as ex:
                problemas.append(f"{item.nome}: {ex}")
        total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if total > ctx.orcamento:
            problemas.append(f"custo R$ {total} passa do orçamento de R$ {ctx.orcamento}")
        if problemas:
            raise ValueError("; ".join(problemas))
        self._custo = total
        return self

    @property
    def custo(self) -> Decimal:
        return self._custo


# ---------------------------------------------------------------- 08: capacidades e políticas
class Perfil(StrEnum):
    VISITANTE = "visitante"
    CLIENTE = "cliente"


class Capacidade(Flag):
    LER_PRECOS = auto()
    LER_DESPENSA = auto()
    FINALIZAR_PEDIDO = auto()


class Ferramenta(StrEnum):
    CONSULTAR_PRECO = "consultar_preco"
    VERIFICAR_DESPENSA = "verificar_despensa"
    FINALIZAR_PEDIDO = "finalizar_pedido"


PERMISSOES: dict[Perfil, Capacidade] = {
    Perfil.VISITANTE: Capacidade.LER_PRECOS,
    Perfil.CLIENTE: Capacidade.LER_PRECOS | Capacidade.LER_DESPENSA | Capacidade.FINALIZAR_PEDIDO,
}
CAPACIDADE_EXIGIDA: dict[Ferramenta, Capacidade] = {
    Ferramenta.CONSULTAR_PRECO: Capacidade.LER_PRECOS,
    Ferramenta.VERIFICAR_DESPENSA: Capacidade.LER_DESPENSA,
    Ferramenta.FINALIZAR_PEDIDO: Capacidade.FINALIZAR_PEDIDO,
}
EXIGE_CONFIRMACAO = Capacidade.FINALIZAR_PEDIDO


class Decisao(StrEnum):
    PERMITIR = "permitir"
    NEGAR = "negar"
    CONFIRMAR = "confirmar_com_humano"


def decidir(perfil: Perfil, nome_ferramenta: str) -> tuple[Decisao, str]:
    try:
        ferramenta = Ferramenta(nome_ferramenta)
    except ValueError:
        return Decisao.NEGAR, f"ferramenta desconhecida: {nome_ferramenta}"
    exigida = CAPACIDADE_EXIGIDA.get(ferramenta)
    if exigida is None:
        return Decisao.NEGAR, f"{ferramenta} sem capacidade mapeada"
    if perfil not in PERMISSOES or exigida not in PERMISSOES[perfil]:
        return Decisao.NEGAR, f"perfil {perfil} não tem {exigida.name}"
    if exigida & EXIGE_CONFIRMACAO:
        return Decisao.CONFIRMAR, "ação irreversível"
    return Decisao.PERMITIR, "ok"


class IntencaoAberta(StrEnum):
    RECEITA = "receita"
    PRECO = "preco"
    FORA_DO_ESCOPO = "fora_do_escopo"
    DESCONHECIDO = "desconhecido"


VALORES_CONHECIDOS = {membro.value for membro in IntencaoAberta}
INTENCOES_VISTAS_DESCONHECIDAS: list[str] = []


def aceitar_desconhecido(valor):
    if isinstance(valor, str) and valor not in VALORES_CONHECIDOS:
        INTENCOES_VISTAS_DESCONHECIDAS.append(valor)
        return IntencaoAberta.DESCONHECIDO
    return valor


class Classificacao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intencao: Annotated[IntencaoAberta, BeforeValidator(aceitar_desconhecido)]
    confianca: float = Field(ge=0, le=1)
    prato: str | None = None
    ingrediente: str | None = None


# ---------------------------------------------------------------- 09: uso e custo
@dataclass
class Uso:
    chamadas: int = 0
    tokens_entrada: int = 0
    tokens_saida: int = 0

    def registrar(self, usage) -> None:
        self.chamadas += 1
        self.tokens_entrada += usage.prompt_tokens
        self.tokens_saida += usage.completion_tokens

    def custo(self, preco_entrada_por_milhao: Decimal, preco_saida_por_milhao: Decimal) -> Decimal:
        return (self.tokens_entrada * preco_entrada_por_milhao + self.tokens_saida * preco_saida_por_milhao) / Decimal(1_000_000)
