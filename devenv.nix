{ pkgs, lib, ... }:
{
  name = "pyshb";
  languages = {
    python = {
      enable = true;
      uv = {
        enable = true;
        sync.enable = true;
      };
    };
  };
  # The git hook runs the nixpkgs `ty` with language = "system", so unlike
  # `uv run ty check` it does not resolve imports against the uv-managed
  # environment at .devenv/state/venv. Left alone, the first test module to
  # `import pytest` fails the hook with `unresolved-import`, even though
  # pytest is declared in [dependency-groups].
  #
  # VIRTUAL_ENV is the variable ty reads for this, and exporting it here is
  # what reaches the hook: the hook is a child process of this shell and
  # inherits its environment. git-hooks has no `env` option to set it at the
  # hook itself, and wrapping the entry in a store-built script is not an
  # option either, because git-hooks writes the entry path without realising
  # the derivation, so the hook would fail on a missing executable.
  #
  # Naming the venv directory rather than its site-packages keeps this
  # version-agnostic, and builtins.toString keeps the path a plain string
  # instead of copying the venv into /nix/store.
  enterShell = ''
    export VIRTUAL_ENV=${builtins.toString ./.devenv/state/venv}
  '';
  git-hooks.hooks = {
    ruff.enable = true;
    ty = {
      enable = true;
      name = "ty";
      entry = "${lib.getExe pkgs.ty} check";
      files = "\\.py$";
      language = "system";
      pass_filenames = true;
    };
  };
}