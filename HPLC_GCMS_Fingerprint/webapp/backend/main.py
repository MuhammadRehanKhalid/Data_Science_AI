from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from functools import lru_cache
from io import StringIO
from typing import Any
import threading
import time
import uuid
import json
import sys

import pandas as pd
import joblib
from fastapi import FastAPI
from fastapi import File, Form, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Marine Biotech Vision API",
    version="0.1.0",
    description="Lightweight API wrapper for the HPLC/GCMS/FTIR pipeline.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    sample_id: str = Field(..., examples=["FTIR_S001"])
    project_area: str = Field(default="marine-biotech", examples=["marine-biotech", "vision"])
    source_type: str = Field(default="FTIR", examples=["FTIR", "HPLC", "GCMS"])
    payload: dict[str, Any] = Field(default_factory=dict)


class PredictionResponse(BaseModel):
    sample_id: str
    source_type: str
    project_area: str
    predicted_label: str
    confidence: float
    summary: str
    resource_mode: str


class UploadAnalysisResponse(BaseModel):
    filename: str
    rows: int
    columns: int
    detected_source: str
    non_numeric_cells: int
    missing_cells: int
    summary: str


class PipelineStatusResponse(BaseModel):
    available: bool
    predictions_path: str | None = None
    insights_path: str | None = None
    latest_predictions: list[dict[str, Any]] = Field(default_factory=list)
    insights_excerpt: str = ""
    summary: str


class ModelStatusResponse(BaseModel):
    available: bool
    model_path: str | None = None
    model_type: str | None = None
    summary: str


@lru_cache(maxsize=1)
def get_model_info() -> dict[str, str]:
    model_path = os.getenv("MODEL_PATH", "not-configured")
    return {
        "model_path": model_path,
        "resource_mode": "low-overhead",
    }


@lru_cache(maxsize=1)
def _load_model_artifact() -> Any | None:
    model_path = os.getenv("MODEL_PATH", "").strip()
    if not model_path:
        return None

    path = Path(model_path)
    if not path.exists():
        return None

    try:
        return joblib.load(path)
    except Exception:
        return None


def _model_status() -> dict[str, Any]:
    model = _load_model_artifact()
    model_path = os.getenv("MODEL_PATH", "").strip() or None
    return {
        "available": model is not None,
        "model_path": model_path,
        "model_type": type(model).__name__ if model is not None else None,
    }


def _extract_features(payload: dict[str, Any]) -> list[float] | None:
    raw_features = payload.get("features") or payload.get("feature_vector")
    if raw_features is None:
        return None

    if isinstance(raw_features, Sequence) and not isinstance(raw_features, (str, bytes, bytearray)):
        try:
            return [float(value) for value in raw_features]
        except (TypeError, ValueError):
            return None
    return None


def _label_from_prediction(prediction: Any) -> tuple[str, float]:
    if isinstance(prediction, dict):
        if "predicted_species" in prediction:
            return str(prediction["predicted_species"]), 0.91
        if "pred_species" in prediction:
            value = prediction["pred_species"]
            try:
                return f"Species class {int(value)}", 0.88
            except (TypeError, ValueError):
                return str(value), 0.88
        if "best_solvent" in prediction:
            return str(prediction["best_solvent"]), 0.82

    if isinstance(prediction, Sequence) and not isinstance(prediction, (str, bytes, bytearray)):
        if len(prediction) == 0:
            return "No prediction", 0.0
        first = prediction[0]
        if isinstance(first, Sequence) and not isinstance(first, (str, bytes, bytearray)):
            first = first[0] if first else first
        return str(first), 0.85

    return str(prediction), 0.8


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# Ensure project root is on sys.path for local imports
_ROOT = _repo_root()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _artifact_path(*parts: str) -> Path:
    return _repo_root() / "pipeline_output" / Path(*parts)


