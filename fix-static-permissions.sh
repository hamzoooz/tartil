#!/bin/bash
# Fix static files permissions for Nginx

echo "Fixing static files permissions..."

# Make directories readable and executable by all
cd /home/hamzoooz123/qurancourses/tartil

# Fix permissions on staticfiles directory and subdirectories
chmod -R 755 staticfiles/

# Make sure the directories are executable (so nginx can traverse them)
find staticfiles -type d -exec chmod 755 {} \;

# Make sure files are readable
find staticfiles -type f -exec chmod 644 {} \;

# Also fix the parent directories so nginx can traverse
chmod 755 /home/hamzoooz123
chmod 755 /home/hamzoooz123/qurancourses
chmod 755 /home/hamzoooz123/qurancourses/tartil
chmod 755 /home/hamzoooz123/qurancourses/tartil/staticfiles

echo "Permissions fixed!"
echo ""
echo "Current permissions:"
ls -la /home/hamzoooz123/qurancourses/tartil/staticfiles/
