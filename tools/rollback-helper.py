#!/usr/bin/env python3
"""
Script de ayuda para rollback automatizado.
Verifica health checks y ejecuta rollback si es necesario.
"""

import requests
import time
import sys
import os
import logging
from kubernetes import client, config
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RollbackHelper:
    def __init__(self, namespace="default", deployment="microservice-a"):
        self.namespace = namespace
        self.deployment = deployment
        
        # Cargar configuración de kubeconfig
        try:
            config.load_kube_config()
        except:
            config.load_incluster_config()
        
        self.api = client.AppsV1Api()
        self.core_api = client.CoreV1Api()
    
    def check_health(self, max_retries=10, retry_interval=30):
        """Verificar health checks del deployment"""
        logger.info(f"Verificando health del deployment {self.deployment}...")
        
        for attempt in range(max_retries):
            try:
                # Obtener pods del deployment
                pods = self.core_api.list_namespaced_pod(
                    namespace=self.namespace,
                    label_selector=f"app={self.deployment}"
                )
                
                if not pods.items:
                    logger.error("No se encontraron pods del deployment")
                    return False
                
                healthy_pods = 0
                for pod in pods.items:
                    # Verificar estado del pod
                    if pod.status.phase == "Running":
                        # Verificar readiness probe
                        for container in pod.status.container_statuses:
                            if container.ready:
                                healthy_pods += 1
                                # Verificar endpoint de health
                                pod_ip = pod.status.pod_ip
                                try:
                                    response = requests.get(
                                        f"http://{pod_ip}:8000/api/v1/health",
                                        timeout=5
                                    )
                                    if response.status_code == 200:
                                        logger.info(f"Pod {pod.metadata.name} health: OK")
                                    else:
                                        logger.warning(f"Pod {pod.metadata.name} health check failed")
                                        healthy_pods -= 1
                                except Exception as e:
                                    logger.warning(f"Error en health check del pod {pod.metadata.name}: {e}")
                                    healthy_pods -= 1
                
                total_pods = len(pods.items)
                healthy_percentage = (healthy_pods / total_pods) * 100
                
                logger.info(f"Pods saludables: {healthy_pods}/{total_pods} ({healthy_percentage:.1f}%)")
                
                if healthy_percentage >= 80:  # Umbral para considerar saludable
                    return True
                elif attempt < max_retries - 1:
                    logger.info(f"Esperando {retry_interval} segundos antes de reintentar...")
                    time.sleep(retry_interval)
            
            except Exception as e:
                logger.error(f"Error verificando health: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
        
        return False
    
    def execute_rollback(self, revision=None):
        """Ejecutar rollback del deployment"""
        try:
            # Obtener historial del deployment
            deployments = self.api.list_namespaced_deployment(
                namespace=self.namespace,
                field_selector=f"metadata.name={self.deployment}"
            )
            
            if not deployments.items:
                logger.error(f"Deployment {self.deployment} no encontrado")
                return False
            
            deployment = deployments.items[0]
            
            if revision:
                target_revision = revision
            else:
                # Buscar revisión anterior saludable
                target_revision = self.find_previous_revision()
            
            logger.info(f"Ejecutando rollback a revisión {target_revision}")
            
            # Rollback usando kubectl (más confiable)
            cmd = [
                "kubectl", "rollout", "undo",
                f"deployment/{self.deployment}",
                f"--namespace={self.namespace}",
                f"--to-revision={target_revision}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Rollback exitoso: {result.stdout}")
                
                # Notificar
                self.send_notification(
                    f"Rollback ejecutado para {self.deployment} en {self.namespace}"
                )
                return True
            else:
                logger.error(f"Error en rollback: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Error ejecutando rollback: {e}")
            return False
    
    def find_previous_revision(self):
        """Encontrar la revisión anterior estable"""
        try:
            # Listar ReplicaSets del deployment
            label_selector = f"app={self.deployment}"
            replicasets = self.api.list_namespaced_replica_set(
                namespace=self.namespace,
                label_selector=label_selector
            )
            
            # Ordenar por timestamp (más reciente primero)
            replicasets.items.sort(
                key=lambda rs: rs.metadata.creation_timestamp,
                reverse=True
            )
            
            # Saltar la revisión actual (primera) y tomar la anterior
            if len(replicasets.items) > 1:
                return replicasets.items[1].metadata.annotations.get(
                    'deployment.kubernetes.io/revision', '1'
                )
            else:
                return '1'
        
        except Exception as e:
            logger.error(f"Error encontrando revisión anterior: {e}")
            return '1'
    
    def send_notification(self, message):
        """Enviar notificación del rollback"""
        # Implementar según tu sistema de notificaciones
        # Ejemplo con Slack
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if webhook_url:
            import json
            payload = {
                "text": message,
                "username": "Rollback Bot",
                "icon_emoji": ":warning:"
            }
            try:
                requests.post(webhook_url, json=payload)
            except Exception as e:
                logger.error(f"Error enviando notificación: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Herramienta de rollback automatizado")
    parser.add_argument("--namespace", default="default", help="Namespace Kubernetes")
    parser.add_argument("--deployment", required=True, help="Nombre del deployment")
    parser.add_argument("--check-only", action="store_true", help="Solo verificar, no ejecutar rollback")
    parser.add_argument("--revision", help="Revisión específica a la que hacer rollback")
    
    args = parser.parse_args()
    
    helper = RollbackHelper(args.namespace, args.deployment)
    
    # Verificar health
    is_healthy = helper.check_health()
    
    if is_healthy:
        logger.info("Deployment saludable, no se requiere rollback")
        sys.exit(0)
    else:
        logger.warning("Deployment no saludable, preparando rollback...")
        
        if not args.check_only:
            success = helper.execute_rollback(args.revision)
            if success:
                logger.info("Rollback completado exitosamente")
                sys.exit(0)
            else:
                logger.error("Falló el rollback")
                sys.exit(1)
        else:
            logger.info("Modo check-only, no se ejecutó rollback")
            sys.exit(1)

if __name__ == "__main__":
    main()
