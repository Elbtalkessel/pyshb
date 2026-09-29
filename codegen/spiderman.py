#!/usr/bin/env python
# Manual pages crawler, mainly created to crawl devenv man pages
# to generate nushell extern completions.

import argparse
import re
import subprocess
import typing

EXPORT_EXTERN_TMPL = """
{description}
export extern "{name}" [
{body}
]"""

DEF_TMPL = """def "nu-complete {name}" [] {{
  {{
    options: {{
      sort: false,
      completion_algorithm: substring,
      case_sensitive: false,
    }},
    completions: [
{body}
    ],
  }}
}}"""

COMP_TMPL = """{{value: "{value}", description: "{description}"}}"""


def get_manual_lines(command: str) -> typing.Generator[str]:
    """
    Manpage lines for `command`, newline charactes stripped,
    empty lines ignored.
    """
    v = subprocess.Popen(["man", command], stdout=subprocess.PIPE)
    if v.stderr:
        raise RuntimeError(b"".join(v.stderr.readlines()).decode("utf-8"))
    if out := v.stdout:
        return (
            l
            for l in (s.decode("utf-8").strip("\n") for s in out.readlines())
            if l.strip()
        )
    raise RuntimeError(f"man {command} return nothing")


def group_by_section(
    lines: typing.Generator[str],
) -> typing.Generator[tuple[str, list[str]]]:
    """
    Uppercase only lines consider as section title,
    anything between such lines considered as the section content:
        SECTION A
            section `a` content.
        SECTION B
            section `b` content.
    """
    rgx = re.compile(r"^[A-Z][A-Z ]+$")
    content: list[str] = []
    section = ""
    for line in lines:
        if not rgx.search(line):
            if section:
                content.append(line)
            continue
        if section and content:
            yield section, content
        section = line
        content = []
    if section and content:
        yield section, content


class FlagTuple(typing.NamedTuple):
    # Short form, e.g. -f
    short: str | None
    # Long form, e.g. --flag
    long: str | None
    # Anything remaining, usually flag value hint.
    args: str | None
    # All lines after the flag name up until the next flag name.
    desc: list[str]

    def __str__(self) -> str:
        tok: list[str] = []
        if self.long and self.short:
            tok.extend((self.long, f"({self.short})"))
        elif self.long or self.short:
            tok.append(typing.cast(str, self.long or self.short))
        if self.desc:
            tok.append(f"# {self.desc[0]}")
        return " ".join(tok)

    def __hash__(self) -> int:
        return hash(self.short or self.long)


def get_flags(lines: typing.Sequence[str]) -> typing.Generator[FlagTuple]:
    """
    Parses each line, if it looks like a flag name, collects all lines
    after up until a line looks like a flag again.
    Example:
        --between, -b <min> <max>
            Random number between min max.

            Example:
                -b 0 100
                --between 30 50
    Output:
        FlagTuple(
            short="-b",
            long="--between",
            args="<min> <max>",
            desc=["Random number between min max.", "Example:", "..you got the idea..."]
        )
    Note: Description and flags have any leading and trailing spaces stripped.
    """
    rgx = re.compile(
        r"^(?:(?P<short>-[\w])(?:, )?)?(?P<long>--[^ ]+)?\s?(?P<args>.*)?$"
    )
    desc: list[str] = []
    head = (None, None, None)
    for line in lines:
        if line.startswith("     -"):
            m = rgx.search(line.strip())
            assert m
            if head != (None, None, None):
                yield FlagTuple(*head, desc=desc)
            head = m.groups()
            continue
        desc.append(line.strip())


class SubpageTuple(typing.NamedTuple):
    # Last part of a subcommand, e.g. for `devenv processes up` it is `up`
    command: str
    # Manpage, for example `devenv-processes-up`.
    page: str
    # Manpage short description.
    desc: list[str]

    def __str__(self) -> str:
        tok = [self.command]
        if self.desc:
            tok.append(f"# {self.desc[0]}")
        return " ".join(tok)

    def __hash__(self) -> int:
        return hash(self.page)


