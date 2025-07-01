from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .base import AIProviderStrategy
from .openai_strategy import OpenAIStrategy
from .gemini_strategy import GeminiStrategy
from .cortex_strategy import CortexStrategy


class AIManager:
    """
    Главный класс для управления различными AI-провайдерами.
    Использует паттерн "Стратегия" для переключения между провайдерами.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Инициализирует AIManager с доступными стратегиями.
        
        Args:
            db_session: Асинхронная сессия базы данных для Cortex стратегии
        """
        self._strategies: Dict[str, AIProviderStrategy] = {}
        self._db_session = db_session
        
        # Инициализируем доступные стратегии
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """
        Инициализирует все доступные стратегии AI-провайдеров.
        """
        try:
            # OpenAI стратегия
            openai_strategy = OpenAIStrategy()
            if openai_strategy.validate_configuration():
                self._strategies["openai"] = openai_strategy
        except Exception as e:
            print(f"Warning: OpenAI strategy initialization failed: {e}")
        
        try:
            # Gemini стратегия
            gemini_strategy = GeminiStrategy()
            if gemini_strategy.validate_configuration():
                self._strategies["gemini"] = gemini_strategy
        except Exception as e:
            print(f"Warning: Gemini strategy initialization failed: {e}")
        
        try:
            # Cortex стратегия (не требует db_session для REST API)
            cortex_strategy = CortexStrategy()
            if cortex_strategy.validate_configuration():
                self._strategies["cortex"] = cortex_strategy
        except Exception as e:
            print(f"Warning: Cortex strategy initialization failed: {e}")
    
    async def generate_response(self, provider: str, prompt: str, **kwargs) -> str:
        """
        Генерирует ответ используя указанный провайдер.
        
        Args:
            provider: Название провайдера ("openai", "gemini", "cortex")
            prompt: Текст запроса
            **kwargs: Дополнительные параметры для конкретного провайдера
            
        Returns:
            str: Сгенерированный ответ
            
        Raises:
            ValueError: Если указанный провайдер не поддерживается
            Exception: При ошибке генерации ответа
        """
        if provider not in self._strategies:
            available_providers = list(self._strategies.keys())
            raise ValueError(
                f"Unsupported AI provider: {provider}. "
                f"Available providers: {available_providers}"
            )
        
        strategy = self._strategies[provider]
        return await strategy.generate_response(prompt, **kwargs)
    
    async def generate_sql_from_question(self, provider: str, question: str, semantic_model: str) -> str:
        """
        Специализированный метод для генерации SQL из вопроса на естественном языке.
        
        Args:
            provider: Название провайдера
            question: Вопрос на естественном языке
            semantic_model: Семантическая модель базы данных
            
        Returns:
            str: Сгенерированный SQL запрос
        """
        if provider not in self._strategies:
            available_providers = list(self._strategies.keys())
            raise ValueError(
                f"Unsupported AI provider: {provider}. "
                f"Available providers: {available_providers}"
            )
        
        strategy = self._strategies[provider]
        
        # Проверяем, поддерживает ли стратегия специализированный метод
        if hasattr(strategy, 'generate_sql_from_question'):
            return await strategy.generate_sql_from_question(question, semantic_model)
        else:
            # Используем общий метод с системным промптом
            system_prompt = f"""
            You are an expert PostgreSQL data analyst. Your task is to convert a user's question in natural language into a valid PostgreSQL query.
            You must only respond with the SQL query and nothing else. Do not add explanations, comments, or any surrounding text.
            The database has the following schema, defined by this semantic model:

            --- SEMANTIC MODEL START ---
            {semantic_model}
            --- SEMANTIC MODEL END ---

            - The query must be compatible with PostgreSQL.
            - Only use tables and columns defined in the semantic model above.
            - Use the relationships defined in the model to correctly join tables.
            - If the question cannot be answered with the given schema, respond with "I cannot answer this question."
            """
            
            return await strategy.generate_response(
                question,
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=500
            )
    
    def get_available_providers(self) -> List[str]:
        """
        Возвращает список доступных провайдеров.
        
        Returns:
            List[str]: Список названий доступных провайдеров
        """
        return list(self._strategies.keys())
    
    def is_provider_available(self, provider: str) -> bool:
        """
        Проверяет, доступен ли указанный провайдер.
        
        Args:
            provider: Название провайдера
            
        Returns:
            bool: True если провайдер доступен, False в противном случае
        """
        return provider in self._strategies
    
    def get_provider_info(self, provider: str) -> Optional[Dict]:
        """
        Возвращает информацию о провайдере.
        
        Args:
            provider: Название провайдера
            
        Returns:
            Optional[Dict]: Информация о провайдере или None если не найден
        """
        if provider not in self._strategies:
            return None
        
        strategy = self._strategies[provider]
        return {
            "name": strategy.get_provider_name(),
            "available": strategy.validate_configuration(),
            "type": type(strategy).__name__
        } 