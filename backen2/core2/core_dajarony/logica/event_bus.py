"""
SUME DOCBLOCK

Nombre: Event Bus
Tipo: Lógica

Entradas:
- Suscripciones a eventos (event_name, callback)
- Emisiones de eventos (event_name, payload)
- Cancelaciones de suscripciones

Acciones:
- Registrar suscriptores para eventos específicos
- Distribuir eventos a los suscriptores correspondientes
- Manejar eventos con comodines (wildcards)
- Ejecutar callbacks de forma síncrona o asíncrona
- Mantener registro de patrones de suscripción
- Proporcionar trazabilidad de eventos emitidos

Salidas:
- Notificaciones a suscriptores
- Resultados de procesamiento asíncrono
- Estadísticas de eventos (opcional)
"""
import asyncio
import fnmatch
import logging
import time
import uuid
from typing import Dict, List, Any, Callable, Union, Set, Optional, Tuple, Coroutine


# Tipos para los callbacks
SyncCallback = Callable[[Any, str], None]  # payload, event_name -> None
AsyncCallback = Callable[[Any], Coroutine[Any, Any, Any]]  # payload -> Coroutine
Callback = Union[SyncCallback, AsyncCallback]


class EventBus:
    """
    Sistema de publicación/suscripción para comunicación desacoplada entre componentes.
    
    Permite a los componentes suscribirse a eventos específicos y ser notificados
    cuando estos ocurren, sin crear dependencias directas entre ellos.
    """

    def __init__(self, logger=None):
        """
        Inicializa un nuevo EventBus.
        
        Args:
            logger: Logger opcional para registrar actividad. Si es None, se crea uno.
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Mapa de suscriptores por evento
        self._subscribers: Dict[str, List[Tuple[str, Callback]]] = {}
        
        # Conjunto de patrones de suscripción para búsqueda rápida
        self._patterns: Set[str] = set()
        
        # Estadísticas de eventos para diagnóstico
        self._stats: Dict[str, int] = {
            'events_emitted': 0,
            'events_processed': 0,
            'subscribers_notified': 0,
        }
        
        self.logger.debug("EventBus inicializado")

    def on(self, event_pattern: str, callback: Callback) -> str:
        """
        Suscribe un callback a eventos que coincidan con el patrón.
        
        Args:
            event_pattern: Nombre del evento o patrón con comodines (e.g., 'user:*')
            callback: Función a llamar cuando ocurra el evento. Puede ser síncrona o asíncrona.
                     Las funciones síncronas recibirán (payload, event_name).
                     Las funciones asíncronas recibirán solo payload.
        
        Returns:
            ID de suscripción que puede usarse para cancelar la suscripción
        """
        # Generar ID único para la suscripción
        subscription_id = str(uuid.uuid4())
        
        # Registrar la suscripción
        if event_pattern not in self._subscribers:
            self._subscribers[event_pattern] = []
        
        self._subscribers[event_pattern].append((subscription_id, callback))
        
        # Si tiene comodines, registrar como patrón
        if '*' in event_pattern:
            self._patterns.add(event_pattern)
        
        self.logger.debug(f"Suscripción registrada: {event_pattern} -> {subscription_id}")
        return subscription_id

    def off(self, subscription_id: str) -> bool:
        """
        Cancela una suscripción específica.
        
        Args:
            subscription_id: ID de la suscripción a cancelar
        
        Returns:
            True si se encontró y canceló la suscripción, False en caso contrario
        """
        # Buscar la suscripción en todos los eventos
        for event_pattern, subscribers in self._subscribers.items():
            for i, (sub_id, _) in enumerate(subscribers):
                if sub_id == subscription_id:
                    # Eliminar la suscripción
                    subscribers.pop(i)
                    self.logger.debug(f"Suscripción cancelada: {subscription_id} de {event_pattern}")
                    
                    # Si no quedan suscriptores para este evento, eliminar la clave
                    if not subscribers:
                        del self._subscribers[event_pattern]
                        if event_pattern in self._patterns:
                            self._patterns.remove(event_pattern)
                    
                    return True
        
        self.logger.warning(f"Intento de cancelar suscripción inexistente: {subscription_id}")
        return False

    def emit(self, event_name: str, payload: Any = None) -> int:
        """
        Emite un evento síncronamente a todos los suscriptores correspondientes.
        
        Args:
            event_name: Nombre del evento a emitir
            payload: Datos asociados al evento
        
        Returns:
            Número de suscriptores notificados
        """
        start_time = time.perf_counter()
        subscribers_notified = 0
        
        # Actualizar estadísticas
        self._stats['events_emitted'] += 1
        
        # Log del evento
        self.logger.debug(f"Emitiendo evento: {event_name}")
        
        # Buscar suscriptores directos
        direct_subscribers = self._get_subscribers_for_event(event_name)
        
        # Notificar a cada suscriptor
        for _, callback in direct_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # Para callbacks asíncronos, creamos una tarea pero no esperamos
                    asyncio.create_task(callback(payload))
                else:
                    # Para callbacks síncronos, llamamos directamente
                    callback(payload, event_name)
                
                subscribers_notified += 1
            except Exception as e:
                self.logger.error(f"Error en suscriptor de {event_name}: {str(e)}")
        
        # Actualizar estadísticas
        self._stats['subscribers_notified'] += subscribers_notified
        self._stats['events_processed'] += 1
        
        # Log de rendimiento si hay muchos suscriptores o toma mucho tiempo
        duration_ms = (time.perf_counter() - start_time) * 1000
        if subscribers_notified > 5 or duration_ms > 10:
            self.logger.debug(f"Evento {event_name}: {subscribers_notified} suscriptores, {duration_ms:.2f}ms")
        
        return subscribers_notified

    async def emit_async(self, event_name: str, payload: Any = None) -> List[Any]:
        """
        Emite un evento asíncronamente y espera a que todos los suscriptores asíncronos terminen.
        
        Args:
            event_name: Nombre del evento a emitir
            payload: Datos asociados al evento
        
        Returns:
            Lista de resultados de los callbacks asíncronos (puede incluir None)
        """
        start_time = time.perf_counter()
        
        # Actualizar estadísticas
        self._stats['events_emitted'] += 1
        
        # Log del evento
        self.logger.debug(f"Emitiendo evento asíncrono: {event_name}")
        
        # Buscar suscriptores
        direct_subscribers = self._get_subscribers_for_event(event_name)
        
        # Resultados y tareas
        results = []
        tasks = []
        
        # Procesar suscriptores
        for _, callback in direct_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # Crear tarea para callbacks asíncronos
                    task = asyncio.create_task(callback(payload))
                    tasks.append(task)
                else:
                    # Llamar síncronamente a los callbacks síncronos
                    callback(payload, event_name)
                    results.append(None)  # No hay resultado para callbacks síncronos
                
                self._stats['subscribers_notified'] += 1
            except Exception as e:
                self.logger.error(f"Error en suscriptor de {event_name}: {str(e)}")
                results.append(None)
        
        # Esperar a que terminen todas las tareas asíncronas
        if tasks:
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in completed_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Error asíncrono en suscriptor de {event_name}: {str(result)}")
                    results.append(None)
                else:
                    results.append(result)
        
        # Actualizar estadísticas
        self._stats['events_processed'] += 1
        
        # Log de rendimiento
        duration_ms = (time.perf_counter() - start_time) * 1000
        self.logger.debug(
            f"Evento asíncrono {event_name} completado: {len(direct_subscribers)} suscriptores, {duration_ms:.2f}ms"
        )
        
        return results

    def _get_subscribers_for_event(self, event_name: str) -> List[Tuple[str, Callback]]:
        """
        Obtiene todos los suscriptores que deben ser notificados para un evento.
        
        Args:
            event_name: Nombre del evento
        
        Returns:
            Lista de tuplas (subscription_id, callback)
        """
        subscribers = []
        
        # Añadir suscriptores directos
        if event_name in self._subscribers:
            subscribers.extend(self._subscribers[event_name])
        
        # Buscar patrones que coincidan
        for pattern in self._patterns:
            if fnmatch.fnmatch(event_name, pattern):
                subscribers.extend(self._subscribers[pattern])
        
        return subscribers

    def get_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas del EventBus para diagnóstico.
        
        Returns:
            Diccionario con estadísticas
        """
        # Añadir número actual de suscripciones
        stats = self._stats.copy()
        total_subscribers = sum(len(subs) for subs in self._subscribers.values())
        stats['active_subscriptions'] = total_subscribers
        stats['event_patterns'] = len(self._subscribers)
        return stats

    def clear(self) -> None:
        """
        Elimina todas las suscripciones.
        Útil para limpiar entre pruebas o al reiniciar componentes.
        """
        self._subscribers.clear()
        self._patterns.clear()
        self.logger.debug("Todas las suscripciones eliminadas")

    def get_subscribers_count(self, event_pattern: Optional[str] = None) -> int:
        """
        Obtiene el número de suscriptores para un patrón de evento específico o en total.
        
        Args:
            event_pattern: Patrón de evento específico o None para contar todos
            
        Returns:
            Número de suscriptores
        """
        if event_pattern is None:
            # Contar todos los suscriptores
            return sum(len(subs) for subs in self._subscribers.values())
        elif event_pattern in self._subscribers:
            # Contar suscriptores para un patrón específico
            return len(self._subscribers[event_pattern])
        else:
            return 0