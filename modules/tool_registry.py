# """
# Tool Registry Module for Universal AI Agents
# SIMPLIFIED VERSION - Rock solid tools!
# """

# import os
# import requests
# import logging
# from typing import Dict, List, Any, Optional
# from dataclasses import dataclass

# logger = logging.getLogger(__name__)

# @dataclass
# class Tool:
#     name: str
#     description: str
#     parameters: Dict[str, Any]
#     function: callable

# class ToolRegistry:
#     def __init__(self, knowledge_base):
#         self.tools = {}
#         self.knowledge_base = knowledge_base
#         self._register_tools()
#         logger.info("🛠️ Tools registered!")

#     def _register_tools(self):
#         """Register all tools"""

#         # Knowledge Base Tools
#         if self.knowledge_base:
#             self.register_tool(Tool(
#                 name="search_knowledge",
#                 description="Search the knowledge base.",
#                 parameters={
#                     "query": {"type": "string", "description": "Search query", "required": True}
#                 },
#                 function=self._search_knowledge
#             ))

#         # Web Search Tools
#         self.register_tool(Tool(
#             name="web_search",
#             description="Search the web for information.",
#             parameters={
#                 "query": {"type": "string", "description": "Search query", "required": True}
#             },
#             function=self._web_search
#         ))

#         # Crypto Tools
#         self.register_tool(Tool(
#             name="get_crypto_price",
#             description="Get cryptocurrency prices.",
#             parameters={
#                 "symbol": {"type": "string", "description": "Crypto symbol", "default": "bitcoin"}
#             },
#             function=self._get_crypto_price
#         ))

#         # News Tools
#         self.register_tool(Tool(
#             name="get_news",
#             description="Get latest news.",
#             parameters={
#                 "topic": {"type": "string", "description": "News topic", "default": None},
#                 "count": {"type": "integer", "description": "Number of articles", "default": 3}
#             },
#             function=self._get_news
#         ))

#         # Weather Tools
#         self.register_tool(Tool(
#             name="get_weather",
#             description="Get weather information.",
#             parameters={
#                 "location": {"type": "string", "description": "City name", "required": True}
#             },
#             function=self._get_weather
#         ))

#     def register_tool(self, tool: Tool):
#         self.tools[tool.name] = tool

#     def get_tool(self, name: str) -> Optional[Tool]:
#         return self.tools.get(name)

#     def _search_knowledge(self, query: str) -> str:
#         """Search knowledge base"""
#         if not self.knowledge_base:
#             return "Knowledge base not available!"

#         results = self.knowledge_base.search_knowledge(query, n_results=2)

#         if not results:
#             return "No information found in my knowledge base."

#         response = f"Based on my knowledge:\\n\\n"
#         for i, result in enumerate(results, 1):
#             source_name = os.path.basename(result['source']) if result['type'] != 'website' else result['source']
#             response += f"{i}. From {result['type']} '{source_name}':\\n"
#             response += f"   {result['content'][:150]}...\\n\\n"

#         return response

#     def _web_search(self, query: str) -> str:
#         """Search the web"""
#         try:
#             # Simple DuckDuckGo search
#             search_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"

#             response = requests.get(search_url, timeout=10)
#             if response.status_code == 200:
#                 data = response.json()

#                 if data.get('Abstract'):
#                     return f"Search result: {data['Abstract']}"
#                 elif data.get('Answer'):
#                     return f"Answer: {data['Answer']}"
#                 elif data.get('Definition'):
#                     return f"Definition: {data['Definition']}"
#                 else:
#                     topics = data.get('RelatedTopics', [])
#                     if topics and len(topics) > 0:
#                         return f"Related info: {topics[0].get('Text', 'No specific results found')}"
#                     else:
#                         return "No specific web results found."

#             return "Web search temporarily unavailable."

#         except Exception as e:
#             logger.error(f"Web search failed: {e}")
#             return f"Web search had an issue."

#     def _get_crypto_price(self, symbol: str = "bitcoin") -> str:
#         """Get crypto prices"""
#         try:
#             response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true", timeout=10)
#             if response.status_code == 200:
#                 data = response.json()
#                 if symbol in data:
#                     price = data[symbol]["usd"]
#                     change = data[symbol].get("usd_24h_change", 0)
#                     change_text = f"({change:+.2f}%)" if change else ""
#                     return f"{symbol.title()} is priced at ${price:,} {change_text}"
#             return f"Could not fetch {symbol} price."
#         except Exception as e:
#             logger.error(f"Crypto price error: {e}")
#             return f"Error fetching {symbol} price."

#     def _get_news(self, topic: str = None, count: int = 3) -> str:
#         """Get news"""
#         try:
#             # Try NewsAPI if available
#             newsapi_key = os.getenv("NEWSAPI_KEY")
#             if newsapi_key:
#                 if topic and ("bitcoin" in topic.lower() or "crypto" in topic.lower()):
#                     url = f"https://newsapi.org/v2/everything?q=bitcoin+cryptocurrency&sortBy=publishedAt&language=en&apiKey={newsapi_key}"
#                 else:
#                     url = f"https://newsapi.org/v2/top-headlines?country=us&language=en&apiKey={newsapi_key}"

