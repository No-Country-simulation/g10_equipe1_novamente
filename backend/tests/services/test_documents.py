import hashlib

import pytest

from app.services.documents import (
    MAX_FILE_BYTES,
    MAX_TEXT_CHARS,
    DocumentError,
    DocumentErrorCode,
    read_document,
    read_documents,
)

TOO_LONG = "O documento é longo demais. Envie um documento menor ou divida o arquivo."


def error(filename: str, data: bytes) -> DocumentError:
    with pytest.raises(DocumentError) as raised:
        read_document(filename, data)
    return raised.value


@pytest.mark.parametrize("filename", ["guia.md", "texto-digitado.md"])
def test_valid_markdown_returns_text_and_metadata(filename: str) -> None:
    data = "# Guia\n\nAção de reembolso.\n".encode()

    document = read_document(filename, data)

    assert document.filename == filename
    assert document.extension == "md"
    assert document.mime_type == "text/markdown"
    assert document.size_bytes == len(data)
    assert document.sha256 == hashlib.sha256(data).hexdigest()
    assert document.text == "# Guia\n\nAção de reembolso.\n"


def test_extension_ignores_case() -> None:
    document = read_document("GUIA.MD", b"texto")

    assert document.filename == "GUIA.MD"
    assert document.extension == "md"


@pytest.mark.parametrize("filename", ["guia.txt", "guia", ".md", ""])
def test_other_extensions_are_unsupported(filename: str) -> None:
    raised = error(filename, b"texto")

    assert raised.code == DocumentErrorCode.unsupported_type
    assert raised.message == "Envie um arquivo .md ou PDF, ou digite o texto."
    assert str(raised) == raised.message
    assert raised.filename == filename


def test_file_size_limit() -> None:
    # A limpeza remove os nulos, então o texto fica abaixo do limite de caracteres.
    data = b"a" + b"\x00" * (MAX_FILE_BYTES - 1)

    assert read_document("a.md", data).size_bytes == MAX_FILE_BYTES
    assert error("a.md", b"a" * MAX_FILE_BYTES).code == DocumentErrorCode.too_long

    raised = error("a.md", data + b"\x00")

    assert raised.code == DocumentErrorCode.too_large
    assert raised.message == "O arquivo passa de 5 MiB."
    assert raised.filename == "a.md"


def test_latin1_bytes_are_not_utf8() -> None:
    raised = error("a.md", "ação".encode("latin-1"))

    assert raised.code == DocumentErrorCode.not_utf8
    assert raised.message == "Não foi possível ler o arquivo como texto."
    assert raised.filename == "a.md"


@pytest.mark.parametrize("data", [b"", b" \n\r\n\t ", b"\xef\xbb\xbf\x00\n"])
def test_file_without_text_is_empty(data: bytes) -> None:
    raised = error("a.md", data)

    assert raised.code == DocumentErrorCode.empty
    assert raised.message == "O arquivo não tem texto."
    assert raised.filename == "a.md"


def test_text_length_limit() -> None:
    # "é" ocupa 2 bytes: o limite conta caracteres, não bytes.
    assert len(read_document("a.md", ("é" * MAX_TEXT_CHARS).encode()).text) == (
        MAX_TEXT_CHARS
    )

    raised = error("a.md", ("é" * (MAX_TEXT_CHARS + 1)).encode())

    assert raised.code == DocumentErrorCode.too_long
    assert raised.message == TOO_LONG
    assert raised.filename == "a.md"


def test_text_length_counts_cleaned_text() -> None:
    data = ("a" * MAX_TEXT_CHARS + "\x00").encode()

    assert len(read_document("a.md", data).text) == MAX_TEXT_CHARS


def test_text_is_cleaned_and_hash_uses_original_bytes() -> None:
    data = b"\xef\xbb\xbflinha 1\r\nlinha\x00 2\rlinha 3\n"

    document = read_document("a.md", data)

    assert document.text == "linha 1\nlinha 2\nlinha 3\n"
    assert document.size_bytes == len(data)
    assert document.sha256 == hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize("filename", ["pasta/guia.md", "C:\\pasta\\guia.md"])
def test_filename_drops_folder(filename: str) -> None:
    assert read_document(filename, b"texto").filename == "guia.md"


