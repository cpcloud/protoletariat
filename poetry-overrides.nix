{ ... }: self: super: {
  grpc-stubs = super.grpc-stubs.overridePythonAttrs (attrs: {
    nativeBuildInputs = attrs.nativeBuildInputs or [ ] ++ [
      self.setuptools
    ];
  });
}
