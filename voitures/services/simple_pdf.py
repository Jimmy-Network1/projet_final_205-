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


def _pdf_string(text: str) -> bytes:
    """
    Construit une chaîne PDF (entre parenthèses) encodée en WinAnsi (cp1252),
    ce qui couvre correctement la plupart des caractères français (accents, ’, —, …).
    """
    raw = (text or "").replace("\r", "").encode("cp1252", errors="replace")
    raw = raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    return b"(" + raw + b")"


def _fmt_num(value: float) -> str:
    # PDF accepte les nombres en notation décimale avec '.' ; on limite le bruit.
    s = f"{value:.3f}".rstrip("0").rstrip(".")
    return s if s else "0"


class PdfCanvas:
    """
    Mini-canvas PDF (1 page) sans dépendances externes.
    Supporte texte, lignes et rectangles, suffisant pour des reçus/factures.
    """

    def __init__(self) -> None:
        self._ops: list[bytes] = []

    def stream(self) -> bytes:
        return b"\n".join(self._ops) + (b"\n" if self._ops else b"")

    def raw(self, op: str) -> None:
        self._ops.append(op.encode("ascii", errors="strict"))

    def save(self) -> None:
        self._ops.append(b"q")

    def restore(self) -> None:
        self._ops.append(b"Q")

    def set_stroke_color(self, r: float, g: float, b: float) -> None:
        self.raw(f"{_fmt_num(r)} {_fmt_num(g)} {_fmt_num(b)} RG")

    def set_fill_color(self, r: float, g: float, b: float) -> None:
        self.raw(f"{_fmt_num(r)} {_fmt_num(g)} {_fmt_num(b)} rg")

    def set_line_width(self, width: float) -> None:
        self.raw(f"{_fmt_num(width)} w")

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.raw(
            f"{_fmt_num(x1)} {_fmt_num(y1)} m {_fmt_num(x2)} {_fmt_num(y2)} l S"
        )

    def rect(self, x: float, y: float, w: float, h: float, *, stroke: bool, fill: bool) -> None:
        paint = "B" if (stroke and fill) else ("S" if stroke else "f")
        self.raw(f"{_fmt_num(x)} {_fmt_num(y)} {_fmt_num(w)} {_fmt_num(h)} re {paint}")

    def text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        font: str = "F1",
        size: float = 12,
        color: tuple[float, float, float] | None = None,
    ) -> None:
        self._ops.append(b"BT")
        self._ops.append(f"/{font} {_fmt_num(size)} Tf".encode("ascii"))
        if color is not None:
            r, g, b = color
            self._ops.append(f"{_fmt_num(r)} {_fmt_num(g)} {_fmt_num(b)} rg".encode("ascii"))
        self._ops.append(f"1 0 0 1 {_fmt_num(x)} {_fmt_num(y)} Tm".encode("ascii"))
        self._ops.append(_pdf_string(text) + b" Tj")
        self._ops.append(b"ET")


def estimate_text_width(text: str, *, font: str, size: float) -> float:
    """
    Estimation simple (sans métriques). Suffisant pour aligner proprement à droite/centrer.
    """
    if not text:
        return 0.0
    if font.upper() in {"F3", "COURIER"}:
        return len(text) * 0.6 * size

    narrow = set(" .,:;!|iIl1'’`")
    wide = set("MW@#%&")
    total = 0.0
    for ch in text:
        if ch in narrow:
            total += 0.28
        elif ch in wide:
            total += 0.78
        elif ch == " ":
            total += 0.28
        else:
            total += 0.56
    return total * size


def build_one_page_pdf(*, content_stream: bytes, filename: str, fonts: dict[str, str]) -> PdfDocument:
    """
    Construit un PDF 1 page avec un content stream et des polices Type1 (Base14).
    `fonts` mappe un nom de ressource (ex: F1) vers un BaseFont (ex: Helvetica).
    """
    objects: list[bytes] = []

    def add(obj: bytes) -> int:
        objects.append(obj)
        return len(objects)

    # Réservation des 3 premiers objets (Catalog / Pages / Page)
    # Les références seront insérées après création des fonts/contents.
    add(b"<< /Type /Catalog /Pages 2 0 R >>")  # 1
    add(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")  # 2
    add(b"")  # 3 placeholder /Page

    font_obj_nums: dict[str, int] = {}
    for res_name, base_font in fonts.items():
        font_obj_nums[res_name] = add(
            (
                f"<< /Type /Font /Subtype /Type1 /BaseFont /{base_font} "
                f"/Encoding /WinAnsiEncoding >>"
            ).encode("ascii")
        )

    contents_obj_num = add(b"")  # placeholder; stream géré à l'écriture

    # Page object (références connues maintenant)
    font_entries = " ".join(f"/{k} {v} 0 R" for k, v in font_obj_nums.items())
    page_obj = (
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        f"/Resources << /Font << {font_entries} >> >> "
        f"/Contents {contents_obj_num} 0 R >>"
    ).encode("ascii")
    objects[2] = page_obj

    pdf_parts: list[bytes] = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets: list[int] = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(p) for p in pdf_parts))
        if index == contents_obj_num:
            pdf_parts.append(f"{index} 0 obj\n".encode("ascii"))
            pdf_parts.append(b"<< /Length " + str(len(content_stream)).encode("ascii") + b" >>\n")
            pdf_parts.append(b"stream\n")
            pdf_parts.append(content_stream)
            if not content_stream.endswith(b"\n"):
                pdf_parts.append(b"\n")
            pdf_parts.append(b"endstream\nendobj\n")
            continue

        pdf_parts.append(f"{index} 0 obj\n".encode("ascii"))
        pdf_parts.append(obj)
        pdf_parts.append(b"\nendobj\n")

    xref_offset = sum(len(p) for p in pdf_parts)
    pdf_parts.append(b"xref\n")
    pdf_parts.append(f"0 {len(objects) + 1}\n".encode("ascii"))
    pdf_parts.append(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf_parts.append(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf_parts.append(b"trailer\n")
    pdf_parts.append(f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("ascii"))
    pdf_parts.append(b"startxref\n")
    pdf_parts.append(f"{xref_offset}\n".encode("ascii"))
    pdf_parts.append(b"%%EOF\n")

    return PdfDocument(content=b"".join(pdf_parts), filename=filename)


def build_simple_text_pdf(*, title: str, lines: list[str], filename: str) -> PdfDocument:
    """
    Génère un PDF 1 page simple (texte) sans dépendances externes.
    Suffisant pour un reçu / preuve académique.
    """

    safe_lines = [title, ""] + [line for line in lines if line is not None]
    ops: list[bytes] = [
        b"BT",
        b"/F1 12 Tf",
        b"14 TL",
        b"1 0 0 1 72 760 Tm",
    ]
    for line in safe_lines:
        ops.append(_pdf_string(line) + b" Tj")
        ops.append(b"T*")
    ops.append(b"ET")

    content_stream = b"\n".join(ops) + b"\n"
    return build_one_page_pdf(
        content_stream=content_stream,
        filename=filename,
        fonts={"F1": "Helvetica"},
    )
