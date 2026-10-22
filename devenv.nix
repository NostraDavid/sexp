{pkgs, ...}: {
  dotenv.enable = false;
  packages = [pkgs.python314 pkgs.uv pkgs.just pkgs.git];
  env = {
    UV_PYTHON = "3.14";
    UV_PYTHON_PREFERENCE = "only-system";
    UV_PYTHON_DOWNLOADS = "never";
    PYTHONNOUSERSITE = "1";
  };
  enterShell = ''
    unset PYTHONPATH PYTHONHOME _PYTHON_SYSCONFIGDATA_NAME
  '';
}
