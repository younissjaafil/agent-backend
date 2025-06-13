"""
Agent Configuration Manager
Enhanced with User-Specific Knowledge Support
"""

import os
import json
import logging
from datetime import datetime
from modules.voice_cloner import VoiceCloner

logger = logging.getLogger(__name__)

class AgentConfig:
    def __init__(self):
        self.agents_dir = "./agents"
        self.ensure_agents_directory()
    
    def ensure_agents_directory(self):
        """Ensure agents directory exists"""
        if not os.path.exists(self.agents_dir):
            os.makedirs(self.agents_dir)
            logger.info(f"📁 Created agents directory: {self.agents_dir}")
    
    def collect_agent_info(self, name):
        """Collect agent information from user"""
        print(f"\\n🎭 CREATING AGENT: {name}")
        print("=" * 40)
        
        # Tone selection
        print("\\n📝 Select agent tone:")
        tones = ["friendly", "professional", "casual", "enthusiastic", "calm", "witty", "serious"]
        for i, tone in enumerate(tones, 1):
            print(f"{i}. {tone}")
        
        while True:
            try:
                tone_choice = input("\\nSelect tone (1-7): ").strip()
                tone_index = int(tone_choice) - 1
                if 0 <= tone_index < len(tones):
                    selected_tone = tones[tone_index]
                    break
                else:
                    print("❌ Invalid choice. Please select 1-7.")
            except ValueError:
                print("❌ Please enter a valid number.")
        
        # Interests
        print(f"\\n🎯 What are {name}'s interests? (comma-separated)")
        print("Examples: technology, sports, music, cooking, travel, science")
        interests_input = input("Interests: ").strip()
        interests = [interest.strip() for interest in interests_input.split(",") if interest.strip()]
        
        if not interests:
            interests = ["general conversation", "helping users"]
        
        return {
            "tone": selected_tone,
            "interests": interests
        }
    
    def create_agent(self, name, api_keys):
        """Create a new agent with voice cloning and knowledge setup"""
        try:
            # Collect agent information
            agent_info = self.collect_agent_info(name)
            
            # Voice cloning
            print(f"\\n🎙️ VOICE CLONING for {name}")
            print("=" * 30)
            print("We'll now clone your voice for this agent.")
            print("You'll need to record a 15-second audio sample.")
            
            voice_cloner = VoiceCloner(api_keys["MINIMAX_API_KEY"])
            voice_id = voice_cloner.clone_voice(name)
            
            if not voice_id:
                print("⚠️ Voice cloning failed, but agent will still work with default voice")
            
            # Create agent configuration
            agent_config = {
                "name": name,
                "tone": agent_info["tone"],
                "interests": agent_info["interests"],
                "voice_id": voice_id,
                "api_keys": api_keys,
                "created_at": datetime.now().isoformat(),
                "knowledge_setup": {
                    "user_knowledge_enabled": True,
                    "company_knowledge_enabled": True,
                    "knowledge_user": name  # Use agent name as knowledge user
                }
            }
            
            # Save agent configuration
            agent_file = os.path.join(self.agents_dir, f"{name}.json")
            with open(agent_file, 'w') as f:
                json.dump(agent_config, f, indent=2)
            
            # Create user knowledge directory for this agent
            user_knowledge_dir = f"./user_knowledge/{name}"
            if not os.path.exists(user_knowledge_dir):
                os.makedirs(user_knowledge_dir)
                os.makedirs(f"{user_knowledge_dir}/docs")
                os.makedirs(f"{user_knowledge_dir}/uploads")
                logger.info(f"📁 Created knowledge directories for {name}")
            
            # Create a welcome knowledge file for the agent
            welcome_file = f"{user_knowledge_dir}/docs/welcome.txt"
            welcome_content = f"""Welcome to {name}'s Knowledge Base!

Agent Profile:
- Name: {name}
- Tone: {agent_info["tone"]}
- Interests: {", ".join(agent_info["interests"])}

This agent has access to:
1. Company knowledge (shared with all agents)
2. Personal knowledge (unique to this agent)

You can add more knowledge by:
- Uploading files through the Knowledge UI (python knowledge_ui.py)
- Adding documents to the user_knowledge/{name}/docs/ folder
- The agent will automatically load this knowledge when launched

Created on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
            
            with open(welcome_file, 'w') as f:
                f.write(welcome_content)
            
            logger.info(f"✅ Agent {name} created successfully!")
            logger.info(f"📁 Configuration: {agent_file}")
            logger.info(f"🧠 Knowledge directory: {user_knowledge_dir}")
            
            print(f"\\n🎉 SUCCESS! Agent '{name}' is ready!")
            print(f"\\n📋 Agent Details:")
            print(f"   - Tone: {agent_info['tone']}")
            print(f"   - Interests: {', '.join(agent_info['interests'])}")
            print(f"   - Voice: {'Cloned' if voice_id else 'Default'}")
            print(f"   - Knowledge: Company + Personal")
            print(f"\\n💡 To add knowledge:")
            print(f"   1. Run: python knowledge_ui.py")
            print(f"   2. Set username: {name}")
            print(f"   3. Upload files for this agent")
            
            return agent_file
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent {name}: {e}")
            return None
    
    def load_agent(self, name):
        """Load agent configuration"""
        try:
            agent_file = os.path.join(self.agents_dir, f"{name}.json")
            
            if not os.path.exists(agent_file):
                logger.error(f"❌ Agent {name} not found!")
                return None
            
            with open(agent_file, 'r') as f:
                config = json.load(f)
            
            # Ensure knowledge setup exists
            if "knowledge_setup" not in config:
                config["knowledge_setup"] = {
                    "user_knowledge_enabled": True,
                    "company_knowledge_enabled": True,
                    "knowledge_user": name
                }
            
            logger.info(f"✅ Loaded agent: {name}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to load agent {name}: {e}")
            return None
    
    def list_agents(self):
        """List all available agents"""
        try:
            if not os.path.exists(self.agents_dir):
                return []
            
            agents = []
            for filename in os.listdir(self.agents_dir):
                if filename.endswith('.json'):
                    agent_name = filename[:-5]  # Remove .json
                    try:
                        config = self.load_agent(agent_name)
                        if config:
                            agents.append({
                                "name": agent_name,
                                "tone": config.get("tone", "unknown"),
                                "created_at": config.get("created_at", "unknown"),
                                "file": filename,
                                "has_voice": bool(config.get("voice_id")),
                                "knowledge_enabled": config.get("knowledge_setup", {}).get("user_knowledge_enabled", False)
                            })
                    except Exception as e:
                        logger.error(f"Failed to load agent {agent_name}: {e}")
            
            return sorted(agents, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to list agents: {e}")
            return []
    
    def get_agent_knowledge_stats(self, name):
        """Get knowledge statistics for an agent"""
        try:
            from modules.knowledge_base import KnowledgeBase
            
            kb = KnowledgeBase(user_name=name)
            kb.load_all_knowledge()
            return kb.get_stats()
            
        except Exception as e:
            logger.error(f"Failed to get knowledge stats for {name}: {e}")
            return {"error": str(e)}# """
