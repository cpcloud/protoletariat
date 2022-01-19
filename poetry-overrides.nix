{ ... }:
self: super:
{
  isort = super.isort.overridePythonAttrs (attrs: {
    nativeBuildInputs = (attrs.nativeBuildInputs or [ ]) ++ [ self.poetry ];
  });
}
