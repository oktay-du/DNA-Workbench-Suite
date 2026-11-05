"""Coverage-guided local parser fuzzing; never reads profiles or launches tools."""

import sys
import atheris

with atheris.instrument_imports():
    from genealogy_research import parse
    from security_paths import identifier


def test_input(data):
    text = data.decode("utf-8", errors="replace")
    for operation in (parse, identifier):
        try:
            operation(text)
        except ValueError:
            pass  # Malformed input is expected; unexpected exceptions are failures.


if __name__ == "__main__":
    atheris.Setup(sys.argv, test_input)
    atheris.Fuzz()
