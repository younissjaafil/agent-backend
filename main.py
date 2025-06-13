 
"""
Universal AI Agent System - Complete Web API Server
FastAPI wrapper with full tool integration
"""

import os
import sys
import json
import logging
import openai
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import your existing modules
try:
    from modules.agent_config import AgentConfig
    from modules.knowledge_base import KnowledgeBase
    from modules.tool_registry import ToolRegistry
    from modules.voice_cloner import VoiceCloner
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    logger.error("Make sure all modules are in the correct directories")
    sys.exit(1)

# Universal Agent Class (missing from your uploads)
class UniversalAgent:
    """Universal AI Agent with full tool integration"""
    
    def __init__(self, config):
        self.config = config
        self.name = config['name']
        self.tone = config.get('tone', 'friendly')
        self.interests = config.get('interests', [])
        self.voice_id = config.get('voice_id')
        self.api_keys = config['api_keys']
        
        # Initialize OpenAI
        openai.api_key = self.api_keys['OPENAI_API_KEY']
        
        # Initialize components
        self._initialize_components()
        
        # Memory
        self.memory = []
        self.load_memory()
        
    def _initialize_components(self):
        """Initialize knowledge base and tools"""
        try:
            # Initialize knowledge base with user-specific knowledge
            knowledge_user = self.config.get('knowledge_setup', {}).get('knowledge_user', self.name)
            self.knowledge_base = KnowledgeBase(user_name=knowledge_user)
            self.knowledge_base.load_all_knowledge()
            
            # Initialize tool registry
            self.tool_registry = ToolRegistry(self.knowledge_base)
            
            logger.info(f"✅ Components initialized for {self.name}")
            
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            self.knowledge_base = None
            self.tool_registry = None
    
    def load_memory(self):
        """Load conversation memory"""
        try:
            memory_file = f"./memory/{self.name}_memory.json"
            if os.path.exists(memory_file):
                with open(memory_file, "r") as f:
                    self.memory = json.load(f)
                logger.info(f"✅ Loaded {len(self.memory)} previous conversations for {self.name}")
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            self.memory = []
    
    def save_memory(self):
        """Save conversation memory"""
        try:
            os.makedirs("./memory", exist_ok=True)
            memory_file = f"./memory/{self.name}_memory.json"
            
            with open(memory_file, "w") as f:
                json.dump(self.memory, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def build_personality_prompt(self):
        """Build the personality prompt for the agent"""
        interests_text = ", ".join(self.interests) if self.interests else "general topics"
        
        prompt = f"""You are {self.name}, an AI assistant with the following personality:

TONE: {self.tone}
INTERESTS: {interests_text}

BEHAVIOR GUIDELINES:
- Always stay in character as {self.name}
- Maintain your {self.tone} tone throughout conversations
- Draw upon your interests when relevant
- Use tools when appropriate to provide accurate information
- Keep responses engaging and helpful
- Remember previous conversations when possible

Available tools: search_knowledge, web_search, get_crypto_price, get_news, get_weather

Respond naturally as {self.name} would, incorporating your personality traits into every interaction."""
        
        return prompt
    
    def detect_tool_usage(self, user_input):
        """Detect if user input requires tool usage"""
        user_lower = user_input.lower()
        
        # Knowledge search triggers
        if any(word in user_lower for word in ['what is', 'tell me about', 'explain', 'define']):
            return 'search_knowledge', user_input
        
        # Web search triggers
        if any(word in user_lower for word in ['search', 'look up', 'find', 'latest']):
            return 'web_search', user_input
        
        # Crypto triggers
        if any(word in user_lower for word in ['bitcoin', 'crypto', 'price', 'btc', 'ethereum']):
            crypto_words = ['bitcoin', 'ethereum', 'btc', 'eth']
            for word in crypto_words:
                if word in user_lower:
                    return 'get_crypto_price', word
            return 'get_crypto_price', 'bitcoin'
        
        # News triggers
        if any(word in user_lower for word in ['news', 'headlines', 'current events']):
            return 'get_news', user_input
        
        # Weather triggers
        if any(word in user_lower for word in ['weather', 'temperature', 'forecast']):
            # Extract location if possible
            words = user_input.split()
            for i, word in enumerate(words):
                if word.lower() in ['in', 'at', 'for']:
                    if i + 1 < len(words):
                        return 'get_weather', words[i + 1]
            return 'get_weather', 'New York'  # Default location
        
        return None, None
    
    def process_with_openai(self, user_input, context=""):
        """Process user input with OpenAI"""
        try:
            # Build conversation history
            messages = [
                {"role": "system", "content": self.build_personality_prompt()}
            ]
            
            # Add recent memory
            for entry in self.memory[-5:]:  # Last 5 conversations
                messages.append({"role": "user", "content": entry.get("user", "")})
                messages.append({"role": "assistant", "content": entry.get("assistant", "")})
            
            # Add context if available
            if context:
                messages.append({"role": "system", "content": f"Additional context: {context}"})
            
            # Add current user input
            messages.append({"role": "user", "content": user_input})
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI processing failed: {e}")
            return f"I'm {self.name}, and I'm having trouble processing that right now. Could you try rephrasing?"
    
    def process_message(self, user_input, conversation_id=None):
        """Process a user message and return response"""
        try:
            logger.info(f"🤖 {self.name} processing: {user_input}")
            
            # Check if tools should be used
            tool_name, tool_query = self.detect_tool_usage(user_input)
            context = ""
            
            if tool_name and self.tool_registry:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    logger.info(f"🛠️ Using tool: {tool_name}")
                    try:
                        if tool_name == 'search_knowledge':
                            context = tool.function(tool_query)
                        elif tool_name == 'web_search':
                            context = tool.function(tool_query)
                        elif tool_name == 'get_crypto_price':
                            context = tool.function(tool_query)
                        elif tool_name == 'get_news':
                            context = tool.function(tool_query)
                        elif tool_name == 'get_weather':
                            context = tool.function(tool_query)
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}")
                        context = ""
            
            # Process with OpenAI
            response = self.process_with_openai(user_input, context)
            
            # Save to memory
            memory_entry = {
                "user": user_input,
                "assistant": response,
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "tool_used": tool_name
            }
            self.memory.append(memory_entry)
            self.save_memory()
            
            return response
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return f"I'm {self.name}, and I encountered an error. Please try again."