def _latest_predictions() -> tuple[Path | None, list[dict[str, Any]]]:
    predictions_path = _artifact_path("predictions", "predictions.csv")
    if not predictions_path.exists():
        return None, []

    df = pd.read_csv(predictions_path)
    preview_cols = [
        col
        for col in ["sample_id", "data_source", "predicted_species", "predicted_phylum", "confidence_pct"]
        if col in df.columns
    ]
    preview = df[preview_cols].head(6).to_dict(orient="records") if preview_cols else df.head(6).to_dict(orient="records")
    return predictions_path, preview


def _insights_excerpt() -> tuple[Path | None, str]:
    insights_path = _artifact_path("reports", "insights_report.txt")
    if not insights_path.exists():
        return None, ""

    text = insights_path.read_text(encoding="utf-8", errors="ignore").strip()
    return insights_path, text[:900]


# Simple in-memory job store for training jobs
_TRAINING_JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()

# Simple in-memory upload/store for user-provided datasets
_UPLOADS: dict[str, dict] = {}
_UPLOADS_LOCK = threading.Lock()


def _new_job_record(kind: str, params: dict[str, Any]) -> str:
    job_id = uuid.uuid4().hex
    record = {
        "id": job_id,
        "kind": kind,
        "params": params,
        "status": "queued",
        "percent": 0.0,
        "start_time": None,
        "end_time": None,
        "history": [],
        "error": None,
    }
    with _JOBS_LOCK:
        _TRAINING_JOBS[job_id] = record
    return job_id


def _update_job_progress(job_id: str, percent: float, info: dict | None = None):
    with _JOBS_LOCK:
        rec = _TRAINING_JOBS.get(job_id)
        if not rec:
            return
        rec["percent"] = float(percent)
        if info is not None:
            rec["history"].append({"ts": time.time(), "info": info})
        if rec["start_time"] is None:
            rec["start_time"] = time.time()


def _finish_job(job_id: str, error: str | None = None):
    with _JOBS_LOCK:
        rec = _TRAINING_JOBS.get(job_id)
        if not rec:
            return
        rec["end_time"] = time.time()
        rec["status"] = "error" if error else "finished"
        if error:
            rec["error"] = error
        rec["percent"] = 100.0


def _run_ml_job(job_id: str, params: dict[str, Any]):
    from training.trainer import train_ml
    try:
        _update_job_progress(job_id, 1.0, {"stage": "ml_start"})
        # Prefer a prepared dataset supplied by the user (via upload flow)
        ds = None
        dataset_id = params.get("dataset_id")
        if dataset_id:
            with _UPLOADS_LOCK:
                rec = _UPLOADS.get(dataset_id)
                if rec and rec.get("prepared_df") is not None:
                    try:
                        # Ensure minimal required target columns exist to avoid builder errors
                        prep = rec.get("prepared_df")
                        if "phylum" not in prep.columns:
                            prep = prep.copy()
                            prep["phylum"] = "Unknown"
                        if "species" not in prep.columns:
                            prep = prep.copy()
                            prep["species"] = prep.index.astype(str)
                        from ingestion.dataset import MultiTaskDataset
                        ds = MultiTaskDataset.from_sources(hplc_df=prep)
                        # Validate constructed dataset has non-empty features/targets
                        try:
                            if getattr(ds, 'X', None) is None or ds.X.size == 0:
                                ds = None
                            elif getattr(ds, 'y_solvents', None) is None or ds.y_solvents.size == 0:
                                ds = None
                            elif getattr(ds, 'y_assays', None) is None or ds.y_assays.size == 0:
                                ds = None
                        except Exception:
                            ds = None
                    except Exception:
                        ds = None

        # Generate a small synthetic dataset using SampleDataGenerator if no user dataset
        from modules.sample_data_generator import SampleDataGenerator
        from data_generation.constants import SOLVENTS, ASSAYS, PHYLA, SPECIES_BASELINE, ASSAY_POLARITY_WEIGHT, PHYLUM_ASSAY_AFFINITY
        import numpy as np

        if ds is None:
            gen = SampleDataGenerator()
            hplc_df = gen.generate_hplc_data(n_samples=80)
            # Map phylum and create synthetic activity + assay targets
            hplc_df["phylum"] = hplc_df["species"].map(PHYLA).fillna("Unknown")
            for s in SOLVENTS:
                baseline = hplc_df["species"].map(SPECIES_BASELINE).fillna(0.6).to_numpy(dtype=float)
                hplc_df[f"activity_{s}"] = np.clip(baseline + np.random.normal(0.0, 0.12, size=len(hplc_df)), 0.0, 1.0)

            for assay in ASSAYS:
                weight = ASSAY_POLARITY_WEIGHT.get(assay, 0.5)
                for s in SOLVENTS:
                    ph_aff = hplc_df["phylum"].map(lambda p: PHYLUM_ASSAY_AFFINITY.get(p, {}).get(assay, 0.0)).to_numpy(dtype=float)
                    hplc_df[f"{assay}_{s}"] = np.clip(hplc_df[f"activity_{s}"].to_numpy(dtype=float) * weight + ph_aff + np.random.normal(0.0, 0.06, size=len(hplc_df)), 0.0, 1.0)

            from ingestion.dataset import MultiTaskDataset
            ds = MultiTaskDataset.from_sources(hplc_df=hplc_df)
            # validate
            if ds is None or getattr(ds, 'X', None) is None or ds.X.size == 0:
                raise RuntimeError('synthetic_generation_failed')
            train_ds, val_ds = ds.train_test_split(test_size=0.2)
        else:
            train_ds, val_ds = ds.train_test_split(test_size=0.2)

        def cb(pct, info):
            _update_job_progress(job_id, pct, info)

        # Fit a lightweight ML baseline
        model = train_ml(train_ds, progress_callback=lambda pct, info: _update_job_progress(job_id, pct, info))
        _finish_job(job_id)
    except Exception as exc:
        import traceback as _tb
        _finish_job(job_id, error=_tb.format_exc())


