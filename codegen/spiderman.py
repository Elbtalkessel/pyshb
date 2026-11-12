#!/usr/bin/env python
"""Structured manpage parser for the Phase 3 codegen pipeline.

Turns a manpage into a :class:`codegen.schema.CommandSchema`: flags with their
exact spelling, value type, arity and docstring; a one-line summary; and
subcommand references. Fetching is confined to :func:`fetch_manual_lines` — every
parser below is pure over a ``Sequence[str]`` of lines, so tests run against
captured fixtures, never against ``man``.

The nushell ``dump_to_extern`` / ``dump_to_comfunc`` / ``dump_to_nuscript``
emitters this module used to ship are gone; the Python emitter (step 3) consumes
the schema instead.
"""

import argparse
import re
import subprocess
from collections.abc import Iterator, Sequence

from codegen.schema import (
    CommandSchema,
    ParamArity,
    ParamSchema,
    ParamValueType,
    SubcommandSchema,
)

# A flag entry is a line indented five spaces and starting with a dash.
# Description lines are indented further (twelve spaces) and section
# sub-headings three, so neither collides with this.
_FLAG_PREFIX = "     -"

# Value placeholders that mean "an integer" rather than "a string". After the
# surrounding ``<...>`` / ``[...]`` brackets are stripped, a token matching one
# of these is an INT; anything else is a STR, because guessing INT from a name
# like ``pattern`` is silent damage the schema should not record.
_NUMERIC_HINTS = frozenset({"n", "num", "number"})

# Sections that never carry flag definitions: NAME is the summary source and
# SYNOPSIS is a usage listing. DESCRIPTION is *not* excluded — the GNU coreutils
# manpages (help2man-generated) document their flags there rather than in a
# separate OPTIONS section, and :func:`parse_flags` only matches flag-tag lines.
_NON_FLAG_SECTIONS = frozenset({"NAME", "SYNOPSIS"})

# An all-uppercase line is a section title.
_SECTION_RE = re.compile(r"^[A-Z][A-Z ]+$")


