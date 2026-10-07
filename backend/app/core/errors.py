import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class DomainError(Exception):
    status_code = 400
    message = "Error de negocio"

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class UnauthorizedError(DomainError):
    status_code = 401
    message = "No autenticado"


class ForbiddenError(DomainError):
    status_code = 403
    message = "Sin permiso"


class NotFoundError(DomainError):
    status_code = 404
    message = "Recurso no encontrado"


class ConflictError(DomainError):
    status_code = 409
    message = "Conflicto de integridad"


class BusinessRuleError(DomainError):
    status_code = 400
    message = "Operación inválida"


class UnprocessableError(DomainError):
    status_code = 422
    message = "Datos inválidos"


class DependencyUnavailableError(DomainError):
    status_code = 503
    message = "Servicio no disponible"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _handle_domain_error(request: Request, exc: DomainError):
        logger.warning("domain error en %s: %s", request.url.path, exc.message)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
