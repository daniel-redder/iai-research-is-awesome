{
  description = "IAI Research Pipeline Development Environment with uv";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.python312
            pkgs.uv
            pkgs.git
          ];

          shellHook = ''
            echo "Entering IAI Research Pipeline Nix shell"
            echo "Python $(python --version)"
            echo "uv $(uv --version)"
            
            # Natively sync dependencies and create a virtualenv
            if [ -f pyproject.toml ]; then
              uv sync
            fi
          '';
        };
      }
    );
}