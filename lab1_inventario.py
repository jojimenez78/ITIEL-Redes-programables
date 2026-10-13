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

# Diccionario de comandos por device_type (R4)
COMANDOS = {
    "mikrotik_routeros": {
        "nombre": "/system identity print",
        "tiempo_encendido": "/system resource print",
        "interfaces_ip": "/ip address print terse",
        "ruta_defecto": "/ip route print terse where dst-address=0.0.0.0/0"
    },
    "cisco_ios": {
        "nombre": "show running-config | include hostname",
        "tiempo_encendido": "show version | include uptime",
        "interfaces_ip": "show ip interface brief",
        "ruta_defecto": "show ip route 0.0.0.0 0.0.0.0"
    }
}

def cargar_inventario(ruta_inventario):
    """Carga el inventario desde archivo YAML"""
    with open(ruta_inventario, 'r') as file:
        return yaml.safe_load(file)

def obtener_contrasena(equipo):
    """Obtiene la contraseña de variables de entorno o solicita al usuario"""
    # Convertir nombre del equipo a formato de variable de entorno
    # Ejemplo: mt-lab → LAB_PASS_MT_LAB
    var_env = f"LAB_PASS_{equipo['nombre'].upper().replace('-', '_')}"
    password = os.environ.get(var_env)
    
    if not password:
        password = getpass.getpass(f"Contraseña para {equipo['nombre']}: ")
    
    return password

def conectar_equipo(equipo):
    """Establece conexión SSH con el equipo usando Netmiko con manejo de errores"""
    # Obtener contraseña ANTES de abrir la conexión
    password = obtener_contrasena(equipo)
    
    dispositivo = {
        'device_type': equipo['device_type'],
        'host': equipo['host'],
        'username': equipo['usuario'],
        'password': password,
        'timeout': 10,
        'session_log': f"logs/session_{equipo['nombre']}.log"
    }
    
    try:
        with ConnectHandler(**dispositivo) as conexion:
            # Devolver un diccionario indicando éxito
            return {"estado": "ok", "conexion": conexion}
    except NetmikoTimeoutException as e:
        error_msg = f"Timeout conectando a {equipo['nombre']} ({equipo['host']}): {str(e)}"
        print(error_msg)
        return {"estado": "error", "mensaje": error_msg}
    except NetmikoAuthenticationException as e:
        error_msg = f"Error de autenticación en {equipo['nombre']} ({equipo['host']}): {str(e)}"
        print(error_msg)
        return {"estado": "error", "mensaje": error_msg}
    except Exception as e:
        error_msg = f"Error inesperado conectando a {equipo['nombre']} ({equipo['host']}): {str(e)}"
        print(error_msg)
        return {"estado": "error", "mensaje": error_msg}

def obtener_estado_equipo(equipo):
    """Obtiene y parsea el estado estructurado de un equipo"""
    resultado_conexion = conectar_equipo(equipo)
    
    # Si hubo un error en la conexión, devolverlo directamente
    if resultado_conexion.get("estado") == "error":
        return resultado_conexion
    
    # Si la conexión fue exitosa, obtener los comandos y parsearlos
    conexion = resultado_conexion["conexion"]
    comandos_equipo = COMANDOS.get(equipo['device_type'], {})
    estado_parsed = {}
    
    try:
        for clave, comando in comandos_equipo.items():
            salida = conexion.send_command(comando)
            estado_parsed[clave] = salida.strip()
        return {"estado": "ok", "datos": estado_parsed}
    except Exception as e:
        error_msg = f"Error obteniendo estado de {equipo['nombre']}: {str(e)}"
        print(error_msg)
        return {"estado": "error", "mensaje": error_msg}
    finally:
        # La conexión se cierra automáticamente al salir del bloque 'with'
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
        print(f"Procesando {equipo['nombre']} ({equipo['host']})...")
        
        if args.limpiar and equipo['rol'] == 'escritura':
            # TODO: Implementar limpieza para equipos con rol escritura (R6)
            pass
        elif not args.limpiar:
            # Obtener estado del equipo
            estado = obtener_estado_equipo(equipo)
            equipos_estado.append({
                'equipo': equipo['nombre'],
                'host': equipo['host'],
                'timestamp': datetime.now().isoformat(),
                'estado': estado
            })
    
    # Generar reporte (R5 - se implementará más adelante)
    # Por ahora, solo mostramos lo que tenemos
    print("\n=== RESUMEN DE ESTADOS ===")
    for equipo_info in equipos_estado:
        print(f"Equipo: {equipo_info['equipo']}")
        print(f"IP: {equipo_info['host']}")
        print(f"Timestamp: {equipo_info['timestamp']}")
        estado_info = equipo_info['estado']
        if estado_info.get('estado') == 'ok':
            print(f"Estado: OK")
            if 'datos' in estado_info:
                for clave, valor in estado_info['datos'].items():
                    print(f"  {clave}: {valor[:100]}{'...' if len(valor) > 100 else ''}")
        else:
            print(f"Estado: ERROR - {estado_info.get('mensaje', 'Error desconocido')}")
        print("-" * 50)

if __name__ == "__main__":
    main()