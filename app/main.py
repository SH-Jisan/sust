from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routers import health, analyze

app = FastAPI(
    title="QueueStorm Investigator",
    description="Digital Finance SupportOps copilot for ticket analysis and safety",
    version="1.0.0"
)

# Include API endpoints
app.include_router(health.router)
app.include_router(analyze.router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors (missing fields, bad formats) and return HTTP 400.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Malformed input",
            "message": "Invalid JSON payload or missing required fields.",
            "details": exc.errors()
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Handle semantic validation failures (e.g., empty complaint) and return HTTP 422.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Unprocessable Entity",
            "message": str(exc)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for internal runtime errors, returning a clean HTTP 500 without leaking stack traces.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please contact administrator."
        }
    )
