#!/bin/bash

# Get the current directory
PROJECT_ROOT=$(pwd)

# Function to find all Odoo modules in the current directory
find_odoo_modules() {
    find . -maxdepth 2 -name "__manifest__.py" -exec dirname {} \; | sed 's|^\./||' | sort
}

# If arguments are passed (pre-commit passes specific files), use them
# Otherwise, find and check all Odoo modules
if [ $# -eq 0 ]; then
    MODULES=$(find_odoo_modules)
    if [ -z "$MODULES" ]; then
        echo "No Odoo modules found (no __manifest__.py files)" >&2
        exit 0
    fi
    TARGET="$MODULES"
else
    TARGET="$@"
fi

# Debug: Show what we're checking
echo "Checking: $TARGET" >&2

# Run pylint and convert relative paths to absolute paths for all modules
# Create a sed pattern for all found modules
SED_PATTERN=""
for module in $(find_odoo_modules); do
    if [ -z "$SED_PATTERN" ]; then
        SED_PATTERN="s|^$module|$PROJECT_ROOT/$module|g"
    else
        SED_PATTERN="$SED_PATTERN; s|^$module|$PROJECT_ROOT/$module|g"
    fi
done

# Run pylint and apply path conversion
# Add --msg-template to include more info (if available)
pylint --load-plugins=pylint_odoo --rcfile=.pylintrc --msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}' $TARGET 2>&1 | sed "$SED_PATTERN" | python3 ./scripts/add-info-urls.py

# Capture pylint exit code
EXIT_CODE=${PIPESTATUS[0]}

# Exit with pylint's original exit code
exit $EXIT_CODE
