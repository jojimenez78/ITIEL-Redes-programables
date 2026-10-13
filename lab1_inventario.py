#!/usr/bin/env python3
"""
Laboratorio 1: Inventario, Estado y Configuración Segura con Python + SSH (Netmiko)
"""

import argparse
import getpass
import json
import os
import sys
import time
import yaml
from datetime import datetime
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetmikoTimeoutException, NetmikoAuthenticationException

def cargar_inventario(ruta_inventario):
    """Carga el inventario desde archivo YAML"""
    with open(ruta_inventario, 'r') as file:
        return yaml.safe_load(file)

def obtener_contrasena(equipo):
    """Obtiene la contraseña de variables de entorno o solicita al usuario"""
    # Convertir nombre del equipo a formato de variable de entorno
    var_env = f"LAB_PASS_{equipo['name'].upper().replace('-', '_')}"
    password = os.environ.get(var_env)
    
    if not password:
        password = getpass.getpass(f"Contraseña para {equipo['name']}: ")
    
    return password

def conectar_equipo(equipo):
    """Establece conexión SSH con el equipo usando Netmiko"""
    dispositivo = {
        'device_type': equipo['device_type'],
        'host': equipo['host'],
        'username': equipo['usuario'],
        'password': obtener_contrasena(equipo),
        'timeout': 10,
        'session_log': f"logs/session_{equipo['name']}.log"
    }
    
    try:
        conexion = ConnectHandler(**dispositivo)
        return conexion
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        print(f"Error conectando a {equipo['name']}: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado conectando a {equipo['name']}: {e}")
        return None

def parsear_estado_mikrotik(salida_comandos):
    """Parsea la salida de comandos de MikroTik a diccionario estructurado"""
    # TODO: Implementar parsers específicos para MikroTik
    # Comandos necesarios según R4:
    # - /system identity print
    # - /system resource print
    # - /ip address print terse
    # - /ip route print terse where dst-address=0.0.0.0/0
    estado = {}
    return estado

def parsear_estado_cisco(salida_comandos):
    """Parsea la salida de comandos de Cisco IOS a diccionario estructurado"""
    # TODO: Implementar parsers específicos para Cisco IOS
    # Comandos necesarios según R4 (ejemplo):
    # - show running-config | include hostname
    # - show version | include uptime
    # - show ip interface brief
    # - show ip route 0.0.0.0 0.0.0.0
    estado = {}
    return estado

def obtener_estado_equipo(equipo):
    """Obtiene y parsea el estado estructurado de un equipo"""
    conexion = conectar_equipo(equipo)
    if not conexion:
        return {"error": "No se pudo establecer conexión"}
    
    try:
        # TODO: Ejecutar comandos específicos según device_type
        # TODO: Parsear salidas usando las funciones apropiadas
        estado = {}
        return estado
    finally:
        conexion.disconnect()

def aplicar_configuracion_mikrotik(equipo):
    """Aplica cambio de configuración idempotente en MikroTik"""
    # TODO: Implementar R6:
    # - Asegurar interfaz lo-ssh-<N> con IP 10.253.0.<N>/32 y comentario
    # - Consultar antes de crear
    # - Verificar después del cambio
    # - Opción --limpiar para eliminar objetos
    pass

def generar_reporte(equipos_estado):
    """Genera reporte_estado.json y muestra tabla resumen"""
    # TODO: Implementar R5:
    # - reporte_estado.json: lista de equipos con datos, fecha/hora y estado
    # - Resumen en consola como tabla: equipo, IP, estado, interfaces, gateway
    pass

def main():
    parser = argparse.ArgumentParser(description='Script de inventario y configuración para laboratorio GNS3')
    parser.add_argument('--limpiar', action='store_true', help='Eliminar solo los objetos creados por este script')
    args = parser.parse_args()
    
    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)
    
    # Cargar inventario
    try:
        inventario = cargar_inventario('inventario.yaml')
    except FileNotFoundError:
        print("Error: No se encontró el archivo inventario.yaml")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error al parsear inventario.yaml: {e}")
        sys.exit(1)
    
    # Procesar cada equipo
    equipos_estado = []
    for equipo in inventario:
        print(f"Procesando {equipo['name']} ({equipo['host']})...")
        
        if args.limpiar and equipo['rol'] == 'escritura':
            # TODO: Ejecutar limpieza para equipos con rol escritura
            pass
        elif not args.limpiar:
            # Obtener estado del equipo
            estado = obtener_estado_equipo(equipo)
            equipos_estado.append({
                'equipo': equipo['name'],
                'host': equipo['host'],
                'timestamp': datetime.now().isoformat(),
                'estado': estado
            })
            
            # Aplicar configuración en MikroTik (solo rol escritura)
            if equipo['rol'] == 'escritura':
                aplicar_configuracion_mikrotik(equipo)
    
    # Generar reporte
    generar_reporte(equipos_estado)

if __name__ == "__main__":
    main()