def test_filename_keeps_255_chars_and_extension() -> None:
    document = read_document("a" * 300 + ".md", b"texto")

    assert document.filename == "a" * 252 + ".md"


def test_checks_run_in_contract_order() -> None:
    big_latin1 = b"\xe7" * (MAX_FILE_BYTES + 1)

    assert error("a.txt", big_latin1).code == DocumentErrorCode.unsupported_type
    assert error("a.md", big_latin1).code == DocumentErrorCode.too_large


def test_read_documents_returns_documents_in_order() -> None:
    documents = read_documents([("a.md", b"um"), ("pasta/b.md", b"dois")])

    assert [d.filename for d in documents] == ["a.md", "b.md"]
    assert [d.text for d in documents] == ["um", "dois"]


@pytest.mark.parametrize(
    "count,message",
    [
        (0, "Envie pelo menos um documento e escolha pelo menos uma saída."),
        (4, "Envie até 3 documentos e escolha até 3 saídas."),
    ],
)
def test_read_documents_checks_count(count: int, message: str) -> None:
    files = [(f"{i}.md", str(i).encode()) for i in range(count)]

    with pytest.raises(DocumentError) as raised:
        read_documents(files)

    assert raised.value.code == DocumentErrorCode.count
    assert raised.value.message == message
    assert raised.value.filename is None


def test_read_documents_rejects_duplicate_content() -> None:
    with pytest.raises(DocumentError) as raised:
        read_documents([("a.md", b"igual"), ("b.md", b"igual")])

    assert raised.value.code == DocumentErrorCode.duplicate
    assert raised.value.message == "Este arquivo já está no curso."
    assert raised.value.filename == "b.md"


def test_read_documents_reports_invalid_file() -> None:
    with pytest.raises(DocumentError) as raised:
        read_documents([("a.md", b"um"), ("b.txt", b"dois")])

    assert raised.value.code == DocumentErrorCode.unsupported_type
    assert raised.value.filename == "b.txt"


def pdf_bytes(*texts: str, password: bool = False) -> bytes:
    from io import BytesIO

    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    for text in texts:
        page = writer.add_blank_page(width=200, height=200)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
        )
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 20 100 Td ({text}) Tj ET".encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
    if password:
        writer.encrypt("senha")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_pdf_pages_and_metadata():
    import hashlib

    from app.services.documents import PAGE_BREAK, read_document, read_documents

    data = pdf_bytes("A", "", "C")
    doc = read_document("GUIA.PDF", data)
    assert doc.extension == "pdf"
    assert doc.mime_type == "application/pdf"
    assert doc.size_bytes == len(data)
    assert doc.sha256 == hashlib.sha256(data).hexdigest()
    assert [page.strip() for page in doc.text.split(PAGE_BREAK)] == ["A", "", "C"]
    assert PAGE_BREAK not in read_document("a.pdf", pdf_bytes("A")).text
    assert len(read_documents([("a.md", b"texto"), ("a.pdf", data)])) == 2
    with pytest.raises(DocumentError) as exc:
        read_documents([("a.pdf", data), ("b.pdf", data)])
    assert exc.value.code == DocumentErrorCode.duplicate


@pytest.mark.parametrize(
    ("data", "code", "message"),
    [
        (
            pdf_bytes("", ""),
            DocumentErrorCode.empty,
            "Este PDF não tem texto. Envie um PDF com texto.",
        ),
        (
            b"invalido",
            DocumentErrorCode.unreadable,
            "Não foi possível abrir o PDF. Envie um PDF sem senha.",
        ),
        (
            pdf_bytes("A", password=True),
            DocumentErrorCode.unreadable,
            "Não foi possível abrir o PDF. Envie um PDF sem senha.",
        ),
    ],
)
def test_pdf_errors(data, code, message):
    with pytest.raises(DocumentError) as exc:
        read_document("guia.pdf", data)
    assert (exc.value.code, exc.value.message, exc.value.filename) == (
        code,
        message,
        "guia.pdf",
    )


def test_pdf_size_limit():
    with pytest.raises(DocumentError) as exc:
        read_document("guia.pdf", b"x" * (5 * 1024 * 1024 + 1))
    assert exc.value.code == DocumentErrorCode.too_large
