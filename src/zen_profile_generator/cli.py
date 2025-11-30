import os
import sys
import json
import shutil
import configparser
import subprocess
import glob
from pathlib import Path

# Configuración de Colores para Terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class ZenProfileGenerator:
    def __init__(self):
        # Ruta base Flatpak definida en las especificaciones
        self.base_path = Path(os.path.expanduser("~/.var/app/app.zen_browser.zen/.zen"))
        self.profiles_ini_path = self.base_path / "profiles.ini"

        self._check_requirements()

        # Seleccionar perfil origen desde menú
        self.source_path = self._select_source_profile()

    def _check_requirements(self):
        """Verifica que existan las rutas y archivos base."""
        if not self.base_path.exists():
            print(f"{Colors.FAIL}Error: No se encontró la carpeta de Zen en: {self.base_path}{Colors.ENDC}")
            sys.exit(1)
        if not self.profiles_ini_path.exists():
            print(f"{Colors.FAIL}Error: No se encontró profiles.ini en: {self.profiles_ini_path}{Colors.ENDC}")
            sys.exit(1)

        print(f"{Colors.WARNING}⚠️  IMPORTANTE: Cierra Zen Browser completamente antes de continuar para evitar corrupción de archivos.{Colors.ENDC}")
        input(f"Presiona {Colors.BOLD}Enter{Colors.ENDC} cuando Zen esté cerrado...")

    def _get_all_profiles(self):
        """Lee profiles.ini y retorna una lista de todos los perfiles disponibles."""
        config = configparser.ConfigParser()
        config.read(self.profiles_ini_path)

        profiles = []
        for section in config.sections():
            if section.startswith("Profile"):
                name = config[section].get("Name", "Sin nombre")
                path_relative = config[section].get("Path", "")
                path_absolute = self.base_path / path_relative

                if path_absolute.exists():
                    profiles.append({
                        'name': name,
                        'path': path_absolute,
                        'description': f"Ruta: {path_relative}"
                    })

        return profiles

    def _select_source_profile(self):
        """Muestra un menú para seleccionar el perfil origen."""
        profiles = self._get_all_profiles()

        if not profiles:
            print(f"{Colors.FAIL}Error: No se encontraron perfiles disponibles.{Colors.ENDC}")
            sys.exit(1)

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Colors.HEADER}=== Selecciona el perfil origen (base para clonar) ==={Colors.ENDC}")
        print(f"{Colors.CYAN}Escribe el número del perfil que quieres usar como base.{Colors.ENDC}\n")

        for idx, profile in enumerate(profiles):
            print(f"[{idx + 1}] {Colors.BOLD}{profile['name']}{Colors.ENDC}")
            print(f"    {Colors.BLUE}{profile['description']}{Colors.ENDC}\n")

        while True:
            selection = input(f"{Colors.GREEN}Selección > {Colors.ENDC}").strip()

            try:
                idx = int(selection) - 1
                if 0 <= idx < len(profiles):
                    selected = profiles[idx]
                    print(f"\n{Colors.GREEN}✓ Perfil seleccionado: {selected['name']}{Colors.ENDC}\n")
                    return selected['path']
                else:
                    print(f"{Colors.WARNING}Número fuera de rango. Intenta de nuevo.{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.WARNING}Entrada inválida. Escribe un número.{Colors.ENDC}")

    def _get_new_profile_path(self, profile_name):
        """Lee profiles.ini para encontrar la ruta de la carpeta del nuevo perfil."""
        config = configparser.ConfigParser()
        config.read(self.profiles_ini_path)
        
        for section in config.sections():
            if section.startswith("Profile"):
                if config[section].get("Name") == profile_name:
                    path_relative = config[section].get("Path")
                    return self.base_path / path_relative
        return None

    def _select_from_menu(self, items, title, object_type="elemento"):
        """Genera un menú de selección múltiple estándar."""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Colors.HEADER}=== Selecciona {title} ==={Colors.ENDC}")
        print(f"{Colors.CYAN}Escribe los números separados por coma (ej: 1,3). Dejar vacío no selecciona nada.{Colors.ENDC}")
        print(f"{Colors.CYAN}Escribe 'A' para seleccionar TODOS.{Colors.ENDC}\n")

        for idx, item in enumerate(items):
            desc = item.get('description', '')
            desc_str = f"- {Colors.BLUE}{desc}{Colors.ENDC}" if desc else ""
            print(f"[{idx + 1}] {Colors.BOLD}{item['name']}{Colors.ENDC} {desc_str}")

        selection = input(f"\n{Colors.GREEN}Selección > {Colors.ENDC}").strip()

        if not selection:
            return []
        
        if selection.upper() == 'A':
            return items

        selected_items = []
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip().isdigit()]
            for i in indices:
                if 0 <= i < len(items):
                    selected_items.append(items[i])
        except ValueError:
            print(f"{Colors.WARNING}Entrada inválida. No se seleccionaron {object_type}s.{Colors.ENDC}")
        
        return selected_items

    # --- LÓGICA DE MODS ---
    def get_mods(self):
        json_path = self.source_path / "zen-themes.json"
        if not json_path.exists():
            return []
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        mods = []
        # El json puede ser un dict con IDs como keys o una lista
        for key, val in data.items():
            mods.append({
                'id': key,
                'name': val.get('name', 'Desconocido'),
                'description': val.get('description', '')
            })
        return mods

    def process_mods(self, dest_path, selected_mods):
        if not selected_mods:
            return

        print(f"{Colors.BLUE} Procesando Mods...{Colors.ENDC}")
        src_chrome = self.source_path / "chrome"
        dest_chrome = dest_path / "chrome"

        # 1. Copiar carpeta chrome completa
        if src_chrome.exists():
            if dest_chrome.exists():
                shutil.rmtree(dest_chrome)
            shutil.copytree(src_chrome, dest_chrome)

        # 2. Modificar JSON
        json_path = dest_chrome.parent / "zen-themes.json" # Suele estar en root del perfil o chrome, ajustamos a root segun diff
        # Nota: En tu diff `zen-themes.json` esta en la raiz del perfil, no dentro de chrome.
        # Pero `zen-themes.css` esta DENTRO de chrome.

        # Corregimos ruta json origen/destino basado en tu diff
        src_json = self.source_path / "zen-themes.json"
        dest_json = dest_path / "zen-themes.json"

        if not src_json.exists():
            print(f"{Colors.WARNING}   -> Advertencia: No se encontró zen-themes.json en el perfil origen.{Colors.ENDC}")
            return

        shutil.copy2(src_json, dest_json)

        with open(dest_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        selected_ids = [m['id'] for m in selected_mods]
        
        for mod_id in data:
            if mod_id in selected_ids:
                data[mod_id]['enabled'] = True
            else:
                data[mod_id]['enabled'] = False
        
        with open(dest_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        # 3. Borrar cache CSS para forzar regeneración
        css_cache = dest_chrome / "zen-themes.css"
        if css_cache.exists():
            os.remove(css_cache)
            print(f"   -> Cache CSS eliminado para forzar regeneración.")

    # --- LÓGICA DE EXTENSIONES ---
    def get_extensions(self):
        ext_path = self.source_path / "extensions"
        extensions = []
        if ext_path.exists():
            for xpi in ext_path.glob("*.xpi"):
                # Usamos el nombre del archivo como nombre visual
                extensions.append({
                    'name': xpi.name,
                    'path': xpi,
                    'description': '(Extension)'
                })
        return extensions

    def process_extensions(self, dest_path, selected_exts):
        if not selected_exts:
            return

        print(f"{Colors.BLUE} Instalando Extensiones...{Colors.ENDC}")
        dest_ext_dir = dest_path / "extensions"
        dest_ext_dir.mkdir(parents=True, exist_ok=True)

        for ext in selected_exts:
            shutil.copy2(ext['path'], dest_ext_dir / ext['path'].name)
            print(f"   -> Instalada: {ext['name']}")

    # --- LÓGICA DE CONTENEDORES ---
    def get_containers(self):
        cont_path = self.source_path / "containers.json"
        if not cont_path.exists():
            return []
        
        with open(cont_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        containers = []
        for identity in data.get('identities', []):
            if identity.get('public', False): # Solo listar los públicos/usables
                containers.append({
                    'name': identity.get('name', f"ID {identity.get('userContextId')}"),
                    'description': f"Color: {identity.get('color')} | Icon: {identity.get('icon')}",
                    'data': identity
                })
        return containers

    def process_containers(self, dest_path, selected_containers):
        if not selected_containers:
            return

        print(f"{Colors.BLUE} Configurando Contenedores...{Colors.ENDC}")
        src_json = self.source_path / "containers.json"
        dest_json = dest_path / "containers.json"

        if not src_json.exists():
            print(f"{Colors.WARNING}   -> Advertencia: No se encontró containers.json en el perfil origen.{Colors.ENDC}")
            return

        with open(src_json, 'r', encoding='utf-8') as f:
            base_data = json.load(f)

        # Filtramos identities manteniendo la estructura original
        selected_data = [c['data'] for c in selected_containers]
        
        # Siempre mantener userContextIdInternal (generalmente ids altos o de sistema) si es necesario
        # Pero segun tu diff, el perfil cero tiene pocos. Vamos a reemplazar la lista identities
        # con los seleccionados + los por defecto del sistema si se requiere.
        # Para ser limpios: Usamos la lista seleccionada.
        
        base_data['identities'] = selected_data
        
        # Ajustar lastUserContextId al máximo ID seleccionado para evitar colisiones futuras
        if selected_data:
            max_id = max(c['userContextId'] for c in selected_data)
            base_data['lastUserContextId'] = max_id

        with open(dest_json, 'w', encoding='utf-8') as f:
            json.dump(base_data, f)

    # --- LÓGICA DE CONFIGURACIÓN (PREFS.JS) ---
    def process_prefs(self, dest_path):
        print(f"{Colors.BLUE} Migrando Configuración (prefs.js)...{Colors.ENDC}")
        src_prefs = self.source_path / "prefs.js"
        dest_prefs = dest_path / "prefs.js"

        # Lista Negra de configuraciones que NO deben pasar
        blacklist = [
            "toolkit.telemetry",
            "datareporting",
            "services.sync",
            "browser.download.lastDir",
            "extensions.webextensions.uuids", # CRÍTICO: Dejar que se regeneren
            "security.webauthn",
            "places.database.lastMaintenance",
            "browser.sessionstore.resume_from_crash",
            "browser.startup.last_success"
        ]

        new_lines = []
        
        # Cabecera segura
        new_lines.append('// Generado por Zen Profile Assistant\n')
        
        if src_prefs.exists():
            with open(src_prefs, 'r', encoding='utf-8') as f:
                for line in f:
                    # Filtro
                    if any(bad_item in line for bad_item in blacklist):
                        continue
                    new_lines.append(line)
        
        # Escribir nuevo archivo
        with open(dest_prefs, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    # --- LÓGICA DE ATAJOS ---
    def process_shortcuts(self, dest_path):
        print(f"{Colors.BLUE} Copiando Atajos de Teclado...{Colors.ENDC}")
        src = self.source_path / "zen-keyboard-shortcuts.json"
        dest = dest_path / "zen-keyboard-shortcuts.json"
        if src.exists():
            shutil.copy2(src, dest)

    # --- FLUJO PRINCIPAL ---
    def run(self):
        # 1. Recolección de datos
        mods_list = self.get_mods()
        selected_mods = self._select_from_menu(mods_list, "Mods (Temas y UI)")

        ext_list = self.get_extensions()
        selected_exts = self._select_from_menu(ext_list, "Extensiones (.xpi)")

        cont_list = self.get_containers()
        selected_containers = self._select_from_menu(cont_list, "Contenedores Multi-Account")

        # 2. Nombre del perfil
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Colors.HEADER}=== Creación del Perfil ==={Colors.ENDC}")
        new_name = input("Nombre para el nuevo perfil (Dejar vacío para automático): ").strip()
        
        # 3. Creación vía Flatpak
        print(f"\n{Colors.CYAN}Ejecutando comando de creación de perfil...{Colors.ENDC}")
        cmd = ["flatpak", "run", "app.zen_browser.zen", "-CreateProfile", new_name]
        
        try:
            # Capturamos output para que no ensucie la pantalla, pero checkeamos errores
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"{Colors.FAIL}Error al crear perfil: {result.stderr}{Colors.ENDC}")
                return
        except Exception as e:
            print(f"{Colors.FAIL}Error ejecutando Flatpak: {e}{Colors.ENDC}")
            return

        # 4. Detectar la nueva ruta
        # Importante: Como el nombre puede ser auto-generado si estaba vacío, necesitamos 
        # una estrategia. Si el usuario dejó vacío, Zen crea algo como "Profile1". 
        # Asumiremos que si el usuario puso nombre, buscamos ese. Si no, es complejo saber cual es el nuevo.
        # Simplificación: Si dejó vacío, el script pedirá buscar el perfil más reciente o fallará controladamente.
        
        target_profile_name = new_name if new_name else None
        
        # Si el usuario no puso nombre, Zen usa "Default User", "Default User 1", etc.
        # Vamos a intentar buscar el perfil mas reciente modificado en la carpeta base.
        new_profile_path = None
        
        if target_profile_name:
            new_profile_path = self._get_new_profile_path(target_profile_name)
        else:
             # Buscar directorio más reciente en .zen
             print(f"{Colors.WARNING}Nombre vacío: Buscando el directorio modificado más recientemente...{Colors.ENDC}")
             # Releer ini no sirve si no sabemos el nombre. Buscamos por fecha de carpeta.
             dirs = [d for d in self.base_path.iterdir() if d.is_dir()]
             if dirs:
                 new_profile_path = max(dirs, key=os.path.getmtime)

        if not new_profile_path or not new_profile_path.exists():
            print(f"{Colors.FAIL}No se pudo localizar la carpeta del nuevo perfil.{Colors.ENDC}")
            return

        print(f"{Colors.GREEN}Perfil localizado en: {new_profile_path.name}{Colors.ENDC}\n")

        # 5. Aplicar configuraciones
        try:
            self.process_mods(new_profile_path, selected_mods)
            self.process_extensions(new_profile_path, selected_exts)
            self.process_containers(new_profile_path, selected_containers)
            self.process_prefs(new_profile_path)
            self.process_shortcuts(new_profile_path)
            
            print(f"\n{Colors.HEADER}✨ ¡Perfil '{new_name or new_profile_path.name}' creado exitosamente! ✨{Colors.ENDC}")
            print(f"Puedes iniciarlo desde el gestor de perfiles de Zen.")
            
        except Exception as e:
            print(f"\n{Colors.FAIL}Ocurrió un error durante la configuración: {e}{Colors.ENDC}")

def main():
    """Entry point para el CLI."""
    app = ZenProfileGenerator()
    app.run()

if __name__ == "__main__":
    main()
