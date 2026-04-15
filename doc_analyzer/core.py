from pathlib import Path
from typing import Optional, Tuple

from .profile import DocumentProfile, ProcessingRecommendation
from .analyzers.base import BaseAnalyzer
from .analyzers.pdf import PDFAnalyzer
from .analyzers.image import ImageAnalyzer
from .router.base import BaseRouter
from .router.rule_based import RuleBasedRouter


class DocAnalyzer:
    """
    Ponto de entrada principal do smart-doc-analyzer.

    Detecta automaticamente o tipo do arquivo, seleciona o analisador
    correto e, opcionalmente, roteia o documento para o modelo ideal.

    Uso básico:
        analyzer = DocAnalyzer(routes_config="routes.json")
        profile, recommendation = analyzer.analyze_and_route("documento.pdf")

    Uso apenas para análise (sem roteamento):
        analyzer = DocAnalyzer()
        profile = analyzer.analyze("documento.pdf")

    Extensibilidade:
        # Registrar um analisador customizado
        analyzer.register_analyzer(MyDocxAnalyzer())

        # Usar um roteador customizado
        analyzer = DocAnalyzer(router=MyMLRouter())
    """

    def __init__(
        self,
        routes_config: Optional[str] = None,
        router: Optional[BaseRouter] = None,
    ):
        """
        Args:
            routes_config: Caminho para o JSON de rotas (usa RuleBasedRouter).
            router: Instância de BaseRouter customizado. Se fornecido, ignora routes_config.
        """
        self._analyzers: list[BaseAnalyzer] = [
            PDFAnalyzer(),
            ImageAnalyzer(),
        ]

        if router:
            self._router: Optional[BaseRouter] = router
        elif routes_config:
            self._router = RuleBasedRouter(routes_config)
        else:
            self._router = None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def analyze(self, file_path: str) -> DocumentProfile:
        """
        Analisa o documento e retorna seu perfil.

        Args:
            file_path: Caminho do arquivo (PDF, PNG, JPG, TIFF...).

        Returns:
            DocumentProfile com todas as características detectadas.

        Raises:
            ValueError: Se o formato do arquivo não for suportado.
            FileNotFoundError: Se o arquivo não existir.
        """
        self._validate_file(file_path)
        analyzer = self._select_analyzer(file_path)
        return analyzer.analyze(file_path)

    def route(self, profile: DocumentProfile) -> ProcessingRecommendation:
        """
        Roteia um DocumentProfile já calculado.

        Args:
            profile: Perfil do documento.

        Returns:
            ProcessingRecommendation.

        Raises:
            RuntimeError: Se nenhum roteador foi configurado.
        """
        if not self._router:
            raise RuntimeError(
                "Nenhum roteador configurado. "
                "Passe routes_config ou router ao instanciar DocAnalyzer."
            )
        return self._router.route(profile)

    def analyze_and_route(
        self, file_path: str
    ) -> Tuple[DocumentProfile, ProcessingRecommendation]:
        """
        Analisa o documento e retorna perfil + recomendação de processamento.

        Args:
            file_path: Caminho do arquivo.

        Returns:
            Tupla (DocumentProfile, ProcessingRecommendation).
        """
        profile = self.analyze(file_path)
        recommendation = self.route(profile)
        return profile, recommendation

    def register_analyzer(self, analyzer: BaseAnalyzer) -> None:
        """
        Registra um analisador customizado para novos formatos.
        Analisadores customizados têm prioridade sobre os padrão.

        Args:
            analyzer: Instância de BaseAnalyzer.
        """
        self._analyzers.insert(0, analyzer)

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _select_analyzer(self, file_path: str) -> BaseAnalyzer:
        for analyzer in self._analyzers:
            if analyzer.can_analyze(file_path):
                return analyzer
        ext = Path(file_path).suffix.lower()
        raise ValueError(f"Formato não suportado: '{ext}'. Registre um analisador customizado.")

    def _validate_file(self, file_path: str) -> None:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        if not path.is_file():
            raise ValueError(f"O caminho não aponta para um arquivo: {file_path}")
