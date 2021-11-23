{ ... }:
_: super:
{
  typing-extensions = super.typing-extensions.overridePythonAttrs (
    old: {
      buildInputs = old.buildInputs ++ [ super.flit-core ];
    }
  );
}
