"""
task_manager.py - Gestor de Tareas Concurrente para KR-Studio

Esta clase proporciona un sistema robusto para manejar operaciones en segundo
plano utilizando un pool de hilos. Permite ejecutar tareas de diferentes
tipos de forma controlada para evitar conflictos de concurrencia.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum, auto
from typing import Callable, Any

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Define los tipos de tareas para un control de concurrencia granular."""
    AI_GENERATION = auto()  # Tareas que involucran llamadas a la API de IA
    DIRECTOR_EXECUTION = auto() # Tareas que ejecutan el MasterDirector
    TTS_SYNTHESIS = auto()  # Tareas de generación de audio
    FILE_IO = auto()        # Tareas de lectura/escritura de archivos
    GENERIC = auto()        # Tareas generales


class TaskManager:
    """
    Gestiona la ejecución de tareas en segundo plano de manera concurrente y segura.
    """
    def __init__(self, max_workers: int = 10):
        """
        Inicializa el TaskManager.

        Args:
            max_workers (int): El número máximo de hilos en el pool.
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="KR_Task")
        self.active_tasks: dict[TaskType, list[tuple[Future[Any], str]]] = {task_type: [] for task_type in TaskType}
        logger.info(f"TaskManager inicializado con un máximo de {max_workers} hilos.")

    def submit_task(self, task_func: Callable[..., Any],
                    task_type: TaskType = TaskType.GENERIC,
                    *args: Any, **kwargs: Any) -> Future[Any] | None:
        """
        Envía una tarea para su ejecución en el pool de hilos.

        Permite un control básico para evitar la duplicación de tareas críticas.

        Args:
            task_func (Callable): La función (tarea) a ejecutar.
            task_type (TaskType): El tipo de tarea para control de concurrencia.
            *args: Argumentos posicionales para la función de la tarea.
            **kwargs: Argumentos de palabra clave para la función de la tarea.
        
        Returns:
            Future | None: Un objeto Future que representa la ejecución de la tarea,
                          o None si la tarea fue bloqueada.
        """
        # Regla de concurrencia: No permitir más de una ejecución de director a la vez.
        if task_type == TaskType.DIRECTOR_EXECUTION and self.is_task_type_active(TaskType.DIRECTOR_EXECUTION):
            logger.warning("Se ha bloqueado un intento de iniciar un segundo director mientras uno ya está activo.")
            return None
        
        # Regla de concurrencia: No permitir más de una generación de IA a la vez para evitar conflictos de estado.
        if task_type == TaskType.AI_GENERATION and self.is_task_type_active(TaskType.AI_GENERATION):
            logger.warning("Se ha bloqueado un intento de iniciar una segunda generación de IA mientras una ya está en curso.")
            return None

        logger.info(f"Enviando tarea de tipo '{task_type.name}' al ejecutor.")
        future = self.executor.submit(task_func, *args, **kwargs)
        
        # Registrar la tarea activa
        task_entry = (future, task_func.__name__)
        self.active_tasks[task_type].append(task_entry)
        
        # Añadir un callback para limpiar la tarea cuando se complete
        future.add_done_callback(lambda f: self._task_completed(f, task_type, task_entry))
        
        return future

    def _task_completed(self, future: Future[Any], task_type: TaskType, task_entry: tuple[Future[Any], str]):
        """Callback que se ejecuta cuando una tarea ha finalizado."""
        try:
            # Comprobar si la tarea lanzó una excepción
            exception = future.exception()
            if exception:
                logger.error(f"La tarea '{task_entry[1]}' del tipo '{task_type.name}' ha fallado con una excepción: {exception}",
                             exc_info=exception)
            else:
                logger.info(f"La tarea '{task_entry[1]}' del tipo '{task_type.name}' se ha completado exitosamente.")
        finally:
            # Asegurarse de que la tarea se elimine de la lista de activas
            if task_entry in self.active_tasks[task_type]:
                self.active_tasks[task_type].remove(task_entry)

    def is_task_type_active(self, task_type: TaskType) -> bool:
        """Verifica si hay alguna tarea de un tipo específico en ejecución."""
        return len(self.active_tasks[task_type]) > 0

    def shutdown(self, wait: bool = True):
        """
        Cierra el pool de hilos, esperando a que las tareas actuales se completen.
        """
        logger.info("Cerrando el TaskManager...")
        self.executor.shutdown(wait=wait)
        logger.info("TaskManager cerrado.")

# Ejemplo de uso (esto no se ejecutará directamente aquí)
if __name__ == '__main__':
    import time

    # Crear una instancia del gestor de tareas
    task_manager = TaskManager(max_workers=3)

    # Definir algunas funciones de ejemplo
    def ai_task(duration):
        print("Iniciando tarea de IA...")
        time.sleep(duration)
        print("Tarea de IA finalizada.")
        return "Resultado de IA"

    def director_task():
        print("Iniciando director...")
        time.sleep(4)
        print("Director finalizado.")
        # Simular un error
        raise ValueError("Fallo en el director")

    # Enviar tareas
    task_manager.submit_task(ai_task, TaskType.AI_GENERATION, 2)
    task_manager.submit_task(director_task, TaskType.DIRECTOR_EXECUTION)
    
    # Intentar enviar otro director (debería ser bloqueado)
    task_manager.submit_task(director_task, TaskType.DIRECTOR_EXECUTION)

    # Esperar un poco para que las tareas se ejecuten
    time.sleep(5)

    # Cerrar el gestor
    task_manager.shutdown()
