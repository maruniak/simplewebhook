#!/bin/bash

print_file_contents() {
  IFS=',' read -r -a file_names <<< "$1"
  
  for file_name in "${file_names[@]}"
  do
    file_name=$(echo "$file_name" | xargs)  # Trim whitespace
    if [[ -f "$file_name" ]]; then
      echo "file '$file_name' :"
      echo '"""'
      cat "$file_name"
      echo '"""'
      echo
    else
      echo "Error: File '$file_name' not found."
    fi
  done
}

# Ensure the argument passed from the command line is used, not a hardcoded string
file_names_str="$1"
print_file_contents "$file_names_str"