def _run_dl_job(job_id: str, params: dict[str, Any]):
    from training.trainer import train_dl
    try:
        _update_job_progress(job_id, 0.5, {"stage": "dl_start"})
        # Prefer a prepared dataset supplied by the user (via upload flow)
        ds = None
        dataset_id = params.get("dataset_id")
        if dataset_id:
            with _UPLOADS_LOCK:
                rec = _UPLOADS.get(dataset_id)
                if rec and rec.get("prepared_df") is not None:
                    try:
                        # Defensive: ensure minimal target columns exist before building dataset
                        prep = rec.get("prepared_df")
                        if "phylum" not in prep.columns:
                            prep = prep.copy()
                            prep["phylum"] = "Unknown"
                        if "species" not in prep.columns:
                            prep = prep.copy()
                            prep["species"] = prep.index.astype(str)
                        from ingestion.dataset import MultiTaskDataset
                        ds = MultiTaskDataset.from_sources(hplc_df=prep)
                        # Validate constructed dataset
                        try:
                            if getattr(ds, 'X', None) is None or ds.X.size == 0:
                                ds = None
                            elif getattr(ds, 'y_solvents', None) is None or ds.y_solvents.size == 0:
                                ds = None
                            elif getattr(ds, 'y_assays', None) is None or ds.y_assays.size == 0:
                                ds = None
                        except Exception:
                            ds = None
                    except Exception:
                        ds = None

        if ds is None:
            from modules.sample_data_generator import SampleDataGenerator
            from data_generation.constants import SOLVENTS, ASSAYS, PHYLA, SPECIES_BASELINE, ASSAY_POLARITY_WEIGHT, PHYLUM_ASSAY_AFFINITY
            import numpy as np

            gen = SampleDataGenerator()
            hplc_df = gen.generate_hplc_data(n_samples=120)
            hplc_df["phylum"] = hplc_df["species"].map(PHYLA).fillna("Unknown")

            for s in SOLVENTS:
                baseline = hplc_df["species"].map(SPECIES_BASELINE).fillna(0.6).to_numpy(dtype=float)
                hplc_df[f"activity_{s}"] = np.clip(baseline + np.random.normal(0.0, 0.12, size=len(hplc_df)), 0.0, 1.0)

            for assay in ASSAYS:
                weight = ASSAY_POLARITY_WEIGHT.get(assay, 0.5)
                for s in SOLVENTS:
                    ph_aff = hplc_df["phylum"].map(lambda p: PHYLUM_ASSAY_AFFINITY.get(p, {}).get(assay, 0.0)).to_numpy(dtype=float)
                    hplc_df[f"{assay}_{s}"] = np.clip(hplc_df[f"activity_{s}"].to_numpy(dtype=float) * weight + ph_aff + np.random.normal(0.0, 0.06, size=len(hplc_df)), 0.0, 1.0)

            from ingestion.dataset import MultiTaskDataset
            ds = MultiTaskDataset.from_sources(hplc_df=hplc_df)
            train_ds, val_ds = ds.train_test_split(test_size=0.2)
        else:
            train_ds, val_ds = ds.train_test_split(test_size=0.2)

        def cb(pct, info):
            _update_job_progress(job_id, pct, info)

        model, history = train_dl(train_ds, val_ds, progress_callback=cb, **params)
        try:
            out_dir = _artifact_path('models')
            out_dir.mkdir(parents=True, exist_ok=True)
            model_path = out_dir / f'model_{job_id}.pt'
            try:
                import torch
                torch.save(model.state_dict(), model_path)
            except Exception:
                import joblib
                joblib.dump(model, out_dir / f'model_{job_id}.joblib')
        except Exception:
            pass

        _finish_job(job_id)
    except Exception as exc:
        import traceback as _tb
        _finish_job(job_id, error=_tb.format_exc())


