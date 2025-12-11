# backend/app/services/compression_service.py
import os
import subprocess
import uuid
from typing import Tuple


def get_file_size_mb(path: str) -> float:
    """Return size of a file in MB."""
    return os.path.getsize(path) / (1024 * 1024)


def convert_pptx_to_pdf(input_path: str, output_dir: str) -> str:
    """
    Convert PPT/PPTX to PDF using LibreOffice in headless mode.

    We explicitly use the 'impress_pdf_Export' filter which is tuned
    for presentation documents and usually gives better / more stable
    results than the generic 'pdf' filter.
    """
    os.makedirs(output_dir, exist_ok=True)

    subprocess.run(
        [
            "soffice",  # in Docker/WSL this is fine; on Windows desktop it would be 'soffice.exe'
            "--headless",
            "--convert-to",
            "pdf:impress_pdf_Export",
            "--outdir",
            output_dir,
            input_path,
        ],
        check=True,
    )

    base = os.path.splitext(os.path.basename(input_path))[0]
    return os.path.join(output_dir, base + ".pdf")


def compress_pdf(input_pdf: str, output_pdf: str, config: dict) -> None:
    """
    Compress a PDF using Ghostscript with tunable quality.

    Config fields used (all optional):
      - pdf_profile: "screen" / "ebook" / "printer"   (default: "ebook")
      - image_dpi: int, e.g. 150, 200, 300          (default: 200)
      - image_quality: float 0–1                    (default: 0.75)
          mapped to Ghostscript -dJPEGQ ≈ 40–95
    """
    profile_map = {
        "screen": "/screen",
        "ebook": "/ebook",
        "printer": "/printer",
    }
    pdf_profile = profile_map.get(config.get("pdf_profile", "ebook"), "/ebook")

    image_dpi = int(config.get("image_dpi", 200))
    image_quality = float(config.get("image_quality", 0.75))

    # Clamp and map image_quality 0–1 → JPEGQ ~40–95
    clamped_q = max(0.0, min(1.0, image_quality))
    jpeg_q = int(40 + (95 - 40) * clamped_q)

    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.5",
        f"-dPDFSETTINGS={pdf_profile}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        # Image downsampling – main lever for size vs quality
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dColorImageDownsampleType=/Bicubic",
        f"-dColorImageResolution={image_dpi}",
        "-dGrayImageDownsampleType=/Bicubic",
        f"-dGrayImageResolution={image_dpi}",
        "-dMonoImageDownsampleType=/Subsample",
        "-dMonoImageResolution=300",
        # JPEG quality for color/gray images
        f"-dJPEGQ={jpeg_q}",
        # Output file
        f"-sOutputFile={output_pdf}",
        input_pdf,
    ]

    subprocess.run(cmd, check=True)


def process_document(
    upload_path: str, work_dir: str, config: dict
) -> Tuple[str, float, float]:
    """
    Full pipeline:
      - If PPT/PPTX: convert to PDF (LibreOffice).
      - If PDF: use as-is.
      - Compress PDF with Ghostscript.

    Returns:
      (output_pdf_path, original_size_mb, final_size_mb)
    """
    os.makedirs(work_dir, exist_ok=True)

    original_size = get_file_size_mb(upload_path)
    ext = os.path.splitext(upload_path)[1].lower()

    if ext in [".ppt", ".pptx"]:
        pdf_path = convert_pptx_to_pdf(upload_path, work_dir)
    elif ext == ".pdf":
        pdf_path = upload_path
    else:
        raise ValueError("Unsupported file type. Only PPT, PPTX and PDF are allowed.")

    job_id = str(uuid.uuid4())
    output_pdf = os.path.join(work_dir, f"compressed_{job_id}.pdf")

    # Compress PDF
    compress_pdf(pdf_path, output_pdf, config)

    final_size = get_file_size_mb(output_pdf)
    return output_pdf, original_size, final_size
