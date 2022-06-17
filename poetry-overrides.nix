{ ... }: self: super: {
  platformdirs = super.platformdirs.overridePythonAttrs (attrs: {
    nativeBuildInputs = attrs.nativeBuildInputs or [ ] ++ [ self.setuptools ];
  });

  pytest-runner = super.pytest-runner.overridePythonAttrs (attrs: {
    nativeBuildInputs = attrs.nativeBuildInputs or [ ] ++ [ self.setuptools ];
  });
}
