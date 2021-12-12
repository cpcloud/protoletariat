{ ... }:
pyself: pysuper:
{
  typing-extensions = pysuper.typing-extensions.overridePythonAttrs (attrs: {
    buildInputs = (attrs.buildInputs or [ ]) ++ [ pyself.flit-core ];
  });
}
