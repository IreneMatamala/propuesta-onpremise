#!/bin/bash
# Script de backup para PostgreSQL con retención y cifrado

set -e

# Variables configurables
BACKUP_DIR="/backup/postgres"
RETENTION_DAYS=7
ENCRYPTION_KEY="${ENCRYPTION_KEY}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/backup-postgres.log"

# Funciones de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Verificar variables requeridas
if [ -z "$PGHOST" ] || [ -z "$PGDATABASE" ] || [ -z "$PGUSER" ]; then
    log "ERROR: Variables de PostgreSQL no configuradas"
    exit 1
fi

# Crear directorio de backup si no existe
mkdir -p $BACKUP_DIR

# Nombre del archivo de backup
BACKUP_FILE="${BACKUP_DIR}/${PGDATABASE}_${TIMESTAMP}.sql.gz"

log "Iniciando backup de ${PGDATABASE}..."

# Realizar backup
if pg_dump -h $PGHOST -U $PGUSER $PGDATABASE | gzip > $BACKUP_FILE; then
    BACKUP_SIZE=$(du -h $BACKUP_FILE | cut -f1)
    log "Backup completado: $BACKUP_FILE (Tamaño: $BACKUP_SIZE)"
    
    # Cifrar backup si hay clave de encriptación
    if [ -n "$ENCRYPTION_KEY" ]; then
        openssl enc -aes-256-cbc -salt -in $BACKUP_FILE -out "${BACKUP_FILE}.enc" -pass pass:$ENCRYPTION_KEY
        rm $BACKUP_FILE
        BACKUP_FILE="${BACKUP_FILE}.enc"
        log "Backup cifrado: $BACKUP_FILE"
    fi
    
    # Rotación de backups antiguos
    find $BACKUP_DIR -name "${PGDATABASE}_*.sql.gz*" -mtime +$RETENTION_DAYS -delete
    log "Rotación completada (retención: $RETENTION_DAYS días)"
    
    # Verificar integridad del backup
    if [ -n "$ENCRYPTION_KEY" ]; then
        openssl enc -d -aes-256-cbc -in $BACKUP_FILE -out /tmp/verify.sql.gz -pass pass:$ENCRYPTION_KEY 2>/dev/null
    else
        cp $BACKUP_FILE /tmp/verify.sql.gz
    fi
    
    if gzip -t /tmp/verify.sql.gz; then
        log "Verificación de integridad: OK"
        rm /tmp/verify.sql.gz
    else
        log "ERROR: Backup corrupto"
        exit 1
    fi
    
else
    log "ERROR: Falló el backup de ${PGDATABASE}"
    exit 1
fi

log "Proceso de backup finalizado exitosamente"
exit 0
