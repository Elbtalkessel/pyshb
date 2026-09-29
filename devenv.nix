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
