{
  description = "Python protocol buffers for the rest of us";

  inputs = {
    nix2container = {
      url = "github:nlewo/nix2container";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
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

          projectDir = ./.;
          src = pkgs.gitignoreSource ./.;

          propagatedBuildInputs = with pkgs; [ buf grpc protobuf3_21 ];

          overrides = pkgs.poetry2nix.overrides.withDefaults (
            import ./poetry-overrides.nix { }
          );

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
          overrides = pkgs.poetry2nix.overrides.withDefaults (
            import ./poetry-overrides.nix { }
          );
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
          prettierTOML = pkgs.pkgsBuildBuild.writeShellScriptBin "prettier" ''
            ${pkgs.pkgsBuildBuild.nodePackages.prettier}/bin/prettier \
            --plugin-search-dir "${pkgs.pkgsBuildBuild.nodePackages.prettier-plugin-toml}/lib" \
            "$@"
          '';
          protoletariatDevEnv = pkgs.protoletariatDevEnv310;
        } // (super.lib.listToAttrs (
          super.lib.concatMap
            (py: [
              (mkApp { inherit py pkgs; })
              (mkEnv {
                inherit py;
                pkgs = pkgs.pkgsBuildBuild;
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
          } // legacyPkgs.lib.optionalAttrs (!legacyPkgs.stdenv.isDarwin) {
            crossSystem = nixpkgs.lib.systems.examples.musl64;
          };
          pkgs = import nixpkgs attrs;
          inherit (pkgs) lib;
        in
        rec {
          packages.protoletariat38 = pkgs.protoletariat38;
          packages.protoletariat39 = pkgs.protoletariat39;
          packages.protoletariat310 = pkgs.protoletariat310;
          packages.protoletariat = packages.protoletariat310;

          packages.protoletariat-image = nix2containerPkgs.nix2container.buildImage {
            name = "protoletariat";
            config = {
              entrypoint = [ defaultApp.program ];
              command = [ defaultApp.program ];
            };
            maxLayers = 128;
          };

          defaultPackage = packages.protoletariat;

          apps.protoletariat = flake-utils.lib.mkApp {
            drv = packages.protoletariat;
            exePath = "/bin/protol";
          };
          defaultApp = apps.protoletariat;

          checks = {
            pre-commit-check = pre-commit-hooks.lib.${localSystem}.run {
              src = ./.;
              hooks = {
                nix-linter.enable = true;
                nixpkgs-fmt.enable = true;

                prettier = {
                  enable = true;
                  types_or = [ "json" "markdown" "toml" "yaml" ];
                };

                black.enable = true;
                isort.enable = true;

                flake8 = {
                  enable = true;
                  entry = "${pkgs.protoletariatDevEnv}/bin/flake8";
                  types = [ "python" ];
                };

                pyupgrade = {
                  enable = true;
                  entry = "${pkgs.protoletariatDevEnv}/bin/pyupgrade --py38-plus";
                  types = [ "python" ];
                };

                mypy = {
                  enable = true;
                  entry = "${pkgs.protoletariatDevEnv}/bin/mypy";
                  types = [ "python" ];
                };

                shellcheck = {
                  enable = true;
                  files = "\\.sh$";
                  types_or = [ "file" ];
                };

                shfmt = {
                  enable = true;
                  entry = lib.mkForce "${pkgs.pkgsBuildBuild.shfmt}/bin/shfmt -i 2 -sr -d -s -l";
                  files = "\\.sh$";
                };
              };
              settings.prettier.binPath = "${pkgs.pkgsBuildBuild.prettierTOML}/bin/prettier";
            };
          };

          devShell = pkgs.pkgsBuildBuild.mkShell {
            nativeBuildInputs = with pkgs.pkgsBuildBuild; [
              buf
              dive
              grpc
              poetry
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
