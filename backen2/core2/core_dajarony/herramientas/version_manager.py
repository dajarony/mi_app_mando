"""
SUME DOCBLOCK

Nombre: Gestor de Versiones
Tipo: Herramienta

Entradas:
- Archivos de código fuente
- Archivos de configuración
- Registros de cambios (changelog)
- Número de versión actual
- Tipo de incremento (major, minor, patch)

Acciones:
- Incrementar versiones según SemVer
- Actualizar versiones en archivos
- Generar registros de cambios
- Detectar cambios entre versiones
- Actualizar referencias de versión
- Crear etiquetas de versión
- Validar formato de versiones
- Gestionar listado de cambios por componente

Salidas:
- Archivos actualizados con nuevas versiones
- Registro de cambios generado o actualizado
- Informe de cambios de versión
- Confirmación de operaciones realizadas
"""
import re
import os
import sys
import argparse
import logging
import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import yaml
import json


# Configurar logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("version_manager")


def find_version_in_file(file_path: Path) -> Optional[str]:
    """
    Busca la versión en un archivo.
    
    Soporta formatos comunes como:
    - __version__ = "x.y.z"
    - version = "x.y.z"
    - "version": "x.y.z"
    - <version>x.y.z</version>
    
    Args:
        file_path: Ruta al archivo
        
    Returns:
        Versión encontrada o None
    """
    if not file_path.exists():
        logger.warning(f"Archivo no encontrado: {file_path}")
        return None
    
    # Patrones de búsqueda para diferentes formatos
    patterns = [
        r'__version__\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']',
        r'version\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']',
        r'["\']version["\']\s*:\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']',
        r'<version>([0-9]+\.[0-9]+\.[0-9]+)</version>'
    ]
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Probar cada patrón
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        logger.debug(f"No se encontró versión en {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error al leer {file_path}: {str(e)}")
        return None


def update_version_in_file(file_path: Path, new_version: str) -> bool:
    """
    Actualiza la versión en un archivo.
    
    Args:
        file_path: Ruta al archivo
        new_version: Nueva versión
        
    Returns:
        True si se actualizó correctamente
    """
    if not file_path.exists():
        logger.warning(f"Archivo no encontrado: {file_path}")
        return False
    
    # Patrones de reemplazo para diferentes formatos
    patterns = [
        (r'__version__\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', 
         f'__version__ = "{new_version}"'),
        (r'version\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', 
         f'version = "{new_version}"'),
        (r'["\']version["\']\s*:\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', 
         f'"version": "{new_version}"'),
        (r'<version>([0-9]+\.[0-9]+\.[0-9]+)</version>', 
         f'<version>{new_version}</version>')
    ]
    
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Aplicar cada patrón de reemplazo
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # Verificar si hubo cambios
        if content == original_content:
            logger.warning(f"No se encontró versión para actualizar en {file_path}")
            return False
        
        # Guardar cambios
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"Versión actualizada en {file_path}: {new_version}")
        return True
    except Exception as e:
        logger.error(f"Error al actualizar versión en {file_path}: {str(e)}")
        return False


def bump_version(current_version: str, bump_type: str) -> str:
    """
    Incrementa la versión según el tipo de incremento.
    
    Args:
        current_version: Versión actual (x.y.z)
        bump_type: Tipo de incremento (major, minor, patch)
        
    Returns:
        Nueva versión
    """
    # Validar formato
    if not re.match(r'^[0-9]+\.[0-9]+\.[0-9]+$', current_version):
        raise ValueError(f"Formato de versión inválido: {current_version}")
    
    # Separar componentes
    major, minor, patch = map(int, current_version.split('.'))
    
    # Incrementar según tipo
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Tipo de incremento inválido: {bump_type}")


