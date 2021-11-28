{ pkgs, ... }:
pyself: pysuper:
{
  typing-extensions = pysuper.typing-extensions.overridePythonAttrs (attrs: {
    buildInputs = (attrs.buildInputs or [ ]) ++ [ pyself.flit-core ];
  });

  protobuf = pysuper.protobuf.overridePythonAttrs (attrs: {
    nativeBuildInputs = (attrs.nativeBuildInputs or [ ]) ++ [ pyself.pyext ];
    propagatedNativeBuildInputs = (attrs.propagatedNativeBuildInputs or [ ]) ++ [
      pkgs.buildPackages.protobuf
    ];
    buildInputs = (attrs.buildInputs or [ ]) ++ [ pkgs.buildPackages.protobuf ];
    preConfigure = ''
      export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=cpp
      export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION_VERSION=2
    '';

    preBuild = ''
      ${pyself.python.pythonForBuild.interpreter} setup.py build
      ${pyself.python.pythonForBuild.interpreter} setup.py build_ext --cpp_implementation
    '';

    installFlags = "--install-option='--cpp_implementation'";
    postInstall = ''
      cp -v $(find build -name "_message*") $out/${pyself.python.sitePackages}/google/protobuf/pyext
    '';
  });
}