# FastAPI app
app = FastAPI(title="Universal AI Agent System API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AgentCreateRequest(BaseModel):
    name: str
    personality: str
    voice_model: Optional[str] = None
    description: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    personality: str
    voice_model: Optional[str]
    description: Optional[str]
    created_at: str

# Global variables
config_manager = AgentConfig()
api_keys = None
active_agents = {}  # Cache for active agents

def get_api_keys():
    """Get API keys from environment"""
    global api_keys
    if api_keys is None:
        openai_key = os.getenv("OPENAI_API_KEY")
        minimax_key = os.getenv("MINIMAX_API_KEY")
        
        if not openai_key or not minimax_key:
            logger.error("❌ MISSING API KEYS!")
            raise HTTPException(status_code=500, detail="Missing API keys")
        
        api_keys = {
            "OPENAI_API_KEY": openai_key,
            "MINIMAX_API_KEY": minimax_key,
            "NEWSAPI_KEY": os.getenv("NEWSAPI_KEY"),
            "WEATHER_API_KEY": os.getenv("WEATHER_API_KEY")
        }
    
    return api_keys

def get_or_create_agent(agent_id: str):
    """Get or create an agent instance"""
    if agent_id not in active_agents:
        agent_config = config_manager.load_agent(agent_id)
        if not agent_config:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update API keys
        agent_config['api_keys'] = get_api_keys()
        
        # Create agent instance
        active_agents[agent_id] = UniversalAgent(agent_config)
    
    return active_agents[agent_id]

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Universal AI Agent System API", "version": "1.0.0"}

@app.get("/agents", response_model=List[AgentResponse])
async def get_agents():
    """Get all available agents"""
    try:
        agents = config_manager.list_agents()
        
        response_agents = []
        for agent in agents:
            response_agents.append(AgentResponse(
                id=agent["name"],
                name=agent["name"],
                personality=agent.get("tone", "friendly"),
                voice_model=agent.get("voice_id", "default"),
                description=f"A {agent.get('tone', 'friendly')} AI assistant interested in {', '.join(agent.get('interests', ['general topics']))}",
                created_at=agent.get("created_at", datetime.now().isoformat())
            ))
        
        return response_agents
    
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/agents", response_model=AgentResponse)
async def create_agent(agent_data: AgentCreateRequest):
    """Create a new agent"""
    try:
        logger.info(f"Creating agent: {agent_data.name}")
        
        # Get API keys
        keys = get_api_keys()
        
        # Create a simplified agent configuration for API use
        agent_config = {
            "name": agent_data.name,
            "tone": agent_data.personality or "friendly",
            "interests": ["general conversation", "helping users"],
            "voice_id": agent_data.voice_model or "default",
            "api_keys": keys,
            "created_at": datetime.now().isoformat(),
            "knowledge_setup": {
                "user_knowledge_enabled": True,
                "company_knowledge_enabled": True,
                "knowledge_user": agent_data.name
            }
        }
        
        # Save agent configuration directly (bypass interactive creation)
        agent_file = os.path.join(config_manager.agents_dir, f"{agent_data.name}.json")
        with open(agent_file, 'w') as f:
            json.dump(agent_config, f, indent=2)
        
        # Create user knowledge directory
        user_knowledge_dir = f"./user_knowledge/{agent_data.name}"
        if not os.path.exists(user_knowledge_dir):
            os.makedirs(user_knowledge_dir)
            os.makedirs(f"{user_knowledge_dir}/docs")
            os.makedirs(f"{user_knowledge_dir}/uploads")
        
        # Create welcome file
        welcome_file = f"{user_knowledge_dir}/docs/welcome.txt"
        welcome_content = f"""Welcome to {agent_data.name}'s Knowledge Base!

Agent Profile:
- Name: {agent_data.name}
- Personality: {agent_data.personality or 'friendly'}
- Description: {agent_data.description or 'AI Assistant'}

This agent has access to powerful tools:
- Knowledge search from uploaded documents
- Web search for current information
- Cryptocurrency prices
- Latest news
- Weather information

Created on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        with open(welcome_file, 'w') as f:
            f.write(welcome_content)
        
        logger.info(f"✅ Agent {agent_data.name} created successfully!")
        
        return AgentResponse(
            id=agent_data.name,
            name=agent_data.name,
            personality=agent_data.personality or "friendly",
            voice_model=agent_data.voice_model or "default",
            description=agent_data.description or f"A {agent_data.personality or 'friendly'} AI assistant",
            created_at=agent_config["created_at"]
        )
    
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    try:
        agent_config = config_manager.load_agent(agent_id)
        if not agent_config:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        interests = agent_config.get("interests", ["general topics"])
        description = f"A {agent_config.get('tone', 'friendly')} AI assistant interested in {', '.join(interests)}"
        
        return AgentResponse(
            id=agent_id,
            name=agent_config["name"],
            personality=agent_config.get("tone", "friendly"),
            voice_model=agent_config.get("voice_id", "default"),
            description=description,
            created_at=agent_config.get("created_at", datetime.now().isoformat())
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        agent_file = os.path.join(config_manager.agents_dir, f"{agent_id}.json")
        if not os.path.exists(agent_file):
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Remove from active agents cache
        if agent_id in active_agents:
            del active_agents[agent_id]
        
        os.remove(agent_file)
        logger.info(f"✅ Agent {agent_id} deleted successfully!")
        
        return {"message": f"Agent {agent_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/{agent_id}")
async def chat_with_agent(agent_id: str, chat_data: ChatMessage):
    """Send message to agent and get response"""
    try:
        # Get or create agent instance
        agent = get_or_create_agent(agent_id)
        
        # Process message
        response_text = agent.process_message(
            chat_data.message, 
            chat_data.conversation_id
        )
        
        return {
            "response": response_text,
            "conversation_id": chat_data.conversation_id or f"conv_{datetime.now().timestamp()}",
            "agent_id": agent_id,
            "audio_url": None  # Would be generated by voice cloner
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat with agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), agent_id: Optional[str] = Form(None)):
    """Upload file to knowledge base"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "./uploads"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Save uploaded file
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # If agent_id is provided, also copy to agent's knowledge directory
        if agent_id:
            agent_upload_dir = f"./user_knowledge/{agent_id}/uploads"
            if not os.path.exists(agent_upload_dir):
                os.makedirs(agent_upload_dir)
            
            agent_file_path = os.path.join(agent_upload_dir, file.filename)
            with open(agent_file_path, "wb") as buffer:
                buffer.write(content)
            
            # Reload agent's knowledge base if it's active
            if agent_id in active_agents:
                try:
                    active_agents[agent_id].knowledge_base.load_all_knowledge()
                    logger.info(f"🔄 Reloaded knowledge base for {agent_id}")
                except Exception as e:
                    logger.error(f"Failed to reload knowledge base: {e}")
        
        logger.info(f"✅ File {file.filename} uploaded successfully!")
        
        return {
            "message": f"File {file.filename} uploaded successfully",
            "filename": file.filename,
            "size": len(content),
            "agent_id": agent_id
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/voice/{agent_id}")
async def generate_voice(agent_id: str, text_data: dict):
    """Generate voice response for agent"""
    try:
        # Load agent configuration
        agent_config = config_manager.load_agent(agent_id)
        if not agent_config:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # For now, return a placeholder
        # In a full implementation, you'd use the VoiceCloner
        return {
            "message": "Voice generation not implemented yet",
            "text": text_data.get("text", ""),
            "agent_id": agent_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating voice for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    logger.info("🚀 Starting Universal AI Agent System API Server...")
    
    # Check if required directories exist
    os.makedirs("./agents", exist_ok=True)
    os.makedirs("./user_knowledge", exist_ok=True)
    os.makedirs("./uploads", exist_ok=True)
    os.makedirs("./memory", exist_ok=True)
    
    # Start the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )
 