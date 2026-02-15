from __future__ import annotations

from dataclasses import dataclass


def _pdf_escape(text: str) -> str:
    return (
        (text or "")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", "")
    )


@dataclass(frozen=True)
class PdfDocument:
    content: bytes
    filename: str


def build_simple_text_pdf(*, title: str, lines: list[str], filename: str) -> PdfDocument:
    """
    Génère un PDF 1 page simple (texte) sans dépendances externes.
    Suffisant pour un reçu / preuve académique.
    """

    safe_lines = [title, ""] + [line for line in lines if line is not None]
    content_lines = []
    for line in safe_lines:
        content_lines.append(f"({_pdf_escape(line)}) Tj")
        content_lines.append("T*")

    content_stream = "\n".join(
        [
            "BT",
            "/F1 12 Tf",
            "14 TL",
            "72 760 Td",
            *content_lines,
            "ET",
            "",
        ]
    ).encode("latin-1", errors="replace")

    objects: list[bytes] = []

    def add(obj: str) -> int:
        objects.append(obj.encode("latin-1", errors="replace"))
        return len(objects)

    add("<< /Type /Catalog /Pages 2 0 R >>")
    add("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    add(
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
    )
    add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    add("<< /Length 0 >>")

    pdf_parts: list[bytes] = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets: list[int] = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(p) for p in pdf_parts))
        if index == 5:
            pdf_parts.append(f"{index} 0 obj\n".encode("latin-1"))
            pdf_parts.append(b"<< /Length " + str(len(content_stream)).encode("latin-1") + b" >>\n")
            pdf_parts.append(b"stream\n")
            pdf_parts.append(content_stream)
            pdf_parts.append(b"endstream\nendobj\n")
            continue
        pdf_parts.append(f"{index} 0 obj\n".encode("latin-1"))
        pdf_parts.append(obj)
        pdf_parts.append(b"\nendobj\n")

    xref_offset = sum(len(p) for p in pdf_parts)
    pdf_parts.append(b"xref\n")
    pdf_parts.append(f"0 {len(objects) + 1}\n".encode("latin-1"))
    pdf_parts.append(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf_parts.append(f"{off:010d} 00000 n \n".encode("latin-1"))
    pdf_parts.append(b"trailer\n")
    pdf_parts.append(f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("latin-1"))
    pdf_parts.append(b"startxref\n")
    pdf_parts.append(f"{xref_offset}\n".encode("latin-1"))
    pdf_parts.append(b"%%EOF\n")

    return PdfDocument(content=b"".join(pdf_parts), filename=filename)