def find_version_files(project_dir: Path) -> List[Path]:
    """
    Encuentra archivos que contienen versiones en el proyecto.
    
    Args:
        project_dir: Directorio del proyecto
        
    Returns:
        Lista de archivos con versiones
    """
    version_files = []
    
    # Archivos comunes donde se suelen almacenar versiones
    common_files = [
        project_dir / "core_dajarony" / "__init__.py",
        project_dir / "core_dajarony" / "logica" / "__init__.py",
        project_dir / "core_dajarony" / "herramientas" / "__init__.py",
        project_dir / "setup.py",
        project_dir / "pyproject.toml",
        project_dir / "package.json",
        project_dir / "VERSION",
    ]
    
    # Verificar archivos comunes
    for file_path in common_files:
        if file_path.exists() and find_version_in_file(file_path) is not None:
            version_files.append(file_path)
    
    # Si no se encontraron archivos comunes, buscar en todo el proyecto
    if not version_files:
        logger.info("Buscando archivos con versión en todo el proyecto...")
        for file_path in project_dir.rglob("*.py"):
            if find_version_in_file(file_path) is not None:
                version_files.append(file_path)
    
    return version_files


def update_version(project_dir: Path, bump_type: str, dry_run: bool = False) -> Tuple[str, str]:
    """
    Actualiza la versión en todo el proyecto.
    
    Args:
        project_dir: Directorio del proyecto
        bump_type: Tipo de incremento (major, minor, patch)
        dry_run: Si es True, no realiza cambios reales
        
    Returns:
        Tupla (versión_anterior, nueva_versión)
    """
    logger.info(f"Actualizando versión ({bump_type}) en {project_dir}")
    
    # Encontrar archivos con versión
    version_files = find_version_files(project_dir)
    if not version_files:
        raise ValueError("No se encontraron archivos con versión")
    
    # Obtener versión actual
    current_version = None
    for file_path in version_files:
        version = find_version_in_file(file_path)
        if version:
            if current_version is None:
                current_version = version
            elif current_version != version:
                logger.warning(f"Versión inconsistente en {file_path}: {version} (esperada: {current_version})")
    
    if not current_version:
        raise ValueError("No se pudo determinar la versión actual")
    
    # Calcular nueva versión
    new_version = bump_version(current_version, bump_type)
    logger.info(f"Versión actual: {current_version} -> Nueva versión: {new_version}")
    
    # Actualizar en cada archivo
    if not dry_run:
        for file_path in version_files:
            update_version_in_file(file_path, new_version)
    else:
        logger.info("Modo dry run: no se realizan cambios reales")
    
    return current_version, new_version


def parse_changelog(changelog_path: Path) -> Dict[str, Any]:
    """
    Parsea un archivo de registro de cambios.
    
    Args:
        changelog_path: Ruta al archivo de registro de cambios
        
    Returns:
        Diccionario con el contenido parseado
    """
    if not changelog_path.exists():
        return {"versions": {}}
    
    # Intentar parsear según la extensión
    try:
        if changelog_path.suffix.lower() == '.md':
            return _parse_markdown_changelog(changelog_path)
        elif changelog_path.suffix.lower() == '.json':
            return json.loads(changelog_path.read_text(encoding='utf-8'))
        elif changelog_path.suffix.lower() in ('.yaml', '.yml'):
            return yaml.safe_load(changelog_path.read_text(encoding='utf-8'))
        else:
            logger.warning(f"Formato de changelog no soportado: {changelog_path.suffix}")
            return {"versions": {}}
    except Exception as e:
        logger.error(f"Error al parsear changelog: {str(e)}")
        return {"versions": {}}