def _landing_page_html() -> str:
    return (Path(__file__).with_name("landing.html")).read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", **get_model_info()}


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    return HTMLResponse(_landing_page_html())


@app.get("/favicon.ico")
def favicon() -> Response:
        return Response(status_code=204)


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    return {
        "app": "Marine Biotech Vision API",
        "theme": "marine + research",
        "supported_sources": ["FTIR", "HPLC", "GCMS"],
        "deployment_hint": "Keep the frontend static and the backend minimal for low resource usage.",
        "model_status": _model_status(),
        **get_model_info(),
    }


@app.get("/api/model-status", response_model=ModelStatusResponse)
def model_status() -> ModelStatusResponse:
    status = _model_status()
    return ModelStatusResponse(
        available=bool(status["available"]),
        model_path=status["model_path"],
        model_type=status["model_type"],
        summary=(
            "A serialized model artifact is "
            + ("loaded." if status["available"] else "not loaded; using demo fallback.")
        ),
    )


@app.get("/api/pipeline-status", response_model=PipelineStatusResponse)
def pipeline_status() -> PipelineStatusResponse:
    predictions_path, latest_predictions = _latest_predictions()
    insights_path, excerpt = _insights_excerpt()

    available = predictions_path is not None or insights_path is not None
    return PipelineStatusResponse(
        available=available,
        predictions_path=str(predictions_path) if predictions_path else None,
        insights_path=str(insights_path) if insights_path else None,
        latest_predictions=latest_predictions,
        insights_excerpt=excerpt,
        summary=(
            "Pipeline artifacts are being surfaced from the latest run output. "
            "Use this as a lightweight bridge to your full model deployment."
        ),
    )


@app.post("/api/train")
def start_training(kind: str = "dl", epochs: int = 50, batch_size: int = 32, dataset_id: str | None = None) -> dict[str, str]:
    """Start a training job (kind: 'dl' or 'ml'). Returns a job id."""
    params = {"epochs": int(epochs), "batch_size": int(batch_size), "dataset_id": dataset_id}
    job_id = _new_job_record(kind, params)

    thread = None
    if kind.lower() == "ml":
        thread = threading.Thread(target=_run_ml_job, args=(job_id, params), daemon=True)
    else:
        thread = threading.Thread(target=_run_dl_job, args=(job_id, params), daemon=True)

    thread.start()
    return {"job_id": job_id, "status": "started"}


