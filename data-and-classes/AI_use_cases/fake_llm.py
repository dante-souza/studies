"""LLM simulado para os notebooks de AI_use_cases.

Os notebooks precisam rodar offline, sem chave de API e de forma determinística.
`ScriptedLLM` devolve respostas pré-roteirizadas (na ordem) e registra cada chamada,
imitando o formato mínimo de uma resposta de chat: texto e/ou blocos de tool use.

Para usar um modelo real, troque `ScriptedLLM` por uma função que chame o SDK do provedor
(exemplos nos próprios notebooks) e devolva o mesmo formato `LLMResponse`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    stop_reason: str = "end_turn"
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class ScriptedLLM:
    """Devolve as respostas do roteiro, uma por chamada.

    Cada item do roteiro pode ser:
      * str                  -> resposta de texto
      * LLMResponse          -> resposta completa (tool calls, stop_reason...)
      * callable(messages)   -> resposta calculada a partir das mensagens
    """

    script: list[Any]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, messages: list[dict[str, Any]], **kwargs: Any) -> LLMResponse:
        if not self.script:
            raise RuntimeError("roteiro do ScriptedLLM acabou: mais chamadas do que o esperado")
        item = self.script.pop(0)
        if callable(item) and not isinstance(item, LLMResponse):
            item = item(messages)
        resp = item if isinstance(item, LLMResponse) else LLMResponse(text=str(item))
        prompt_chars = sum(len(str(m.get("content", ""))) for m in messages) + len(str(kwargs.get("system", "")))
        resp = LLMResponse(
            text=resp.text,
            tool_calls=resp.tool_calls,
            stop_reason=resp.stop_reason if not resp.tool_calls else "tool_use",
            input_tokens=resp.input_tokens or max(1, prompt_chars // 4),
            output_tokens=resp.output_tokens or max(1, (len(resp.text) + len(str(resp.tool_calls))) // 4),
        )
        self.calls.append({"messages": [dict(m) for m in messages], "kwargs": kwargs, "response": resp})
        return resp


def keyword_llm(rules: dict[str, str], default: str) -> Callable[[list[dict[str, Any]]], str]:
    """Fábrica de "LLM" baseado em palavras-chave: devolve o JSON da primeira regra cujo termo
    aparece na última mensagem do usuário. Útil para simular classificadores."""

    def respond(messages: list[dict[str, Any]]) -> str:
        last = str(messages[-1]["content"]).lower()
        for keyword, answer in rules.items():
            if keyword in last:
                return answer
        return default

    return respond