def _parse_markdown_changelog(changelog_path: Path) -> Dict[str, Any]:
    """
    Parsea un archivo de registro de cambios en formato Markdown.
    
    Args:
        changelog_path: Ruta al archivo de registro de cambios
        
    Returns:
        Diccionario con el contenido parseado
    """
    content = changelog_path.read_text(encoding='utf-8')
    result = {"versions": {}}
    
    # Patrón para detectar secciones de versión
    version_pattern = re.compile(r'^## \[?([0-9]+\.[0-9]+\.[0-9]+)\]?(?: - (.+?))?$', re.MULTILINE)
    
    # Encontrar todas las secciones de versión
    version_matches = list(version_pattern.finditer(content))
    
    for i, match in enumerate(version_matches):
        version = match.group(1)
        date_str = match.group(2) if match.group(2) else None
        
        # Determinar el rango de contenido para esta versión
        start_pos = match.end()
        end_pos = version_matches[i+1].start() if i < len(version_matches) - 1 else len(content)
        
        version_content = content[start_pos:end_pos].strip()
        
        # Extraer secciones (Added, Changed, Fixed, etc.)
        sections = {}
        section_pattern = re.compile(r'^### (.+?)$', re.MULTILINE)
        section_matches = list(section_pattern.finditer(version_content))
        
        for j, section_match in enumerate(section_matches):
            section_name = section_match.group(1)
            
            # Determinar el rango de contenido para esta sección
            section_start = section_match.end()
            section_end = section_matches[j+1].start() if j < len(section_matches) - 1 else len(version_content)
            
            section_content = version_content[section_start:section_end].strip()
            
            # Extraer elementos de la lista
            items = []
            for line in section_content.split('\n'):
                if line.strip().startswith('- '):
                    items.append(line.strip()[2:])
            
            sections[section_name] = items
        
        # Guardar información de versión
        result["versions"][version] = {
            "date": date_str,
            "sections": sections
        }
    
    return result


def update_changelog(
    changelog_path: Path, 
    new_version: str, 
    changes: Dict[str, List[str]], 
    dry_run: bool = False
) -> bool:
    """
    Actualiza el archivo de registro de cambios.
    
    Args:
        changelog_path: Ruta al archivo de registro de cambios
        new_version: Nueva versión
        changes: Diccionario de cambios por sección
        dry_run: Si es True, no realiza cambios reales
        
    Returns:
        True si se actualizó correctamente
    """
    logger.info(f"Actualizando changelog en {changelog_path}")
    
    # Si el archivo no existe, crear uno nuevo
    if not changelog_path.exists():
        if dry_run:
            logger.info(f"Modo dry run: se crearía un nuevo archivo {changelog_path}")
            return True
        
        # Determinar formato según extensión
        if changelog_path.suffix.lower() == '.md':
            return _create_markdown_changelog(changelog_path, new_version, changes)
        elif changelog_path.suffix.lower() == '.json':
            return _create_json_changelog(changelog_path, new_version, changes)
        elif changelog_path.suffix.lower() in ('.yaml', '.yml'):
            return _create_yaml_changelog(changelog_path, new_version, changes)
        else:
            logger.error(f"Formato de changelog no soportado: {changelog_path.suffix}")
            return False
    
    # Actualizar archivo existente
    if dry_run:
        logger.info(f"Modo dry run: se actualizaría {changelog_path}")
        return True
    
    # Actualizar según formato
    if changelog_path.suffix.lower() == '.md':
        return _update_markdown_changelog(changelog_path, new_version, changes)
    elif changelog_path.suffix.lower() == '.json':
        return _update_json_changelog(changelog_path, new_version, changes)
    elif changelog_path.suffix.lower() in ('.yaml', '.yml'):
        return _update_yaml_changelog(changelog_path, new_version, changes)
    else:
        logger.error(f"Formato de changelog no soportado: {changelog_path.suffix}")
        return False


