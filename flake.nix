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
    , ...
    }:
    flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
      inherit (pkgs) lib;
      prettierTOML = pkgs.writeShellScriptBin "prettier" ''
        ${pkgs.nodePackages.prettier}/bin/prettier \
        --plugin-search-dir "${pkgs.nodePackages.prettier-plugin-toml}/lib" \
        "$@"
      '';

      mkPoetryEnv = python: pkgs.poetry2nix.mkPoetryEnv {
        inherit python;
        projectDir = ./.;
        editablePackageSources = {
          protoletariat = ./protoletariat;
        };
        overrides = pkgs.poetry2nix.overrides.withDefaults (
          import ./poetry-overrides.nix {
            inherit pkgs;
            inherit (pkgs) lib stdenv;
          }
        );
      };

      mkApp = python: pkgs.poetry2nix.mkPoetryApplication {
        inherit python;

        pyproject = ./pyproject.toml;
        poetrylock = ./poetry.lock;
        src = lib.cleanSource ./.;

        overrides = pkgs.poetry2nix.overrides.withDefaults (
          import ./poetry-overrides.nix {
            inherit pkgs;
            inherit (pkgs) lib stdenv;
          }
        );

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
    in
    rec {
      packages.protoletariat37 = mkApp pkgs.python37;
      packages.protoletariat38 = mkApp pkgs.python38;
      packages.protoletariat39 = mkApp pkgs.python39;
      packages.protoletariat = mkApp pkgs.python3;

      defaultPackage = packages.protoletariat;

      apps.protoletariat = flake-utils.lib.mkApp {
        drv = packages.protoletariat;
        exePath = "/bin/protol";
      };
      defaultApp = apps.protoletariat;

      packages.protoletariat-image = pkgs.dockerTools.buildLayeredImage {
        name = "protoletariat";
        config = {
          Entrypoint = [ "${packages.protoletariat}/bin/protol" ];
          Command = [ "${packages.protoletariat}/bin/protol" ];
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

            shellcheck = {
              enable = true;
              entry = "${pkgs.shellcheck}/bin/shellcheck";
              files = "\\.sh$";
            };

            shfmt = {
              enable = true;
              entry = "${pkgs.shfmt}/bin/shfmt -i 2 -sr -d -s -l";
              files = "\\.sh$";
            };

            prettier = {
              enable = true;
              entry = lib.mkForce "${prettierTOML}/bin/prettier --check";
              types_or = [ "json" "toml" "yaml" "markdown" ];
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
        nativeBuildInputs = (with pkgs; [
          buf
          commitizen
          grpc
          poetry
          protobuf
        ]) ++ [
          prettierTOML
          (mkPoetryEnv pkgs.python3)
        ];
        shellHook = self.checks.${system}.pre-commit-check.shellHook;
      };
    });
}
