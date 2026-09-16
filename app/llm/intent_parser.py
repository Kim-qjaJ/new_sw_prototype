import time

import httpx
from pydantic import ValidationError

from app.config import BASE_DIR, settings
from app.schemas.intent import UserIntent

PROMPT_PATH = BASE_DIR / "prompts" / "intent.md"


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[4:] if text.lower().startswith("json") else text
    return text.strip()


class LLMUnavailableError(Exception):
    """Ollama 서버에 연결할 수 없거나 모델 호출이 실패한 경우."""


class IntentParseError(Exception):
    """LLM 응답이 UserIntent 스키마를 만족하지 못한 경우."""


class OllamaIntentParser:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        self.schema = UserIntent.model_json_schema()

    async def parse(self, message: str, max_attempts: int = 2) -> tuple[UserIntent, float]:
        started = time.perf_counter()
        last_error: Exception | None = None

        for _ in range(max_attempts):
            content = _strip_code_fence(await self._chat(message))
            try:
                intent = UserIntent.model_validate_json(content)
                return intent, round((time.perf_counter() - started) * 1000, 2)
            except ValidationError as exc:
                last_error = exc

        raise IntentParseError(str(last_error))

    async def _chat(self, message: str) -> str:
        payload = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message},
            ],
            # JSON Schema를 넘겨 출력 형식을 강제한다. 값 검증은 Pydantic이 한 번 더 한다.
            # 스키마 방식에서 Ollama 오류가 나면 OLLAMA_STRUCTURED_OUTPUT=false로 일반 JSON 모드를 쓴다.
            "format": self.schema if settings.ollama_structured_output else "json",
            "stream": False,
            "keep_alive": settings.ollama_keep_alive,
            "options": {"temperature": 0},
        }
        try:
            response = await self.client.post(
                f"{settings.ollama_url}/api/chat",
                json=payload,
                timeout=settings.ollama_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMUnavailableError(
                f"Ollama가 {settings.ollama_timeout_seconds:g}초 안에 응답하지 않았습니다."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise LLMUnavailableError(
                f"Ollama 오류 {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailableError(
                f"Ollama 서버({settings.ollama_url})에 연결할 수 없습니다. `ollama serve` 실행 여부를 확인하세요."
            ) from exc

        return response.json().get("message", {}).get("content", "")

    async def status(self) -> dict:
        try:
            response = await self.client.get(f"{settings.ollama_url}/api/tags", timeout=3)
            response.raise_for_status()
        except httpx.HTTPError:
            return {"reachable": False, "model": settings.ollama_model, "model_installed": False}

        names = {model.get("name") for model in response.json().get("models", [])}
        wanted = {settings.ollama_model, f"{settings.ollama_model}:latest"}
        return {
            "reachable": True,
            "model": settings.ollama_model,
            "model_installed": bool(names & wanted),
        }

    async def warm_up(self) -> None:
        """서버 시작 시 모델을 미리 메모리에 올려 첫 요청 지연을 줄인다."""
        try:
            await self.client.post(
                f"{settings.ollama_url}/api/chat",
                json={"model": settings.ollama_model, "messages": [], "keep_alive": settings.ollama_keep_alive},
                timeout=settings.ollama_timeout_seconds,
            )
        except httpx.HTTPError:
            pass
