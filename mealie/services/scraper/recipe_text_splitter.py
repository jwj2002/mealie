import re

from mealie.core.root_logger import get_logger
from mealie.lang.providers import Translator
from mealie.repos.repository_factory import AllRepositories
from mealie.services.openai import OpenAINotEnabledException, OpenAIService
from mealie.services.openai.openai import OpenAIBase

MAX_RECIPES = 50
# Minimum token length to attempt LLM fallback (~1500 tokens ≈ 6000 chars)
LLM_FALLBACK_THRESHOLD = 6000

logger = get_logger()

# Markdown heading regex — matches lines starting with one or more # characters
_HEADING_RE = re.compile(r"^#{1,6} .+", re.MULTILINE)


class _SplitDocumentResponse(OpenAIBase):
    """OpenAI structured-output schema for the split-document prompt."""

    chunks: list[str]


class BulkTextSplitterService:
    def __init__(self, repos: AllRepositories, translator: Translator) -> None:
        self.repos = repos
        self.translator = translator

    async def split(self, text: str) -> tuple[list[str], bool]:
        """Split text into recipe chunks.

        Returns a tuple of (chunks, truncated) where truncated is True if the
        input produced more than MAX_RECIPES chunks (first MAX_RECIPES returned).
        """
        chunks = self._split_by_headings(text)

        if len(chunks) <= 1 and len(text) >= LLM_FALLBACK_THRESHOLD:
            try:
                llm_chunks = await self._split_via_llm(text)
                if llm_chunks and len(llm_chunks) > 1:
                    chunks = llm_chunks
            except OpenAINotEnabledException:
                # AI not configured; treat whole input as single recipe
                pass
            except Exception:
                logger.exception("LLM split fallback failed; treating input as single chunk")

        # Ensure we always have at least one chunk
        if not chunks:
            chunks = [text]

        truncated = len(chunks) > MAX_RECIPES
        if truncated:
            logger.warning(f"Bulk text ingest: input produced {len(chunks)} chunks, truncating to {MAX_RECIPES}")
            chunks = chunks[:MAX_RECIPES]

        return chunks, truncated

    def _split_by_headings(self, text: str) -> list[str]:
        """Split text on markdown heading boundaries (# or ##, etc.)."""
        matches = list(_HEADING_RE.finditer(text))
        if len(matches) < 2:
            # Zero or one heading — not enough to split
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

        return chunks

    async def _split_via_llm(self, text: str) -> list[str]:
        """Call the LLM to split text into recipe chunks."""
        service = OpenAIService(self.repos)
        prompt = service.get_prompt("recipes.split-document")
        response = await service.get_response(prompt, text, response_schema=_SplitDocumentResponse)
        if response and response.chunks:
            return [c.strip() for c in response.chunks if c.strip()]
        return [text]