def _create_markdown_changelog(
    changelog_path: Path,
    new_version: str,
    changes: Dict[str, List[str]]
) -> bool:
    """
    Crea un nuevo archivo de registro de cambios en formato Markdown.
    
    Args:
        changelog_path: Ruta al archivo de registro de cambios
        new_version: Nueva versión
        changes: Diccionario de cambios por sección
        
    Returns:
        True si se creó correctamente
    """
    try:
        # Crear contenido
        content = "# Registro de Cambios\n\n"
        content += "Todos los cambios notables en este proyecto serán documentados en este archivo.\n\n"
        
        # Añadir nueva versión
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        content += f"## {new_version} - {date_str}\n\n"
        
        # Añadir secciones de cambios
        for section, items in changes.items():
            if items:
                content += f"### {section}\n\n"
                for item in items:
                    content += f"- {item}\n"
                content += "\n"
        
        # Guardar archivo
        changelog_path.write_text(content, encoding='utf-8')
        logger.info(f"Creado nuevo changelog en {changelog_path}")
        return True
    except Exception as e:
        logger.error(f"Error al crear changelog: {str(e)}")
        return False


def _update_markdown_changelog(
    changelog_path: Path,
    new_version: str,
    changes: Dict[str, List[str]]
) -> bool:
    """
    Actualiza un archivo de registro de cambios en formato Markdown.
    
    Args:
        changelog_path: Ruta al archivo de registro de cambios
        new_version: Nueva versión
        changes: Diccionario de cambios por sección
        
    Returns:
        True si se actualizó correctamente
    """
    try:
        # Leer contenido actual
        content = changelog_path.read_text(encoding='utf-8')
        
        # Preparar nueva sección
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        new_section = f"## {new_version} - {date_str}\n\n"
        
        # Añadir cambios por sección
        for section, items in changes.items():
            if items:
                new_section += f"### {section}\n\n"
                for item in items:
                    new_section += f"- {item}\n"
                new_section += "\n"
        
        # Buscar dónde insertar (después del encabezado principal)
        header_match = re.search(r'^# .+?$', content, re.MULTILINE)
        if header_match:
            # Insertar después del encabezado y una línea en blanco
            insert_pos = header_match.end()
            
            # Buscar línea en blanco después del encabezado
            blank_line_pos = content.find('\n\n', insert_pos)
            if blank_line_pos > 0:
                insert_pos = blank_line_pos + 2
            
            # Insertar nueva sección
            updated_content = content[:insert_pos] + new_section + content[insert_pos:]
        else:
            # Si no hay encabezado, añadir al inicio
            updated_content = new_section + content
        
        # Guardar archivo
        changelog_path.write_text(updated_content, encoding='utf-8')
        logger.info(f"Actualizado changelog en {changelog_path}")
        return True
    except Exception as e:
        logger.error(f"Error al actualizar changelog: {str(e)}")
        return False


