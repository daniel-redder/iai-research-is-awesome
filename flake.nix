{
  description = "IAI Research Pipeline Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux"; # Or your specific architecture
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        # 1. Add the missing C++ and Zlib libraries here
        buildInputs = with pkgs; [
          python312
          uv
          stdenv.cc.cc.lib
          zlib
        ];

        # 2. Tell the pre-compiled Python wheels where to find them
        shellHook = ''
          export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH
        '';
      };
    };
}