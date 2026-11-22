import hashlib
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO
from math import hypot
from pathlib import PurePosixPath

from pypdf import PageObject, PdfReader, mult
from pypdf.generic import DictionaryObject
from pypdf.generic._font import Font

PAGE_BREAK = "\f"

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 150_000
MAX_DOCUMENTS = 3
MAX_FILENAME_CHARS = 255


class DocumentErrorCode(StrEnum):
    unsupported_type = "unsupported_type"
    empty = "empty"
    too_large = "too_large"
    too_long = "too_long"
    not_utf8 = "not_utf8"
    duplicate = "duplicate"
    count = "count"  # type: ignore[assignment]  # o contrato fixa o nome, que coincide com str.count
    unreadable = "unreadable"


class DocumentError(ValueError):
    def __init__(
        self, code: DocumentErrorCode, message: str, filename: str | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.filename = filename


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    filename: str
    extension: str
    mime_type: str
    size_bytes: int
    sha256: str
    text: str


def _read_markdown(filename: str, data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise DocumentError(
            DocumentErrorCode.not_utf8,
            "Não foi possível ler o arquivo como texto.",
            filename,
        ) from None


@dataclass(frozen=True, slots=True)
class _PdfTextRun:
    text: str
    x: float
    y: float
    direction: tuple[bool, bool]
    height: float
    width_scale: float
    font: DictionaryObject | None


def _extract_pdf_page(page: PageObject) -> str:
    lines: list[str] = []
    line: list[str] = []
    previous: _PdfTextRun | None = None
    pending_line_break = False
    widths_by_font: dict[int, tuple[dict[str, float], float, float]] = {}

    def word_gap(run: _PdfTextRun, next_x: float) -> bool:
        font_key = id(run.font)
        if font_key not in widths_by_font:
            font = Font.from_font_resource(run.font or DictionaryObject())
            # O visitante entrega Unicode. As larguras da fonte usam códigos de glifos.
            widths = {}
            for code, width in font.character_widths.items():
                if len(code) == 1:
                    char = code
                    if isinstance(font.encoding, dict):
                        char = font.encoding.get(ord(code), code)
                    widths[font.character_map.get(char, char)] = width
            widths_by_font[font_key] = (
                widths,
                font.character_widths["default"],
                font.space_width,
            )
        widths, default_width, space_width = widths_by_font[font_key]
        text_width = sum(widths.get(char, default_width) for char in run.text)
        return next_x - run.x >= (text_width + space_width) * run.width_scale

    def visit(
        text: str,
        cm: list[float],
        tm: list[float],
        font: DictionaryObject | None,
        font_size: float,
    ) -> None:
        nonlocal pending_line_break, previous
        pending_line_break |= text.startswith(("\r", "\n"))
        ends_line = text.endswith(("\r", "\n"))
        text = text.strip("\r\n")
        if not text:
            return
        a, b, c, d, x, y = mult(tm, cm)
        vertical = abs(b) > abs(a)
        if vertical:
            x, y = y, x
        backwards = (b if vertical else a) < 0
        if backwards:
            x = -x
        height = abs(font_size) * hypot(c, d)
        direction = (vertical, backwards)
        if previous is not None:
            height_reference = max(previous.height, height)
            gap = abs(y - previous.y)
            # A geometria só intervém nas quebras emitidas pelo pypdf. A soma das
            # larguras dos glifos ignora os ajustes de TJ dentro de uma palavra.
            same_baseline = direction == previous.direction and gap <= 0.01
            same_line = not pending_line_break or same_baseline
            if not text.strip(" \t"):
                if same_line and not line[-1].endswith((" ", "\t")):
                    line.append(" ")
                pending_line_break |= ends_line
                return
            if not same_line:
                lines.append("".join(line).strip(" \t"))
                line.clear()
                if gap > 1.5 * height_reference:
                    lines.append("")
            elif (
                pending_line_break
                and not line[-1].endswith((" ", "\t"))
                and not text.startswith((" ", "\t"))
                and word_gap(previous, x)
            ):
                line.append(" ")
        elif not text.strip(" \t"):
            return
        line.append(text)
        pending_line_break = ends_line
        previous = _PdfTextRun(
            text, x, y, direction, height, abs(font_size) * hypot(a, b) / 1000, font
        )

    page.extract_text(visitor_text=visit)
    if line:
        lines.append("".join(line).strip(" \t"))
    return "\n".join(lines)


def _read_pdf(filename: str, data: bytes) -> str:
    # Diagnósticos do pypdf podem conter bytes do documento.
    logger = logging.getLogger("pypdf")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise ValueError("PDF protegido")
        pages = [
            _extract_pdf_page(page).replace(PAGE_BREAK, "\n") for page in reader.pages
        ]
    except Exception:
        raise DocumentError(
            DocumentErrorCode.unreadable,
            "Não foi possível abrir o PDF. Envie um PDF sem senha.",
            filename,
        ) from None
    if not any(page.strip() for page in pages):
        raise DocumentError(
            DocumentErrorCode.empty,
            "Este PDF não tem texto. Envie um PDF com texto.",
            filename,
        )
    return PAGE_BREAK.join(pages)


@dataclass(frozen=True, slots=True)
class _Reader:
    mime_type: str
    extract: Callable[[str, bytes], str]


# Um leitor por extensão. Um formato novo entra com uma linha aqui.
_READERS = {
    "md": _Reader("text/markdown", _read_markdown),
    "pdf": _Reader("application/pdf", _read_pdf),
}


def _clean_filename(filename: str) -> str:
    name = PurePosixPath(filename.replace("\\", "/")).name
    if len(name) <= MAX_FILENAME_CHARS:
        return name
    suffix = PurePosixPath(name).suffix
    return name[: MAX_FILENAME_CHARS - len(suffix)] + suffix


def _clean_text(text: str) -> str:
    return (
        text.removeprefix("﻿")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\x00", "")
    )


def read_document(filename: str, data: bytes) -> ExtractedDocument:
    name = _clean_filename(filename)
    extension = PurePosixPath(name).suffix.removeprefix(".").lower()
    reader = _READERS.get(extension)
    if reader is None:
        raise DocumentError(
            DocumentErrorCode.unsupported_type,
            "Envie um arquivo .md ou PDF, ou digite o texto.",
            name,
        )
    if len(data) > MAX_FILE_BYTES:
        raise DocumentError(
            DocumentErrorCode.too_large, "O arquivo passa de 5 MiB.", name
        )
    text = _clean_text(reader.extract(name, data))
    if not text.strip():
        raise DocumentError(DocumentErrorCode.empty, "O arquivo não tem texto.", name)
    if len(text) > MAX_TEXT_CHARS:
        raise DocumentError(
            DocumentErrorCode.too_long,
            "O documento é longo demais. Envie um documento menor ou divida o arquivo.",
            name,
        )
    return ExtractedDocument(
        filename=name,
        extension=extension,
        mime_type=reader.mime_type,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        text=text,
    )


def read_documents(files: Sequence[tuple[str, bytes]]) -> list[ExtractedDocument]:
    if not files:
        raise DocumentError(
            DocumentErrorCode.count,
            "Envie pelo menos um documento e escolha pelo menos uma saída.",
        )
    if len(files) > MAX_DOCUMENTS:
        raise DocumentError(
            DocumentErrorCode.count,
            "Envie até 3 documentos e escolha até 3 saídas.",
        )
    documents: list[ExtractedDocument] = []
    seen: set[str] = set()
    for filename, data in files:
        document = read_document(filename, data)
        if document.sha256 in seen:
            raise DocumentError(
                DocumentErrorCode.duplicate,
                "Este arquivo já está no curso.",
                document.filename,
            )
        seen.add(document.sha256)
        documents.append(document)
    return documents