@app.get("/api/train-status/{job_id}")
def train_status(job_id: str) -> dict[str, Any]:
    with _JOBS_LOCK:
        rec = _TRAINING_JOBS.get(job_id)
        if not rec:
            return {"error": "not_found"}
        return {
            k: v for k, v in rec.items() if k in ("id", "kind", "status", "percent", "start_time", "end_time", "error")
        }


@app.get("/api/train-stream/{job_id}")
def train_stream(job_id: str):
    """Server-Sent Events stream of progress updates for a job."""
    def event_generator():
        last_sent = -1.0
        while True:
            with _JOBS_LOCK:
                rec = _TRAINING_JOBS.get(job_id)
                if rec is None:
                    yield f"data: {json.dumps({'error':'not_found'})}\n\n"
                    break
                pct = rec.get('percent', 0.0)
                status = rec.get('status')
                error = rec.get('error')
                payload = {'percent': pct, 'status': status, 'error': error}

            # only send when progress changed or when finished
            if pct != last_sent or status in ('finished', 'error'):
                yield f"data: {json.dumps(payload)}\n\n"
                last_sent = pct

            if status in ('finished', 'error'):
                break

            time.sleep(0.5)

    return StreamingResponse(event_generator(), media_type='text/event-stream')


@app.post("/api/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    model = _load_model_artifact()
    features = _extract_features(request.payload)

    if model is not None and features is not None and hasattr(model, "predict"):
        try:
            prediction = model.predict([features])
            predicted_label, confidence = _label_from_prediction(prediction)
            summary = (
                "Prediction generated from the loaded model artifact. "
                "The app is still lightweight because the model is loaded only on demand."
            )
        except Exception as exc:
            predicted_label = f"Model load fallback: {request.source_type.upper()}"
            confidence = 0.5
            summary = f"Loaded model could not score the payload, so fallback mode was used: {exc}"
    else:
        label_pool = {
            "FTIR": "High spectral match",
            "HPLC": "Chromatographic signature aligned",
            "GCMS": "Metabolomic profile aligned",
        }
        predicted_label = label_pool.get(request.source_type.upper(), "Signature aligned")
        confidence = 0.84 if request.project_area.lower() == "marine-biotech" else 0.76
        summary = (
            "Lightweight demo response. Connect your trained pipeline here to "
            "return real predictions without adding heavy runtime overhead."
        )

    return PredictionResponse(
        sample_id=request.sample_id,
        source_type=request.source_type,
        project_area=request.project_area,
        predicted_label=predicted_label,
        confidence=confidence,
        summary=summary,
        resource_mode=get_model_info()["resource_mode"],
    )


@app.post("/api/analyze-upload", response_model=UploadAnalysisResponse)
async def analyze_upload(
    file: UploadFile = File(...),
    source_type: str = Form(default="FTIR"),
) -> UploadAnalysisResponse:
    raw_text = (await file.read()).decode("utf-8", errors="ignore")
    df = pd.read_csv(StringIO(raw_text))

    metadata_cols = {"sample_id", "species", "phylum", "replicate"}
    if source_type.upper() == "FTIR":
        feature_prefix = "wn_"
    elif source_type.upper() == "HPLC":
        feature_prefix = "intensity_RT_"
    else:
        feature_prefix = "intensity_mz_"

    feature_cols = [c for c in df.columns if c.startswith(feature_prefix)]
    feature_frame = df[feature_cols].copy() if feature_cols else df.drop(columns=[c for c in metadata_cols if c in df.columns], errors="ignore")

    non_numeric_cells = int(feature_frame.apply(lambda col: pd.to_numeric(col, errors="coerce").isna().sum()).sum())
    missing_cells = int(df.isna().sum().sum())

    return UploadAnalysisResponse(
        filename=file.filename or "uploaded-file.csv",
        rows=int(df.shape[0]),
        columns=int(df.shape[1]),
        detected_source=source_type.upper(),
        non_numeric_cells=non_numeric_cells,
        missing_cells=missing_cells,
        summary=(
            "Upload accepted. The current backend is a low-resource starter, so "
            "this endpoint validates the file and reports basic quality metrics. "
            "Wire your trained pipeline here when you are ready for true predictions."
        ),
    )


@app.post("/api/upload-file")
async def upload_file(file: UploadFile = File(...), source_type: str = Form(default="FTIR")) -> dict:
    """Upload a CSV dataset and return an upload id with analysis/suggested steps."""
    raw_text = (await file.read()).decode("utf-8", errors="ignore")
    df = pd.read_csv(StringIO(raw_text))

    metadata_cols = {"sample_id", "species", "phylum", "replicate"}
    if source_type.upper() == "FTIR":
        feature_prefix = "wn_"
    elif source_type.upper() == "HPLC":
        feature_prefix = "intensity_RT_"
    else:
        feature_prefix = "intensity_mz_"

    feature_cols = [c for c in df.columns if c.startswith(feature_prefix)]
    feature_frame = df[feature_cols].copy() if feature_cols else df.drop(columns=[c for c in metadata_cols if c in df.columns], errors="ignore")

    non_numeric_cells = int(feature_frame.apply(lambda col: pd.to_numeric(col, errors="coerce").isna().sum()).sum())
    missing_cells = int(df.isna().sum().sum())

    upload_id = uuid.uuid4().hex
    with _UPLOADS_LOCK:
        _UPLOADS[upload_id] = {
            "filename": file.filename or "uploaded.csv",
            "raw_df": df,
            "prepared_df": None,
            "source_type": source_type.upper(),
            "created_at": time.time(),
        }

    return {
        "upload_id": upload_id,
        "filename": file.filename or "uploaded.csv",
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "detected_source": source_type.upper(),
        "non_numeric_cells": non_numeric_cells,
        "missing_cells": missing_cells,
        "suggested_next": ["coerce_numeric", "impute_missing", "scale_features", "prepare_for_training"],
    }


class PrepareRequest(BaseModel):
    upload_id: str
    impute: str = Field(default="median", examples=["median", "mean", "zero"])
    scale: str = Field(default="standard", examples=["standard", "minmax", "none"])


@app.post("/api/prepare-dataset")
def prepare_dataset(req: PrepareRequest) -> dict:
    with _UPLOADS_LOCK:
        rec = _UPLOADS.get(req.upload_id)
        if not rec:
            return {"error": "not_found"}

        df = rec.get("raw_df").copy()

    # Detect feature columns heuristically
    metadata_cols = {"sample_id", "species", "phylum", "replicate"}
    # Coerce numeric where possible for non-metadata columns only
    for c in df.columns:
        if c in metadata_cols:
            continue
        # coerce non-numeric values to NaN so we can impute them deterministically
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Apply imputation to numeric columns
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if req.impute == "median":
        for c in num_cols:
            df[c] = df[c].fillna(df[c].median())
    elif req.impute == "mean":
        for c in num_cols:
            df[c] = df[c].fillna(df[c].mean())
    else:
        for c in num_cols:
            df[c] = df[c].fillna(0.0)

    # Scaling
    scaler = None
    if req.scale in ("standard", "minmax"):
        from sklearn.preprocessing import StandardScaler, MinMaxScaler
        if req.scale == "standard":
            scaler = StandardScaler()
        else:
            scaler = MinMaxScaler()
        df[num_cols] = scaler.fit_transform(df[num_cols])

    # Persist prepared df
    with _UPLOADS_LOCK:
        _UPLOADS[req.upload_id]["prepared_df"] = df
        _UPLOADS[req.upload_id]["prepared_meta"] = {"impute": req.impute, "scale": req.scale}

    preview = df.head(6).to_dict(orient="records")
    return {"upload_id": req.upload_id, "preview": preview, "rows": int(df.shape[0]), "columns": int(df.shape[1]), "next": ["start_training"]}


@app.get("/api/upload/{upload_id}")
def upload_status(upload_id: str) -> dict:
    with _UPLOADS_LOCK:
        rec = _UPLOADS.get(upload_id)
        if not rec:
            return {"error": "not_found"}
        return {"upload_id": upload_id, "filename": rec.get("filename"), "has_prepared": rec.get("prepared_df") is not None}
