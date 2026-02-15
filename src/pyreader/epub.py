from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import posixpath
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from .models import BookMeta, Chapter
from .text_utils import html_to_text


NS_CONTAINER = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
NS_OPF = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}


@dataclass(slots=True)
class EpubBook:
    meta: BookMeta
    chapters: list[Chapter]


def _read_container_path(zf: ZipFile) -> str:
    xml = zf.read("META-INF/container.xml")
    root = ET.fromstring(xml)
    node = root.find("c:rootfiles/c:rootfile", NS_CONTAINER)
    if node is None:
        raise ValueError("Invalid EPUB: missing rootfile in container.xml")
    full_path = node.attrib.get("full-path")
    if not full_path:
        raise ValueError("Invalid EPUB: rootfile has no full-path")
    return full_path


def _child_text(root: ET.Element, xpath: str, default: str = "") -> str:
    node = root.find(xpath, NS_OPF)
    return (node.text or default).strip() if node is not None else default


def _resolve_href(base_opf: str, href: str) -> str:
    opf_dir = str(PurePosixPath(base_opf).parent)
    if opf_dir in {"", "."}:
        return posixpath.normpath(href)
    return posixpath.normpath(posixpath.join(opf_dir, href))


def load_epub(path: str) -> EpubBook:
    with ZipFile(path) as zf:
        opf_path = _read_container_path(zf)
        opf_xml = zf.read(opf_path)
        package = ET.fromstring(opf_xml)

        title = _child_text(package, "opf:metadata/dc:title", "Untitled")
        creator = _child_text(package, "opf:metadata/dc:creator", "Unknown")
        language = _child_text(package, "opf:metadata/dc:language", "")
        meta = BookMeta(title=title, creator=creator, language=language)

        manifest_map: dict[str, tuple[str, str]] = {}
        for item in package.findall("opf:manifest/opf:item", NS_OPF):
            item_id = item.attrib.get("id", "")
            href = item.attrib.get("href", "")
            media = item.attrib.get("media-type", "")
            if item_id and href:
                manifest_map[item_id] = (href, media)

        chapters: list[Chapter] = []
        chapter_index = 1
        for itemref in package.findall("opf:spine/opf:itemref", NS_OPF):
            idref = itemref.attrib.get("idref", "")
            if not idref or idref not in manifest_map:
                continue
            href, media = manifest_map[idref]
            if media not in {"application/xhtml+xml", "text/html", "application/xml"}:
                continue

            full_href = _resolve_href(opf_path, href)
            try:
                html = zf.read(full_href).decode("utf-8", errors="replace")
            except KeyError:
                continue

            text = html_to_text(html)
            chapter = Chapter(
                id=idref,
                title=f"Chapter {chapter_index}",
                href=full_href,
                text=text,
            )
            chapters.append(chapter)
            chapter_index += 1

        if not chapters:
            raise ValueError("No readable chapters found in EPUB spine")

        return EpubBook(meta=meta, chapters=chapters)