def _create_json_changelog(
    changelog_path: Path,
    new_version: str,
    changes: Dict[str, List[str]]
) -> bool:
    """
    Crea un nuevo archivo de registro de cambios en formato JSON.
    
    Args:
        changelog_path: Ruta al archivo de registro de cambios
        new_version: Nueva versión
        changes: Diccionario de cambios por sección
        
    Returns:
        True si se creó correctamente
    """
    try:
        # Crear estructura
        changelog = {
            "project": "Core Dajarony",
            "versions": {
                new_version: {
                    "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "sections": changes
                }
            }
        }
        
        # Guardar archivo
        changelog_path.write_text(
            json.dumps(changelog, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        logger.info(f"Creado nuevo changelog en {changelog_path}")
        return True
    except Exception as e:
        logger.error(f"Error al crear changelog: {str(e)}")
        return False


def _update_json_changelog(
    changelog_path: Path,
    new_version: str,
    changes: Dict[str, List[str]]
) -> bool:
    """
    Actualiza un archivo de registro de cambios en formato JSON.
    
    Args:
        changelog_path: Ruta al archivo de registro de cambios
        new_version: Nueva versión
        changes: Diccionario de cambios por sección
        
    Returns:
        True si se actualizó correctamente
    """
    try:
        # Leer contenido actual
        changelog = json.loads(changelog_path.read_text(encoding='utf-8'))
        
        # Asegurar estructura mínima
        if "versions" not in changelog:
            changelog["versions"] = {}
        
        # Añadir nueva versión
        changelog["versions"][new_version] = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "sections": changes
        }
        
        # Guardar archivo
        changelog_path.write_text(
            json.dumps(changelog, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        logger.info(f"Actualizado changelog en {changelog_path}")
        return True
    except Exception as e:
        logger.error(f"Error al actualizar changelog: {str(e)}")
        return False


def _create_yaml_changelog(
    changelog_path: Path,
    new_version: str,
    changes: Dict[str, List[str]]
) -> bool:
    """
    Crea un nuevo archivo de registro de cambios en formato YAML.
    
    Args:
        changelog_path: Ruta al archivo de registro de cambios
        new_version: Nueva versión
        changes: Diccionario de cambios por sección
        
    Returns:
        True si se creó correctamente
    """
    try:
        # Crear estructura
        changelog = {
            "project": "Core Dajarony",
            "versions": {
                new_version: {
                    "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "sections": changes
                }
            }
        }
        
        # Guardar archivo
        changelog_path.write_text(
            yaml.dump(changelog, sort_keys=False, default_flow_style=False),
            encoding='utf-8'
        )
        logger.info(f"Creado nuevo changelog en {changelog_path}")
        return True
    except Exception as e:
        logger.error(f"Error al crear changelog: {str(e)}")
        return False


def _update_yaml_changelog(
    changelog_path: Path,
    new_version: str,
    changes: Dict[str, List[str]]
) -> bool:
    """
    Actualiza un archivo de registro de cambios en formato YAML.
    
    Args:
        changelog_path: Ruta al archivo de registro de cambios
        new_version: Nueva versión
        changes: Diccionario de cambios por sección
        
    Returns:
        True si se actualizó correctamente
    """
    try:
        # Leer contenido actual
        changelog = yaml.safe_load(changelog_path.read_text(encoding='utf-8'))
        
        # Asegurar estructura mínima
        if changelog is None:
            changelog = {}
        if "versions" not in changelog:
            changelog["versions"] = {}
        
        # Añadir nueva versión
        changelog["versions"][new_version] = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "sections": changes
        }
        
        # Guardar archivo
        changelog_path.write_text(
            yaml.dump(changelog, sort_keys=False, default_flow_style=False),
            encoding='utf-8'
        )
        logger.info(f"Actualizado changelog en {changelog_path}")
        return True
    except Exception as e:
        logger.error(f"Error al actualizar changelog: {str(e)}")
        return False


def prompt_for_changes() -> Dict[str, List[str]]:
    """
    Solicita al usuario los cambios para la nueva versión.
    
    Returns:
        Diccionario de cambios por sección
    """
    print("\n=== Ingrese los cambios para la nueva versión ===")
    print("(Deje en blanco y presione Enter para terminar cada sección)")
    
    changes = {}
    sections = ["Added", "Changed", "Fixed", "Removed", "Security"]
    
    for section in sections:
        print(f"\n--- {section} ---")
        items = []
        while True:
            item = input(f"{section}> ").strip()
            if not item:
                break
            items.append(item)
        
        if items:
            changes[section] = items
    
    return changes


def generate_changelog(
    project_dir: Path,
    version: Optional[str] = None,
    changes: Optional[Dict[str, List[str]]] = None,
    format: str = 'md',
    dry_run: bool = False
) -> Tuple[str, Dict[str, List[str]]]:
    """
    Genera o actualiza el registro de cambios.
    
    Args:
        project_dir: Directorio del proyecto
        version: Versión específica (si es None, se detecta automáticamente)
        changes: Diccionario de cambios (si es None, se solicita interactivamente)
        format: Formato del changelog (md, json, yaml)
        dry_run: Si es True, no realiza cambios reales
        
    Returns:
        Tupla (versión, cambios)
    """
    # Determinar versión
    if version is None:
        version_files = find_version_files(project_dir)
        if not version_files:
            raise ValueError("No se encontraron archivos con versión")
        
        version = find_version_in_file(version_files[0])
        if not version:
            raise ValueError("No se pudo determinar la versión actual")
    
    # Solicitar cambios si no se proporcionaron
    if changes is None:
        changes = prompt_for_changes()
    
    # Determinar archivo de changelog
    format = format.lower()
    if format not in ('md', 'json', 'yaml', 'yml'):
        raise ValueError(f"Formato no soportado: {format}")
    
    # Usar 'yml' como extensión para yaml
    if format == 'yaml':
        format = 'yml'
    
    changelog_path = project_dir / f"CHANGELOG.{format}"
    
    # Actualizar changelog
    update_changelog(changelog_path, version, changes, dry_run)
    
    return version, changes


def main():
    """Función principal para uso como script."""
    parser = argparse.ArgumentParser(description="Gestor de versiones para Core Dajarony")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: bump
    bump_parser = subparsers.add_parser("bump", help="Incrementar versión")
    bump_parser.add_argument("type", choices=["major", "minor", "patch"], 
                           help="Tipo de incremento")
    bump_parser.add_argument("--dir", "-d", default=".", 
                           help="Directorio del proyecto (por defecto: directorio actual)")
    bump_parser.add_argument("--changelog", "-c", action="store_true", 
                           help="Actualizar también el registro de cambios")
    bump_parser.add_argument("--format", "-f", choices=["md", "json", "yaml"], default="md",
                           help="Formato del registro de cambios (por defecto: md)")
    bump_parser.add_argument("--dry-run", action="store_true", 
                           help="No realizar cambios reales")
    
    # Comando: changelog
    changelog_parser = subparsers.add_parser("changelog", help="Gestionar registro de cambios")
    changelog_parser.add_argument("--dir", "-d", default=".", 
                                help="Directorio del proyecto (por defecto: directorio actual)")
    changelog_parser.add_argument("--version", "-v", 
                                help="Versión específica (por defecto: se detecta automáticamente)")
    changelog_parser.add_argument("--format", "-f", choices=["md", "json", "yaml"], default="md",
                                help="Formato del registro de cambios (por defecto: md)")
    changelog_parser.add_argument("--dry-run", action="store_true", 
                                help="No realizar cambios reales")
    
    args = parser.parse_args()
    
    try:
        if args.command == "bump":
            project_dir = Path(args.dir).resolve()
            
            # Incrementar versión
            current_version, new_version = update_version(
                project_dir, 
                args.type, 
                args.dry_run
            )
            
            # Actualizar changelog si se solicitó
            if args.changelog:
                changes = prompt_for_changes()
                changelog_path = project_dir / f"CHANGELOG.{args.format}"
                update_changelog(changelog_path, new_version, changes, args.dry_run)
                
                if not args.dry_run:
                    print(f"\nVersión actualizada: {current_version} -> {new_version}")
                    print(f"Changelog actualizado: {changelog_path}")
                else:
                    print(f"\n[DRY RUN] Se actualizaría versión: {current_version} -> {new_version}")
                    print(f"[DRY RUN] Se actualizaría changelog: {changelog_path}")
            else:
                if not args.dry_run:
                    print(f"\nVersión actualizada: {current_version} -> {new_version}")
                else:
                    print(f"\n[DRY RUN] Se actualizaría versión: {current_version} -> {new_version}")
            
        elif args.command == "changelog":
            project_dir = Path(args.dir).resolve()
            
            # Generar changelog
            version, changes = generate_changelog(
                project_dir,
                args.version,
                None,  # Solicitar cambios interactivamente
                args.format,
                args.dry_run
            )
            
            if not args.dry_run:
                print(f"\nChangelog actualizado para versión: {version}")
            else:
                print(f"\n[DRY RUN] Se actualizaría changelog para versión: {version}")
            
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()