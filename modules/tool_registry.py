"""
Tool Registry Module for Universal AI Agents
SIMPLIFIED VERSION - Rock solid tools!
"""

import os
import requests
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: callable

class ToolRegistry:
    def __init__(self, knowledge_base):
        self.tools = {}
        self.knowledge_base = knowledge_base
        self._register_tools()
        logger.info("🛠️ Tools registered!")

    def _register_tools(self):
        """Register all tools"""

        # Knowledge Base Tools
        if self.knowledge_base:
            self.register_tool(Tool(
                name="search_knowledge",
                description="Search the knowledge base.",
                parameters={
                    "query": {"type": "string", "description": "Search query", "required": True}
                },
                function=self._search_knowledge
            ))

        # Web Search Tools
        self.register_tool(Tool(
            name="web_search",
            description="Search the web for information.",
            parameters={
                "query": {"type": "string", "description": "Search query", "required": True}
            },
            function=self._web_search
        ))

        # Crypto Tools
        self.register_tool(Tool(
            name="get_crypto_price",
            description="Get cryptocurrency prices.",
            parameters={
                "symbol": {"type": "string", "description": "Crypto symbol", "default": "bitcoin"}
            },
            function=self._get_crypto_price
        ))

        # News Tools
        self.register_tool(Tool(
            name="get_news",
            description="Get latest news.",
            parameters={
                "topic": {"type": "string", "description": "News topic", "default": None},
                "count": {"type": "integer", "description": "Number of articles", "default": 3}
            },
            function=self._get_news
        ))

        # Weather Tools
        self.register_tool(Tool(
            name="get_weather",
            description="Get weather information.",
            parameters={
                "location": {"type": "string", "description": "City name", "required": True}
            },
            function=self._get_weather
        ))

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def _search_knowledge(self, query: str) -> str:
        """Search knowledge base"""
        if not self.knowledge_base:
            return "Knowledge base not available!"

        results = self.knowledge_base.search_knowledge(query, n_results=2)

        if not results:
            return "No information found in my knowledge base."

        response = f"Based on my knowledge:\\n\\n"
        for i, result in enumerate(results, 1):
            source_name = os.path.basename(result['source']) if result['type'] != 'website' else result['source']
            response += f"{i}. From {result['type']} '{source_name}':\\n"
            response += f"   {result['content'][:150]}...\\n\\n"

        return response

    def _web_search(self, query: str) -> str:
        """Search the web"""
        try:
            # Simple DuckDuckGo search
            search_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"

            response = requests.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()

                if data.get('Abstract'):
                    return f"Search result: {data['Abstract']}"
                elif data.get('Answer'):
                    return f"Answer: {data['Answer']}"
                elif data.get('Definition'):
                    return f"Definition: {data['Definition']}"
                else:
                    topics = data.get('RelatedTopics', [])
                    if topics and len(topics) > 0:
                        return f"Related info: {topics[0].get('Text', 'No specific results found')}"
                    else:
                        return "No specific web results found."

            return "Web search temporarily unavailable."

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"Web search had an issue."

    def _get_crypto_price(self, symbol: str = "bitcoin") -> str:
        """Get crypto prices"""
        try:
            response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if symbol in data:
                    price = data[symbol]["usd"]
                    change = data[symbol].get("usd_24h_change", 0)
                    change_text = f"({change:+.2f}%)" if change else ""
                    return f"{symbol.title()} is priced at ${price:,} {change_text}"
            return f"Could not fetch {symbol} price."
        except Exception as e:
            logger.error(f"Crypto price error: {e}")
            return f"Error fetching {symbol} price."

    def _get_news(self, topic: str = None, count: int = 3) -> str:
        """Get news"""
        try:
            # Try NewsAPI if available
            newsapi_key = os.getenv("NEWSAPI_KEY")
            if newsapi_key:
                if topic and ("bitcoin" in topic.lower() or "crypto" in topic.lower()):
                    url = f"https://newsapi.org/v2/everything?q=bitcoin+cryptocurrency&sortBy=publishedAt&language=en&apiKey={newsapi_key}"
                else:
                    url = f"https://newsapi.org/v2/top-headlines?country=us&language=en&apiKey={newsapi_key}"

                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    articles = response.json().get("articles", [])[:count]
                    if articles:
                        news_items = []
                        for i, article in enumerate(articles, 1):
                            title = article.get('title', '')
                            news_items.append(f"{i}. {title}")
                        return "Latest news:\\n" + "\\n".join(news_items)

            # Fallback to web search
            return self._web_search(f"latest news {topic}" if topic else "latest news today")

        except Exception as e:
            logger.error(f"News error: {e}")
            return f"News temporarily unavailable."

    def _get_weather(self, location: str) -> str:
        """Get weather"""
        try:
            weather_api_key = os.getenv("WEATHER_API_KEY")
            if weather_api_key:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={weather_api_key}&units=metric"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    temp = data['main']['temp']
                    description = data['weather'][0]['description']
                    humidity = data['main']['humidity']
                    return f"Weather in {location}: {temp}°C, {description}, humidity {humidity}%"

            # Fallback to web search
            return self._web_search(f"weather in {location} today")

        except Exception as e:
            logger.error(f"Weather error: {e}")
            return f"Weather info temporarily unavailable."