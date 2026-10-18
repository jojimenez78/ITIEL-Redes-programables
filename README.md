# Laboratorio 1: Inventario, Estado y Configuración Segura (Python + SSH con Netmiko)
ITIEL-13 - Redes Programables (Grupo 01) - TU NOMBRE COMPLETO

## Descripción
Script que lee un inventario YAML, se conecta por SSH (Netmiko) a un MikroTik RouterOS v7 y a un Cisco IOS 3725, recolecta su estado como datos estructurados (JSON) y asegura en el MikroTik, sin duplicar, la interfaz `lo-ssh-<N>` con la IP `10.253.0.<N>/32`.

## Entorno de pruebas
Trabajé con un GNS3 **local** (Fedora Linux) en lugar del servidor del profesor por Tailscale. Usé las mismas IPs, usuario y nombres del enunciado: MikroTik `10.60.30.202` y Cisco `10.60.30.203`, usuario `lab-ssh`. Mi Fedora llega a los routers por una interfaz tap (`10.60.30.1/24`) conectada a un switch en GNS3.

## Estructura
- `inventario.yaml`: equipos (sin contraseñas)
- `lab1_inventario.py`: script principal
- `reporte_estado.json`: salida de una ejecución real
- `logs/`: session_log de cada equipo
- `requirements.txt`: dependencias

## Instalación
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Nota: `requirements.txt` fija `paramiko==3.4.1`. El IOS 3725 solo ofrece el algoritmo `diffie-hellman-group1-sha1`, que las versiones recientes de Paramiko rechazan. pip puede avisar de un conflicto con Netmiko, pero el script funciona.

## Credenciales
Se leen de variables de entorno `LAB_PASS_<NOMBRE>` (nombre en mayúsculas, guiones como guion bajo). Si no existen, se piden con `getpass`.
```bash
export LAB_PASS_MT_LAB='su_clave'
export LAB_PASS_CISCO_LAB='su_clave'
```

## Ejecución
```bash
python lab1_inventario.py --n 7             # estado + configuración (idempotente)
python lab1_inventario.py --n 7 --limpiar   # elimina solo lo-ssh-7
```
`--n` es el número de lista. La segunda ejecución seguida muestra `sin cambios`.

## Extra
Multivendor: el Cisco IOS está en el inventario y sus comandos y parser están en los diccionarios `COMANDOS` y `PARSERS`. No hice el extra REST.

## Declaración de uso de IA
- **OpenCode con Nemotron 3 Super (NVIDIA):** generó el esqueleto inicial del script, que luego corregí.
- **Claude (Anthropic):** me guió en la configuración de GNS3, la red y SSH, depuró errores y escribió y revisó gran parte del código (parsers, R6 y manejo de errores). Revisé y probé el código en mis equipos y puedo explicarlo.