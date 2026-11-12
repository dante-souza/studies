"""Cliente de LLM simulado, no formato da API da OpenAI — para o avançado rodar offline e de forma determinística.

`ClienteSimulado` imita `OpenAI(...)`: tem `.chat.completions.create(model=..., messages=..., tools=...)` e devolve um
`ChatCompletion` montado com os tipos do próprio SDK `openai`. O código que usa o cliente não sabe a diferença; trocar pelo
cliente real é trocar uma linha (veja o notebook 10).

As respostas vêm de um **roteiro** (lista, uma por chamada). Cada item pode ser:
  * str                         -> resposta de texto
  * ChatCompletionMessage       -> resposta completa (por exemplo, com tool_calls)
  * callable(messages) -> um dos dois acima, calculado a partir da conversa
Com `padrao=funcao`, a função responde toda chamada que o roteiro não cobrir.

Uso de tokens: ESTIMATIVA (1 token ≈ 4 caracteres). O tokenizer real dá números diferentes.
"""

from __future__ import annotations

import itertools
import json
from typing import Any, Callable

from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_function_tool_call import (
    ChatCompletionMessageFunctionToolCall,
    Function,
)
from openai.types.completion_usage import CompletionUsage

_ids_de_chamada = itertools.count(1)


def estimar_tokens(texto: str) -> int:
    return max(1, len(texto) // 4)


def _texto_das_mensagens(mensagens: list[dict[str, Any]]) -> str:
    return "".join(str(m.get("content") or "") + json.dumps(m.get("tool_calls") or "") for m in mensagens)


class _Completions:
    def __init__(self, cliente: ClienteSimulado):
        self._cliente = cliente

    def create(self, *, model: str, messages: list[dict[str, Any]], tools: list | None = None, **kwargs: Any) -> ChatCompletion:
        return self._cliente._responder(model, messages, tools, kwargs)


class _Chat:
    def __init__(self, cliente: ClienteSimulado):
        self.completions = _Completions(cliente)


class ClienteSimulado:
    def __init__(self, roteiro: list[Any] = (), padrao: Callable[[list[dict[str, Any]]], Any] | None = None):
        """roteiro: respostas na ordem; padrao: função usada quando o roteiro acaba (ou sempre, se não houver roteiro)."""
        self.roteiro = list(roteiro)
        self.padrao = padrao
        self.chamadas: list[dict[str, Any]] = []
        self.chat = _Chat(self)

    def _responder(self, model, messages, tools, kwargs) -> ChatCompletion:
        if self.roteiro:
            item = self.roteiro.pop(0)
        elif self.padrao is not None:
            item = self.padrao
        else:
            raise RuntimeError("roteiro do ClienteSimulado acabou: mais chamadas do que o esperado")
        if callable(item):
            item = item(messages)
        mensagem = item if isinstance(item, ChatCompletionMessage) else ChatCompletionMessage(role="assistant", content=str(item))
        saida = (mensagem.content or "") + json.dumps([c.model_dump() for c in mensagem.tool_calls or []])
        uso = CompletionUsage(
            prompt_tokens=estimar_tokens(_texto_das_mensagens(messages)),
            completion_tokens=estimar_tokens(saida),
            total_tokens=0,
        )
        uso.total_tokens = uso.prompt_tokens + uso.completion_tokens
        resposta = ChatCompletion(
            id=f"sim-{len(self.chamadas) + 1}",
            object="chat.completion",
            created=0,
            model=model,
            choices=[Choice(index=0, message=mensagem, finish_reason="tool_calls" if mensagem.tool_calls else "stop")],
            usage=uso,
        )
        self.chamadas.append({"model": model, "messages": [dict(m) for m in messages], "tools": tools, "resposta": resposta})
        return resposta


def pedido_de_ferramenta(*chamadas: tuple[str, dict[str, Any]]) -> ChatCompletionMessage:
    """Mensagem do assistente pedindo ferramentas: pedido_de_ferramenta(("consultar_preco", {"nome": "azeite"}), ...).
    Cada chamada recebe um ID único (call_1, call_2, ...), como na API real."""
    return ChatCompletionMessage(role="assistant", content=None, tool_calls=[
        ChatCompletionMessageFunctionToolCall(id=f"call_{next(_ids_de_chamada)}", type="function",
                                              function=Function(name=nome, arguments=json.dumps(args, ensure_ascii=False)))
        for nome, args in chamadas
    ])


def por_palavra_chave(regras: dict[str, str], padrao: str) -> Callable[[list[dict[str, Any]]], str]:
    """Classificador simulado: devolve a resposta da primeira palavra-chave presente na última mensagem do usuário."""

    def responder(mensagens: list[dict[str, Any]]) -> str:
        ultima = str(mensagens[-1]["content"]).lower()
        for palavra, resposta in regras.items():
            if palavra in ultima:
                return resposta
        return padrao

    return responder
