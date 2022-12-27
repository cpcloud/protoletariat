self: super: {
  wheel = super.wheel.override { preferWheel = false; };
  protobuf = super.protobuf.override { preferWheel = false; };
  grpcio = super.grpcio.override { preferWheel = false; };
}
