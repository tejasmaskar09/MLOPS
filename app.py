"""
Experiments 2–4: FastAPI Backend for Model Inference
=====================================================
Expt 2 — /predict endpoint with Pydantic schemas
Expt 3 — Structured logging & exception handlers
Expt 4 — API Key / JWT authentication on secured endpoints

Run:
    uvicorn app:app --reload
"""

import os
import pickle
import time
import traceback
import numpy as np
from fastapi.security import APIKeyHeader
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    ErrorResponse,
)

from logging_config import setup_logging, generate_request_id
from auth import create_jwt_token, verify_auth

# --------------- Initialisation ---------------

logger = setup_logging()

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def load_model():
    """Load the pickled model from disk."""
    if not os.path.exists(MODEL_PATH):
        logger.error("Model file not found", extra={"path": MODEL_PATH})
        return None
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    logger.info("Model loaded successfully", extra={"path": MODEL_PATH})
    return model


model = load_model()

app = FastAPI(
    title="MLOps Student Score Predictor",
    description="Predicts student final scores based on study hours, attendance, and previous score.",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# Experiment 3: Logging Middleware — logs every request / response
# =====================================================================

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = generate_request_id()
    request.state.request_id = request_id
    start = time.perf_counter()

    logger.info(
        "Incoming request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error(
            "Unhandled exception during request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "duration_ms": duration_ms,
                "error_type": type(exc).__name__,
                "error_detail": str(exc),
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                detail=str(exc),
                request_id=request_id,
            ).model_dump(),
        )

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


# =====================================================================
# Experiment 3: Custom Exception Handlers
# =====================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "error_type": "HTTPException",
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP {exc.status_code}",
            detail=exc.detail,
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"ValueError: {exc}",
        extra={
            "request_id": request_id,
            "error_type": "ValueError",
            "error_detail": str(exc),
        },
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc),
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.critical(
        f"Unexpected error: {exc}",
        extra={
            "request_id": request_id,
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred. Check logs for details.",
            request_id=request_id,
        ).model_dump(),
    )


# =====================================================================
# Public Endpoints
# =====================================================================

@app.get("/", tags=["General"])
async def root():
    return {"message": "MLOps Student Score Predictor API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    return HealthResponse(status="healthy", model_loaded=model is not None)


# --------------- Token endpoint (Experiment 4) ---------------

@app.post("/token", tags=["Authentication"])
async def get_token(username: str = "demo_user"):
    """Issue a JWT token (for demo/testing purposes)."""
    token = create_jwt_token(subject=username)
    logger.info(f"JWT token issued for user: {username}")
    return {"access_token": token, "token_type": "bearer"}


# =====================================================================
# Experiment 2 + 4: Secured /predict Endpoint
# =====================================================================

@app.post(
    "/predict",
    response_model=PredictionResponse,
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    tags=["Prediction"],
)
async def predict(
    request: PredictionRequest,
    api_key: str = Depends(api_key_header),
    auth_info: str = Depends(verify_auth),
):
    """
    Predict a student's final score.

    **Requires authentication** — supply either:
    - `X-API-Key` header, or
    - `Authorization: Bearer <jwt>` header
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Run experiment1_train_model.py first.",
        )

    features = np.array([[request.hours, request.attendance, request.previous_score]])
    prediction = float(model.predict(features)[0])

    logger.info(
        "Prediction served",
        extra={
            "hours": request.hours,
            "attendance": request.attendance,
            "previous_score": request.previous_score,
            "predicted_score": round(prediction, 2),
        },
    )

    return PredictionResponse(
    predicted_final_score=round(prediction, 2),
    model_version="1.0.0"
)
