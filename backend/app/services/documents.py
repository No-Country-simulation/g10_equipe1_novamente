import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

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
class _Reader:
    mime_type: str
    extract: Callable[[str, bytes], str]


# Um leitor por extensão. Um formato novo entra com uma linha aqui.
_READERS = {"md": _Reader("text/markdown", _read_markdown)}


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
