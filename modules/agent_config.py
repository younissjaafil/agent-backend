
# agent_config.py - UPDATED VERSION
"""
Agent Configuration Manager
Handles creation, loading, and management of AI agents
UPDATED: Now supports voice_id parameter for voice cloning
"""

import os
import json
import time
import logging
from datetime import datetime
from voice_cloner import VoiceCloner

logger = logging.getLogger(__name__)

class AgentConfig:
    def __init__(self):
        self.agents_dir = "agents"
        self.ensure_agents_directory()

    def ensure_agents_directory(self):
        """Ensure agents directory exists"""
        if not os.path.exists(self.agents_dir):
            os.makedirs(self.agents_dir)
            logger.info(f"📁 Created agents directory: {self.agents_dir}")

    def create_agent(self, name, api_keys, personality="", tone="friendly", voice_id=None):
        """
        Create a new AI agent with optional voice cloning

        Args:
            name: Agent name
            api_keys: Dictionary of API keys
            personality: Agent personality description
            tone: Agent tone (friendly, professional, etc.)
            voice_id: Pre-cloned voice ID (optional)
        """
        try:
            logger.info(f"🤖 Creating agent: {name}")

            # If no voice_id provided, attempt voice cloning
            if not voice_id:
                logger.info("🎙️ No voice ID provided, attempting voice cloning...")
                voice_cloner = VoiceCloner()
                voice_id = voice_cloner.setup_voice_cloning()

                if voice_id:
                    logger.info(f"✅ Voice cloned successfully: {voice_id}")
                else:
                    logger.warning("⚠️ Voice cloning failed, agent will use default voice")
            else:
                logger.info(f"🎙️ Using provided voice ID: {voice_id}")

            # Create agent configuration
            agent_config = {
                "name": name,
                "personality": personality,
                "tone": tone,
                "voice_id": voice_id,
                "api_keys": api_keys,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": "1.0"
            }

            # Save configuration
            filename = f"{name.lower().replace(' ', '_')}.json"
            filepath = os.path.join(self.agents_dir, filename)

            with open(filepath, 'w') as f:
                json.dump(agent_config, f, indent=2)

            logger.info(f"✅ Agent configuration saved: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to create agent: {e}")
            return None

    def load_agent(self, name):
        """Load an existing agent configuration"""
        try:
            filename = f"{name.lower().replace(' ', '_')}.json"
            filepath = os.path.join(self.agents_dir, filename)

            if not os.path.exists(filepath):
                logger.error(f"❌ Agent file not found: {filepath}")
                return None

            with open(filepath, 'r') as f:
                config = json.load(f)

            logger.info(f"✅ Agent loaded: {name}")
            return config

        except Exception as e:
            logger.error(f"❌ Failed to load agent: {e}")
            return None

    def list_agents(self):
        """List all available agents"""
        try:
            agents = []

            if not os.path.exists(self.agents_dir):
                return agents

            for filename in os.listdir(self.agents_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.agents_dir, filename)

                    try:
                        with open(filepath, 'r') as f:
                            config = json.load(f)

                        agents.append({
                            "name": config.get("name", "Unknown"),
                            "personality": config.get("personality", ""),
                            "tone": config.get("tone", "friendly"),
                            "voice_id": config.get("voice_id"),
                            "created_at": config.get("created_at", ""),
                            "file": filename
                        })

                    except Exception as e:
                        logger.warning(f"⚠️ Failed to load agent file {filename}: {e}")
                        continue

            # Sort by creation date (newest first)
            agents.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            logger.info(f"📋 Found {len(agents)} agents")
            return agents

        except Exception as e:
            logger.error(f"❌ Failed to list agents: {e}")
            return []

    def update_agent(self, name, updates):
        """Update an existing agent configuration"""
        try:
            config = self.load_agent(name)
            if not config:
                return False

            # Update fields
            for key, value in updates.items():
                config[key] = value

            config["updated_at"] = datetime.now().isoformat()

            # Save updated configuration
            filename = f"{name.lower().replace(' ', '_')}.json"
            filepath = os.path.join(self.agents_dir, filename)

            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"✅ Agent updated: {name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to update agent: {e}")
            return False

    def delete_agent(self, name):
        """Delete an agent configuration"""
        try:
            filename = f"{name.lower().replace(' ', '_')}.json"
            filepath = os.path.join(self.agents_dir, filename)

            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"✅ Agent deleted: {name}")
                return True
            else:
                logger.warning(f"⚠️ Agent file not found: {filepath}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to delete agent: {e}")
            return False

    def get_agent_voice_id(self, name):
        """Get the voice ID for a specific agent"""
        try:
            config = self.load_agent(name)
            if config:
                return config.get("voice_id")
            return None

        except Exception as e:
            logger.error(f"❌ Failed to get voice ID for agent {name}: {e}")
            return None
