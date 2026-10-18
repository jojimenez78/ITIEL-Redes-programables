#!/usr/bin/env python3
"""Laboratorio 1: inventario, estado y configuración segura (Netmiko)."""
import argparse
import getpass
import json
import os
import re
import sys
from datetime import datetime

import yaml
from netmiko import (ConnectHandler, NetmikoTimeoutException,
                     NetmikoAuthenticationException)

NOMBRE_ESTUDIANTE = "Jose Alonso Jimenez Garcia"   # <- cámbialo por tu nombre completo

# R4: comandos por device_type (agregar un fabricante = agregar una entrada)
COMANDOS = {
    "mikrotik_routeros": {
        "nombre": "/system identity print",
        "tiempo_encendido": "/system resource print",
        "interfaces_ip": "/ip address print terse",
        "ruta_defecto": "/ip route print terse where dst-address=0.0.0.0/0",
    },
    "cisco_ios": {
        "nombre": "show running-config | include hostname",
        "tiempo_encendido": "show version | include uptime",
        "interfaces_ip": "show ip interface brief",
        "ruta_defecto": "show ip route 0.0.0.0",
    },
}


# ---------- R1 y R2: inventario y credenciales ----------
def cargar_inventario(ruta):
    with open(ruta, "r") as f:
        return yaml.safe_load(f)


def obtener_contrasena(equipo):
    """mt-lab -> LAB_PASS_MT_LAB; si no existe, se pide con getpass."""
    var = "LAB_PASS_" + equipo["nombre"].upper().replace("-", "_")
    return os.environ.get(var) or getpass.getpass(
        f"Contraseña para {equipo['nombre']}: ")


# ---------- R4: parsers (texto -> diccionarios) ----------
def parsear_clave_valor(texto):
    """'name: MikroTik' -> {'name': 'MikroTik'}"""
    datos = {}
    for linea in texto.splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            datos[clave.strip()] = valor.strip()
    return datos


def parsear_terse(texto):
    """Cada línea 'clave=valor ...' -> un diccionario. Devuelve una lista."""
    registros = []
    for linea in texto.splitlines():
        reg = {}
        for token in linea.split():
            if "=" in token:
                k, v = token.split("=", 1)
                reg[k] = v
        if reg:
            registros.append(reg)
    return registros


def parsear_mikrotik(crudo):
    interfaces = [{"interfaz": r.get("interface"), "ip": r["address"]}
                  for r in parsear_terse(crudo["interfaces_ip"])
                  if "address" in r]
    rutas = parsear_terse(crudo["ruta_defecto"])
    return {
        "nombre": parsear_clave_valor(crudo["nombre"]).get("name"),
        "uptime": parsear_clave_valor(crudo["tiempo_encendido"]).get("uptime"),
        "interfaces": interfaces,
        "gateway_defecto": rutas[0].get("gateway") if rutas else None,
    }


def parsear_cisco(crudo):
    m = re.search(r"hostname\s+(\S+)", crudo["nombre"])
    u = re.search(r"uptime is (.+)", crudo["tiempo_encendido"])
    interfaces = []
    for linea in crudo["interfaces_ip"].splitlines()[1:]:
        p = linea.split()
        if len(p) >= 2 and re.match(r"\d+\.\d+\.\d+\.\d+$", p[1]):
            interfaces.append({"interfaz": p[0], "ip": p[1]})
    g = (re.search(r"via (\d+\.\d+\.\d+\.\d+)", crudo["ruta_defecto"]) or
         re.search(r"\*\s*(\d+\.\d+\.\d+\.\d+)", crudo["ruta_defecto"]))
    return {
        "nombre": m.group(1) if m else None,
        "uptime": u.group(1).strip() if u else None,
        "interfaces": interfaces,
        "gateway_defecto": g.group(1) if g else None,
    }


PARSERS = {"mikrotik_routeros": parsear_mikrotik, "cisco_ios": parsear_cisco}


def recolectar_estado(conexion, device_type):
    crudo = {k: conexion.send_command(c).strip()
             for k, c in COMANDOS[device_type].items()}
    return PARSERS[device_type](crudo)


