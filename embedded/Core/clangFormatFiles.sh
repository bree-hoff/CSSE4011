#!/bin/bash

# Shell script to run the clang format tool on all required files

directories=(
    "apps/Thingy52/src"
)

for directory in "${directories[@]}"
do
    files=$(find "$directory" -type f \( -name '*.c' -o -name '*.h' \))

    for file in $files
    do
        echo "Running clang format tool on $file ..."
        clang-format -i "$file"
    done
done

echo "Done"
