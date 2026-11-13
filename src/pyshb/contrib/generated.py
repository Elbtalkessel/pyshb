"""Generated coreutils wrappers — do not edit by hand.

Emitted by :mod:`codegen.emit` from the pinned manpage snapshots in
``tests/fixtures/``. Regenerate with ``python -m codegen.emit``; this file
is the committed output of that run and is never hand-edited.

Each class is a frozen dataclass whose fields are the command's flags.
Build a :class:`pyshb.builder.CommandBuilder` with :meth:`build`.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from pyshb.ast import SimpleCommand, Word
from pyshb.builder import CommandBuilder, ParamSpec


@dataclass(frozen=True, slots=True)
class grep:
    """print lines that match patterns

    Attributes:
        help_: Output a usage message and exit.
        version: Output the version number of grep and exit.
        extended_regexp: Interpret PATTERNS as extended regular expressions.
        fixed_strings: Interpret PATTERNS as fixed strings, not regular expressions.
        ignore_case: Ignore case distinctions in patterns and input data.
        invert_match: Invert the sense of matching, to select non-matching lines.
        regexp: Use PATTERNS as the patterns.
        file: Obtain patterns from FILE, one per line.
        max_count: Stop reading a file after NUM matching lines.
        color: Surround the matched strings with escape sequences. (assumption: assumed optional value takes one string)
        after_context: Print NUM lines of trailing context after matching lines.
        before_context: Print NUM lines of leading context before matching lines.
    """
    help_: bool = False
    version: bool = False
    extended_regexp: bool = False
    fixed_strings: bool = False
    ignore_case: bool = False
    invert_match: bool = False
    regexp: str | None = None
    file: str | None = None
    max_count: int | None = None
    color: str | None = None
    after_context: int | None = None
    before_context: int | None = None

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
        "extended_regexp": ParamSpec(flag="--extended-regexp"),
        "fixed_strings": ParamSpec(flag="--fixed-strings"),
        "ignore_case": ParamSpec(flag="--ignore-case"),
        "invert_match": ParamSpec(flag="--invert-match"),
        "regexp": ParamSpec(flag="--regexp"),
        "file": ParamSpec(flag="--file"),
        "max_count": ParamSpec(flag="--max-count"),
        "color": ParamSpec(flag="--color"),
        "after_context": ParamSpec(flag="--after-context"),
        "before_context": ParamSpec(flag="--before-context"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("grep")),
            schema=self.schema,
        )
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        if self.extended_regexp:
            builder = builder.set(extended_regexp=True)
        if self.fixed_strings:
            builder = builder.set(fixed_strings=True)
        if self.ignore_case:
            builder = builder.set(ignore_case=True)
        if self.invert_match:
            builder = builder.set(invert_match=True)
        if self.regexp is not None:
            builder = builder.set(regexp=self.regexp)
        if self.file is not None:
            builder = builder.set(file=self.file)
        if self.max_count is not None:
            builder = builder.set(max_count=self.max_count)
        if self.color is not None:
            builder = builder.set(color=self.color)
        if self.after_context is not None:
            builder = builder.set(after_context=self.after_context)
        if self.before_context is not None:
            builder = builder.set(before_context=self.before_context)
        return builder


@dataclass(frozen=True, slots=True)
class find:
    """search for files in a directory hierarchy

    Attributes:
        D: Print diagnostic information.
        help_: Print a summary of the command-line usage of find and exit.
        version: Print the find version number and exit.
        daystart: Measure times from the beginning of today rather than from 24 hours ago.
        regextype: Changes the regular expression syntax understood by -regex and -iregex tests.
        maxdepth: Descend at most levels directories below the starting-points.
        mindepth: Do not apply any tests or actions at levels less than levels.
        amin: File was last accessed less than, more than or exactly n minutes ago.
        name: Base of file name matches shell pattern pattern.
        type_: File is of type c.
        empty: File is empty and is either a regular file or a directory.
    """
    D: str | None = None
    help_: bool = False
    version: bool = False
    daystart: bool = False
    regextype: str | None = None
    maxdepth: str | None = None
    mindepth: str | None = None
    amin: int | None = None
    name: str | None = None
    type_: str | None = None
    empty: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "D": ParamSpec(flag="-D", arg_join=" "),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
        "daystart": ParamSpec(flag="-daystart"),
        "regextype": ParamSpec(flag="-regextype", arg_join=" "),
        "maxdepth": ParamSpec(flag="-maxdepth", arg_join=" "),
        "mindepth": ParamSpec(flag="-mindepth", arg_join=" "),
        "amin": ParamSpec(flag="-amin", arg_join=" "),
        "name": ParamSpec(flag="-name", arg_join=" "),
        "type_": ParamSpec(flag="-type", arg_join=" "),
        "empty": ParamSpec(flag="-empty"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("find")),
            schema=self.schema,
        )
        if self.D is not None:
            builder = builder.set(D=self.D)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        if self.daystart:
            builder = builder.set(daystart=True)
        if self.regextype is not None:
            builder = builder.set(regextype=self.regextype)
        if self.maxdepth is not None:
            builder = builder.set(maxdepth=self.maxdepth)
        if self.mindepth is not None:
            builder = builder.set(mindepth=self.mindepth)
        if self.amin is not None:
            builder = builder.set(amin=self.amin)
        if self.name is not None:
            builder = builder.set(name=self.name)
        if self.type_ is not None:
            builder = builder.set(type_=self.type_)
        if self.empty:
            builder = builder.set(empty=True)
        return builder


@dataclass(frozen=True, slots=True)
class ls:
    """list directory contents

    Attributes:
        all_: do not ignore entries starting with .
        almost_all: do not list implied . and ..
        author: with -l, print the author of each file
        escape: print C-style escapes for nongraphic characters
        block_size: with   -l,   scale   sizes   by  SIZE  when  printing  them;  e.g., '--block-size=M'; see SIZE format below
        ignore_backups: do not list implied entries ending with ~
        c: status  information);  with -l: show ctime and sort by name; other wise: sort by ctime, newest first
        C
        color: color the output WHEN; more info below (assumption: assumed optional value takes one string)
        directory: list directories themselves, not their contents
        dired: generate output designed for Emacs' dired mode
        f
        classify: append indicator (one of */=>@|) to entries WHEN (assumption: assumed optional value takes one string)
        file_type: like -F, except do not append '*'
        format_: across,horizontal (-x), commas (-m), long (-l), single-column (-1), verbose (-l), vertical (-C)
        full_time: like -l --time-style=full-iso
        g
        group_directories_first: group directories before files
        no_group: in a long listing, don't print group names
        human_readable: with -l and -s, print sizes like 1K 234M 2G etc.
        si
        dereference_command_line: follow symbolic links listed on the command line
        dereference_command_line_symlink_to_dir: follow each command line symbolic link that points to a directory
        hide: do not list implied entries matching shell PATTERN  (overridden  by -a or -A)
        hyperlink: hyperlink file names WHEN (assumption: assumed optional value takes one string)
        indicator_style: append  indicator  with  style WORD to entry names: none (default), slash (-p), file-type (--file-type), classify (-F)
        inode: print the index number of each file
        ignore: do not list implied entries matching shell PATTERN
        kibibytes: default to 1024-byte blocks for file system usage; used  only  with -s and per directory totals
        l
        dereference: when showing file information for a symbolic link, show information for the file the link references rather than for the link itself
        m
        numeric_uid_gid: like -l, but list numeric user and group IDs
        literal: print entry names without quoting
        o
        p: append / indicator to directories
        hide_control_chars: print ? instead of nongraphic characters
        show_control_chars: show  nongraphic  characters  as-is; the default, unless program is 'ls' and output is a terminal
        quote_name: enclose entry names in double quotes
        quoting_style: use quoting style WORD for entry  names:  literal,  locale,  shell, shell-always,  shell-escape,  shell-escape-always, c, escape (over rides QUOTING_STYLE environment variable)
        reverse: reverse order while sorting
        recursive: list subdirectories recursively
        size: print the allocated size of each file, in blocks
        S
        sort: change default 'name' sort to WORD:  none  (-U),  size  (-S),  time (-t), version (-v), extension (-X), name, width
        time: select  which  timestamp used to display or sort; access time (-u): atime, access, use; metadata change time (-c): ctime, status; modi fied time (default): mtime, modification; birth time:  birth,  cre ation;   with   -l,  WORD  determines  which  time  to  show;  with --sort=time, sort by WORD (newest first)
        time_style: time/date format with -l; see TIME_STYLE below
        t
        tabsize: assume tab stops at each COLS instead of 8
        u: and sort by name; otherwise: sort by access time, newest first
        U
        v
        width: set output width to COLS.  0 means no limit
        x
        X
        context: print any security context of each file
        zero: end each output line with NUL, not newline
        f_1
        help_: display this help and exit
        version: output version information and exit
    """
    all_: bool = False
    almost_all: bool = False
    author: bool = False
    escape: bool = False
    block_size: str | None = None
    ignore_backups: bool = False
    c: bool = False
    C: bool = False
    color: str | None = None
    directory: bool = False
    dired: bool = False
    f: bool = False
    classify: str | None = None
    file_type: bool = False
    format_: str | None = None
    full_time: bool = False
    g: bool = False
    group_directories_first: bool = False
    no_group: bool = False
    human_readable: bool = False
    si: bool = False
    dereference_command_line: bool = False
    dereference_command_line_symlink_to_dir: bool = False
    hide: str | None = None
    hyperlink: str | None = None
    indicator_style: str | None = None
    inode: bool = False
    ignore: str | None = None
    kibibytes: bool = False
    l: bool = False
    dereference: bool = False
    m: bool = False
    numeric_uid_gid: bool = False
    literal: bool = False
    o: bool = False
    p: bool = False
    hide_control_chars: bool = False
    show_control_chars: bool = False
    quote_name: bool = False
    quoting_style: str | None = None
    reverse: bool = False
    recursive: bool = False
    size: bool = False
    S: bool = False
    sort: str | None = None
    time: str | None = None
    time_style: str | None = None
    t: bool = False
    tabsize: str | None = None
    u: bool = False
    U: bool = False
    v: bool = False
    width: str | None = None
    x: bool = False
    X: bool = False
    context: bool = False
    zero: bool = False
    f_1: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "all_": ParamSpec(flag="--all"),
        "almost_all": ParamSpec(flag="--almost-all"),
        "author": ParamSpec(flag="--author"),
        "escape": ParamSpec(flag="--escape"),
        "block_size": ParamSpec(flag="--block-size"),
        "ignore_backups": ParamSpec(flag="--ignore-backups"),
        "c": ParamSpec(flag="-c"),
        "C": ParamSpec(flag="-C"),
        "color": ParamSpec(flag="--color"),
        "directory": ParamSpec(flag="--directory"),
        "dired": ParamSpec(flag="--dired"),
        "f": ParamSpec(flag="-f"),
        "classify": ParamSpec(flag="--classify"),
        "file_type": ParamSpec(flag="--file-type"),
        "format_": ParamSpec(flag="--format"),
        "full_time": ParamSpec(flag="--full-time"),
        "g": ParamSpec(flag="-g"),
        "group_directories_first": ParamSpec(flag="--group-directories-first"),
        "no_group": ParamSpec(flag="--no-group"),
        "human_readable": ParamSpec(flag="--human-readable"),
        "si": ParamSpec(flag="--si"),
        "dereference_command_line": ParamSpec(flag="--dereference-command-line"),
        "dereference_command_line_symlink_to_dir": ParamSpec(flag="--dereference-command-line-symlink-to-dir"),
        "hide": ParamSpec(flag="--hide"),
        "hyperlink": ParamSpec(flag="--hyperlink"),
        "indicator_style": ParamSpec(flag="--indicator-style"),
        "inode": ParamSpec(flag="--inode"),
        "ignore": ParamSpec(flag="--ignore"),
        "kibibytes": ParamSpec(flag="--kibibytes"),
        "l": ParamSpec(flag="-l"),
        "dereference": ParamSpec(flag="--dereference"),
        "m": ParamSpec(flag="-m"),
        "numeric_uid_gid": ParamSpec(flag="--numeric-uid-gid"),
        "literal": ParamSpec(flag="--literal"),
        "o": ParamSpec(flag="-o"),
        "p": ParamSpec(flag="-p"),
        "hide_control_chars": ParamSpec(flag="--hide-control-chars"),
        "show_control_chars": ParamSpec(flag="--show-control-chars"),
        "quote_name": ParamSpec(flag="--quote-name"),
        "quoting_style": ParamSpec(flag="--quoting-style"),
        "reverse": ParamSpec(flag="--reverse"),
        "recursive": ParamSpec(flag="--recursive"),
        "size": ParamSpec(flag="--size"),
        "S": ParamSpec(flag="-S"),
        "sort": ParamSpec(flag="--sort"),
        "time": ParamSpec(flag="--time"),
        "time_style": ParamSpec(flag="--time-style"),
        "t": ParamSpec(flag="-t"),
        "tabsize": ParamSpec(flag="--tabsize"),
        "u": ParamSpec(flag="-u"),
        "U": ParamSpec(flag="-U"),
        "v": ParamSpec(flag="-v"),
        "width": ParamSpec(flag="--width"),
        "x": ParamSpec(flag="-x"),
        "X": ParamSpec(flag="-X"),
        "context": ParamSpec(flag="--context"),
        "zero": ParamSpec(flag="--zero"),
        "f_1": ParamSpec(flag="-1"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("ls")),
            schema=self.schema,
        )
        if self.all_:
            builder = builder.set(all_=True)
        if self.almost_all:
            builder = builder.set(almost_all=True)
        if self.author:
            builder = builder.set(author=True)
        if self.escape:
            builder = builder.set(escape=True)
        if self.block_size is not None:
            builder = builder.set(block_size=self.block_size)
        if self.ignore_backups:
            builder = builder.set(ignore_backups=True)
        if self.c:
            builder = builder.set(c=True)
        if self.C:
            builder = builder.set(C=True)
        if self.color is not None:
            builder = builder.set(color=self.color)
        if self.directory:
            builder = builder.set(directory=True)
        if self.dired:
            builder = builder.set(dired=True)
        if self.f:
            builder = builder.set(f=True)
        if self.classify is not None:
            builder = builder.set(classify=self.classify)
        if self.file_type:
            builder = builder.set(file_type=True)
        if self.format_ is not None:
            builder = builder.set(format_=self.format_)
        if self.full_time:
            builder = builder.set(full_time=True)
        if self.g:
            builder = builder.set(g=True)
        if self.group_directories_first:
            builder = builder.set(group_directories_first=True)
        if self.no_group:
            builder = builder.set(no_group=True)
        if self.human_readable:
            builder = builder.set(human_readable=True)
        if self.si:
            builder = builder.set(si=True)
        if self.dereference_command_line:
            builder = builder.set(dereference_command_line=True)
        if self.dereference_command_line_symlink_to_dir:
            builder = builder.set(dereference_command_line_symlink_to_dir=True)
        if self.hide is not None:
            builder = builder.set(hide=self.hide)
        if self.hyperlink is not None:
            builder = builder.set(hyperlink=self.hyperlink)
        if self.indicator_style is not None:
            builder = builder.set(indicator_style=self.indicator_style)
        if self.inode:
            builder = builder.set(inode=True)
        if self.ignore is not None:
            builder = builder.set(ignore=self.ignore)
        if self.kibibytes:
            builder = builder.set(kibibytes=True)
        if self.l:
            builder = builder.set(l=True)
        if self.dereference:
            builder = builder.set(dereference=True)
        if self.m:
            builder = builder.set(m=True)
        if self.numeric_uid_gid:
            builder = builder.set(numeric_uid_gid=True)
        if self.literal:
            builder = builder.set(literal=True)
        if self.o:
            builder = builder.set(o=True)
        if self.p:
            builder = builder.set(p=True)
        if self.hide_control_chars:
            builder = builder.set(hide_control_chars=True)
        if self.show_control_chars:
            builder = builder.set(show_control_chars=True)
        if self.quote_name:
            builder = builder.set(quote_name=True)
        if self.quoting_style is not None:
            builder = builder.set(quoting_style=self.quoting_style)
        if self.reverse:
            builder = builder.set(reverse=True)
        if self.recursive:
            builder = builder.set(recursive=True)
        if self.size:
            builder = builder.set(size=True)
        if self.S:
            builder = builder.set(S=True)
        if self.sort is not None:
            builder = builder.set(sort=self.sort)
        if self.time is not None:
            builder = builder.set(time=self.time)
        if self.time_style is not None:
            builder = builder.set(time_style=self.time_style)
        if self.t:
            builder = builder.set(t=True)
        if self.tabsize is not None:
            builder = builder.set(tabsize=self.tabsize)
        if self.u:
            builder = builder.set(u=True)
        if self.U:
            builder = builder.set(U=True)
        if self.v:
            builder = builder.set(v=True)
        if self.width is not None:
            builder = builder.set(width=self.width)
        if self.x:
            builder = builder.set(x=True)
        if self.X:
            builder = builder.set(X=True)
        if self.context:
            builder = builder.set(context=True)
        if self.zero:
            builder = builder.set(zero=True)
        if self.f_1:
            builder = builder.set(f_1=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class cat:
    """concatenate files and print on the standard output

    Attributes:
        show_all: equivalent to -vET
        number_nonblank: number nonempty output lines, overrides -n
        e
        show_ends: display $ or ^M$ at end of each line
        number: number all output lines
        squeeze_blank: suppress repeated empty output lines
        t
        show_tabs: display TAB characters as ^I
        u
        show_nonprinting: use ^ and M- notation, except for LFD and TAB
        help_: display this help and exit
        version: output version information and exit
    """
    show_all: bool = False
    number_nonblank: bool = False
    e: bool = False
    show_ends: bool = False
    number: bool = False
    squeeze_blank: bool = False
    t: bool = False
    show_tabs: bool = False
    u: bool = False
    show_nonprinting: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "show_all": ParamSpec(flag="--show-all"),
        "number_nonblank": ParamSpec(flag="--number-nonblank"),
        "e": ParamSpec(flag="-e"),
        "show_ends": ParamSpec(flag="--show-ends"),
        "number": ParamSpec(flag="--number"),
        "squeeze_blank": ParamSpec(flag="--squeeze-blank"),
        "t": ParamSpec(flag="-t"),
        "show_tabs": ParamSpec(flag="--show-tabs"),
        "u": ParamSpec(flag="-u"),
        "show_nonprinting": ParamSpec(flag="--show-nonprinting"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("cat")),
            schema=self.schema,
        )
        if self.show_all:
            builder = builder.set(show_all=True)
        if self.number_nonblank:
            builder = builder.set(number_nonblank=True)
        if self.e:
            builder = builder.set(e=True)
        if self.show_ends:
            builder = builder.set(show_ends=True)
        if self.number:
            builder = builder.set(number=True)
        if self.squeeze_blank:
            builder = builder.set(squeeze_blank=True)
        if self.t:
            builder = builder.set(t=True)
        if self.show_tabs:
            builder = builder.set(show_tabs=True)
        if self.u:
            builder = builder.set(u=True)
        if self.show_nonprinting:
            builder = builder.set(show_nonprinting=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class mkdir:
    """make directories

    Attributes:
        mode: set file mode (as in chmod), not a=rwx - umask
        parents: no error if existing, make parent directories as needed, with their file modes unaffected by any -m option
        verbose: print a message for each created directory
        Z: fault type
        context: like -Z, or if CTX is specified then set the SELinux or SMACK secu rity context to CTX (assumption: assumed optional value takes one string)
        help_: display this help and exit
        version: output version information and exit
    """
    mode: str | None = None
    parents: bool = False
    verbose: bool = False
    Z: bool = False
    context: str | None = None
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "mode": ParamSpec(flag="--mode"),
        "parents": ParamSpec(flag="--parents"),
        "verbose": ParamSpec(flag="--verbose"),
        "Z": ParamSpec(flag="-Z"),
        "context": ParamSpec(flag="--context"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("mkdir")),
            schema=self.schema,
        )
        if self.mode is not None:
            builder = builder.set(mode=self.mode)
        if self.parents:
            builder = builder.set(parents=True)
        if self.verbose:
            builder = builder.set(verbose=True)
        if self.Z:
            builder = builder.set(Z=True)
        if self.context is not None:
            builder = builder.set(context=self.context)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class cp:
    """copy files and directories

    Attributes:
        archive: same as -dR --preserve=all
        attributes_only: don't copy the file data, just the attributes
        backup: make a backup of each existing destination file (assumption: assumed optional value takes one string)
        b
        copy_contents: copy contents of special files when recursive
        d
        debug: explain how a file is copied.  Implies -v
        force: if an existing destination file cannot be opened, remove it and try again (this option is ignored when the -n option is also used)
        interactive: prompt before overwrite (overrides a previous -n option)
        H
        dereference: always follow symbolic links in SOURCE
        no_dereference: never follow symbolic links in SOURCE
        keep_directory_symlink: follow existing symlinks to directories
        link: hard link files instead of copying
        no_clobber: (deprecated) silently skip existing files.  See also --update
        p
        preserve: preserve the specified attributes (assumption: assumed optional value takes one string)
        no_preserve: don't preserve the specified attributes
        parents: use full source file name under DIRECTORY
        recursive: copy directories recursively
        reflink: control clone/CoW copies. See below (assumption: assumed optional value takes one string)
        remove_destination: remove  each existing destination file before attempting to open it (contrast with --force)
        sparse: control creation of sparse files. See below
        strip_trailing_slashes: remove any trailing slashes from each SOURCE argument
        symbolic_link: make symbolic links instead of copying
        suffix: override the usual backup suffix
        target_directory: copy all SOURCE arguments into DIRECTORY
        no_target_directory: treat DEST as a normal file
        update: control    which    existing     files     are     updated;     UP DATE={all,none,none-fail,older(default)} (assumption: assumed optional value takes one string)
        u
        verbose: explain what is being done
        one_file_system: stay on this file system
        Z
        context: like -Z, or if CTX is specified then set the SELinux or SMACK secu rity context to CTX (assumption: assumed optional value takes one string)
        help_: display this help and exit
        version: output version information and exit
    """
    archive: bool = False
    attributes_only: bool = False
    backup: str | None = None
    b: bool = False
    copy_contents: bool = False
    d: bool = False
    debug: bool = False
    force: bool = False
    interactive: bool = False
    H: bool = False
    dereference: bool = False
    no_dereference: bool = False
    keep_directory_symlink: bool = False
    link: bool = False
    no_clobber: bool = False
    p: bool = False
    preserve: str | None = None
    no_preserve: str | None = None
    parents: bool = False
    recursive: bool = False
    reflink: str | None = None
    remove_destination: bool = False
    sparse: str | None = None
    strip_trailing_slashes: bool = False
    symbolic_link: bool = False
    suffix: str | None = None
    target_directory: str | None = None
    no_target_directory: bool = False
    update: str | None = None
    u: bool = False
    verbose: bool = False
    one_file_system: bool = False
    Z: bool = False
    context: str | None = None
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "archive": ParamSpec(flag="--archive"),
        "attributes_only": ParamSpec(flag="--attributes-only"),
        "backup": ParamSpec(flag="--backup"),
        "b": ParamSpec(flag="-b"),
        "copy_contents": ParamSpec(flag="--copy-contents"),
        "d": ParamSpec(flag="-d"),
        "debug": ParamSpec(flag="--debug"),
        "force": ParamSpec(flag="--force"),
        "interactive": ParamSpec(flag="--interactive"),
        "H": ParamSpec(flag="-H"),
        "dereference": ParamSpec(flag="--dereference"),
        "no_dereference": ParamSpec(flag="--no-dereference"),
        "keep_directory_symlink": ParamSpec(flag="--keep-directory-symlink"),
        "link": ParamSpec(flag="--link"),
        "no_clobber": ParamSpec(flag="--no-clobber"),
        "p": ParamSpec(flag="-p"),
        "preserve": ParamSpec(flag="--preserve"),
        "no_preserve": ParamSpec(flag="--no-preserve"),
        "parents": ParamSpec(flag="--parents"),
        "recursive": ParamSpec(flag="--recursive"),
        "reflink": ParamSpec(flag="--reflink"),
        "remove_destination": ParamSpec(flag="--remove-destination"),
        "sparse": ParamSpec(flag="--sparse"),
        "strip_trailing_slashes": ParamSpec(flag="--strip-trailing-slashes"),
        "symbolic_link": ParamSpec(flag="--symbolic-link"),
        "suffix": ParamSpec(flag="--suffix"),
        "target_directory": ParamSpec(flag="--target-directory"),
        "no_target_directory": ParamSpec(flag="--no-target-directory"),
        "update": ParamSpec(flag="--update"),
        "u": ParamSpec(flag="-u"),
        "verbose": ParamSpec(flag="--verbose"),
        "one_file_system": ParamSpec(flag="--one-file-system"),
        "Z": ParamSpec(flag="-Z"),
        "context": ParamSpec(flag="--context"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("cp")),
            schema=self.schema,
        )
        if self.archive:
            builder = builder.set(archive=True)
        if self.attributes_only:
            builder = builder.set(attributes_only=True)
        if self.backup is not None:
            builder = builder.set(backup=self.backup)
        if self.b:
            builder = builder.set(b=True)
        if self.copy_contents:
            builder = builder.set(copy_contents=True)
        if self.d:
            builder = builder.set(d=True)
        if self.debug:
            builder = builder.set(debug=True)
        if self.force:
            builder = builder.set(force=True)
        if self.interactive:
            builder = builder.set(interactive=True)
        if self.H:
            builder = builder.set(H=True)
        if self.dereference:
            builder = builder.set(dereference=True)
        if self.no_dereference:
            builder = builder.set(no_dereference=True)
        if self.keep_directory_symlink:
            builder = builder.set(keep_directory_symlink=True)
        if self.link:
            builder = builder.set(link=True)
        if self.no_clobber:
            builder = builder.set(no_clobber=True)
        if self.p:
            builder = builder.set(p=True)
        if self.preserve is not None:
            builder = builder.set(preserve=self.preserve)
        if self.no_preserve is not None:
            builder = builder.set(no_preserve=self.no_preserve)
        if self.parents:
            builder = builder.set(parents=True)
        if self.recursive:
            builder = builder.set(recursive=True)
        if self.reflink is not None:
            builder = builder.set(reflink=self.reflink)
        if self.remove_destination:
            builder = builder.set(remove_destination=True)
        if self.sparse is not None:
            builder = builder.set(sparse=self.sparse)
        if self.strip_trailing_slashes:
            builder = builder.set(strip_trailing_slashes=True)
        if self.symbolic_link:
            builder = builder.set(symbolic_link=True)
        if self.suffix is not None:
            builder = builder.set(suffix=self.suffix)
        if self.target_directory is not None:
            builder = builder.set(target_directory=self.target_directory)
        if self.no_target_directory:
            builder = builder.set(no_target_directory=True)
        if self.update is not None:
            builder = builder.set(update=self.update)
        if self.u:
            builder = builder.set(u=True)
        if self.verbose:
            builder = builder.set(verbose=True)
        if self.one_file_system:
            builder = builder.set(one_file_system=True)
        if self.Z:
            builder = builder.set(Z=True)
        if self.context is not None:
            builder = builder.set(context=self.context)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class mv:
    """move (rename) files

    Attributes:
        backup: make a backup of each existing destination file (assumption: assumed optional value takes one string)
        b
        debug: explain how a file is copied.  Implies -v
        exchange: exchange source and destination
        force: do not prompt before overwriting
        interactive: prompt before overwrite
        no_clobber: (deprecated) silently skip existing files.  See also --update
        no_copy: do not copy if renaming fails
        strip_trailing_slashes: remove any trailing slashes from each SOURCE argument
        suffix: override the usual backup suffix
        target_directory: move all SOURCE arguments into DIRECTORY
        no_target_directory: treat DEST as a normal file
        update: control    which    existing     files     are     updated;     UP DATE={all,none,none-fail,older(default)} (assumption: assumed optional value takes one string)
        u
        verbose: explain what is being done
        context: set SELinux security context of destination file to default type
        help_: display this help and exit
        version: output version information and exit
    """
    backup: str | None = None
    b: bool = False
    debug: bool = False
    exchange: bool = False
    force: bool = False
    interactive: bool = False
    no_clobber: bool = False
    no_copy: bool = False
    strip_trailing_slashes: bool = False
    suffix: str | None = None
    target_directory: str | None = None
    no_target_directory: bool = False
    update: str | None = None
    u: bool = False
    verbose: bool = False
    context: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "backup": ParamSpec(flag="--backup"),
        "b": ParamSpec(flag="-b"),
        "debug": ParamSpec(flag="--debug"),
        "exchange": ParamSpec(flag="--exchange"),
        "force": ParamSpec(flag="--force"),
        "interactive": ParamSpec(flag="--interactive"),
        "no_clobber": ParamSpec(flag="--no-clobber"),
        "no_copy": ParamSpec(flag="--no-copy"),
        "strip_trailing_slashes": ParamSpec(flag="--strip-trailing-slashes"),
        "suffix": ParamSpec(flag="--suffix"),
        "target_directory": ParamSpec(flag="--target-directory"),
        "no_target_directory": ParamSpec(flag="--no-target-directory"),
        "update": ParamSpec(flag="--update"),
        "u": ParamSpec(flag="-u"),
        "verbose": ParamSpec(flag="--verbose"),
        "context": ParamSpec(flag="--context"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("mv")),
            schema=self.schema,
        )
        if self.backup is not None:
            builder = builder.set(backup=self.backup)
        if self.b:
            builder = builder.set(b=True)
        if self.debug:
            builder = builder.set(debug=True)
        if self.exchange:
            builder = builder.set(exchange=True)
        if self.force:
            builder = builder.set(force=True)
        if self.interactive:
            builder = builder.set(interactive=True)
        if self.no_clobber:
            builder = builder.set(no_clobber=True)
        if self.no_copy:
            builder = builder.set(no_copy=True)
        if self.strip_trailing_slashes:
            builder = builder.set(strip_trailing_slashes=True)
        if self.suffix is not None:
            builder = builder.set(suffix=self.suffix)
        if self.target_directory is not None:
            builder = builder.set(target_directory=self.target_directory)
        if self.no_target_directory:
            builder = builder.set(no_target_directory=True)
        if self.update is not None:
            builder = builder.set(update=self.update)
        if self.u:
            builder = builder.set(u=True)
        if self.verbose:
            builder = builder.set(verbose=True)
        if self.context:
            builder = builder.set(context=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class rm:
    """remove files or directories

    Attributes:
        force: ignore nonexistent files and arguments, never prompt
        i
        I: recursively; less intrusive than -i, while still giving  protection against most mistakes
        interactive: prompt according to WHEN: never, once (-I), or always (-i); without WHEN, prompt always (assumption: assumed optional value takes one string)
        one_file_system: when  removing  a hierarchy recursively, skip any directory that is on a file system different from that of the  corresponding  command line argument
        no_preserve_root: do not treat '/' specially
        preserve_root: do  not  remove  '/' (default); with 'all', reject any command line argument on a separate device from its parent (assumption: assumed optional value takes one string)
        recursive: remove directories and their contents recursively
        dir_: remove empty directories
        verbose: explain what is being done
        help_: display this help and exit
        version: output version information and exit
    """
    force: bool = False
    i: bool = False
    I: bool = False
    interactive: str | None = None
    one_file_system: bool = False
    no_preserve_root: bool = False
    preserve_root: str | None = None
    recursive: bool = False
    dir_: bool = False
    verbose: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "force": ParamSpec(flag="--force"),
        "i": ParamSpec(flag="-i"),
        "I": ParamSpec(flag="-I"),
        "interactive": ParamSpec(flag="--interactive"),
        "one_file_system": ParamSpec(flag="--one-file-system"),
        "no_preserve_root": ParamSpec(flag="--no-preserve-root"),
        "preserve_root": ParamSpec(flag="--preserve-root"),
        "recursive": ParamSpec(flag="--recursive"),
        "dir_": ParamSpec(flag="--dir"),
        "verbose": ParamSpec(flag="--verbose"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("rm")),
            schema=self.schema,
        )
        if self.force:
            builder = builder.set(force=True)
        if self.i:
            builder = builder.set(i=True)
        if self.I:
            builder = builder.set(I=True)
        if self.interactive is not None:
            builder = builder.set(interactive=self.interactive)
        if self.one_file_system:
            builder = builder.set(one_file_system=True)
        if self.no_preserve_root:
            builder = builder.set(no_preserve_root=True)
        if self.preserve_root is not None:
            builder = builder.set(preserve_root=self.preserve_root)
        if self.recursive:
            builder = builder.set(recursive=True)
        if self.dir_:
            builder = builder.set(dir_=True)
        if self.verbose:
            builder = builder.set(verbose=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class chmod:
    """change file mode bits

    Attributes:
        changes: like verbose but report only when a change is made
        silent: suppress most error messages
        verbose: output a diagnostic for every file processed
        dereference: affect the referent of each symbolic link, rather than the symbolic link itself
        no_dereference: affect each symbolic link, rather than the referent
        no_preserve_root: do not treat '/' specially (the default)
        preserve_root: fail to operate recursively on '/'
        reference: use  RFILE's  mode instead of specifying MODE values.  RFILE is al ways dereferenced if a symbolic link.
        recursive: change files and directories recursively
        H
        L
        P
        help_: display this help and exit
        version: output version information and exit
    """
    changes: bool = False
    silent: bool = False
    verbose: bool = False
    dereference: bool = False
    no_dereference: bool = False
    no_preserve_root: bool = False
    preserve_root: bool = False
    reference: str | None = None
    recursive: bool = False
    H: bool = False
    L: bool = False
    P: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "changes": ParamSpec(flag="--changes"),
        "silent": ParamSpec(flag="--silent"),
        "verbose": ParamSpec(flag="--verbose"),
        "dereference": ParamSpec(flag="--dereference"),
        "no_dereference": ParamSpec(flag="--no-dereference"),
        "no_preserve_root": ParamSpec(flag="--no-preserve-root"),
        "preserve_root": ParamSpec(flag="--preserve-root"),
        "reference": ParamSpec(flag="--reference"),
        "recursive": ParamSpec(flag="--recursive"),
        "H": ParamSpec(flag="-H"),
        "L": ParamSpec(flag="-L"),
        "P": ParamSpec(flag="-P"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("chmod")),
            schema=self.schema,
        )
        if self.changes:
            builder = builder.set(changes=True)
        if self.silent:
            builder = builder.set(silent=True)
        if self.verbose:
            builder = builder.set(verbose=True)
        if self.dereference:
            builder = builder.set(dereference=True)
        if self.no_dereference:
            builder = builder.set(no_dereference=True)
        if self.no_preserve_root:
            builder = builder.set(no_preserve_root=True)
        if self.preserve_root:
            builder = builder.set(preserve_root=True)
        if self.reference is not None:
            builder = builder.set(reference=self.reference)
        if self.recursive:
            builder = builder.set(recursive=True)
        if self.H:
            builder = builder.set(H=True)
        if self.L:
            builder = builder.set(L=True)
        if self.P:
            builder = builder.set(P=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class sort:
    """sort lines of text files

    Attributes:
        ignore_leading_blanks: ignore leading blanks when finding sort keys in each line
        dictionary_order: consider only blanks and alphanumeric characters
        ignore_case: fold lower case to upper case characters
        general_numeric_sort: compare according to general numerical value
        ignore_nonprinting: consider only printable characters
        month_sort: compare (unknown) < 'JAN' < ... < 'DEC'
        human_numeric_sort: compare human readable numbers (e.g., 2K 1G)
        numeric_sort: compare according to string numerical value; see full documentation for supported strings
        random_sort: shuffle, but group identical keys.  See also shuf(1)
        random_source: get random bytes from FILE
        reverse: reverse the result of comparisons
        sort: sort according to WORD: general-numeric -g, human-numeric -h, month -M, numeric -n, random -R, version -V
        version_sort: natural sort of (version) numbers within text
        batch_size: merge at most NMERGE inputs at once; for more use temp files
        check: check for sorted input; do not sort
        C: like -c, but do not report first bad line
        compress_program: compress temporaries with PROG; decompress them with PROG -d
        debug: annotate the part of the line used to sort, and  warn  about  ques tionable usage to standard error
        files0_from: read input from the files specified by NUL-terminated names in file F; If F is -, read names from standard input
        key: sort via a key; KEYDEF gives location and type
        merge: merge already sorted files; do not sort
        output: write result to FILE instead of standard output
        stable: stabilize sort by disabling last-resort comparison
        buffer_size: use SIZE for main memory buffer
        field_separator: use SEP instead of non-blank to blank transition
        temporary_directory: use  DIR  for  temporaries,  not  $TMPDIR or /tmp; multiple options specify multiple directories
        parallel: change the number of sorts run concurrently to N
        unique: output only the first of lines with equal keys; with -c, check  for strict ordering
        zero_terminated: line delimiter is NUL, not newline
        help_: display this help and exit
        version: output version information and exit
    """
    ignore_leading_blanks: bool = False
    dictionary_order: bool = False
    ignore_case: bool = False
    general_numeric_sort: bool = False
    ignore_nonprinting: bool = False
    month_sort: bool = False
    human_numeric_sort: bool = False
    numeric_sort: bool = False
    random_sort: bool = False
    random_source: str | None = None
    reverse: bool = False
    sort: str | None = None
    version_sort: bool = False
    batch_size: str | None = None
    check: bool = False
    C: bool = False
    compress_program: str | None = None
    debug: bool = False
    files0_from: str | None = None
    key: str | None = None
    merge: bool = False
    output: str | None = None
    stable: bool = False
    buffer_size: str | None = None
    field_separator: str | None = None
    temporary_directory: str | None = None
    parallel: int | None = None
    unique: bool = False
    zero_terminated: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "ignore_leading_blanks": ParamSpec(flag="--ignore-leading-blanks"),
        "dictionary_order": ParamSpec(flag="--dictionary-order"),
        "ignore_case": ParamSpec(flag="--ignore-case"),
        "general_numeric_sort": ParamSpec(flag="--general-numeric-sort"),
        "ignore_nonprinting": ParamSpec(flag="--ignore-nonprinting"),
        "month_sort": ParamSpec(flag="--month-sort"),
        "human_numeric_sort": ParamSpec(flag="--human-numeric-sort"),
        "numeric_sort": ParamSpec(flag="--numeric-sort"),
        "random_sort": ParamSpec(flag="--random-sort"),
        "random_source": ParamSpec(flag="--random-source"),
        "reverse": ParamSpec(flag="--reverse"),
        "sort": ParamSpec(flag="--sort"),
        "version_sort": ParamSpec(flag="--version-sort"),
        "batch_size": ParamSpec(flag="--batch-size"),
        "check": ParamSpec(flag="--check"),
        "C": ParamSpec(flag="-C"),
        "compress_program": ParamSpec(flag="--compress-program"),
        "debug": ParamSpec(flag="--debug"),
        "files0_from": ParamSpec(flag="--files0-from"),
        "key": ParamSpec(flag="--key"),
        "merge": ParamSpec(flag="--merge"),
        "output": ParamSpec(flag="--output"),
        "stable": ParamSpec(flag="--stable"),
        "buffer_size": ParamSpec(flag="--buffer-size"),
        "field_separator": ParamSpec(flag="--field-separator"),
        "temporary_directory": ParamSpec(flag="--temporary-directory"),
        "parallel": ParamSpec(flag="--parallel"),
        "unique": ParamSpec(flag="--unique"),
        "zero_terminated": ParamSpec(flag="--zero-terminated"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("sort")),
            schema=self.schema,
        )
        if self.ignore_leading_blanks:
            builder = builder.set(ignore_leading_blanks=True)
        if self.dictionary_order:
            builder = builder.set(dictionary_order=True)
        if self.ignore_case:
            builder = builder.set(ignore_case=True)
        if self.general_numeric_sort:
            builder = builder.set(general_numeric_sort=True)
        if self.ignore_nonprinting:
            builder = builder.set(ignore_nonprinting=True)
        if self.month_sort:
            builder = builder.set(month_sort=True)
        if self.human_numeric_sort:
            builder = builder.set(human_numeric_sort=True)
        if self.numeric_sort:
            builder = builder.set(numeric_sort=True)
        if self.random_sort:
            builder = builder.set(random_sort=True)
        if self.random_source is not None:
            builder = builder.set(random_source=self.random_source)
        if self.reverse:
            builder = builder.set(reverse=True)
        if self.sort is not None:
            builder = builder.set(sort=self.sort)
        if self.version_sort:
            builder = builder.set(version_sort=True)
        if self.batch_size is not None:
            builder = builder.set(batch_size=self.batch_size)
        if self.check:
            builder = builder.set(check=True)
        if self.C:
            builder = builder.set(C=True)
        if self.compress_program is not None:
            builder = builder.set(compress_program=self.compress_program)
        if self.debug:
            builder = builder.set(debug=True)
        if self.files0_from is not None:
            builder = builder.set(files0_from=self.files0_from)
        if self.key is not None:
            builder = builder.set(key=self.key)
        if self.merge:
            builder = builder.set(merge=True)
        if self.output is not None:
            builder = builder.set(output=self.output)
        if self.stable:
            builder = builder.set(stable=True)
        if self.buffer_size is not None:
            builder = builder.set(buffer_size=self.buffer_size)
        if self.field_separator is not None:
            builder = builder.set(field_separator=self.field_separator)
        if self.temporary_directory is not None:
            builder = builder.set(temporary_directory=self.temporary_directory)
        if self.parallel is not None:
            builder = builder.set(parallel=self.parallel)
        if self.unique:
            builder = builder.set(unique=True)
        if self.zero_terminated:
            builder = builder.set(zero_terminated=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class uniq:
    """report or omit repeated lines

    Attributes:
        count: prefix lines by the number of occurrences
        repeated: only print duplicate lines, one for each group
        D
        all_repeated: like  -D,  but  allow  separating  groups  with  an   empty   line; METHOD={none(default),prepend,separate} (assumption: assumed optional value takes one string)
        skip_fields: avoid comparing the first N fields
        group: show all items, separating groups with an empty line; METHOD={sepa rate(default),prepend,append,both} (assumption: assumed optional value takes one string)
        ignore_case: ignore differences in case when comparing
        skip_chars: avoid comparing the first N characters
        unique: only print unique lines
        zero_terminated: line delimiter is NUL, not newline
        check_chars: compare no more than N characters in lines
        help_: display this help and exit
        version: output version information and exit
    """
    count: bool = False
    repeated: bool = False
    D: bool = False
    all_repeated: str | None = None
    skip_fields: int | None = None
    group: str | None = None
    ignore_case: bool = False
    skip_chars: int | None = None
    unique: bool = False
    zero_terminated: bool = False
    check_chars: int | None = None
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "count": ParamSpec(flag="--count"),
        "repeated": ParamSpec(flag="--repeated"),
        "D": ParamSpec(flag="-D"),
        "all_repeated": ParamSpec(flag="--all-repeated"),
        "skip_fields": ParamSpec(flag="--skip-fields"),
        "group": ParamSpec(flag="--group"),
        "ignore_case": ParamSpec(flag="--ignore-case"),
        "skip_chars": ParamSpec(flag="--skip-chars"),
        "unique": ParamSpec(flag="--unique"),
        "zero_terminated": ParamSpec(flag="--zero-terminated"),
        "check_chars": ParamSpec(flag="--check-chars"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("uniq")),
            schema=self.schema,
        )
        if self.count:
            builder = builder.set(count=True)
        if self.repeated:
            builder = builder.set(repeated=True)
        if self.D:
            builder = builder.set(D=True)
        if self.all_repeated is not None:
            builder = builder.set(all_repeated=self.all_repeated)
        if self.skip_fields is not None:
            builder = builder.set(skip_fields=self.skip_fields)
        if self.group is not None:
            builder = builder.set(group=self.group)
        if self.ignore_case:
            builder = builder.set(ignore_case=True)
        if self.skip_chars is not None:
            builder = builder.set(skip_chars=self.skip_chars)
        if self.unique:
            builder = builder.set(unique=True)
        if self.zero_terminated:
            builder = builder.set(zero_terminated=True)
        if self.check_chars is not None:
            builder = builder.set(check_chars=self.check_chars)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class wc:
    """word, line, and byte or character count

    Attributes:
        bytes_: print the byte counts
        chars: print the character counts
        lines: print the newline counts
        debug: indicate what line count acceleration is used
        files0_from: read input from the files specified by NUL-terminated names in file F; If F is -, read names from standard input
        max_line_length: print the maximum display width
        words: print the word counts
        total: when to print a line with total counts; WHEN can be: auto,  always, only, never
        help_: display this help and exit
        version: output version information and exit
    """
    bytes_: bool = False
    chars: bool = False
    lines: bool = False
    debug: bool = False
    files0_from: str | None = None
    max_line_length: bool = False
    words: bool = False
    total: str | None = None
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "bytes_": ParamSpec(flag="--bytes"),
        "chars": ParamSpec(flag="--chars"),
        "lines": ParamSpec(flag="--lines"),
        "debug": ParamSpec(flag="--debug"),
        "files0_from": ParamSpec(flag="--files0-from"),
        "max_line_length": ParamSpec(flag="--max-line-length"),
        "words": ParamSpec(flag="--words"),
        "total": ParamSpec(flag="--total"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("wc")),
            schema=self.schema,
        )
        if self.bytes_:
            builder = builder.set(bytes_=True)
        if self.chars:
            builder = builder.set(chars=True)
        if self.lines:
            builder = builder.set(lines=True)
        if self.debug:
            builder = builder.set(debug=True)
        if self.files0_from is not None:
            builder = builder.set(files0_from=self.files0_from)
        if self.max_line_length:
            builder = builder.set(max_line_length=True)
        if self.words:
            builder = builder.set(words=True)
        if self.total is not None:
            builder = builder.set(total=self.total)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class head:
    """output the first part of files

    Attributes:
        bytes_: print the first NUM bytes of each file; with the leading '-', print all but the last NUM bytes of each file (assumption: assumed optional value takes one string)
        lines: print the first NUM lines instead of the first 10; with the leading '-', print all but the last NUM lines of each file (assumption: assumed optional value takes one string)
        quiet: never print headers giving file names
        verbose: always print headers giving file names
        zero_terminated: line delimiter is NUL, not newline
        help_: display this help and exit
        version: output version information and exit
    """
    bytes_: str | None = None
    lines: str | None = None
    quiet: bool = False
    verbose: bool = False
    zero_terminated: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "bytes_": ParamSpec(flag="--bytes"),
        "lines": ParamSpec(flag="--lines"),
        "quiet": ParamSpec(flag="--quiet"),
        "verbose": ParamSpec(flag="--verbose"),
        "zero_terminated": ParamSpec(flag="--zero-terminated"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("head")),
            schema=self.schema,
        )
        if self.bytes_ is not None:
            builder = builder.set(bytes_=self.bytes_)
        if self.lines is not None:
            builder = builder.set(lines=self.lines)
        if self.quiet:
            builder = builder.set(quiet=True)
        if self.verbose:
            builder = builder.set(verbose=True)
        if self.zero_terminated:
            builder = builder.set(zero_terminated=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class tail:
    """output the last part of files

    Attributes:
        bytes_: output the last NUM bytes; or use -c +NUM to output  starting  with byte NUM of each file (assumption: assumed optional value takes one string)
        debug: indicate which --follow implementation is used
        follow: output  appended  data as the file grows; an absent option argument means 'descriptor' (assumption: assumed optional value takes one string)
        F
        lines: output the last NUM lines, instead of the last 10; or use  -n  +NUM to skip NUM-1 lines at the start (assumption: assumed optional value takes one string)
        max_unchanged_stats: with  --follow=name, reopen a FILE which has not changed size after N (default 5) iterations to see if it has been unlinked or  renamed (this  is  the usual case of rotated log files); with inotify, this option is rarely useful
        pid: with -f, exit after PID no longer exists; can be repeated to  watch multiple processes
        quiet: never output headers giving file names
        retry: keep trying to open a file if it is inaccessible
        sleep_interval: with  -f,  sleep  for approximately N seconds (default 1.0) between iterations; with inotify and --pid=P, check process P at least once every N seconds
        verbose: always output headers giving file names
        zero_terminated: line delimiter is NUL, not newline
        help_: display this help and exit
        version: output version information and exit
    """
    bytes_: str | None = None
    debug: bool = False
    follow: str | None = None
    F: bool = False
    lines: str | None = None
    max_unchanged_stats: int | None = None
    pid: str | None = None
    quiet: bool = False
    retry: bool = False
    sleep_interval: int | None = None
    verbose: bool = False
    zero_terminated: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "bytes_": ParamSpec(flag="--bytes"),
        "debug": ParamSpec(flag="--debug"),
        "follow": ParamSpec(flag="--follow"),
        "F": ParamSpec(flag="-F"),
        "lines": ParamSpec(flag="--lines"),
        "max_unchanged_stats": ParamSpec(flag="--max-unchanged-stats"),
        "pid": ParamSpec(flag="--pid"),
        "quiet": ParamSpec(flag="--quiet"),
        "retry": ParamSpec(flag="--retry"),
        "sleep_interval": ParamSpec(flag="--sleep-interval"),
        "verbose": ParamSpec(flag="--verbose"),
        "zero_terminated": ParamSpec(flag="--zero-terminated"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("tail")),
            schema=self.schema,
        )
        if self.bytes_ is not None:
            builder = builder.set(bytes_=self.bytes_)
        if self.debug:
            builder = builder.set(debug=True)
        if self.follow is not None:
            builder = builder.set(follow=self.follow)
        if self.F:
            builder = builder.set(F=True)
        if self.lines is not None:
            builder = builder.set(lines=self.lines)
        if self.max_unchanged_stats is not None:
            builder = builder.set(max_unchanged_stats=self.max_unchanged_stats)
        if self.pid is not None:
            builder = builder.set(pid=self.pid)
        if self.quiet:
            builder = builder.set(quiet=True)
        if self.retry:
            builder = builder.set(retry=True)
        if self.sleep_interval is not None:
            builder = builder.set(sleep_interval=self.sleep_interval)
        if self.verbose:
            builder = builder.set(verbose=True)
        if self.zero_terminated:
            builder = builder.set(zero_terminated=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class touch:
    """create file, or change file timestamps

    Attributes:
        a
        no_create: do not create any files
        date: parse STRING and use it instead of current time
        f
        no_dereference: affect  each  symbolic  link instead of any referenced file; useful only on systems that can change the timestamps of a symlink
        m
        reference: use this file's times instead of current time
        t: use specified time instead of current time, with a date-time format that differs from -d's (assumption: assumed optional value takes one string)
        time: specify which time to change: access time (-a): 'access',  'atime', 'use'; modification time (-m): 'modify', 'mtime'
        help_: display this help and exit
        version: output version information and exit
    """
    a: bool = False
    no_create: bool = False
    date: str | None = None
    f: bool = False
    no_dereference: bool = False
    m: bool = False
    reference: str | None = None
    t: str | None = None
    time: str | None = None
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "a": ParamSpec(flag="-a"),
        "no_create": ParamSpec(flag="--no-create"),
        "date": ParamSpec(flag="--date"),
        "f": ParamSpec(flag="-f"),
        "no_dereference": ParamSpec(flag="--no-dereference"),
        "m": ParamSpec(flag="-m"),
        "reference": ParamSpec(flag="--reference"),
        "t": ParamSpec(flag="-t", arg_join=" "),
        "time": ParamSpec(flag="--time"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("touch")),
            schema=self.schema,
        )
        if self.a:
            builder = builder.set(a=True)
        if self.no_create:
            builder = builder.set(no_create=True)
        if self.date is not None:
            builder = builder.set(date=self.date)
        if self.f:
            builder = builder.set(f=True)
        if self.no_dereference:
            builder = builder.set(no_dereference=True)
        if self.m:
            builder = builder.set(m=True)
        if self.reference is not None:
            builder = builder.set(reference=self.reference)
        if self.t is not None:
            builder = builder.set(t=self.t)
        if self.time is not None:
            builder = builder.set(time=self.time)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class cut:
    """remove sections from each line of files

    Attributes:
        bytes_: select only these byte positions
        characters: select only these character positions
        complement: complement the set of selected bytes, characters or fields
        delimiter: use DELIM instead of TAB for field delimiter
        fields: select only these fields;  also print any line that contains no de limiter character, unless the -s option is specified
        F: like -f, but also implies -w and -O ' '
        no_partial: with -b, don't output partial multi-byte characters
        output_delimiter: use STRING as the output delimiter; the default is to use the input delimiter
        only_delimited: do not print lines not containing delimiters
        whitespace_delimited: use  a  run  of  blank  characters  as  the  field  delimiter; with 'trimmed', ignore leading and trailing blanks (assumption: assumed optional value takes one string)
        zero_terminated: line delimiter is NUL, not newline
        help_: display this help and exit
        version: output version information and exit
    """
    bytes_: str | None = None
    characters: str | None = None
    complement: bool = False
    delimiter: str | None = None
    fields: str | None = None
    F: str | None = None
    no_partial: bool = False
    output_delimiter: str | None = None
    only_delimited: bool = False
    whitespace_delimited: str | None = None
    zero_terminated: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "bytes_": ParamSpec(flag="--bytes"),
        "characters": ParamSpec(flag="--characters"),
        "complement": ParamSpec(flag="--complement"),
        "delimiter": ParamSpec(flag="--delimiter"),
        "fields": ParamSpec(flag="--fields"),
        "F": ParamSpec(flag="-F", arg_join=" "),
        "no_partial": ParamSpec(flag="--no-partial"),
        "output_delimiter": ParamSpec(flag="--output-delimiter"),
        "only_delimited": ParamSpec(flag="--only-delimited"),
        "whitespace_delimited": ParamSpec(flag="--whitespace-delimited"),
        "zero_terminated": ParamSpec(flag="--zero-terminated"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("cut")),
            schema=self.schema,
        )
        if self.bytes_ is not None:
            builder = builder.set(bytes_=self.bytes_)
        if self.characters is not None:
            builder = builder.set(characters=self.characters)
        if self.complement:
            builder = builder.set(complement=True)
        if self.delimiter is not None:
            builder = builder.set(delimiter=self.delimiter)
        if self.fields is not None:
            builder = builder.set(fields=self.fields)
        if self.F is not None:
            builder = builder.set(F=self.F)
        if self.no_partial:
            builder = builder.set(no_partial=True)
        if self.output_delimiter is not None:
            builder = builder.set(output_delimiter=self.output_delimiter)
        if self.only_delimited:
            builder = builder.set(only_delimited=True)
        if self.whitespace_delimited is not None:
            builder = builder.set(whitespace_delimited=self.whitespace_delimited)
        if self.zero_terminated:
            builder = builder.set(zero_terminated=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class tr:
    """translate or delete characters

    Attributes:
        complement: use the complement of ARRAY1
        delete: delete characters in ARRAY1, do not translate
        squeeze_repeats: replace each sequence of a repeated character that is listed in the last specified ARRAY, with a single occurrence of that character
        truncate_set1: first truncate ARRAY1 to length of ARRAY2
        help_: display this help and exit
        version: output version information and exit
    """
    complement: bool = False
    delete: bool = False
    squeeze_repeats: bool = False
    truncate_set1: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "complement": ParamSpec(flag="--complement"),
        "delete": ParamSpec(flag="--delete"),
        "squeeze_repeats": ParamSpec(flag="--squeeze-repeats"),
        "truncate_set1": ParamSpec(flag="--truncate-set1"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("tr")),
            schema=self.schema,
        )
        if self.complement:
            builder = builder.set(complement=True)
        if self.delete:
            builder = builder.set(delete=True)
        if self.squeeze_repeats:
            builder = builder.set(squeeze_repeats=True)
        if self.truncate_set1:
            builder = builder.set(truncate_set1=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class du:
    """estimate file space usage

    Attributes:
        null: end each output line with NUL, not newline
        all_: write counts for all files, not just directories
        apparent_size: print  apparent sizes rather than device usage; although the appar ent size is usually smaller, it may  be  larger  due  to  holes  in ('sparse') files, internal fragmentation, indirect blocks, etc.
        block_size: scale  sizes  by  SIZE before printing them; See SIZE format below; E.g., '-BM' prints sizes in units of 1,048,576 bytes
        bytes_: equivalent to '--apparent-size --block-size=1'
        total: produce a grand total
        dereference_args: dereference only symlinks that are listed on the command line
        max_depth: print the total for a directory (or file, with --all) only if it is N or fewer levels below the command line  argument;   --max-depth=0 is the same as --summarize
        files0_from: summarize  device  usage of the NUL-terminated file names specified in file F;  if F is -, read names from standard input
        H
        human_readable: print sizes in human readable format (e.g., 1K 234M 2G)
        inodes: list inode usage information instead of block usage
        k
        dereference: dereference all symbolic links
        count_links: count sizes many times if hard linked
        m
        no_dereference: don't follow any symbolic links (this is the default)
        separate_dirs: for directories do not include size of subdirectories
        si
        summarize: display only a total for each argument
        threshold: exclude entries smaller than SIZE if positive, or  entries  greater than SIZE if negative
        time: show time as WORD instead of modification time: atime, access, use, ctime or status
        time_style: time/date format with --time; see TIME_STYLE below
        exclude_from: exclude files that match any pattern in FILE
        exclude: exclude files that match PATTERN
        one_file_system: skip directories on different file systems
        help_: display this help and exit
        version: output version information and exit
    """
    null: bool = False
    all_: bool = False
    apparent_size: bool = False
    block_size: str | None = None
    bytes_: bool = False
    total: bool = False
    dereference_args: bool = False
    max_depth: int | None = None
    files0_from: str | None = None
    H: bool = False
    human_readable: bool = False
    inodes: bool = False
    k: bool = False
    dereference: bool = False
    count_links: bool = False
    m: bool = False
    no_dereference: bool = False
    separate_dirs: bool = False
    si: bool = False
    summarize: bool = False
    threshold: str | None = None
    time: str | None = None
    time_style: str | None = None
    exclude_from: str | None = None
    exclude: str | None = None
    one_file_system: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "null": ParamSpec(flag="--null"),
        "all_": ParamSpec(flag="--all"),
        "apparent_size": ParamSpec(flag="--apparent-size"),
        "block_size": ParamSpec(flag="--block-size"),
        "bytes_": ParamSpec(flag="--bytes"),
        "total": ParamSpec(flag="--total"),
        "dereference_args": ParamSpec(flag="--dereference-args"),
        "max_depth": ParamSpec(flag="--max-depth"),
        "files0_from": ParamSpec(flag="--files0-from"),
        "H": ParamSpec(flag="-H"),
        "human_readable": ParamSpec(flag="--human-readable"),
        "inodes": ParamSpec(flag="--inodes"),
        "k": ParamSpec(flag="-k"),
        "dereference": ParamSpec(flag="--dereference"),
        "count_links": ParamSpec(flag="--count-links"),
        "m": ParamSpec(flag="-m"),
        "no_dereference": ParamSpec(flag="--no-dereference"),
        "separate_dirs": ParamSpec(flag="--separate-dirs"),
        "si": ParamSpec(flag="--si"),
        "summarize": ParamSpec(flag="--summarize"),
        "threshold": ParamSpec(flag="--threshold"),
        "time": ParamSpec(flag="--time"),
        "time_style": ParamSpec(flag="--time-style"),
        "exclude_from": ParamSpec(flag="--exclude-from"),
        "exclude": ParamSpec(flag="--exclude"),
        "one_file_system": ParamSpec(flag="--one-file-system"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("du")),
            schema=self.schema,
        )
        if self.null:
            builder = builder.set(null=True)
        if self.all_:
            builder = builder.set(all_=True)
        if self.apparent_size:
            builder = builder.set(apparent_size=True)
        if self.block_size is not None:
            builder = builder.set(block_size=self.block_size)
        if self.bytes_:
            builder = builder.set(bytes_=True)
        if self.total:
            builder = builder.set(total=True)
        if self.dereference_args:
            builder = builder.set(dereference_args=True)
        if self.max_depth is not None:
            builder = builder.set(max_depth=self.max_depth)
        if self.files0_from is not None:
            builder = builder.set(files0_from=self.files0_from)
        if self.H:
            builder = builder.set(H=True)
        if self.human_readable:
            builder = builder.set(human_readable=True)
        if self.inodes:
            builder = builder.set(inodes=True)
        if self.k:
            builder = builder.set(k=True)
        if self.dereference:
            builder = builder.set(dereference=True)
        if self.count_links:
            builder = builder.set(count_links=True)
        if self.m:
            builder = builder.set(m=True)
        if self.no_dereference:
            builder = builder.set(no_dereference=True)
        if self.separate_dirs:
            builder = builder.set(separate_dirs=True)
        if self.si:
            builder = builder.set(si=True)
        if self.summarize:
            builder = builder.set(summarize=True)
        if self.threshold is not None:
            builder = builder.set(threshold=self.threshold)
        if self.time is not None:
            builder = builder.set(time=self.time)
        if self.time_style is not None:
            builder = builder.set(time_style=self.time_style)
        if self.exclude_from is not None:
            builder = builder.set(exclude_from=self.exclude_from)
        if self.exclude is not None:
            builder = builder.set(exclude=self.exclude)
        if self.one_file_system:
            builder = builder.set(one_file_system=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class df:
    """report file system space usage

    Attributes:
        all_: include pseudo, duplicate, inaccessible file systems
        block_size: scale  sizes  by  SIZE before printing them; see SIZE format below; E.g., '-BM' prints sizes in units of 1,048,576 bytes
        human_readable: print sizes in powers of 1024 (e.g., 1023M)
        si: print sizes in powers of 1000 (e.g., 1.1G)
        inodes: list inode information instead of block usage
        k
        local: limit listing to local file systems
        no_sync: do not invoke sync before getting usage info (default)
        output: use the output format defined by FIELD_LIST, or print all fields if FIELD_LIST is omitted (assumption: assumed optional value takes one string)
        portability: use the POSIX output format
        sync: invoke sync before getting usage info
        total: elide all entries insignificant to available space, and  produce  a grand total
        type_: limit listing to file systems of type TYPE
        print_type: print file system type
        exclude_type: limit listing to file systems not of type TYPE
        v
        help_: display this help and exit
        version: output version information and exit
    """
    all_: bool = False
    block_size: str | None = None
    human_readable: bool = False
    si: bool = False
    inodes: bool = False
    k: bool = False
    local: bool = False
    no_sync: bool = False
    output: str | None = None
    portability: bool = False
    sync: bool = False
    total: bool = False
    type_: str | None = None
    print_type: bool = False
    exclude_type: str | None = None
    v: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "all_": ParamSpec(flag="--all"),
        "block_size": ParamSpec(flag="--block-size"),
        "human_readable": ParamSpec(flag="--human-readable"),
        "si": ParamSpec(flag="--si"),
        "inodes": ParamSpec(flag="--inodes"),
        "k": ParamSpec(flag="-k"),
        "local": ParamSpec(flag="--local"),
        "no_sync": ParamSpec(flag="--no-sync"),
        "output": ParamSpec(flag="--output"),
        "portability": ParamSpec(flag="--portability"),
        "sync": ParamSpec(flag="--sync"),
        "total": ParamSpec(flag="--total"),
        "type_": ParamSpec(flag="--type"),
        "print_type": ParamSpec(flag="--print-type"),
        "exclude_type": ParamSpec(flag="--exclude-type"),
        "v": ParamSpec(flag="-v"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("df")),
            schema=self.schema,
        )
        if self.all_:
            builder = builder.set(all_=True)
        if self.block_size is not None:
            builder = builder.set(block_size=self.block_size)
        if self.human_readable:
            builder = builder.set(human_readable=True)
        if self.si:
            builder = builder.set(si=True)
        if self.inodes:
            builder = builder.set(inodes=True)
        if self.k:
            builder = builder.set(k=True)
        if self.local:
            builder = builder.set(local=True)
        if self.no_sync:
            builder = builder.set(no_sync=True)
        if self.output is not None:
            builder = builder.set(output=self.output)
        if self.portability:
            builder = builder.set(portability=True)
        if self.sync:
            builder = builder.set(sync=True)
        if self.total:
            builder = builder.set(total=True)
        if self.type_ is not None:
            builder = builder.set(type_=self.type_)
        if self.print_type:
            builder = builder.set(print_type=True)
        if self.exclude_type is not None:
            builder = builder.set(exclude_type=self.exclude_type)
        if self.v:
            builder = builder.set(v=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class mktemp:
    """create a temporary file or directory

    Attributes:
        directory: create a directory, not a file
        dry_run: do not create anything; merely print a name (unsafe)
        quiet: suppress diagnostics about file/dir-creation failure
        suffix: append  SUFF  to TEMPLATE; SUFF must not contain a slash.  This op tion is implied if TEMPLATE does not end in X
        tmpdir: interpret TEMPLATE relative to DIR; if DIR is  not  specified,  use $TMPDIR  if set, else /tmp.  With this option, TEMPLATE must not be an absolute name; unlike with -t, TEMPLATE may contain slashes, but mktemp creates only the final component (assumption: assumed optional value takes one string)
        t: directory:  $TMPDIR,  if  set; else the directory specified via -p; else /tmp [deprecated]
        help_: display this help and exit
        version: output version information and exit
    """
    directory: bool = False
    dry_run: bool = False
    quiet: bool = False
    suffix: str | None = None
    tmpdir: str | None = None
    t: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "directory": ParamSpec(flag="--directory"),
        "dry_run": ParamSpec(flag="--dry-run"),
        "quiet": ParamSpec(flag="--quiet"),
        "suffix": ParamSpec(flag="--suffix"),
        "tmpdir": ParamSpec(flag="--tmpdir"),
        "t": ParamSpec(flag="-t"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("mktemp")),
            schema=self.schema,
        )
        if self.directory:
            builder = builder.set(directory=True)
        if self.dry_run:
            builder = builder.set(dry_run=True)
        if self.quiet:
            builder = builder.set(quiet=True)
        if self.suffix is not None:
            builder = builder.set(suffix=self.suffix)
        if self.tmpdir is not None:
            builder = builder.set(tmpdir=self.tmpdir)
        if self.t:
            builder = builder.set(t=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class basename:
    """strip directory and suffix from filenames

    Attributes:
        multiple: support multiple arguments and treat each as a NAME
        suffix: remove a trailing SUFFIX; implies -a
        zero: end each output line with NUL, not newline
        help_: display this help and exit
        version: output version information and exit
    """
    multiple: bool = False
    suffix: str | None = None
    zero: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "multiple": ParamSpec(flag="--multiple"),
        "suffix": ParamSpec(flag="--suffix"),
        "zero": ParamSpec(flag="--zero"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("basename")),
            schema=self.schema,
        )
        if self.multiple:
            builder = builder.set(multiple=True)
        if self.suffix is not None:
            builder = builder.set(suffix=self.suffix)
        if self.zero:
            builder = builder.set(zero=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class dirname:
    """strip last component from file name

    Attributes:
        zero: end each output line with NUL, not newline
        help_: display this help and exit
        version: output version information and exit
    """
    zero: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "zero": ParamSpec(flag="--zero"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("dirname")),
            schema=self.schema,
        )
        if self.zero:
            builder = builder.set(zero=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class echo:
    """display a line of text

    Attributes:
        n
        e
        E
        help_: display this help and exit
        version: output version information and exit
    """
    n: bool = False
    e: bool = False
    E: bool = False
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "n": ParamSpec(flag="-n"),
        "e": ParamSpec(flag="-e"),
        "E": ParamSpec(flag="-E"),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("echo")),
            schema=self.schema,
        )
        if self.n:
            builder = builder.set(n=True)
        if self.e:
            builder = builder.set(e=True)
        if self.E:
            builder = builder.set(E=True)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder


@dataclass(frozen=True, slots=True)
class printf:
    """format and print data

    Attributes:
        help_: display this help and exit
        version: output version information and exit tal escapes should have a leading 0 like \\0NNN escaping non-printable characters with the POSIX $'' syntax
    """
    help_: bool = False
    version: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("printf")),
            schema=self.schema,
        )
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        return builder
