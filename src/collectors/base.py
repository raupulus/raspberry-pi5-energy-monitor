"""Definición del protocolo base para colectores de telemetría."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseCollector(ABC, Generic[T]):
    """Interfaz abstracta para componentes colectores de métricas."""

    @abstractmethod
    def collect(self) -> T | None:
        """Obtiene y retorna una muestra del sensor o métrica.

        Retorna None si el hardware o módulo no está disponible.
        """
        raise NotImplementedError
