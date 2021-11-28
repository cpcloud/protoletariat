{ ... }:
_: super:
{
  typing-extensions = super.typing-extensions.overridePythonAttrs (attrs: {
    buildInputs = (attrs.buildInputs or [ ]) ++ [ super.flit-core ];
  });
}
