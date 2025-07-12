#!/bin/bash

# Database backup script for Visioneers Marketplace
# This script creates automated backups of the PostgreSQL database

set -e

# Configuration
BACKUP_DIR="/backups"
DB_NAME="visioneers_marketplace"
DB_USER="visioneers_user"
DB_HOST="postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Create backup
echo "Creating backup: ${BACKUP_FILE}"
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${DB_HOST}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    > "${BACKUP_FILE}"

# Compress the backup
gzip "${BACKUP_FILE}"
echo "Backup compressed: ${BACKUP_FILE}.gz"

# Keep only the last 7 days of backups
find "${BACKUP_DIR}" -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed successfully at $(date)" 