def fetch_manual_lines(command: str) -> list[str]:
    """Return ``command``'s manpage as non-empty lines, newlines stripped.

    The single function that runs ``man``. Every parsing function in this
    module is pure over the returned ``Sequence[str]``.

    Args:
        command: The command to fetch, as passed to ``man``.

    Returns:
        The manpage's non-empty lines, leading indentation preserved. groff's
        line-hyphenation marker (U+2010) is stripped so the captured text is
        clean ASCII and a hyphenated word re-joins across the line break.

    Raises:
        RuntimeError: If ``man`` fails or returns nothing.
    """
    proc = subprocess.run(
        ["man", command], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip()
        raise RuntimeError(detail or f"man {command} returned nothing")
    return [
        line.replace("\u2010", "")
        for line in proc.stdout.splitlines()
        if line.strip()
    ]


def group_by_section(lines: Sequence[str]) -> Iterator[tuple[str, list[str]]]:
    """Group lines into ``(section_title, content_lines)`` pairs.

    An all-uppercase line is a section title; everything between two titles is
    that section's content.

    Args:
        lines: The manpage's non-empty lines.

    Yields:
        Each section title with its content lines, in order.
    """
    content: list[str] = []
    section = ""
    for line in lines:
        if not _SECTION_RE.search(line):
            if section:
                content.append(line)
            continue
        if section and content:
            yield section, content
        section = line
        content = []
    if section and content:
        yield section, content


def _indent(line: str) -> int:
    """Number of leading spaces in ``line``."""
    return len(line) - len(line.lstrip(" "))


def _is_eq_hint(value: str) -> bool:
    """True if ``value`` is a placeholder, not a literal (``--color=never``).

    A ``--flag=VALUE`` where ``VALUE`` is lowercase is an inline mention of one
    concrete value (help2man prose), not the flag definition; the placeholder
    form is uppercase (``--color=WHEN``) or bracketed.
    """
    v = value.strip()
    if not v:
        return False
    if v.startswith(("[", "<", "{")):
        return True
    return v.split()[0].isupper()


def _is_space_hint(text: str) -> bool:
    """True if ``text`` is a value placeholder, not a same-line description.

    A space-joined value is a single token (``-D debugopts``, ``-F LIST``),
    whereas a same-line description is prose (``-c  with -lt: ...``) or a
    parenthetical note (``-f  (ignored)``).
    """
    t = text.strip()
    if not t:
        return False
    if "..." in t:
        return True
    if t.startswith(("[", "<", "{")):
        return True
    if t.startswith("("):
        return False
    return len(t.split()) == 1


def _parse_flag_line(
    line: str,
) -> tuple[str, str | None, str | None, str | None] | None:
    """Parse one flag-tag line into ``(flag, short, hint, arg_join)``.

    Handles the GNU ``-s HINT, --long=HINT`` shape, the find-style
    ``-flag HINT`` shape, and the help2man shapes where the description runs on
    the same line as the flag (``-c  with -lt: ...``) or where prose wraps onto
    a dash-prefixed line (``-f  or  --force option ...``). The first short and
    first long spelling win when a flag has aliases.

    Args:
        line: The raw flag line, five-space indent and all.

    Returns:
        ``flag`` — canonical spelling (long form when present, else short);
        ``short`` — the single-dash spelling, for reference; ``hint`` — the
        argument placeholder, or ``None`` for a boolean flag; ``arg_join`` —
        ``"="``, ``" "`` or ``None`` (inherit the command default). ``None``
        when the line is prose that merely wraps onto a dash, not a flag.
    """
    text = line[5:]
    short: str | None = None
    short_hint: str | None = None
    long: str | None = None
    long_hint: str | None = None
    long_join: str | None = None
    saw_long = False

    for clause in (part.strip() for part in text.split(", ")):
        if clause.startswith("--"):
            saw_long = True
            body = clause[2:]
            if "[" in body:
                # Optional value: --flag[=VALUE] or --flag=[VALUE] — keep the
                # bracket as the hint so the classifier records the ambiguity.
                head, _, bracketed = body.partition("[")
                head = head.rstrip("=")
                if long is None:
                    long = "--" + head
                if long_hint is None:
                    long_hint = "[" + bracketed
                if "=" in bracketed:
                    long_join = "="
            else:
                name, sep, hint = body.partition("=")
                if sep and hint and _is_eq_hint(hint):
                    # --flag=VALUE (placeholder)
                    if long is None:
                        long = "--" + name
                    if long_hint is None:
                        long_hint = hint
                        long_join = "="
                elif sep:
                    # --flag=literal (e.g. "--color=never" in prose): not a flag
                    # definition — do not record the long spelling.
                    continue
                else:
                    # --flag or --flag VALUE
                    head, _, tail = name.partition(" ")
                    if head and all(c.isalnum() or c == "-" for c in head):
                        if long is None:
                            long = "--" + head
                        if tail and _is_space_hint(tail) and long_hint is None:
                            long_hint = tail
                            long_join = " "
        elif clause.startswith("-"):
            head, _, tail = clause[1:].partition(" ")
            if head and head.isalnum():
                if short is None:
                    short = "-" + head
                if tail and _is_space_hint(tail) and short_hint is None:
                    short_hint = tail

    flag = long or short or ""
    if not flag:
        return None
    hint = long_hint if long_hint is not None else short_hint
    if long_join is not None:
        arg_join = long_join
    elif short_hint is not None:
        arg_join = " "
    else:
        arg_join = None

    # A short-only boolean flag may carry its description on the same line,
    # indented to column 13. Trailing text that starts earlier is a prose
    # paragraph wrapping onto a dash, not a flag body.
    if hint is None and not saw_long and short is not None:
        tag_end = 5 + len(short)
        if len(line) > tag_end and line[tag_end:12].strip():
            return None

    return flag, short, hint, arg_join


def _classify_hint(
    hint: str | None,
) -> tuple[ParamArity, ParamValueType, str | None]:
    """Classify a value hint into ``(arity, value_type, assumption)``.

    Args:
        hint: The argument placeholder, or ``None``.

    Returns:
        The arity, the value type, and an assumption note to record in the
        flag's docstring when the arity is ambiguous and a default was chosen.
    """
    if hint is None or not (value := hint.strip()):
        return ParamArity.NONE, ParamValueType.STR, None
    if "..." in value:
        return ParamArity.MANY, ParamValueType.STR, None
    if "[" in value:
        # Optional value, e.g. ``[=WHEN]`` — genuinely ambiguous between a
        # boolean and a single value; default and say so.
        return (
            ParamArity.ONE,
            ParamValueType.STR,
            "assumed optional value takes one string",
        )
    tokens = value.split()
    if len(tokens) > 1:
        return ParamArity.MANY, ParamValueType.STR, None
    token = tokens[0].lstrip("=").strip("<>[]")
    if token.lower() in _NUMERIC_HINTS:
        return ParamArity.ONE, ParamValueType.INT, None
    return ParamArity.ONE, ParamValueType.STR, None


def _build_param(
    flag: str,
    short: str | None,
    arity: ParamArity,
    value_type: ParamValueType,
    arg_join: str | None,
    assumption: str | None,
    desc: Sequence[str],
) -> ParamSchema:
    """Assemble one :class:`ParamSchema`, folding the assumption into ``doc``."""
    doc = " ".join(d for d in desc if d).strip()
    if assumption:
        doc = f"{doc} (assumption: {assumption})".strip()
    return ParamSchema(
        flag=flag,
        short=short,
        arity=arity,
        value_type=value_type,
        arg_join=arg_join,
        doc=doc,
    )


def parse_flags(lines: Sequence[str]) -> Iterator[ParamSchema]:
    """Parse flag definitions out of a section's content lines.

    A line indented five spaces and starting with ``-`` opens a flag; the
    deeper-indented lines that follow are its description.

    Args:
        lines: A section's content lines.

    Yields:
        One :class:`ParamSchema` per flag, with ``python_name`` left empty
        (keyword collisions are the emitter's job).
    """
    flag: str | None = None
    short: str | None = None
    arity = ParamArity.ONE
    value_type = ParamValueType.STR
    arg_join: str | None = None
    assumption: str | None = None
    desc: list[str] = []

    for line in lines:
        if line.startswith(_FLAG_PREFIX):
            if flag is not None:
                yield _build_param(
                    flag, short, arity, value_type, arg_join, assumption, desc
                )
            parsed = _parse_flag_line(line)
            if parsed is None:
                flag = None
                short = None
                desc = []
                continue
            flag, short, hint, arg_join = parsed
            arity, value_type, assumption = _classify_hint(hint)
            desc = []
        elif flag is not None and _indent(line) > 5 and line.strip():
            desc.append(line.strip())

    if flag is not None:
        yield _build_param(
            flag, short, arity, value_type, arg_join, assumption, desc
        )


def parse_summary(lines: Sequence[str]) -> str:
    """Extract the one-line command summary from the NAME section.

    The NAME section reads ``command - one-line description``; this returns the
    part after the first ``" - "``.

    Args:
        lines: The manpage's non-empty lines.

    Returns:
        The summary, or ``""`` when no NAME section carries one.
    """
    for section, content in group_by_section(lines):
        if section != "NAME":
            continue
        for line in content:
            text = line.strip()
            if " - " in text:
                _, _, summary = text.partition(" - ")
                if summary.strip():
                    return summary.strip()
        if content:
            return content[0].strip()
    return ""


def parse_subcommands(
    command: str, lines: Sequence[str]
) -> Iterator[SubcommandSchema]:
    """Parse subcommand manpage references out of a section's content lines.

    Matches a line like ``devenv-processes-up(1)`` — a page name that starts
    with the parent ``command`` followed by ``-`` — and captures the
    deeper-indented lines that follow as the subcommand summary.

    Args:
        command: The parent command (e.g. ``"devenv"``).
        lines: A section's content lines.

    Yields:
        One :class:`SubcommandSchema` per subcommand reference.
    """
    pattern = re.compile(rf"^\s+({re.escape(command)}-([^\s()]+))\((\d)\)\s*$")
    page: str | None = None
    name: str | None = None
    desc: list[str] = []

    for line in lines:
        if match := pattern.search(line):
            if page is not None:
                yield SubcommandSchema(
                    name=name or "",
                    manpage=page,
                    summary=" ".join(d for d in desc if d).strip(),
                )
            page = match.group(1)
            name = page.rsplit("-", 1)[-1]
            desc = []
        elif page is not None and _indent(line) > 5 and line.strip():
            desc.append(line.strip())

    if page is not None:
        yield SubcommandSchema(
            name=name or "",
            manpage=page,
            summary=" ".join(d for d in desc if d).strip(),
        )


def parse_manpage(
    command: str,
    manpage: str,
    lines: Sequence[str],
    ignore: frozenset[str] = frozenset(),
) -> CommandSchema:
    """Parse one manpage into a :class:`CommandSchema`.

    Args:
        command: The executable the manpage describes (e.g. ``"grep"``).
        manpage: The manpage name it was parsed from (e.g. ``"grep"``).
        lines: The manpage's non-empty lines, as :func:`fetch_manual_lines`
            returns them.
        ignore: Flag spellings to skip — subcommand flags already defined by
            the parent command.

    Returns:
        The command schema.
    """
    summary = parse_summary(lines)
    params: list[ParamSchema] = []
    subcommands: list[SubcommandSchema] = []

    for section, content in group_by_section(lines):
        if section in _NON_FLAG_SECTIONS:
            continue
        params.extend(p for p in parse_flags(content) if p.flag not in ignore)
        subcommands.extend(parse_subcommands(command, content))

    return CommandSchema(
        name=command,
        manpage=manpage,
        summary=summary,
        params=tuple(params),
        subcommands=tuple(subcommands),
    )


def get_all_manpages(
    command: str,
    ignore: frozenset[str] = frozenset(),
) -> list[CommandSchema]:
    """Recursively collect the schema for ``command`` and its subcommands.

    Fetches each manpage via :func:`fetch_manual_lines` and parses it; a
    subcommand's manpage skips flags already defined by its parent.

    Args:
        command: The command to start from.
        ignore: Flag spellings to skip (the parent's flags, on recursion).

    Returns:
        The command schema followed by the schema of each subcommand, flattened.
    """
    schema = parse_manpage(
        command, command, fetch_manual_lines(command), ignore=ignore
    )
    schemas = [schema]
    inherited = ignore | {param.flag for param in schema.params}
    for subcommand in schema.subcommands:
        schemas.extend(get_all_manpages(subcommand.manpage, ignore=inherited))
    return schemas


def main() -> None:
    """Parse a command's manpages and print the resulting schemas."""
    parser = argparse.ArgumentParser(
        description="Parse a command's manpage into a CommandSchema."
    )
    parser.add_argument("command", type=str, help="command to parse manpages for")
    args = parser.parse_args()
    for schema in get_all_manpages(args.command):
        print(schema)


if __name__ == "__main__":
    main()
