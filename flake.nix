{
  description = "Python protocol buffers for the rest of us";

  inputs = {
    nix2container = {
      url = "github:nlewo/nix2container";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
      };
    };

    flake-utils.url = "github:numtide/flake-utils";

    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };

    gitignore = {
      url = "github:hercules-ci/gitignore.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable-small";

    pre-commit-hooks = {
      url = "github:cachix/pre-commit-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
      };
    };
  };

  outputs =
    { self
    , flake-utils
    , gitignore
    , nixpkgs
    , pre-commit-hooks
    , poetry2nix
    , nix2container
    , ...
    }:
    let
      nix2containerPkgs = nix2container.packages.x86_64-linux;
      mkApp = { py, pkgs }: {
        name = "protoletariat${py}";
        value = pkgs.poetry2nix.mkPoetryApplication {
          python = pkgs."python${py}";
          preferWheels = true;
          checkGroups = [ "dev" "test" ];

          projectDir = ./.;
          src = pkgs.gitignoreSource ./.;

          propagatedBuildInputs = with pkgs; [ buf grpc protobuf3_21 ];

          overrides = [
            (import ./poetry-overrides.nix)
            pkgs.poetry2nix.defaultPoetryOverrides
          ];

          nativeCheckInputs = with pkgs; [ buf grpc protobuf3_21 ];

          preCheck = "HOME=$TMPDIR";

          checkPhase = ''
            set -euo pipefail

            runHook preCheck
            pytest
            runHook postCheck
          '';

          pythonImportsCheck = [ "protoletariat" ];
        };

      };
      mkEnv = { py, pkgs }: {
        name = "protoletariatDevEnv${py}";
        value = pkgs.poetry2nix.mkPoetryEnv {
          python = pkgs."python${py}";
          projectDir = ./.;
          groups = [ "dev" "test" ];
          preferWheels = true;
          overrides = [
            (import ./poetry-overrides.nix)
            pkgs.poetry2nix.defaultPoetryOverrides
          ];
          editablePackageSources = {
            protoletariat = ./protoletariat;
          };
        };
      };
    in
    {
      overlay = nixpkgs.lib.composeManyExtensions [
        gitignore.overlay
        poetry2nix.overlays.default
        (pkgs: super: {
          prettierTOML = pkgs.writeShellScriptBin "prettier" ''
            ${pkgs.nodePackages.prettier}/bin/prettier \
            --plugin-search-dir "${pkgs.nodePackages.prettier-plugin-toml}/lib" \
            "$@"
          '';
          protoletariatDevEnv = pkgs.protoletariatDevEnv312;
        } // (super.lib.listToAttrs (
          super.lib.concatMap
            (py: [
              (mkApp { inherit py pkgs; })
              (mkEnv { inherit py pkgs; })
            ])
            [ "39" "310" "311" "312" ]
        )))
      ];
    } // (
      flake-utils.lib.eachDefaultSystem (
        localSystem:
        let
          attrs = {
            inherit localSystem;
            overlays = [ self.overlay ];
          };
          pkgs = import nixpkgs attrs;
          inherit (pkgs) lib;
          mkImage = program: nix2containerPkgs.nix2container.buildImage {
            name = "protoletariat";
            config = {
              entrypoint = [ program ];
              command = [ program ];
            };
            maxLayers = 128;
          };
          mkApp = drv: flake-utils.lib.mkApp {
            inherit drv;
            exePath = "/bin/protol";
          };
        in
        rec {
          packages = {
            inherit (pkgs) protoletariat39 protoletariat310 protoletariat311 protoletariat312;
            protoletariat = pkgs.protoletariat312;
            default = pkgs.protoletariat312;

            protoletariat39-image = mkImage apps.protoletariat39.program;
            protoletariat310-image = mkImage apps.protoletariat310.program;
            protoletariat311-image = mkImage apps.protoletariat311.program;
            protoletariat312-image = mkImage apps.protoletariat312.program;

            protoletariat-image = packages.protoletariat312-image;
          };


          apps = {
            protoletariat39 = mkApp packages.protoletariat39;
            protoletariat310 = mkApp packages.protoletariat310;
            protoletariat311 = mkApp packages.protoletariat311;
            protoletariat312 = mkApp packages.protoletariat312;

            protoletariat = apps.protoletariat312;
            default = apps.protoletariat;
          };

          checks = {
            pre-commit-check = pre-commit-hooks.lib.${localSystem}.run {
              src = ./.;
              hooks = {
                actionlint.enable = true;
                nixpkgs-fmt.enable = true;
                shellcheck.enable = true;
                statix.enable = true;
                taplo.enable = true;
                ruff.enable = true;
                ruff-format.enable = true;
                deadnix.enable = true;

                prettier = {
                  enable = true;
                  types_or = [ "json" "markdown" "yaml" ];
                };

                mypy = {
                  enable = true;
                  entry = lib.mkForce "${pkgs.protoletariatDevEnv}/bin/mypy --config-file ${./pyproject.toml}";
                  types = [ "python" ];
                };

                shfmt = {
                  enable = true;
                  entry = lib.mkForce "${pkgs.shfmt}/bin/shfmt -i 2 -sr -d -s -l";
                };
                prettier.settings.binPath = "${pkgs.prettierTOML}/bin/prettier";
              };

            };
          };

          devShells.release = pkgs.mkShell {
            name = "release";
            nativeBuildInputs = with pkgs; [ git poetry nodejs_20 unzip gnugrep ];
          };

          devShells.default = pkgs.mkShell {
            nativeBuildInputs = with pkgs; [
              poetry
              buf
              grpc
              prettierTOML
              protobuf
              protoletariatDevEnv
            ];

            inherit (self.checks.${localSystem}.pre-commit-check) shellHook;
          };
        }
      )
    );
}
