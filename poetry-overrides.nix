{ lib, stdenv, ... }:
_: super:
{
  mypy = super.mypy.overridePythonAttrs (attrs: {
    MYPY_USE_MYPYC = stdenv.buildPlatform.is64bit &&
      lib.versionOlder attrs.version "0.900";
  });
}
