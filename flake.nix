{
  description = "IAI Research Pipeline Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux"; # Or your specific architecture
      pkgs = nixpkgs.legacyPackages.${system};
      pythonEnv = pkgs.python312.withPackages (ps: [
        ps.pillow
        ps.qrcode
      ]);
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        # 1. Add the missing C++ and Zlib libraries here
        buildInputs = with pkgs; [
          pythonEnv
          uv
          stdenv.cc.cc.lib
          zlib
          poppler-utils
        ];

        # 2. Tell the pre-compiled Python wheels where to find them
        shellHook = ''
          export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH
        '';
      };

      apps.${system}.prepare-brochure-cover = {
        type = "app";
        program = "${pkgs.writeShellScript "prepare-brochure-cover" ''
          repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
          exec ${pythonEnv}/bin/python "$repo_root/scripts/prepare_brochure_cover.py"
        ''}";
      };
    };
}
