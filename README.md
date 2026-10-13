# Laboratorio 1: Inventario, Estado y Configuración Segura con Python + SSH (Netmiko)
## ITIEL-13 - REDES PROGRAMABLES (Grupo 01)

### Descripción
Este laboratorio consiste en crear un script que lea un inventario YAML de equipos GNS3, se conecte por SSH usando Netmiko, recolecte el estado estructurado de los equipos y aplique cambios de configuración idempotentes en el MikroTik.

### Estructura del proyecto
```
lab1-<carne>/
├── README.md                  # este archivo
├── requirements.txt           # dependencias
├── .gitignore                 # archivos excluidos de git
├── inventario.yaml            # inventario externo de equipos (SIN contraseñas)
├── lab1_inventario.py         # script principal
├── reporte_estado.json        # salida de una ejecución real
└── logs/                      # session_log de cada equipo
```

### Instalación
1. Clonar este repositorio
2. Crear y activar el entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate   # Windows
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

### Configuración
1. Editar `inventario.yaml` con los equipos del laboratorio:
   - Reemplazar 'estudiante' por su número de lista
   - Los MikroTik tienen rol `escritura`, Cisco tienen rol `lectura` (opcional)
2. Configurar variables de entorno para las contraseñas:
   ```bash
   export LAB_PASS_MIKROTIK-ESTUDIANTE=su_contraseña_aquí
   export LAB_PASS_CISCO-ESTUDIANTE=su_contraseña_aquí  # opcional
   ```
   Alternativamente, el script solicitará las contraseñas mediante `getpass()` si las variables no existen.

### Ejecución
```bash
python lab1_inventario.py
```

Para la opción de limpieza:
```bash
python lab1_inventario.py --limpiar
```

### Variables de entorno
- `LAB_PASS_<NOMBRE>`: Contraseña para el equipo (nombre en mayúsculas, guiones como _)
  Ejemplo: para `mikrotik-estudiante` usar `LAB_PASS_MIKROTIK-ESTUDIANTE`

### Declaración de uso de IA
Se utilizó el asistente de OpenCode para ayudar en la creación inicial de la estructura del proyecto y archivos de configuración. El desarrollo principal del script `lab1_inventario.py` será realizado manualmente siguiendo los requisitos del laboratorio.

### Notas importantes
- Nunca almacenar contraseñas en el código, inventario.yaml o repositorio
- El script maneja errores de conexión y continúa con otros equipos si uno falla
- Los logs de sesión se guardan en el directorio `logs/`
- El reporte se genera en `reporte_estado.json` y se muestra un resumen en consola