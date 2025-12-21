# Disaster Recovery Plan
## Objetivos
- RTO: 4 horas
- RPO: 15 minutos
## Procedimiento
1. Detectar incidente (monitoreo Prometheus/Grafana).
2. Declarar desastre (aprobación del líder de infraestructura).
3. Activar clúster secundario (script `ansible-playbook dr-activate.yml`).
4. Restaurar base de datos desde backup remoto.
5. Redirigir tráfico (cambio de DNS/balanceador).
6. Validar servicios (pruebas de humo).
...
