from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import os
import uuid

from ..services.llm_service import build_compression_config, generate_explanation
from ..services.compression_service import process_document, get_file_size_mb

router = APIRouter()

UPLOAD_DIR = "uploads"
WORK_DIR = "work"
THRESHOLD_MB = 50.0  # business rule

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)


@router.post("/optimize")
async def optimize_document(
    file: UploadFile = File(...),
    prompt: str = Form("Compress to under 10MB and keep charts/text clear."),
):
    """
    Main entrypoint for the app.

    Rule:
    - If original file size <= THRESHOLD_MB:
        -> Return original file unchanged.
    - If > THRESHOLD_MB:
        -> If PDF: compress to smaller PDF.
        -> If PPT/PPTX: convert to PDF + compress.
    """
    try:
        job_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1].lower()  # .pptx, .ppt, .pdf, etc.
        input_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext or ''}")

        # Save upload to disk
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)

        original_size_mb = get_file_size_mb(input_path)

        # 1. If file <= THRESHOLD_MB: return original, no compression
        if original_size_mb <= THRESHOLD_MB:
            explanation = generate_explanation(
                original_size_mb=original_size_mb,
                final_size_mb=original_size_mb,
                config={},
                threshold_mb=THRESHOLD_MB,
                compressed=False,
            )

            safe_explanation = " ".join(explanation.splitlines()).replace("\r", " ")
            if len(safe_explanation) > 900:
                safe_explanation = safe_explanation[:900] + " ..."

            headers = {
                "X-Original-Size-MB": f"{original_size_mb:.4f}",
                "X-Final-Size-MB": f"{original_size_mb:.4f}",
                "X-Compression-Ratio": "1.0000",
                "X-Compressed": "false",
                "X-Explanation": safe_explanation,
            }

            # Choose correct media type for original
            if ext == ".pdf":
                media_type = "application/pdf"
            elif ext == ".pptx":
                media_type = (
                    "application/vnd.openxmlformats-officedocument."
                    "presentationml.presentation"
                )
            elif ext == ".ppt":
                media_type = "application/vnd.ms-powerpoint"
            else:
                media_type = "application/octet-stream"

            return FileResponse(
                input_path,
                media_type=media_type,
                filename=file.filename,
                headers=headers,
            )

        # 2. If file > THRESHOLD_MB: build config and compress
        config = build_compression_config(original_size_mb, prompt)
        output_pdf, original_size, final_size = process_document(
            input_path, WORK_DIR, config
        )

        compression_ratio = final_size / original_size if original_size > 0 else 0.0

        explanation = generate_explanation(
            original_size_mb=original_size,
            final_size_mb=final_size,
            config=config,
            threshold_mb=THRESHOLD_MB,
            compressed=True,
        )

        # Log explanation for debugging
        print("=== COMPRESSION EXPLANATION ===")
        print(explanation)
        print("=== END EXPLANATION ===")

        # Sanitise explanation for header
        safe_explanation = " ".join(explanation.splitlines()).replace("\r", " ")
        if len(safe_explanation) > 900:
            safe_explanation = safe_explanation[:900] + " ..."

        headers = {
            "X-Original-Size-MB": f"{original_size:.4f}",
            "X-Final-Size-MB": f"{final_size:.4f}",
            "X-Compression-Ratio": f"{compression_ratio:.4f}",
            "X-Compressed": "true",
            "X-Explanation": safe_explanation,
        }

        return FileResponse(
            output_pdf,
            media_type="application/pdf",
            filename=f"compressed_{os.path.splitext(file.filename)[0]}.pdf",
            headers=headers,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