#                 response = requests.get(url, timeout=10)
#                 if response.status_code == 200:
#                     articles = response.json().get("articles", [])[:count]
#                     if articles:
#                         news_items = []
#                         for i, article in enumerate(articles, 1):
#                             title = article.get('title', '')
#                             news_items.append(f"{i}. {title}")
#                         return "Latest news:\\n" + "\\n".join(news_items)

#             # Fallback to web search
#             return self._web_search(f"latest news {topic}" if topic else "latest news today")

#         except Exception as e:
#             logger.error(f"News error: {e}")
#             return f"News temporarily unavailable."

#     def _get_weather(self, location: str) -> str:
#         """Get weather"""
#         try:
#             weather_api_key = os.getenv("WEATHER_API_KEY")
#             if weather_api_key:
#                 url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={weather_api_key}&units=metric"
#                 response = requests.get(url, timeout=10)

#                 if response.status_code == 200:
#                     data = response.json()
#                     temp = data['main']['temp']
#                     description = data['weather'][0]['description']
#                     humidity = data['main']['humidity']
#                     return f"Weather in {location}: {temp}°C, {description}, humidity {humidity}%"

#             # Fallback to web search
#             return self._web_search(f"weather in {location} today")

#         except Exception as e:
#             logger.error(f"Weather error: {e}")
#             return f"Weather info temporarily unavailable."

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
        """Register a new tool"""
        self.tools[tool.name] = tool
        logger.info(f"🔧 Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all available tools"""
        return list(self.tools.keys())

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool with given parameters"""
        tool = self.get_tool(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found!"
        
        try:
            logger.info(f"🔧 Executing tool: {tool_name} with params: {kwargs}")
            result = tool.function(**kwargs)
            logger.info(f"✅ Tool result: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Tool execution error for {tool_name}: {e}")
            return f"Error executing {tool_name}: {str(e)}"

    def get_tools_for_llm(self) -> List[Dict]:
        """Get tools formatted for LLM function calling"""
        tools_list = []
        for tool_name, tool in self.tools.items():
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # Add parameters
            for param_name, param_info in tool.parameters.items():
                tool_def["function"]["parameters"]["properties"][param_name] = {
                    "type": param_info["type"],
                    "description": param_info["description"]
                }
                
                if param_info.get("required", False):
                    tool_def["function"]["parameters"]["required"].append(param_name)
            
            tools_list.append(tool_def)
        
        return tools_list

    def _search_knowledge(self, query: str) -> str:
        """Search knowledge base"""
        if not self.knowledge_base:
            return "Knowledge base not available!"

        try:
            logger.info(f"🔍 Searching knowledge base for: {query}")
            results = self.knowledge_base.search_knowledge(query, n_results=2)

            if not results:
                return "No information found in my knowledge base."

            response = f"Based on my knowledge:\\n\\n"
            for i, result in enumerate(results, 1):
                source_name = os.path.basename(result['source']) if result['type'] != 'website' else result['source']
                response += f"{i}. From {result['type']} '{source_name}':\\n"
                response += f"   {result['content'][:150]}...\\n\\n"

            return response
        except Exception as e:
            logger.error(f"Knowledge search error: {e}")
            return f"Error searching knowledge base: {str(e)}"

    def _web_search(self, query: str) -> str:
        """Search the web"""
        try:
            logger.info(f"🌐 Web searching for: {query}")
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
            return f"Web search had an issue: {str(e)}"

    def _get_crypto_price(self, symbol: str = "bitcoin") -> str:
        """Get crypto prices"""
        try:
            logger.info(f"🪙 Fetching crypto price for symbol: {symbol}")
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true"
            logger.info(f"📡 API URL: {url}")
            
            response = requests.get(url, timeout=10)
            logger.info(f"📊 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📈 API Data: {data}")
                
                if symbol in data:
                    price = data[symbol]["usd"]
                    change = data[symbol].get("usd_24h_change", 0)
                    change_text = f"({change:+.2f}%)" if change else ""
                    result = f"{symbol.title()} is currently priced at ${price:,} {change_text}"
                    logger.info(f"✅ Final result: {result}")
                    return result
                else:
                    logger.warning(f"⚠️ Symbol {symbol} not found in response")
                    return f"Could not find price data for {symbol}."
            else:
                logger.error(f"❌ API request failed: {response.status_code}")
                return f"Could not fetch {symbol} price (API error)."
                
        except Exception as e:
            logger.error(f"❌ Crypto price error: {e}")
            return f"Error fetching {symbol} price: {str(e)}"

    def _get_news(self, topic: str = None, count: int = 3) -> str:
        """Get news"""
        try:
            logger.info(f"📰 Getting news for topic: {topic}")
            
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
            return f"News temporarily unavailable: {str(e)}"

    def _get_weather(self, location: str) -> str:
        """Get weather"""
        try:
            logger.info(f"🌤️ Getting weather for: {location}")
            
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
            return f"Weather info temporarily unavailable: {str(e)}"