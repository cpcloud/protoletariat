{ ... }: self: super: {
  grpc-stubs = super.grpc-stubs.overridePythonAttrs (attrs: {
    nativeBuildInputs = attrs.nativeBuildInputs or [ ] ++ [ self.setuptools ];
  });

  exceptiongroup = super.exceptiongroup.overridePythonAttrs (attrs: {
    nativeBuildInputs = attrs.nativeBuildInputs or [ ] ++ [ self.flit-scm ];
  });

  mypy = super.mypy.overridePythonAttrs (attrs: self.lib.optionalAttrs (self.pythonOlder "3.9") {
    NIX_CFLAGS_COMPILE = self.lib.concatStringsSep " " (attrs.NIX_CFLAGS_COMPILE or [ ] ++ [ "-Wno-error=cpp" ]);
  });
}
