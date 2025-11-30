# Zen Profile Generator

Herramienta de línea de comandos para crear y configurar perfiles de [Zen Browser](https://zen-browser.app/) clonando configuraciones de perfiles existentes.

## Características

- **Selección interactiva de perfil origen**: Elige qué perfil usar como base
- **Gestión de Mods/Temas**: Selecciona qué mods y temas UI copiar al nuevo perfil
- **Migración de extensiones**: Copia extensiones (.xpi) desde el perfil origen
- **Contenedores Multi-Account**: Transfiere contenedores personalizados
- **Configuración inteligente**: Migra preferencias (prefs.js) filtrando configuraciones sensibles
- **Atajos de teclado**: Copia shortcuts personalizados automáticamente
- **Compatible con Flatpak**: Diseñado específicamente para Zen Browser instalado vía Flatpak

## Requisitos

- **Python 3.13+**
- **Zen Browser** instalado como Flatpak (`app.zen_browser.zen`)
- Sistema operativo Linux

## Instalación

### Opción 1: Instalación con uv (recomendado)

```bash
git clone https://github.com/Sr-Alvarado/zen-profile-generator.git
cd zen-profile-generator
uv sync
```

### Opción 2: Instalación directa

```bash
git clone https://github.com/Sr-Alvarado/zen-profile-generator.git
cd zen-profile-generator
pip install -e .
```

## Uso

```bash
pgzen
```

El script te guiará a través de un proceso interactivo:

1. **Cierra Zen Browser completamente** (requisito para evitar corrupción de archivos)
2. Selecciona el **perfil origen** (perfil base desde el que clonar)
3. Elige qué **mods/temas** quieres incluir
4. Selecciona las **extensiones** a copiar
5. Elige los **contenedores** multi-account
6. Ingresa un **nombre** para el nuevo perfil (o deja vacío para nombre automático)
7. El script crea el perfil y aplica todas las configuraciones

### Ejemplo de flujo

```
=== Selecciona el perfil origen (base para clonar) ===
[1] Perfil Principal
    Ruta: abc123.default

Selección > 1

=== Selecciona Mods (Temas y UI) ===
Escribe los números separados por coma (ej: 1,3). Dejar vacío no selecciona nada.
Escribe 'A' para seleccionar TODOS.

[1] Dark Theme - Tema oscuro personalizado
[2] Compact UI - Interfaz compacta

Selección > A

...

( ¡Perfil 'Mi Nuevo Perfil' creado exitosamente! (
```

## Cómo funciona

El generador realiza las siguientes operaciones:

1. **Lee `profiles.ini`** para listar perfiles disponibles en `~/.var/app/app.zen_browser.zen/.zen/`
2. **Extrae configuraciones** del perfil origen:
   - `zen-themes.json` y carpeta `chrome/` para mods
   - Archivos `.xpi` de `extensions/`
   - `containers.json` para contenedores multi-account
   - `prefs.js` con filtrado de preferencias sensibles
   - `zen-keyboard-shortcuts.json`
3. **Crea el nuevo perfil** usando `flatpak run app.zen_browser.zen -CreateProfile`
4. **Aplica configuraciones** seleccionadas al nuevo perfil
5. **Limpia archivos cache** (ej: `zen-themes.css`) para forzar regeneración

### Filtrado de preferencias

El script excluye automáticamente preferencias que no deben migrarse:
- Telemetría y reportes de datos
- Configuración de sincronización
- Rutas de descarga
- UUIDs de extensiones (se regeneran)
- Información de sesión y crash reports

## Contribuir

Las contribuciones son bienvenidas. Para cambios importantes:

1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Advertencias

- **Cierra Zen Browser completamente** antes de ejecutar el script
- La herramienta está diseñada para la versión **Flatpak** de Zen Browser
- Haz **backup de tus perfiles** antes de usar esta herramienta en producción
- Algunos mods pueden requerir configuración manual adicional después de la creación del perfil
