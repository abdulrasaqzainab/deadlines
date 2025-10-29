#!/bin/bash

# Find conferences without deadline fields
grep -n "^- title:" _data/conferences.yml | while read line; do
    line_num=$(echo "$line" | cut -d: -f1)
    title=$(echo "$line" | cut -d: -f2-)
    
    # Check if there's a deadline field in the next 20 lines
    has_deadline=$(sed -n "${line_num},$((line_num+20))p" _data/conferences.yml | grep -q "deadline:" && echo "yes" || echo "no")
    
    if [ "$has_deadline" = "no" ]; then
        echo "Missing deadline: $title"
    fi
done