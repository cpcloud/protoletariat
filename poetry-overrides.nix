{ pkgs, ... }:
self: super:
{
  typing-extensions = super.typing-extensions.overridePythonAttrs (old: {
    buildInputs = (old.buildInputs or [ ]) ++ [ super.flit-core ];
  });

  version-query = super.version-query.overridePythonAttrs (old: {
    nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ pkgs.git ];
    propagatedBuildInputs = (old.propagatedBuildInputs or [ ]) ++ [ self.docutils ];
  });

  typed-astunparse = super.typed-astunparse.overridePythonAttrs (old: {
    nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ pkgs.git ];
  });
}
