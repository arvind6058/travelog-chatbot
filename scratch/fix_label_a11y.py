"""
Add htmlFor/id pairs to sibling <label>/<input> pairs.

These labels are not wrapping labels, so without htmlFor a screen reader cannot
associate any of the ~12 registration fields with their label text.
"""
import re
import pathlib
import sys

TARGETS = [
    pathlib.Path(__file__).resolve().parent.parent
    / "chatbot" / "app" / "(customer)" / "logistics" / "register" / "page.tsx",
]

PATTERN = re.compile(
    r'(?P<label><label )(?P<lattr>className="[^"]*")(?P<lbody>>.*?</label>)'
    r'(?P<gap>\s*)'
    r'(?P<input><input\s*\n(?P<iws>\s*)type="[^"]*"\s*\n(?P<nws>\s*)name="(?P<name>[A-Za-z0-9_]+)")',
    re.S,
)


def add_ids(source: str) -> tuple[str, int]:
    def replace(match: re.Match) -> str:
        name = match.group("name")
        return (
            f'<label htmlFor="{name}" {match.group("lattr")}{match.group("lbody")}'
            f'{match.group("gap")}'
            f'{match.group("input")}\n{match.group("nws")}id="{name}"'
        )

    return PATTERN.subn(replace, source)


def main() -> int:
    total = 0
    for path in TARGETS:
        if not path.exists():
            print(f"missing: {path}")
            return 1
        original = path.read_text(encoding="utf-8")
        updated, count = add_ids(original)
        if count:
            path.write_text(updated, encoding="utf-8")
        print(f"{path.name}: paired {count} label/input(s)")
        total += count
    print(f"total paired: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
