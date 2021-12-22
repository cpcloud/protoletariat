{
  description = "Python protocol buffers for the rest of us";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";

    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable-small";

    pre-commit-hooks = {
      url = "github:cachix/pre-commit-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };

    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs =
    { self
    , nixpkgs
    , flake-utils
    , pre-commit-hooks
    , poetry2nix
    }:
    {
      overlay = nixpkgs.lib.composeManyExtensions [
        poetry2nix.overlay
        (pkgs: super: {
          prettierTOML = pkgs.writeShellScriptBin "prettier" ''
            ${pkgs.nodePackages.prettier}/bin/prettier \
            --plugin-search-dir "${pkgs.nodePackages.prettier-plugin-toml}/lib" \
            "$@"
          '';
        } // (super.lib.listToAttrs (
          super.lib.concatMap
            (py:
              let
                noDotPy = super.lib.replaceStrings [ "." ] [ "" ] py;
                overrides = pkgs.poetry2nix.overrides.withDefaults (
                  import ./poetry-overrides.nix {
                    inherit pkgs;
                    inherit (pkgs) lib stdenv;
                  }
                );
              in
              [
                {
                  name = "protoletariat${noDotPy}";
                  value = pkgs.poetry2nix.mkPoetryApplication {
                    python = pkgs."python${noDotPy}";

                    pyproject = ./pyproject.toml;
                    poetrylock = ./poetry.lock;
                    src = pkgs.lib.cleanSource ./.;

                    buildInputs = [ pkgs.sqlite ];

                    inherit overrides;

                    checkInputs = with pkgs; [ buf grpc protobuf ];

                    preCheck = ''
                      export HOME
                      HOME="$(mktemp -d)"
                    '';

                    checkPhase = ''
                      runHook preCheck
                      pytest
                      runHook postCheck
                    '';

                    pythonImportsCheck = [ "protoletariat" ];
                  };
                }
                {
                  name = "protoletariatDevEnv${noDotPy}";
                  value = pkgs.poetry2nix.mkPoetryEnv {
                    python = pkgs."python${noDotPy}";
                    projectDir = ./.;
                    inherit overrides;
                    editablePackageSources = {
                      protoletariat = ./protoletariat;
                    };
                  };
                }
              ])
            [ "3.7" "3.8" "3.9" "3.10" ]
        )))
      ];
    } // (flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs {
        inherit system;
        overlays = [ self.overlay ];
      };
      inherit (pkgs) lib;
    in
    rec {
      packages.protoletariat37 = pkgs.protoletariat37;
      packages.protoletariat38 = pkgs.protoletariat38;
      packages.protoletariat39 = pkgs.protoletariat39;
      packages.protoletariat310 = pkgs.protoletariat310;
      packages.protoletariat = pkgs.protoletariat310;

      defaultPackage = pkgs.protoletariat310;

      apps.protoletariat = flake-utils.lib.mkApp {
        drv = packages.protoletariat;
        exePath = "/bin/protol";
      };
      defaultApp = apps.protoletariat;

      packages.protoletariat-image = pkgs.dockerTools.buildLayeredImage {
        name = "protoletariat";
        config = {
          Entrypoint = [ "${defaultPackage}/bin/protol" ];
          Command = [ "${defaultPackage}/bin/protol" ];
        };
      };

      checks = {
        pre-commit-check = pre-commit-hooks.lib.${system}.run {
          src = ./.;
          hooks = {
            nix-linter = {
              enable = true;
              entry = lib.mkForce "${pkgs.nix-linter}/bin/nix-linter";
            };

            nixpkgs-fmt = {
              enable = true;
              entry = lib.mkForce "${pkgs.nixpkgs-fmt}/bin/nixpkgs-fmt --check";
            };

            prettier = {
              enable = true;
              entry = lib.mkForce "${pkgs.prettierTOML}/bin/prettier --check";
              types_or = [ "json" "markdown" "toml" "yaml" ];
            };

            black = {
              enable = true;
              entry = lib.mkForce "black --check";
              types = [ "python" ];
            };

            isort = {
              enable = true;
              language = "python";
              entry = lib.mkForce "isort --check";
              types_or = [ "cython" "pyi" "python" ];
            };

            flake8 = {
              enable = true;
              language = "python";
              entry = "flake8";
              types = [ "python" ];
            };

            pyupgrade = {
              enable = true;
              entry = "pyupgrade --py37-plus";
              types = [ "python" ];
            };

            mypy = {
              enable = true;
              entry = "mypy";
              types = [ "python" ];
            };
          };
        };
      };

      devShell = pkgs.mkShell {
        nativeBuildInputs = with pkgs; [
          buf
          commitizen
          grpc
          poetry
          prettierTOML
          protobuf
          protoletariatDevEnv310
        ];

        inherit (self.checks.${system}.pre-commit-check) shellHook;
      };
    }));
}
