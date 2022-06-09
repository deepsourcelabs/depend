#!/usr/bin/env sh

SYSROOT="$(xcrun --sdk macosx --show-sdk-path)"
DIR="$(dirname -- $0)"
CURRENT_DIR="$PWD"

cd $DIR

amd64() {
  CGO_ENABLED=1 GOOS=darwin GOARCH=amd64 CC=clang CGO_CFLAGS="-arch x86_64 -isysroot \"$SYSROOT\"" go build -buildmode=c-shared -o ../darwin/libgomod_amd64.dylib read.go
  mv ../darwin/libgomod_amd64.h ../darwin/libgomod.h
}

arm64() {
  CGO_ENABLED=1 GOOS=darwin GOARCH=arm64 CC=clang CGO_CFLAGS="-arch arm64 -isysroot \"$SYSROOT\"" go build -buildmode=c-shared -o ../darwin/libgomod_arm64.dylib read.go
  rm ../darwin/libgomod_arm64.h
}

combine() {
  lipo ../darwin/libgomod_amd64.dylib ../darwin/libgomod_arm64.dylib -create -output ../darwin/libgomod.dylib
  rm ../darwin/libgomod_amd64.dylib ../darwin/libgomod_arm64.dylib
}

amd64
arm64
combine

cd $CURRENT_DIR
