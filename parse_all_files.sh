#!/bin/bash
while IFS= read -r line; do
    ./FACESParser.py "$line" out
done < "$1"
