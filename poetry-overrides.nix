{ ... }:
_: super:
{
  typing-extensions = super.typing-extensions.overridePythonAttrs (old: {
    buildInputs = (old.buildInputs or [ ]) ++ [ super.flit-core ];
  });
}
