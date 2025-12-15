"""
SUME DOCBLOCK

Nombre: Generador de Documentación
Tipo: Herramienta

Entradas:
- Rutas a archivos fuente Python
- Directorio de salida para documentación
- Opciones de formato (markdown, html)
- Configuración de plantillas

Acciones:
- Escanear código fuente buscando SUME DOCBLOCKs
- Extraer metadatos estructurados de bloques de documentación
- Generar documentación en formatos solicitados
- Crear gráficos de arquitectura y dependencias
- Construir índices y referencias cruzadas
- Mapear flujos de interacción entre componentes

Salidas:
- Archivos de documentación generados
- Diagramas de estructura y flujo
- Índice de componentes y funcionalidades
- Referencias cruzadas entre componentes
"""
import os
import re
import sys
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import markdown
import yaml
from datetime import datetime


class DocGenerator:
    """
    Generador de documentación basado en SUME DOCBLOCKs.
    
    Escanea código fuente para extraer bloques de documentación SUME
    y genera documentación estructurada en varios formatos.
    """
    
    def __init__(self, output_dir: str = "./docs", 
                template_dir: Optional[str] = None,
                logger: Optional[logging.Logger] = None):
        """
        Inicializa el generador de documentación.
        
        Args:
            output_dir: Directorio donde se generará la documentación
            template_dir: Directorio con plantillas personalizadas (opcional)
            logger: Logger para registro de actividad (opcional)
        """
        self.output_dir = Path(output_dir)
        self.template_dir = Path(template_dir) if template_dir else None
        self.logger = logger or logging.getLogger(__name__)
        
        # Almacén de componentes encontrados
        # {nombre_componente: {metadata}}
        self.components: Dict[str, Dict[str, Any]] = {}
        
        # Relaciones entre componentes
        # {componente_origen: {componente_destino: tipo_relacion}}
        self.relationships: Dict[str, Dict[str, str]] = {}
        
        # Componentes por tipo
        # {tipo: [nombres_componentes]}
        self.components_by_type: Dict[str, List[str]] = {}
        
        # Estructura de directorios
        # {directorio: {subdirectorios, archivos}}
        self.directory_structure: Dict[str, Dict[str, Any]] = {}
        
        # Prepare output directory
        self._prepare_output_dir()
        
        self.logger.debug(f"DocGenerator inicializado. Directorio de salida: {output_dir}")
    
    def _prepare_output_dir(self):
        """Prepara el directorio de salida."""
        # Crear directorio si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear subdirectorios necesarios
        (self.output_dir / 'componentes').mkdir(exist_ok=True)
        (self.output_dir / 'diagramas').mkdir(exist_ok=True)
        (self.output_dir / 'assets').mkdir(exist_ok=True)
        
        # Copiar assets estáticos si existen
        if self.template_dir and (self.template_dir / 'assets').exists():
            for asset_file in (self.template_dir / 'assets').glob('*'):
                shutil.copy(asset_file, self.output_dir / 'assets')
                
        self.logger.debug("Directorios de salida preparados")
    
    def scan_directory(self, directory: str, recursive: bool = True) -> int:
        """
        Escanea un directorio en busca de archivos Python con SUME DOCBLOCKs.
        
        Args:
            directory: Ruta al directorio a escanear
            recursive: Si debe escanear subdirectorios
            
        Returns:
            Número de componentes encontrados
        """
        self.logger.info(f"Escaneando directorio: {directory}")
        directory_path = Path(directory)
        
        if not directory_path.exists():
            self.logger.error(f"El directorio {directory} no existe")
            return 0
        
        # Inicializar estructura de este directorio
        dir_info = {
            "subdirectories": [],
            "files": []
        }
        
        # Escanear archivos
        for item in directory_path.iterdir():
            if item.is_file() and item.suffix == '.py':
                # Añadir a estructura
                dir_info["files"].append(item.name)
                
                # Procesar archivo
                self._process_file(item)
            elif item.is_dir() and recursive:
                # Añadir a estructura
                dir_info["subdirectories"].append(item.name)
                
                # Procesar subdirectorio
                self.scan_directory(str(item), recursive=True)
        
        # Guardar estructura
        self.directory_structure[str(directory_path)] = dir_info
        
        return len(self.components)
    
    def _process_file(self, file_path: Path) -> None:
        """
        Procesa un archivo para extraer SUME DOCBLOCKs.
        
        Args:
            file_path: Ruta al archivo a procesar
        """
        try:
            self.logger.debug(f"Procesando archivo: {file_path}")
            
            # Leer contenido del archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar bloques SUME
            sume_blocks = self._extract_sume_blocks(content)
            
            # Procesar cada bloque encontrado
            for block in sume_blocks:
                component_info = self._parse_sume_block(block)
                if component_info and 'Nombre' in component_info:
                    component_name = component_info['Nombre']
                    
                    # Añadir información del archivo
                    component_info['_file_path'] = str(file_path)
                    component_info['_module_path'] = self._get_module_path(file_path)
                    
                    # Guardar componente
                    self.components[component_name] = component_info
                    
                    # Clasificar por tipo
                    component_type = component_info.get('Tipo', 'Desconocido')
                    if component_type not in self.components_by_type:
                        self.components_by_type[component_type] = []
                    self.components_by_type[component_type].append(component_name)
                    
                    self.logger.debug(f"Encontrado componente: {component_name} ({component_type})")
                
            # Analizar relaciones
            self._analyze_relationships()
            
        except Exception as e:
            self.logger.error(f"Error al procesar archivo {file_path}: {str(e)}")
    
    def _extract_sume_blocks(self, content: str) -> List[str]:
        """
        Extrae bloques SUME de un contenido.
        
        Args:
            content: Contenido a analizar
            
        Returns:
            Lista de bloques SUME encontrados
        """
        # Patrón para buscar bloques SUME
        pattern = r'"""[\s\n]*SUME DOCBLOCK\s*\n(.*?)"""'
        
        # Encontrar todas las coincidencias
        matches = re.findall(pattern, content, re.DOTALL)
        
        return matches
    
    def _parse_sume_block(self, block: str) -> Dict[str, Any]:
        """
        Parsea un bloque SUME y extrae su estructura.
        
        Args:
            block: Bloque SUME a parsear
            
        Returns:
            Diccionario con la información estructurada
        """
        result = {}
        current_section = None
        section_content = []
        
        # Procesar línea por línea
        for line in block.split('\n'):
            line = line.strip()
            
            # Línea vacía
            if not line:
                if section_content and current_section:
                    # Finalizar sección actual
                    result[current_section] = '\n'.join(section_content)
                    section_content = []
                continue
            
            # Encabezado de sección (Entradas:, Acciones:, Salidas:)
            if line.endswith(':') and not line.startswith('-'):
                # Guardar sección anterior si existe
                if current_section and section_content:
                    result[current_section] = '\n'.join(section_content)
                
                # Nueva sección
                current_section = line[:-1]  # quitar el :
                section_content = []
                continue
            
            # Par clave-valor directo (Nombre: X, Tipo: Y)
            if ':' in line and not current_section and not line.startswith('-'):
                key, value = [part.strip() for part in line.split(':', 1)]
                result[key] = value
                continue
            
            # Contenido de la sección actual
            section_content.append(line)
        
        # Guardar última sección
        if current_section and section_content:
            result[current_section] = '\n'.join(section_content)
        
        return result
    
    def _get_module_path(self, file_path: Path) -> str:
        """
        Obtiene la ruta de módulo Python a partir de la ruta del archivo.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Ruta de módulo (e.g., 'core_dajarony.logica.container')
        """
        # Obtener ruta relativa respecto a la raíz del proyecto
        try:
            # Intentar encontrar la raíz del proyecto (donde está core_dajarony)
            parts = list(file_path.parts)
            module_parts = []
            
            # Buscar 'core_dajarony' en las partes
            found_root = False
            for part in parts:
                if found_root or part == 'core_dajarony':
                    found_root = True
                    module_parts.append(part)
            
            # Si no encontramos la raíz, usar la ruta completa
            if not found_root:
                return str(file_path.with_suffix('')).replace('/', '.').replace('\\', '.')
            
            # Construir ruta de módulo
            module_path = '.'.join(module_parts)
            
            # Quitar extensión .py
            if module_path.endswith('.py'):
                module_path = module_path[:-3]
                
            return module_path
            
        except Exception:
            # En caso de error, devolver la ruta simple sin extensión
            return file_path.stem
    
    def _analyze_relationships(self) -> None:
        """
        Analiza las relaciones entre componentes basado en sus entradas y salidas.
        """
        # Reiniciar relaciones
        self.relationships = {}
        
        # Analizar cada componente
        for name, info in self.components.items():
            # Inicializar relaciones para este componente
            if name not in self.relationships:
                self.relationships[name] = {}
            
            # Buscar dependencias en Entradas
            if 'Entradas' in info:
                # Buscar referencias a otros componentes
                for other_name in self.components:
                    if other_name != name and other_name in info['Entradas']:
                        self.relationships[other_name][name] = 'provides'
                        self.relationships[name][other_name] = 'consumes'
            
            # Buscar dependientes en Salidas
            if 'Salidas' in info:
                # Buscar referencias a otros componentes
                for other_name in self.components:
                    if other_name != name and other_name in info['Salidas']:
                        self.relationships[name][other_name] = 'provides'
                        self.relationships[other_name][name] = 'consumes'
    
    def generate_documentation(self, 
                              formats: List[str] = ['markdown', 'html'],
                              include_diagrams: bool = True) -> None:
        """
        Genera la documentación en los formatos especificados.
        
        Args:
            formats: Lista de formatos a generar ('markdown', 'html')
            include_diagrams: Si se deben incluir diagramas
        """
        self.logger.info(f"Generando documentación en formatos: {formats}")
        
        # Verificar que hay componentes
        if not self.components:
            self.logger.warning("No hay componentes para generar documentación")
            return
        
        # Generar documentación por componente
        self._generate_component_docs(formats)
        
        # Generar índice
        self._generate_index(formats)
        
        # Generar diagramas
        if include_diagrams:
            self._generate_diagrams()
        
        # Generar vista de arquitectura
        self._generate_architecture_view(formats)
        
        # Generar mapa de relaciones
        self._generate_relationship_matrix(formats)
        
        self.logger.info(f"Documentación generada en {self.output_dir}")
    
    def _generate_component_docs(self, formats: List[str]) -> None:
        """
        Genera documentación individual para cada componente.
        
        Args:
            formats: Formatos a generar
        """
        components_dir = self.output_dir / 'componentes'
        
        # Para cada componente
        for name, info in self.components.items():
            self.logger.debug(f"Generando documentación para componente: {name}")
            
            # Crear contenido Markdown
            md_content = f"# {name}\n\n"
            
            # Tipo
            component_type = info.get('Tipo', 'Desconocido')
            md_content += f"**Tipo:** {component_type}\n\n"
            
            # Ruta de archivo
            if '_file_path' in info:
                md_content += f"**Archivo:** `{info['_file_path']}`\n\n"
            
            # Módulo
            if '_module_path' in info:
                md_content += f"**Módulo:** `{info['_module_path']}`\n\n"
            
            # Secciones principales
            for section in ['Entradas', 'Acciones', 'Salidas']:
                if section in info:
                    md_content += f"## {section}\n\n{info[section]}\n\n"
            
            # Relaciones con otros componentes
            if name in self.relationships and self.relationships[name]:
                md_content += "## Relaciones con otros componentes\n\n"
                
                # Dependencias (consumidas)
                consumes = [other for other, rel in self.relationships[name].items() 
                          if rel == 'consumes']
                if consumes:
                    md_content += "### Dependencias\n\n"
                    for dep in consumes:
                        dep_type = self.components.get(dep, {}).get('Tipo', 'Desconocido')
                        md_content += f"- [{dep}](./componentes/{self._get_safe_filename(dep)}.md) ({dep_type})\n"
                    md_content += "\n"
                
                # Servicios (proporcionados)
                provides = [other for other, rel in self.relationships[name].items() 
                          if rel == 'provides']
                if provides:
                    md_content += "### Proporciona servicios a\n\n"
                    for prov in provides:
                        prov_type = self.components.get(prov, {}).get('Tipo', 'Desconocido')
                        md_content += f"- [{prov}](./componentes/{self._get_safe_filename(prov)}.md) ({prov_type})\n"
                    md_content += "\n"
            
            # Guardar en archivo para cada formato
            safe_name = self._get_safe_filename(name)
            
            # Markdown
            if 'markdown' in formats:
                with open(components_dir / f"{safe_name}.md", 'w', encoding='utf-8') as f:
                    f.write(md_content)
            
            # HTML
            if 'html' in formats:
                html_content = markdown.markdown(md_content)
                html_content = self._wrap_html_template(html_content, title=name)
                
                with open(components_dir / f"{safe_name}.html", 'w', encoding='utf-8') as f:
                    f.write(html_content)
    
    def _generate_index(self, formats: List[str]) -> None:
        """
        Genera un índice para la documentación.
        
        Args:
            formats: Formatos a generar
        """
        self.logger.debug("Generando índice de documentación")
        
        # Crear contenido Markdown
        md_content = "# Documentación del Sistema Core Dajarony\n\n"
        
        # Fecha de generación
        md_content += f"*Documentación generada: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        
        # Resumen de componentes
        md_content += f"## Resumen de Componentes\n\n"
        md_content += f"Total de componentes documentados: **{len(self.components)}**\n\n"
        
        # Componentes por tipo
        for component_type, components in sorted(self.components_by_type.items()):
            md_content += f"### {component_type}s\n\n"
            for name in sorted(components):
                safe_name = self._get_safe_filename(name)
                md_content += f"- [{name}](./componentes/{safe_name}.md)\n"
            md_content += "\n"
        
        # Enlaces a otras secciones
        md_content += "## Vistas del Sistema\n\n"
        
        if 'markdown' in formats:
            md_content += "- [Vista de Arquitectura](./arquitectura.md)\n"
            md_content += "- [Matriz de Relaciones](./relaciones.md)\n"
        else:
            md_content += "- [Vista de Arquitectura](./arquitectura.html)\n"
            md_content += "- [Matriz de Relaciones](./relaciones.html)\n"
        
        md_content += "\n"
        
        # Guardar en archivo para cada formato
        # Markdown
        if 'markdown' in formats:
            with open(self.output_dir / "index.md", 'w', encoding='utf-8') as f:
                f.write(md_content)
        
        # HTML
        if 'html' in formats:
            html_content = markdown.markdown(md_content)
            html_content = self._wrap_html_template(html_content, title="Documentación del Sistema")
            
            with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
                f.write(html_content)
    
    def _generate_architecture_view(self, formats: List[str]) -> None:
        """
        Genera una vista de la arquitectura del sistema.
        
        Args:
            formats: Formatos a generar
        """
        self.logger.debug("Generando vista de arquitectura")
        
        # Crear contenido Markdown
        md_content = "# Vista de Arquitectura del Sistema\n\n"
        
        # Diagrama principal
        md_content += "## Diagrama de Componentes\n\n"
        md_content += f"![Diagrama de Componentes](./diagramas/componentes.png)\n\n"
        
        # Describir capas de la arquitectura
        md_content += "## Capas de la Arquitectura\n\n"
        
        # Ordenar tipos por relevancia
        ordered_types = []
        for priority_type in ['Entrada', 'Lógica', 'Contrato', 'Salida', 'Herramienta', 'Paquete']:
            if priority_type in self.components_by_type:
                ordered_types.append(priority_type)
        
        # Añadir tipos restantes
        for component_type in sorted(self.components_by_type.keys()):
            if component_type not in ordered_types:
                ordered_types.append(component_type)
        
        # Describir cada capa
        for component_type in ordered_types:
            components = self.components_by_type[component_type]
            md_content += f"### Capa de {component_type}\n\n"
            
            # Contar componentes
            md_content += f"**{len(components)} componentes**\n\n"
            
            # Listar componentes
            if components:
                for name in sorted(components):
                    safe_name = self._get_safe_filename(name)
                    # Extraer breve descripción si está disponible
                    description = ""
                    component_info = self.components.get(name, {})
                    if 'Acciones' in component_info:
                        # Tomar primera línea como descripción breve
                        lines = component_info['Acciones'].split('\n')
                        if lines and lines[0].strip():
                            description = f": {lines[0].strip()}"
                    
                    md_content += f"- [{name}](./componentes/{safe_name}.md){description}\n"
                md_content += "\n"
        
        # Guardar en archivo para cada formato
        # Markdown
        if 'markdown' in formats:
            with open(self.output_dir / "arquitectura.md", 'w', encoding='utf-8') as f:
                f.write(md_content)
        
        # HTML
        if 'html' in formats:
            html_content = markdown.markdown(md_content)
            html_content = self._wrap_html_template(html_content, title="Arquitectura del Sistema")
            
            with open(self.output_dir / "arquitectura.html", 'w', encoding='utf-8') as f:
                f.write(html_content)
    
    def _generate_relationship_matrix(self, formats: List[str]) -> None:
        """
        Genera una matriz de relaciones entre componentes.
        
        Args:
            formats: Formatos a generar
        """
        self.logger.debug("Generando matriz de relaciones")
        
        # Crear contenido Markdown
        md_content = "# Matriz de Relaciones entre Componentes\n\n"
        
        # Crear tabla
        md_content += "| Componente |"
        for name in sorted(self.components.keys()):
            safe_name = self._get_safe_filename(name)
            md_content += f" [{name}](./componentes/{safe_name}.md) |"
        md_content += "\n"
        
        # Separador
        md_content += "| --- |" + " --- |" * len(self.components) + "\n"
        
        # Filas
        for row_name in sorted(self.components.keys()):
            safe_row_name = self._get_safe_filename(row_name)
            md_content += f"| [{row_name}](./componentes/{safe_row_name}.md) |"
            
            # Columnas
            for col_name in sorted(self.components.keys()):
                cell_content = ""
                
                # Verificar relación
                if row_name in self.relationships and col_name in self.relationships[row_name]:
                    relation = self.relationships[row_name][col_name]
                    if relation == 'provides':
                        cell_content = "➡️"  # Proporciona a
                    elif relation == 'consumes':
                        cell_content = "⬅️"  # Consume de
                
                md_content += f" {cell_content} |"
            
            md_content += "\n"
        
        # Leyenda
        md_content += "\n**Leyenda**:\n"
        md_content += "- ➡️ El componente de la fila proporciona servicios al componente de la columna\n"
        md_content += "- ⬅️ El componente de la fila consume servicios del componente de la columna\n"
        
        # Guardar en archivo para cada formato
        # Markdown
        if 'markdown' in formats:
            with open(self.output_dir / "relaciones.md", 'w', encoding='utf-8') as f:
                f.write(md_content)
        
        # HTML
        if 'html' in formats:
            html_content = markdown.markdown(md_content)
            html_content = self._wrap_html_template(html_content, title="Matriz de Relaciones")
            
            with open(self.output_dir / "relaciones.html", 'w', encoding='utf-8') as f:
                f.write(html_content)
    
    def _generate_diagrams(self) -> None:
        """Genera diagramas del sistema."""
        self.logger.debug("Generando diagramas")
        
        # Generar diagrama de componentes
        self._generate_component_diagram()
        
        # Generar diagrama de relaciones
        self._generate_relationship_diagram()
    
    def _generate_component_diagram(self) -> None:
        """Genera un diagrama de componentes usando Mermaid."""
        # Generar código Mermaid
        mermaid = "graph TD\n"
        
        # Definir estilos de nodos por tipo
        for component_type, components in self.components_by_type.items():
            # Usar colores diferentes para cada tipo
            color = self._get_color_for_type(component_type)
            mermaid += f"    classDef {component_type.lower()} fill:{color}\n"
        
        # Añadir nodos
        for name, info in self.components.items():
            # Identificador seguro
            safe_id = self._get_safe_id(name)
            display_name = name.replace(' ', '<br>')
            
            # Tipo
            component_type = info.get('Tipo', 'Desconocido')
            
            # Nodo
            mermaid += f"    {safe_id}[\"{display_name}\"]::{component_type.lower()}\n"
        
        # Añadir conexiones
        for source, targets in self.relationships.items():
            source_id = self._get_safe_id(source)
            
            for target, relation in targets.items():
                if relation == 'provides':
                    target_id = self._get_safe_id(target)
                    mermaid += f"    {source_id} ---> {target_id}\n"
        
        # Guardar como archivo Mermaid
        with open(self.output_dir / "diagramas" / "componentes.mmd", 'w', encoding='utf-8') as f:
            f.write(mermaid)
        
        # Intentar generar imagen con mermaid-cli si está disponible
        try:
            # Usar mermaid-cli si está instalado
            import subprocess
            
            # Ruta al archivo de entrada y salida
            input_file = str(self.output_dir / "diagramas" / "componentes.mmd")
            output_file = str(self.output_dir / "diagramas" / "componentes.png")
            
            # Ejecutar mmdc (mermaid-cli)
            subprocess.run(["mmdc", "-i", input_file, "-o", output_file], 
                         check=True, capture_output=True)
            
            self.logger.debug("Diagrama de componentes generado con mermaid-cli")
        except Exception as e:
            self.logger.warning(f"No se pudo generar imagen del diagrama: {str(e)}")
            self.logger.warning("Por favor, use el código Mermaid generado en https://mermaid.live/ para crear la imagen")
    
    def _generate_relationship_diagram(self) -> None:
        """Genera un diagrama de relaciones usando Mermaid."""
        # Generar código Mermaid
        mermaid = "graph LR\n"
        
        # Definir estilos de nodos por tipo
        for component_type, components in self.components_by_type.items():
            # Usar colores diferentes para cada tipo
            color = self._get_color_for_type(component_type)
            mermaid += f"    classDef {component_type.lower()} fill:{color}\n"
        
        # Añadir nodos
        for name, info in self.components.items():
            # Identificador seguro
            safe_id = self._get_safe_id(name)
            display_name = name.replace(' ', '<br>')
            
            # Tipo
            component_type = info.get('Tipo', 'Desconocido')
            
            # Nodo
            mermaid += f"    {safe_id}[\"{display_name}\"]::{component_type.lower()}\n"
        
        # Añadir conexiones
        for source, targets in self.relationships.items():
            source_id = self._get_safe_id(source)
            
            for target, relation in targets.items():
                target_id = self._get_safe_id(target)
                
                if relation == 'provides':
                    mermaid += f"    {source_id} -->|provee| {target_id}\n"
                elif relation == 'consumes':
                    mermaid += f"    {source_id} -.->|consume| {target_id}\n"
        
        # Guardar como archivo Mermaid
        with open(self.output_dir / "diagramas" / "relaciones.mmd", 'w', encoding='utf-8') as f:
            f.write(mermaid)
        
        # Intentar generar imagen con mermaid-cli si está disponible
        try:
            import subprocess
            
            # Ruta al archivo de entrada y salida
            input_file = str(self.output_dir / "diagramas" / "relaciones.mmd")
            output_file = str(self.output_dir / "diagramas" / "relaciones.png")
            
            # Ejecutar mmdc (mermaid-cli)
            subprocess.run(["mmdc", "-i", input_file, "-o", output_file], 
                         check=True, capture_output=True)
            
            self.logger.debug("Diagrama de relaciones generado con mermaid-cli")
        except Exception as e:
            self.logger.warning(f"No se pudo generar imagen del diagrama: {str(e)}")
    
    def _get_safe_filename(self, name: str) -> str:
        """
        Convierte un nombre a un nombre de archivo seguro.
        
        Args:
            name: Nombre a convertir
            
        Returns:
            Nombre de archivo seguro
        """
        return name.lower().replace(' ', '_').replace('/', '_')
    
    def _get_safe_id(self, name: str) -> str:
        """
        Convierte un nombre a un identificador seguro para Mermaid.
        
        Args:
            name: Nombre a convertir
            
        Returns:
            Identificador seguro
        """
        # Eliminar caracteres no alfanuméricos
        safe = re.sub(r'[^a-zA-Z0-9]', '_', name)
        
        # Asegurar que no empiece con número
        if safe[0].isdigit():
            safe = 'id_' + safe
            
        return safe
    
    def _get_color_for_type(self, component_type: str) -> str:
        """
        Devuelve un color para un tipo de componente.
        
        Args:
            component_type: Tipo de componente
            
        Returns:
            Código de color HTML
        """
        # Mapa de colores por tipo
        color_map = {
            'Entrada': '#d4f1f9',
            'Lógica': '#e1f7e1',
            'Salida': '#fde8d9',
            'Contrato': '#fff2cc',
            'Herramienta': '#f2e8ff',
            'Paquete': '#f9f9f9'
        }
        
        # Devolver color o color por defecto
        return color_map.get(component_type, '#f5f5f5')
    
    def _wrap_html_template(self, content: str, title: str = "Documentación") -> str:
        """
        Envuelve contenido HTML en una plantilla.
        
        Args:
            content: Contenido HTML
            title: Título de la página
            
        Returns:
            HTML completo con la plantilla
        """
        # Usar plantilla personalizada si existe
        if self.template_dir and (self.template_dir / 'template.html').exists():
            with open(self.template_dir / 'template.html', 'r', encoding='utf-8') as f:
                template = f.read()
                
            # Reemplazar marcadores
            html = template.replace('{{title}}', title).replace('{{content}}', content)
            return html
        
        # Plantilla por defecto
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Core Dajarony</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        h1, h2, h3 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }}
        h1 {{
            padding-bottom: 0.3em;
            font-size: 2em;
            border-bottom: 1px solid #eaecef;
        }}
        h2 {{
            padding-bottom: 0.3em;
            font-size: 1.5em;
            border-bottom: 1px solid #eaecef;
        }}
        h3 {{
            font-size: 1.25em;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 16px;
        }}
        table, th, td {{
            border: 1px solid #dfe2e5;
        }}
        th, td {{
            padding: 6px 13px;
        }}
        tr:nth-child(even) {{
            background-color: #f6f8fa;
        }}
        code {{
            background-color: rgba(27, 31, 35, 0.05);
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 85%;
            margin: 0;
            padding: 0.2em 0.4em;
        }}
        pre {{
            background-color: #f6f8fa;
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 85%;
            line-height: 1.45;
            overflow: auto;
            padding: 16px;
        }}
        header {{
            background-color: #f6f8fa;
            padding: 16px;
            margin-bottom: 20px;
            border-radius: 3px;
            border-bottom: 1px solid #dfe2e5;
        }}
        header h1 {{
            margin: 0;
            padding: 0;
            border: none;
        }}
        header p {{
            margin: 0;
            color: #586069;
        }}
        nav {{
            margin-bottom: 20px;
        }}
        nav a {{
            margin-right: 15px;
        }}
        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eaecef;
            color: #586069;
            font-size: 14px;
        }}
        img {{
            max-width: 100%;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Core Dajarony</h1>
        <p>Documentación del Sistema</p>
    </header>
    <nav>
        <a href="./index.html">Inicio</a>
        <a href="./arquitectura.html">Arquitectura</a>
        <a href="./relaciones.html">Relaciones</a>
    </nav>
    <main>
        {content}
    </main>
    <footer>
        <p>Documentación generada automáticamente por DocGenerator. Core Dajarony &copy; {datetime.now().year}</p>
    </footer>
</body>
</html>
"""


def generate_documentation(source_dir: str, output_dir: str = "./docs", 
                         formats: List[str] = ['markdown', 'html'],
                         template_dir: Optional[str] = None,
                         recursive: bool = True,
                         include_diagrams: bool = True) -> Dict[str, Any]:
    """
    Función utilitaria para generar documentación de un directorio.
    
    Args:
        source_dir: Directorio con código fuente a documentar
        output_dir: Directorio donde se generará la documentación
        formats: Formatos a generar ('markdown', 'html')
        template_dir: Directorio con plantillas (opcional)
        recursive: Si debe escanear subdirectorios
        include_diagrams: Si se deben incluir diagramas
        
    Returns:
        Resumen del proceso de generación
    """
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger("doc_generator")
    
    # Crear generador
    generator = DocGenerator(output_dir, template_dir, logger)
    
    # Escanear directorio
    components_count = generator.scan_directory(source_dir, recursive)
    
    # Generar documentación
    generator.generate_documentation(formats, include_diagrams)
    
    # Devolver resumen
    return {
        "components_count": components_count,
        "output_directory": str(generator.output_dir),
        "formats": formats,
        "components_by_type": {k: len(v) for k, v in generator.components_by_type.items()},
        "timestamp": datetime.now().isoformat()
    }


# Para ejecutar directamente como script
if __name__ == "__main__":
    # Configurar argumentos
    import argparse
    
    parser = argparse.ArgumentParser(description="Generador de documentación SUME")
    parser.add_argument("source_dir", help="Directorio con código fuente a documentar")
    parser.add_argument("--output", "-o", default="./docs", help="Directorio de salida")
    parser.add_argument("--formats", "-f", nargs="+", default=["markdown", "html"], 
                      choices=["markdown", "html"], help="Formatos a generar")
    parser.add_argument("--template", "-t", help="Directorio con plantillas")
    parser.add_argument("--no-recursive", "-n", action="store_true", help="No escanear subdirectorios")
    parser.add_argument("--no-diagrams", "-d", action="store_true", help="No generar diagramas")
    
    args = parser.parse_args()
    
    # Generar documentación
    result = generate_documentation(
        args.source_dir,
        args.output,
        args.formats,
        args.template,
        not args.no_recursive,
        not args.no_diagrams
    )
    
    # Mostrar resultado
    print(f"Documentación generada en {result['output_directory']}")
    print(f"Componentes encontrados: {result['components_count']}")
    print("Componentes por tipo:")
    for component_type, count in result['components_by_type'].items():
        print(f"  - {component_type}: {count}")