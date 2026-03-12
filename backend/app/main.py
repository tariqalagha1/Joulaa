from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import structlog
from typing import Dict, Any

from .core.config import settings
from .core.database import init_db, close_db
from .api.v1.api import api_router
from .api.v2.orchestration import router as orchestration_v2_router
from .api.v2.platform_access import router as platform_access_v2_router
from .core.logging import setup_logging
from .core.request_id import request_id_middleware
from .core.rate_limit import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Setup structured logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Joulaa Platform", version=settings.APP_VERSION)
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Joulaa Platform")
    await close_db()
    logger.info("Database connection closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Arabic-first AI-driven enterprise copilot platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else ["joulaa.app", "*.joulaa.app"]
)

app.middleware("http")(request_id_middleware)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with structured logging"""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time
        )
        
        return response
    
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=process_time
        )
        raise


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with Arabic-friendly messages"""
    logger.warning(
        "Validation error",
        method=request.method,
        url=str(request.url),
        errors=exc.errors()
    )
    
    # Format validation errors
    formatted_errors = []
    for error in exc.errors():
        field = error["loc"][-1] if error["loc"] else "unknown"
        message = error["msg"]
        
        # Translate common validation messages to Arabic
        arabic_messages = {
            "field required": "هذا الحقل مطلوب",
            "value is not a valid email": "البريد الإلكتروني غير صحيح",
            "ensure this value has at least": "يجب أن يحتوي على الأقل على",
            "ensure this value has at most": "يجب أن يحتوي على الأكثر على",
            "ensure this value is greater than": "يجب أن تكون القيمة أكبر من",
            "ensure this value is less than": "يجب أن تكون القيمة أقل من",
        }
        
        for eng_msg, ar_msg in arabic_messages.items():
            if eng_msg in message.lower():
                message = ar_msg
                break
        
        formatted_errors.append({
            "field": field,
            "message": message,
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "خطأ في التحقق من البيانات",
            "errors": formatted_errors
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with Arabic-friendly messages"""
    logger.warning(
        "HTTP exception",
        method=request.method,
        url=str(request.url),
        status_code=exc.status_code,
        detail=exc.detail
    )
    
    # Translate common HTTP error messages to Arabic
    arabic_messages = {
        "Not Found": "الصفحة غير موجودة",
        "Unauthorized": "غير مصرح لك بالوصول",
        "Forbidden": "ممنوع الوصول",
        "Internal Server Error": "خطأ في الخادم",
        "Bad Request": "طلب غير صحيح",
    }
    
    detail = exc.detail
    if detail in arabic_messages:
        detail = arabic_messages[detail]
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(
        "Unhandled exception",
        method=request.method,
        url=str(request.url),
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "خطأ داخلي في الخادم"}
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }


# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "مرحباً بك في منصة جولة",
        "welcome": "Welcome to Joulaa Platform",
        "version": settings.APP_VERSION
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(orchestration_v2_router, prefix="/api/v2", tags=["orchestration-v2"])
app.include_router(platform_access_v2_router, prefix="/api/v2/admin", tags=["platform-access-v2"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 
