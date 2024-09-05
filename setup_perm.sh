#!/bin/bash

# Set up variables
PROJECT_ROOT=$(pwd)
DIRS_TO_CHANGE=("blog" "works")
USER=$(whoami)
GROUP=$(id -gn)

# Function to set permissions
set_permissions() {
    local dir=$1
    echo "Setting permissions for $dir"
    chown -R $USER:$GROUP $dir
    chmod -R 755 $dir
    find $dir -type d -exec chmod 755 {} \;
    find $dir -type f -exec chmod 644 {} \;
}

# Set permissions for project root
set_permissions $PROJECT_ROOT

# Set permissions for specific directories
for dir in "${DIRS_TO_CHANGE[@]}"; do
    set_permissions "$PROJECT_ROOT/$dir"
done

# Set permissions for index.html
chown $USER:$GROUP "$PROJECT_ROOT/index.html"
chmod 644 "$PROJECT_ROOT/index.html"

echo "Permissions have been set up."