# Data & Classes — Pydantic, Dataclass e Enum

Estudo completo das três ferramentas que modelam dados em Python, com foco em **arquivos de configuração**,
**camadas de dados de APIs e aplicações** e **casos de uso com LLMs**.

Cada módulo tem uma teoria (`.md`) e três notebooks (básico → intermediário → avançado). Todos os notebooks foram
**executados** e estão salvos com as saídas.

```
data-and-classes/
├── README.md                     ← você está aqui
├── requirements.txt
├── pydantic/
│   ├── pydantic.md               teoria: fronteira de confiança, pydantic-core, lax/strict, settings, DTOs de API
│   ├── 01_pydantic_basico.ipynb
│   ├── 02_pydantic_intermediario.ipynb
│   └── 03_pydantic_avancado.ipynb
├── dataclass/
│   ├── dataclass.md              teoria: geração de código, field(), hash/frozen/slots, arquitetura de bordas
│   ├── 01_dataclass_basico.ipynb
│   ├── 02_dataclass_intermediario.ipynb
│   └── 03_dataclass_avancado.ipynb
├── enum/
│   ├── enum.md                   teoria: EnumType, família (Str/Int/Flag), contratos abertos × fechados
│   ├── 01_enum_basico.ipynb
│   ├── 02_enum_intermediario.ipynb
│   └── 03_enum_avancado.ipynb
└── AI_use_cases/
    ├── README.md                 mapa dos casos e divisão de responsabilidades
    ├── fake_llm.py               LLM simulado (roda offline, determinístico)
    ├── 01_pydantic_structured_output.ipynb
    ├── 02_pydantic_tool_calling.ipynb
    ├── 03_enum_routing_and_guardrails.ipynb
    ├── 04_dataclass_agent_runtime.ipynb
    └── 05_agent_pipeline_end_to_end.ipynb
```

## Ordem sugerida

```mermaid
flowchart LR
    E1[enum 01] --> D1[dataclass 01] --> P1[pydantic 01]
    P1 --> E2[enum 02] --> D2[dataclass 02] --> P2[pydantic 02]
    P2 --> E3[enum 03] --> D3[dataclass 03] --> P3[pydantic 03]
    P3 --> AI[AI_use_cases 01→05]
```

Começar pelo Enum (o mais simples) e terminar no Pydantic (o mais completo) em cada nível faz cada notebook reaproveitar
o anterior: o Pydantic intermediário usa Enum, o dataclass avançado faz a ponte com Pydantic, e os casos de LLM usam tudo.

## As três em uma tabela

| | `Enum` | `dataclass` | `pydantic.BaseModel` |
|---|---|---|---|
| o que modela | conjunto **fechado** de valores | registro de dados | **contrato** de dados |
| valida em runtime | só "pertence ao conjunto" | ❌ | ✅ (tipos + restrições + regras) |
| converte tipos | `Enum(valor)` | ❌ | ✅ (lax) / ❌ (strict) |
| serializa JSON | `.value` / `StrEnum` | manual (`asdict` + encoder) | ✅ `model_dump_json` |
| JSON Schema | via Pydantic | via `TypeAdapter` | ✅ |
| custo por objeto | zero (singletons) | mínimo | baixo (Rust), maior que dataclass |
| dependência | stdlib | stdlib | `pip install pydantic` |
| lugar natural | vocabulário do domínio | núcleo / estado interno | bordas: API, config, LLM |

## Arquitetura recomendada

```
            BORDA (não confiável)                       NÚCLEO (confiável)
  ┌─────────────────────────────────┐        ┌───────────────────────────────────┐
  │ Pydantic                        │        │ dataclasses (frozen / slots)      │
  │  • BaseSettings (env, YAML...)  │ ─────► │  • entidades, value objects       │
  │  • Request / Response DTOs      │        │  • estado, eventos internos       │
  │  • saída de LLM, args de tools  │ ◄───── │  • resultados de serviços         │
  └─────────────────────────────────┘        └───────────────────────────────────┘
                    ▲                                         ▲
                    └──────────── Enum (vocabulário) ─────────┘
                       status, tipos, rótulos, permissões (Flag)
```

## Como rodar

```bash
cd data-and-classes
python -m venv .venv && source .venv/bin/activate     # ou conda/uv
pip install -r requirements.txt
jupyter lab
```

Requer **Python ≥ 3.12** (usa sintaxe de genéricos PEP 695 no dataclass avançado e no AI_use_cases 01; o resto roda em 3.11).
Testado com Python 3.13, Pydantic 2.13, pydantic-settings 2.16 e FastAPI 0.162.

Para reexecutar tudo de uma vez (verificação):

```bash
for nb in */*.ipynb; do jupyter nbconvert --to notebook --execute --inplace "$nb" || echo "FALHOU: $nb"; done
```

## Notas sobre o material de partida

Os notebooks originais de estudo (pydantic, dataclasses, enum) serviram de base. Pontos corrigidos/aprofundados aqui:

* **enum** — a seção "Vantagens/Desvantagens" falava de `Flag`, não de `Enum`; agora estão separados.
  O exemplo `BLACK = 12` num `Flag` não cria uma cor nova: é um alias de `YELLOW | BLUE` (demonstrado em `enum/02`).
  `case _: print(f"... {Color} ...")` imprimia a classe, não o valor recebido.
* **dataclass** — o exemplo que dizia usar `object.__setattr__` em classe `frozen` estava com `frozen=False`;
  `frozen` é **raso** (listas internas continuam mutáveis); `slots=True` e `cached_property` não combinam.
* **pydantic** — `EmailStr` exige o extra `pydantic[email]`; "Vantagem 4" estava duplicada; `model_construct` **não** é
  atalho de performance na v2 (medido em `pydantic/03`).
