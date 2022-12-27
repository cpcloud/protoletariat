self: super:
let
  inherit (self) pkgs;
  inherit (pkgs) lib stdenv;
  libPath = lib.makeLibraryPath [ "${stdenv.cc.cc.lib}/${pkgs.targetPlatform.config}" ];
in
{
  wheel = super.wheel.override { preferWheel = false; };
  grpcio = super.grpcio.override { preferWheel = pkgs.targetPlatform == pkgs.buildPlatform; };
  protobuf = super.protobuf.override { preferWheel = pkgs.targetPlatform == pkgs.buildPlatform; };
}
