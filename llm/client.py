"""
Client para interação com LLMs (Local e Remote)
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from api.config import settings


logger = logging.getLogger(__name__)


class LLMResponse:
    """Response de um modelo LLM"""
    
    def __init__(
        self,
        text: str,
        model: str,
        tokens_used: Optional[int] = None,
        stop_reason: Optional[str] = None,
    ):
        self.text = text
        self.model = model
        self.tokens_used = tokens_used
        self.stop_reason = stop_reason


class BaseLLMClient(ABC):
    """Classe base para clientes LLM"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Gerar texto usando o modelo LLM"""
        pass


class OllamaClient(BaseLLMClient):
    """Cliente para Ollama (LLM local)"""
    
    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        model: str = settings.OLLAMA_MODEL,
        temperature: float = settings.OLLAMA_TEMPERATURE,
    ):
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.client = httpx.AsyncClient()
    
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Gerar texto usando Ollama"""
        temp = temperature or self.temperature
        
        logger.info(f"Gerando texto com modelo: {self.model}")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temp,
                    "stream": False,
                },
                # 300s: modelos pequenos em CPU podem levar >120s no cold start
                # (primeira chamada apos o Ollama carregar os pesos na memoria)
                timeout=300.0,
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            data = response.json()
            
            return LLMResponse(
                text=data.get("response", ""),
                model=self.model,
                tokens_used=None,  # Ollama não retorna token count por padrão
            )
        except Exception as e:
            logger.error(f"Erro ao gerar texto com Ollama: {str(e)}")
            raise
    
    async def close(self):
        """Fechar cliente"""
        await self.client.aclose()


class EmbeddingClient:
    """Client para geração de embeddings"""
    
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        from sentence_transformers import SentenceTransformer
        
        logger.info(f"Carregando modelo de embeddings: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
    
    def encode(self, texts: list[str]) -> list[list[float]]:
        """Gerar embeddings para textos"""
        logger.info(f"Gerando embeddings para {len(texts)} texto(s)")
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def encode_single(self, text: str) -> list[float]:
        """Gerar embedding para um único texto"""
        embedding = self.model.encode([text], convert_to_numpy=True)[0]
        return embedding.tolist()
