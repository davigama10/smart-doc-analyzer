from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .profile import DocumentProfile, ProcessingRecommendation
from .analyzers.base import BaseAnalyzer
from .analyzers.pdf import PDFAnalyzer
from .analyzers.image import ImageAnalyzer
from .router.base import BaseRouter
from .router.rule_based import RuleBasedRouter


@dataclass
class FullAnalysisResult:
    """Resultado completo com perfil + recomendação por regras + recomendação da LLM."""
    profile: DocumentProfile
    rule_recommendation: ProcessingRecommendation
    llm_recommendation: ProcessingRecommendation


class DocAnalyzer:
    """
    Ponto de entrada principal do smart-doc-analyzer.

    Detecta automaticamente o tipo do arquivo, seleciona o analisador
    correto e, opcionalmente, roteia o documento para o modelo ideal.

    Uso básico (regras + LLM):
        analyzer = DocAnalyzer(routes_config="routes.json", use_llm=True)
        result = analyzer.analyze_and_route_full("documento.pdf")
        print(result.rule_recommendation.tier)
        print(result.llm_recommendation.tier)

    Uso apenas com regras:
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
        use_llm: bool = False,
        llm_router: Optional[BaseRouter] = None,
        llm_api_key: Optional[str] = None,
        use_ollama: bool = False,
        ollama_model: str = "llama3.2",
        ollama_host: str = "http://host.docker.internal:11434",
    ):
        """
        Args:
            routes_config: Caminho para o JSON de rotas (usa RuleBasedRouter).
            router:        Instância de BaseRouter customizado para regras.
                           Se fornecido, ignora routes_config.
            use_llm:       Se True, instancia um LLMRouter (Claude/Anthropic).
            llm_router:    Instância de BaseRouter customizado para LLM.
                           Se fornecido, ignora use_llm e use_ollama.
            llm_api_key:   Chave da API Anthropic. Se None, usa ANTHROPIC_API_KEY do ambiente.
            use_ollama:    Se True, instancia um OllamaRouter (LLM local, gratuito).
            ollama_model:  Modelo Ollama a usar (ex: llama3.2, qwen2.5:3b, mistral).
            ollama_host:   URL do servidor Ollama.
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

        if llm_router:
            self._llm_router: Optional[BaseRouter] = llm_router
        elif use_ollama:
            from .router.ollama_router import OllamaRouter
            self._llm_router = OllamaRouter(model=ollama_model, host=ollama_host)
        elif use_llm:
            from .router.llm_router import LLMRouter
            self._llm_router = LLMRouter(api_key=llm_api_key)
        else:
            self._llm_router = None

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
        Analisa o documento e retorna perfil + recomendação de processamento (regras).

        Args:
            file_path: Caminho do arquivo.

        Returns:
            Tupla (DocumentProfile, ProcessingRecommendation).
        """
        profile = self.analyze(file_path)
        recommendation = self.route(profile)
        return profile, recommendation

    def analyze_and_route_full(self, file_path: str) -> FullAnalysisResult:
        """
        Analisa o documento e retorna perfil + recomendação por regras + recomendação da LLM.

        Requer que o DocAnalyzer tenha sido instanciado com use_llm=True (ou llm_router).
        Requer também um roteador de regras (routes_config ou router).

        Args:
            file_path: Caminho do arquivo.

        Returns:
            FullAnalysisResult com profile, rule_recommendation e llm_recommendation.

        Raises:
            RuntimeError: Se o roteador de regras ou o LLM router não estiver configurado.
        """
        if not self._router:
            raise RuntimeError(
                "Roteador de regras não configurado. "
                "Passe routes_config ou router ao instanciar DocAnalyzer."
            )
        if not self._llm_router:
            raise RuntimeError(
                "LLM router não configurado. "
                "Passe use_llm=True ou llm_router ao instanciar DocAnalyzer."
            )

        profile = self.analyze(file_path)
        rule_rec = self._router.route(profile)
        llm_rec = self._llm_router.route(profile)

        return FullAnalysisResult(
            profile=profile,
            rule_recommendation=rule_rec,
            llm_recommendation=llm_rec,
        )

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
