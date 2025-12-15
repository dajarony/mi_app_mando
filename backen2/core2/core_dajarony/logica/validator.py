"""
SUME DOCBLOCK

Nombre: Validator
Tipo: Lógica

Entradas:
- Esquemas de validación (tipos, reglas, restricciones)
- Datos a validar (estructuras, primitivos, objetos)
- Configuraciones de validación (strict, partial)

Acciones:
- Validar que los datos cumplan con el esquema definido
- Verificar tipos de datos, rangos, patrones
- Convertir tipos cuando sea posible
- Proporcionar mensajes de error detallados
- Aplicar validaciones condicionales
- Generar datos de ejemplo basados en esquemas

Salidas:
- Resultado de validación (éxito/error)
- Mensajes de error por campo
- Datos convertidos/normalizados
- Información de validación para debugging
"""
import re
import uuid
import json
import logging
from typing import Dict, Any, List, Set, Union, Tuple, Optional, Callable, Pattern
from datetime import datetime
from enum import Enum


class ValidationError(Exception):
    """Excepción para errores de validación."""
    
    def __init__(self, message: str, field: Optional[str] = None, errors: Dict[str, List[str]] = None):
        """
        Inicializa error de validación.
        
        Args:
            message: Mensaje de error general
            field: Campo específico que causó el error
            errors: Diccionario de errores por campo
        """
        super().__init__(message)
        self.field = field
        self.errors = errors or {}
        if field and field not in self.errors:
            self.errors[field] = [message]


class DataType(Enum):
    """Tipos de datos soportados para validación."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    NUMBER = "number"  # Integer o Float
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    EMAIL = "email"
    UUID = "uuid"
    DATE = "date"
    DATETIME = "datetime"
    ANY = "any"


class ValidationRule:
    """Regla de validación para un campo."""
    
    def __init__(
        self,
        type: Union[DataType, str],
        required: bool = True,
        default: Any = None,
        nullable: bool = False,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        pattern: Optional[Union[str, Pattern]] = None,
        enum: Optional[List[Any]] = None,
        items: Optional['ValidationRule'] = None,
        properties: Optional[Dict[str, 'ValidationRule']] = None,
        additional_properties: bool = False,
        custom_validator: Optional[Callable[[Any], Tuple[bool, Optional[str]]]] = None,
        description: Optional[str] = None
    ):
        """
        Inicializa una regla de validación.
        
        Args:
            type: Tipo de datos esperado
            required: Si el campo es obligatorio
            default: Valor por defecto si no se proporciona
            nullable: Si se permite valor None
            min_length: Longitud mínima para strings o listas
            max_length: Longitud máxima para strings o listas
            min_value: Valor mínimo para números
            max_value: Valor máximo para números
            pattern: Patrón regex para strings
            enum: Lista de valores permitidos
            items: Regla para validar elementos de una lista
            properties: Reglas para validar propiedades de un dict
            additional_properties: Si se permiten propiedades adicionales en un dict
            custom_validator: Función personalizada de validación
            description: Descripción del campo
        """
        # Convertir string a enum si es necesario
        self.type = type if isinstance(type, DataType) else DataType(type)
        self.required = required
        self.default = default
        self.nullable = nullable
        self.min_length = min_length
        self.max_length = max_length
        self.min_value = min_value
        self.max_value = max_value
        self.enum = enum
        self.custom_validator = custom_validator
        self.description = description
        
        # Compilar regex si es string
        if pattern and isinstance(pattern, str):
            self.pattern = re.compile(pattern)
        else:
            self.pattern = pattern
        
        # Reglas anidadas
        self.items = items
        self.properties = properties
        self.additional_properties = additional_properties
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la regla a un diccionario para serialización.
        
        Returns:
            Diccionario con la regla
        """
        result = {
            "type": self.type.value,
            "required": self.required,
            "nullable": self.nullable
        }
        
        # Añadir atributos opcionales
        if self.default is not None:
            result["default"] = self.default
        
        if self.min_length is not None:
            result["min_length"] = self.min_length
        
        if self.max_length is not None:
            result["max_length"] = self.max_length
        
        if self.min_value is not None:
            result["min_value"] = self.min_value
        
        if self.max_value is not None:
            result["max_value"] = self.max_value
        
        if self.pattern is not None:
            result["pattern"] = self.pattern.pattern
        
        if self.enum is not None:
            result["enum"] = self.enum
        
        if self.description is not None:
            result["description"] = self.description
        
        # Reglas anidadas
        if self.items is not None:
            result["items"] = self.items.to_dict()
        
        if self.properties is not None:
            result["properties"] = {k: v.to_dict() for k, v in self.properties.items()}
            result["additional_properties"] = self.additional_properties
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationRule':
        """
        Crea una regla a partir de un diccionario.
        
        Args:
            data: Diccionario con la regla
            
        Returns:
            Instancia de ValidationRule
        """
        # Extraer propiedades anidadas si existen
        properties = None
        if "properties" in data:
            properties = {k: cls.from_dict(v) for k, v in data["properties"].items()}
        
        # Extraer regla de items si existe
        items = None
        if "items" in data:
            items = cls.from_dict(data["items"])
        
        # Crear instancia
        return cls(
            type=data["type"],
            required=data.get("required", True),
            default=data.get("default"),
            nullable=data.get("nullable", False),
            min_length=data.get("min_length"),
            max_length=data.get("max_length"),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            pattern=data.get("pattern"),
            enum=data.get("enum"),
            items=items,
            properties=properties,
            additional_properties=data.get("additional_properties", False),
            description=data.get("description")
        )


class Validator:
    """
    Validador de datos con esquemas.
    
    Proporciona funcionalidad para validar datos contra esquemas
    definidos, con conversión de tipos y mensajes de error detallados.
    """
    
    def __init__(self, logger=None):
        """
        Inicializa un validador.
        
        Args:
            logger: Logger opcional para registrar actividad
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Diccionario de esquemas registrados por nombre
        self._schemas: Dict[str, Dict[str, ValidationRule]] = {}
    
    def register_schema(self, name: str, schema: Dict[str, ValidationRule]) -> bool:
        """
        Registra un esquema de validación.
        
        Args:
            name: Nombre único del esquema
            schema: Diccionario de reglas por campo
            
        Returns:
            True si se registró correctamente
        """
        if name in self._schemas:
            self.logger.warning(f"Esquema '{name}' ya existe, será sobrescrito")
        
        self._schemas[name] = schema
        self.logger.debug(f"Esquema '{name}' registrado con {len(schema)} campos")
        return True
    
    def register_schema_from_dict(self, name: str, schema_dict: Dict[str, Dict[str, Any]]) -> bool:
        """
        Registra un esquema a partir de un diccionario plano.
        
        Args:
            name: Nombre único del esquema
            schema_dict: Diccionario con definiciones de reglas
            
        Returns:
            True si se registró correctamente
        """
        schema = {}
        for field, rule_dict in schema_dict.items():
            schema[field] = ValidationRule.from_dict(rule_dict)
        
        return self.register_schema(name, schema)
    
    def get_schema(self, name: str) -> Optional[Dict[str, ValidationRule]]:          
        
        
        """
        Obtiene un esquema registrado.
        
        Args:
            name: Nombre del esquema
        
        Returns:
            Esquema registrado o None si no existe
        """
        return self._schemas.get(name)