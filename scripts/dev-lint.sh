#!/bin/bash

echo "Running Pylint with clickable file paths..."
PROJECT_ROOT=$(pwd)

# Function to find all Odoo modules
find_odoo_modules() {
    find . -maxdepth 2 -name "__manifest__.py" -exec dirname {} \; | sed 's|^\./||' | sort
}

# Find all modules
MODULES=$(find_odoo_modules)
if [ -z "$MODULES" ]; then
    echo "No Odoo modules found (no __manifest__.py files)"
    exit 0
fi

echo "Found modules: $MODULES"

# Create sed pattern for all modules
SED_PATTERN=""
for module in $MODULES; do
    if [ -z "$SED_PATTERN" ]; then
        SED_PATTERN="s|^$module|$PROJECT_ROOT/$module|g"
    else
        SED_PATTERN="$SED_PATTERN; s|^$module|$PROJECT_ROOT/$module|g"
    fi
done

# Run pylint on all modules with absolute paths
# Add --msg-template to include more info (if available)
pylint --load-plugins=pylint_odoo --rcfile=.pylintrc --msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}' $MODULES | sed "$SED_PATTERN" | python3 ./scripts/add-info-urls.py
