from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


HANDBOOK_DIR = Path(__file__).resolve().parents[1] / "data" / "handbook"
REFERENCE_URLS = {
    "01_cpu.md": "https://man7.org/linux/man-pages/man1/top.1.html",
    "02_disk.md": "https://man7.org/linux/man-pages/man1/df.1.html",
    "03_dns.md": "https://www.cloudflare.com/learning/dns/what-is-dns/",
    "04_port.md": "https://man7.org/linux/man-pages/man8/ss.8.html",
    "05_nginx.md": "https://docs.nginx.com/nginx/admin-guide/",
    "06_app_service.md": "https://www.freedesktop.org/software/systemd/man/latest/systemctl.html",
    "07_latency.md": "https://www.cloudflare.com/learning/network-layer/what-is-latency/",
    "08_tls.md": "https://letsencrypt.org/docs/",
}


@dataclass(frozen=True)
class Document:
    source: str
    title: str
    content: str
    url: str = ""


@dataclass(frozen=True)
class Chunk:
    source: str
    title: str
    content: str
    url: str = ""


def load_builtin_documents() -> list[Document]:
    documents: list[Document] = []
    for path in sorted(HANDBOOK_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        title = text.splitlines()[0].lstrip("# ").strip()
        documents.append(
            Document(
                source=path.name,
                title=title,
                content=text,
                url=REFERENCE_URLS.get(path.name, ""),
            )
        )
    return documents


def chunk_documents(
    documents: list[Document], chunk_size: int = 420, overlap: int = 70
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        text = document.content.strip()
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(
                Chunk(
                    source=document.source,
                    title=document.title,
                    content=text[start:end],
                    url=document.url,
                )
            )
            if end == len(text):
                break
            start = max(end - overlap, start + 1)
    return chunks


def parse_uploaded_file(name: str, content: bytes) -> Document:
    suffix = Path(name).suffix.lower()
    if suffix in {".txt", ".md"}:
        text = content.decode("utf-8", errors="replace")
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
            from io import BytesIO

            reader = PdfReader(BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as error:  # noqa: BLE001
            raise ValueError("PDF 解析失败，请确认文件未加密且包含可复制文本。") from error
    else:
        raise ValueError("仅支持 PDF、TXT 和 Markdown 文件。")

    if not text.strip():
        raise ValueError("文件中没有可检索的文本内容。")
    return Document(source=name, title=Path(name).stem, content=text.strip())
