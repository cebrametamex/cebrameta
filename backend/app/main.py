try:  # pragma: no cover - exercised indirectly when FastAPI is available
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
except ModuleNotFoundError:  # pragma: no cover - default path in tests
    from .stubs.fastapi import (  # type: ignore[F401]
        CORSMiddleware,
        FastAPI,
        File,
        Form,
        HTTPException,
        JSONResponse,
        UploadFile,
    )

from .services.pipeline import ConversionRequest, convert_image

app = FastAPI(title="Vector Conversion Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    denoise_strength: float = Form(1.0),
    edge_sigma: float = Form(1.0),
    threshold: float = Form(0.2),
):
    try:
        payload = ConversionRequest(
            file=file,
            denoise_strength=denoise_strength,
            edge_sigma=edge_sigma,
            threshold=threshold,
        )
        result = await convert_image(payload)
        return JSONResponse(content=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - catch unexpected errors for API hygiene
        raise HTTPException(status_code=500, detail="Conversion failed") from exc
