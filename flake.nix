{
  description = "Python protocol buffers for the rest of us";

  inputs = {
    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.nixpkgs.follows = "nixpkgs";
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
    , poetry2nix
    , pre-commit-hooks
    }:
    let
      mkApp = { py, pkgs }:
        {
          name = "protoletariat${py}";
          value = pkgs.poetry2nix.mkPoetryApplication {
            python = pkgs."python${py}Optimized";

            projectDir = ./.;
            src = pkgs.gitignoreSource ./.;

            buildInputs = [ pkgs.sqlite ];

            checkInputs = with pkgs; [ buf grpc protobuf ];

            preCheck = ''
              set -euo pipefail

              export HOME
              HOME="$(mktemp -d)"
            '';

            checkPhase = ''
              set -euo pipefail

              runHook preCheck
              pytest
              runHook postCheck
            '';

            pythonImportsCheck = [ "protoletariat" ];
          };

        };
      mkEnv = { py, pkgs }:
        {
          name = "protoletariatDevEnv${py}";
          value = pkgs.poetry2nix.mkPoetryEnv {
            python = pkgs."python${py}";
            projectDir = ./.;
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
            [ "37" "38" "39" "310" ]
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
      packages.protoletariat = packages.protoletariat310;

      defaultPackage = packages.protoletariat;

      apps.protoletariat = flake-utils.lib.mkApp {
        drv = packages.protoletariat;
        exePath = "/bin/protol";
      };
      defaultApp = apps.protoletariat;

      packages.protoletariat-image = pkgs.dockerTools.buildLayeredImage {
        name = "protoletariat";
        config = {
          Entrypoint = [ defaultApp.program ];
          Command = [ defaultApp.program ];
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
          protoletariatDevEnv
        ];

        inherit (self.checks.${system}.pre-commit-check) shellHook;
      };
    }));
}
