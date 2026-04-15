from abc import ABC, abstractmethod
from ..profile import DocumentProfile


class BaseAnalyzer(ABC):
    """
    Interface que todo analisador de documento deve implementar.

    Para adicionar suporte a um novo formato (ex: DOCX, XLSX),
    basta criar uma nova classe que herda de BaseAnalyzer.
    """

    @abstractmethod
    def can_analyze(self, file_path: str) -> bool:
        """
        Retorna True se este analisador é capaz de processar o arquivo.

        Args:
            file_path: Caminho do arquivo a ser verificado.
        """
        ...

    @abstractmethod
    def analyze(self, file_path: str) -> DocumentProfile:
        """
        Analisa o documento e retorna seu perfil padronizado.

        Args:
            file_path: Caminho do arquivo.

        Returns:
            DocumentProfile com todas as características detectadas.
        """
        ...