def get_subpages(
    command: str,
    lines: typing.Sequence[str],
) -> typing.Generator[SubpageTuple]:
    """
    Parses a manpage lines, locates and returns all
    subcommands for a `command` assuming that manpage for
    the subcommand will look: `<command>-<something>(<page>)`.
    """
    pattern = rf"     ({command}-([^(]+))\(\d+\)$"
    rgx = re.compile(pattern)
    subcommand = None
    page = None
    desc: list[str] = []
    for line in lines:
        if s := rgx.search(line):
            if subcommand and page:
                yield SubpageTuple(command=subcommand, page=page, desc=desc)
                desc = []
            page, subcommand = s.group(1), s.group(2)
            continue
        desc.append(line.strip())


class ManTuple(typing.NamedTuple):
    # Command manpage describes.
    command: str
    # Available command --flags.
    flags: list[FlagTuple]
    # Available command topics (subcommands.)
    topics: list[SubpageTuple]
    # Content of DESCRIPTION section
    description: str


def get_manpage(
    command: str,
    ignore: set[tuple[str | None, str | None]] | None = None,
) -> ManTuple:
    """
    :param command: A command to check manpages for.
    :returns: Manpage tuple object for further parsing.
    """
    ignore_section = ("NAME", "SYNOPSIS", "OPTIONS")
    flags: list[FlagTuple] = []
    topics: list[SubpageTuple] = []
    description: str = ""
    for section, content in group_by_section(get_manual_lines(command)):
        if section in ignore_section:
            continue
        if section == "DESCRIPTION":
            description = "\n".join(f"# {c.strip()}" for c in content)
            continue
        flags.extend(
            f
            for f in get_flags(content)
            if ignore is None or (f.long, f.short) not in ignore
        )
        topics.extend(get_subpages(command, content))
    return ManTuple(
        flags=flags, topics=topics, command=command, description=description
    )


def dump_to_extern(manpage: ManTuple) -> typing.Generator[str]:
    body_lines = []
    if manpage.topics:
        yield dump_to_comfunc(manpage)
        body_lines.append(f'  topic: string@"nu-complete {manpage.command} topics"')
    body_lines.extend(f" {i}" for i in manpage.flags)
    if body_lines:
        yield EXPORT_EXTERN_TMPL.format(
            description=manpage.description,
            name=manpage.command.replace("-", " "),
            body="\n".join(body_lines),
        )


def dump_to_comfunc(manpage: ManTuple) -> str:
    return DEF_TMPL.format(
        name=f"{manpage.command} topics",
        body="\n".join(
            f"      {COMP_TMPL.format(value=i.command, description=i.desc[0])}"
            for i in manpage.topics
        ),
    )


def dump_to_nuscript(manpages: list[ManTuple]) -> typing.Generator[str]:
    for page in manpages:
        yield from dump_to_extern(page)


def get_all_manpages(
    command: str,
    ignore: set[tuple[str | None, str | None]] | None = None,
) -> list[ManTuple]:
    """
    Recursively collect the manpage for `command` and the manpages of
    all of its subcommands (topics), flattened into a single list.
    """
    manpage = get_manpage(command, ignore=ignore)
    pages = [manpage]
    for topic in manpage.topics:
        pages.extend(
            get_all_manpages(
                topic.page,
                ignore={(f.long, f.short) for f in manpage.flags},
            ),
        )
    return pages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        type=str,
        help="Command to check for manpages",
    )
    parser.add_argument("--debug", action="store_true", default=False)
    args = parser.parse_args()
    manpages = get_all_manpages(args.command)
    if args.debug:
        print(manpages)
    else:
        print("\n".join(dump_to_nuscript(manpages)))


if __name__ == "__main__":
    main()
