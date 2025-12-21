
#!/bin/bash
BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h postgres-primary -U postgres mydb | gzip > $BACKUP_DIR/mydb_$DATE.sql.gz
# Rotación: mantener últimos 7 días
find $BACKUP_DIR -type f -mtime +7 -delete
