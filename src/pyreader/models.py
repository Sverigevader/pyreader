from dataclasses import dataclass


@dataclass(slots=True)
class Chapter:
    id: str
    title: str
    href: str
    text: str


@dataclass(slots=True)
class BookMeta:
    title: str
    creator: str
    language: str
