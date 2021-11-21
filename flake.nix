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
    in
    rec {
      packages.protoletariat = poetry2nix.mkPoetryApplication {
        python = pkgs.python3;

        pyproject = ./pyproject.toml;
        poetrylock = ./poetry.lock;
        src = lib.cleanSource ./.;

        overrides = pkgs.poetry2nix.overrides.withDefaults (
          import ./poetry-overrides.nix {
            inherit pkgs;
            inherit (pkgs) lib stdenv;
          }
        );
      };

      defaultPackage = packages.protoletariat;

      apps.protoletariat = flake-utils.lib.mkApp {
        drv = packages.protoletariat;
      };
      defaultApp = apps.protoletariat;

      packages.protoletariat-image = pkgs.dockerTools.buildLayeredImage {
        name = "protoletariat";
        config = {
          Entrypoint = [ "${packages.protoletariat}/bin/protol" ];
          Command = [ "${pkgs.protoletariat}/bin/protol" ];
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
              types_or = [ "json" "toml" "yaml" ];
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
          };
        };
      };

      devShell = pkgs.mkShell {
        nativeBuildInputs = (with pkgs; [
          commitizen
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