# ---------- R6: configuración idempotente (solo objetos propios) ----------
def asegurar_lo_ssh(conexion, n):
    """Crea lo-ssh-<N> (bridge sin puertos) con 10.253.0.<N>/32 solo si falta."""
    nom_if = f"lo-ssh-{n}"
    ip = f"10.253.0.{n}/32"
    comentario = f"Lab1 {NOMBRE_ESTUDIANTE}"
    cambios = []

    # 1) consultar antes de crear
    existe_if = nom_if in conexion.send_command(
        f"/interface bridge print terse where name={nom_if}")
    if not existe_if:
        salida = conexion.send_command(
            f'/interface bridge add name={nom_if} comment="{comentario}"')
        if "failure" in salida.lower():
            raise RuntimeError(f"No se pudo crear {nom_if}: {salida}")
        cambios.append(f"creada interfaz {nom_if}")

    existe_ip = ip in conexion.send_command(
        f"/ip address print terse where interface={nom_if}")
    if not existe_ip:
        salida = conexion.send_command(
            f'/ip address add address={ip} interface={nom_if} '
            f'comment="{comentario}"')
        if "failure" in salida.lower():
            raise RuntimeError(f"No se pudo asignar {ip}: {salida}")
        cambios.append(f"asignada IP {ip}")

    # 2) verificar con un comando de lectura
    verificado = (
        nom_if in conexion.send_command(
            f"/interface bridge print terse where name={nom_if}")
        and ip in conexion.send_command(
            f"/ip address print terse where interface={nom_if}"))
    return {"interfaz": nom_if, "ip": ip, "cambios": cambios or ["sin cambios"],
            "verificado": verificado}


def limpiar_lo_ssh(conexion, n):
    """Elimina SOLO lo-ssh-<N> y su IP."""
    nom_if = f"lo-ssh-{n}"
    conexion.send_command(f"/ip address remove [find interface={nom_if}]")
    conexion.send_command(f"/interface bridge remove [find name={nom_if}]")
    quedan = nom_if in conexion.send_command(
        f"/interface bridge print terse where name={nom_if}")
    return {"interfaz": nom_if,
            "cambios": ["eliminada"] if not quedan else ["no se pudo eliminar"]}


# ---------- R3: conexión robusta ----------
def procesar_equipo(equipo, n, limpiar):
    dt = equipo["device_type"]
    if dt not in COMANDOS:
        return {"estado": f"error: device_type sin comandos ({dt})"}
    dispositivo = {
        "device_type": dt,
        "host": equipo["host"],
        "username": equipo["usuario"],
        "password": obtener_contrasena(equipo),
        "conn_timeout": 10,
        "session_log": f"logs/session_{equipo['nombre']}.log",
    }
    escribe = equipo.get("rol") == "escritura" and dt == "mikrotik_routeros"
    try:
        with ConnectHandler(**dispositivo) as conexion:
            if limpiar:
                if not escribe:
                    return {"estado": "omitido (solo lectura)"}
                return {"estado": "ok", "configuracion": limpiar_lo_ssh(conexion, n)}
            resultado = {"estado": "ok"}
            if escribe:
                resultado["configuracion"] = asegurar_lo_ssh(conexion, n)
            resultado["datos"] = recolectar_estado(conexion, dt)
            return resultado
    except NetmikoTimeoutException as e:
        msg = f"error: timeout ({str(e).splitlines()[0]})"
    except NetmikoAuthenticationException:
        msg = "error: autenticación fallida"
    except Exception as e:
        msg = f"error: {e}"
    print(f"  [{equipo['nombre']}] {msg}")
    return {"estado": msg}


# ---------- R5: reporte ----------
def generar_reporte(resultados):
    with open("reporte_estado.json", "w") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\n{'EQUIPO':<12}{'IP':<15}{'ESTADO':<10}{'IFACES':<8}GATEWAY")
    print("-" * 60)
    for r in resultados:
        datos = r.get("datos", {})
        estado = "ok" if r["estado"] == "ok" else "error"
        print(f"{r['equipo']:<12}{r['host']:<15}{estado:<10}"
              f"{len(datos.get('interfaces', [])):<8}"
              f"{datos.get('gateway_defecto') or '-'}")
    print("\nReporte guardado en reporte_estado.json")


def main():
    ap = argparse.ArgumentParser(description="Lab 1: inventario y estado")
    ap.add_argument("--n", type=int, help="su número de lista (para R6)")
    ap.add_argument("--limpiar", action="store_true",
                    help="elimina solo los objetos lo-ssh-<N>")
    args = ap.parse_args()
    os.makedirs("logs", exist_ok=True)
    try:
        inventario = cargar_inventario("inventario.yaml")
    except (FileNotFoundError, yaml.YAMLError) as e:
        sys.exit(f"Error con inventario.yaml: {e}")
    if args.n is None and any(e.get("rol") == "escritura" for e in inventario):
        sys.exit("Falta su número de lista: use --n <N>")

    resultados = []
    for equipo in inventario:
        print(f"Procesando {equipo['nombre']} ({equipo['host']})...")
        res = procesar_equipo(equipo, args.n, args.limpiar)
        if "configuracion" in res:
            print(f"  configuración: {res['configuracion']['cambios']}")
        resultados.append({"equipo": equipo["nombre"], "host": equipo["host"],
                           "fecha": datetime.now().isoformat(), **res})
    if not args.limpiar:
        generar_reporte(resultados)


if __name__ == "__main__":
    main()