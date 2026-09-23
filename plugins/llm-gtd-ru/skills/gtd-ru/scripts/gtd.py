#!/usr/bin/env python3
"""Создание и обзор отдельной русскоязычной системы GTD."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

FILES = (
    "inbox.md",
    "next-actions.md",
    "projects.md",
    "waiting-for.md",
    "calendar.md",
    "someday-maybe.md",
    "reference.md",
    "horizons.md",
    "product-ideas.md",
)
SKILL = Path(__file__).resolve().parent.parent


def workspace() -> Path:
    configured = os.environ.get("LLM_GTD_RU_ROOT")
    return Path(configured).expanduser().resolve() if configured else Path.cwd().resolve()


def target() -> Path:
    return workspace() / "memory" / "gtd-ru"


def read(name: str) -> str:
    path = target() / name
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def count_lines(name: str, pattern: str) -> int:
    return sum(bool(re.match(pattern, line)) for line in read(name).splitlines())


def project_blocks() -> list[str]:
    return [
        block
        for block in re.split(r"(?=^## )", read("projects.md"), flags=re.M)
        if block.startswith("## ")
    ]


def has_current_step(block: str) -> bool:
    for filename, identifier in re.findall(
        r"\[\[(next-actions|waiting-for)#\^([\w-]+)(?:\||\]\])", block
    ):
        if re.search(
            rf"^- \[ \] .*\^{re.escape(identifier)}(?:\s|$)",
            read(f"{filename}.md"),
            flags=re.M,
        ):
            return True
    return False


def projects() -> tuple[int, int]:
    blocks = project_blocks()
    return len(blocks), sum(not has_current_step(block) for block in blocks)


def init() -> None:
    folder = target()
    folder.mkdir(parents=True, exist_ok=True)
    created = 0
    for name in FILES:
        template = (SKILL / "templates" / "state" / name).read_text(encoding="utf-8")
        path = folder / name
        try:
            with path.open("x", encoding="utf-8") as output:
                output.write(template)
            created += 1
        except FileExistsError:
            pass
    print(f"Каталог: {folder}")
    print(f"Создано файлов: {created}; уже существовало: {len(FILES) - created}.")
    print("Исходная система в memory/gtd/ не затронута.")


def status() -> None:
    folder = target()
    if not folder.is_dir():
        raise SystemExit(f"Каталог {folder} не найден. Сначала запустите команду init.")
    project_count, stalled = projects()
    counts = {
        "Входящие": count_lines("inbox.md", r"^- "),
        "Следующие действия": count_lines("next-actions.md", r"^- \[ \] "),
        "Проекты": project_count,
        "Проекты без следующего шага": stalled,
        "Ожидания": count_lines("waiting-for.md", r"^- \[ \] "),
        "Запасные календарные записи": count_lines("calendar.md", r"^- \d{4}-\d{2}-\d{2} "),
        "Отложенные возможности": count_lines("someday-maybe.md", r"^- \[ \] "),
        "Продуктовые возможности": count_lines("product-ideas.md", r"^- \[ \] "),
    }
    print(f"Состояние GTD: {folder}")
    for label, value in counts.items():
        print(f"{label}: {value}")
    missing = [name for name in FILES if not (folder / name).is_file()]
    if missing:
        print("Не найдены файлы: " + ", ".join(missing))


def review_prep() -> None:
    status()
    print("\nВходящие для разбора:")
    for line in read("inbox.md").splitlines():
        if line.startswith("- "):
            print(line)
    print("\nОжидания для проверки:")
    for line in read("waiting-for.md").splitlines():
        if line.startswith("- [ ] "):
            print(line)
    print("\nПроекты без действующей ссылки на шаг:")
    for block in project_blocks():
        if not has_current_step(block):
            print(block.splitlines()[0])
    print("\nЭто сводка только локальных списков. Внешний календарь прочитайте отдельно.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "status", "review-prep"))
    args = parser.parse_args()
    {"init": init, "status": status, "review-prep": review_prep}[args.command]()


if __name__ == "__main__":
    main()
