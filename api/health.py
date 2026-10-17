"""
Health check endpoints para a API Docky
"""
import logging
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException

from api.config import settings


logger = logging.getLogger(__name__)
health_router = APIRouter(prefix="/health", tags=["Health"])


class HealthStatus:
    """Enum-like class para status de saúde"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


async def check_qdrant_health() -> tuple[str, Optional[str]]:
    """Verificar saúde do Qdrant"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.QDRANT_URL}/health",
                timeout=5.0
            )
            if response.status_code == 200:
                return HealthStatus.HEALTHY, None
            else:
                return HealthStatus.UNHEALTHY, f"Status: {response.status_code}"
    except Exception as e:
        return HealthStatus.UNHEALTHY, str(e)


async def check_ollama_health() -> tuple[str, Optional[str]]:
    """Verificar saúde do Ollama"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5.0
            )
            if response.status_code == 200:
                return HealthStatus.HEALTHY, None
            else:
                return HealthStatus.UNHEALTHY, f"Status: {response.status_code}"
    except Exception as e:
        return HealthStatus.UNHEALTHY, str(e)


@health_router.get("")
async def health_check():
    """Verificação de saúde completa da aplicação"""
    qdrant_status, qdrant_error = await check_qdrant_health()
    ollama_status, ollama_error = await check_ollama_health()
    
    overall_status = (
        HealthStatus.HEALTHY
        if qdrant_status == HealthStatus.HEALTHY and ollama_status == HealthStatus.HEALTHY
        else HealthStatus.DEGRADED
        if (qdrant_status == HealthStatus.HEALTHY or ollama_status == HealthStatus.HEALTHY)
        else HealthStatus.UNHEALTHY
    )
    
    result = {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "qdrant": {
                "status": qdrant_status,
                "error": qdrant_error,
            },
            "ollama": {
                "status": ollama_status,
                "error": ollama_error,
            }
        }
    }
    
    if overall_status == HealthStatus.UNHEALTHY:
        raise HTTPException(status_code=503, detail=result)
    
    return result


@health_router.get("/ready")
async def readiness_check():
    """Verificação de readiness (pronto para receber requisições)"""
    qdrant_status, _ = await check_qdrant_health()
    ollama_status, _ = await check_ollama_health()
    
    if qdrant_status != HealthStatus.HEALTHY or ollama_status != HealthStatus.HEALTHY:
        raise HTTPException(
            status_code=503,
            detail="Serviços dependentes não estão prontos"
        )
    
    return {"status": "ready"}


@health_router.get("/live")
async def liveness_check():
    """Verificação de liveness (aplicação está rodando)"""
    return {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.now().isoformat()
    }
