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
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
      };
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
          python = pkgs."python${py}Optimized";
          preferWheels = true;

          projectDir = ./.;
          src = pkgs.gitignoreSource ./.;
          checkGroups = [ "dev" "test" ];

          propagatedBuildInputs = with pkgs; [ buf grpc protobuf3_21 ];

          overrides = [
            (import ./poetry-overrides.nix)
            pkgs.poetry2nix.defaultPoetryOverrides
          ];

          checkInputs = with pkgs; [ buf grpc protobuf3_21 ];

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
          preferWheels = true;
          groups = [ "dev" "test" "docs" ];
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
        poetry2nix.overlay
        (pkgs: super: {
          prettierTOML = pkgs.writeShellScriptBin "prettier" ''
            ${pkgs.nodePackages.prettier}/bin/prettier \
            --plugin-search-dir "${pkgs.nodePackages.prettier-plugin-toml}/lib" \
            "$@"
          '';
          protoletariatDevEnv = pkgs.protoletariatDevEnv310;
        } // (super.lib.listToAttrs (
          super.lib.concatMap
            (py: [
              (mkApp { inherit py pkgs; })
              (mkEnv {
                inherit py pkgs;
              })
              {
                name = "python${py}Optimized";
                value = (super."python${py}".override {
                  # remove python-config, this contributes around 30MB to the closure
                  stripConfig = true;
                  # remove the IDLE GUI
                  stripIdlelib = true;
                  # remove tests
                  stripTests = true;
                  # remove tkinter things
                  stripTkinter = true;
                  # remove a bunch of unused modules
                  ncurses = null;
                  readline = null;
                  openssl = null;
                  gdbm = null;
                  sqlite = null;
                  configd = null;
                  tzdata = null;
                  # we could reduce the size even futher (< 40MB for the
                  # entire closure) but there's a performance penality:
                  # stripBytecode == true + rebuildBytecode == false means
                  # *no* bytecode on disk until import. Probably not a big
                  # issue for a long running service, but horrible for a CLI
                  # tool
                  stripBytecode = true;
                  rebuildBytecode = true;
                  # no need for site customize in the application
                  includeSiteCustomize = false;
                  # unused in protoletariat
                  mimetypesSupport = false;
                }).overrideAttrs (attrs: {
                  # compile the python interpreter without -Os because we care
                  # about startup time; protoletariat is a CLI tool after all
                  preConfigure = ''
                    ${attrs.preConfigure or ""}
                  '' + (super.lib.optionalString (!super.stdenv.isDarwin) ''
                    export NIX_LDFLAGS+=" --strip-all"
                  '');
                  # remove optimized bytecode; shaves about 15MB
                  #
                  # the application will never be run with any optimization
                  # level so we don't need it
                  postInstall = ''
                    ${attrs.postInstall or ""}
                    find $out -name '*.opt-?.pyc' -exec rm '{}' +
                  '';
                });
              }
            ])
            [ "38" "39" "310" ]
        )))
      ];
    } // (
      flake-utils.lib.eachDefaultSystem (
        localSystem:
        let
          legacyPkgs = nixpkgs.legacyPackages.${localSystem};
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
            inherit (pkgs) protoletariat38 protoletariat39 protoletariat310;
            protoletariat = pkgs.protoletariat310;
            default = pkgs.protoletariat310;

            protoletariat38-image = mkImage apps.protoletariat38.program;
            protoletariat39-image = mkImage apps.protoletariat39.program;
            protoletariat310-image = mkImage apps.protoletariat310.program;
            protoletariat-image = packages.protoletariat310-image;
          };


          apps = {
            protoletariat38 = mkApp packages.protoletariat38;
            protoletariat39 = mkApp packages.protoletariat39;
            protoletariat310 = mkApp packages.protoletariat310;

            protoletariat = apps.protoletariat310;
            default = apps.protoletariat;
          };

          checks = {
            pre-commit-check = pre-commit-hooks.lib.${localSystem}.run {
              src = ./.;
              hooks = {
                actionlint.enable = true;
                black.enable = true;
                nixpkgs-fmt.enable = true;
                shellcheck.enable = true;
                statix.enable = true;

                ruff = {
                  enable = true;
                  entry = "${pkgs.protoletariatDevEnv.pkgs.ruff}/bin/ruff --force-exclude";
                };

                prettier = {
                  enable = true;
                  types_or = [ "json" "markdown" "toml" "yaml" ];
                };

                mypy = {
                  enable = true;
                  entry = "${pkgs.protoletariatDevEnv.pkgs.mypy}/bin/mypy";
                  types = [ "python" ];
                };

                shfmt = {
                  enable = true;
                  entry = lib.mkForce "${pkgs.shfmt}/bin/shfmt -i 2 -sr -d -s -l";
                };
              };

              settings.prettier.binPath = "${pkgs.prettierTOML}/bin/prettier";
            };
          };

          devShells.default = pkgs.mkShell {
            nativeBuildInputs = with pkgs; [
              buf
              grpc
              prettierTOML
              protobuf
              protoletariatDevEnv
              protoletariatDevEnv.pkgs.poetry
            ];

            inherit (self.checks.${localSystem}.pre-commit-check) shellHook;
          };
        }
      )
    );
}
