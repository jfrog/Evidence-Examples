#!/usr/bin/env bash

# Script inspired by https://www.digitalocean.com/community/tutorials/how-to-build-go-executables-for-multiple-platforms-on-ubuntu-16-04

errorExit () {
    echo; echo "ERROR: $1"; echo
    exit 1
}

BIN=sonar-scan-extractor
rm -rf bin
mkdir -p bin

echo "Building $BIN"
#platforms=("darwin/amd64" "linux/arm64" "linux/amd64" "windows/amd64" "windows/386")
platforms=("linux/arm64" "linux/amd64" "darwin/arm64" )

for p in "${platforms[@]}"; do
    platform_array=(${p//\// })
    GOOS=${platform_array[0]}
    GOARCH=${platform_array[1]}

    echo -e "\nBuilding"
    echo "OS:   $GOOS"
    echo "ARCH: $GOARCH"
    final_name=$BIN'-'$GOOS'-'$GOARCH
    if [ "$GOOS" = "windows" ]; then
        final_name+='.exe'
    fi

    env GOOS="$GOOS" GOARCH="$GOARCH" go build -o bin/$final_name . || errorExit "Building $final_name failed"
done

echo -e "\nDone!\nThe following binaries were created in the bin/ directory:"
ls -1 bin/
echo