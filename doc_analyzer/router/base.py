from abc import ABC, abstractmethod
from ..profile import DocumentProfile, ProcessingRecommendation


class BaseRouter(ABC):
    """
    Interface que todo roteador deve implementar.

    Para criar uma estratégia de roteamento customizada
    (ex: baseada em ML, custo, SLA), basta herdar desta classe.
    """

    @abstractmethod
    def route(self, profile: DocumentProfile) -> ProcessingRecommendation:
        """
        Recebe o perfil do documento e retorna a recomendação de processamento.

        Args:
            profile: DocumentProfile gerado pelo analisador.

        Returns:
            ProcessingRecommendation com tier, modelo e justificativa.
        """
        ...
