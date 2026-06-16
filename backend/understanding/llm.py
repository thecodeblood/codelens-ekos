import logging
import json
from openai import OpenAI
from backend.config import Settings

logger = logging.getLogger(__name__)

class LLMClient:
    """Wrapper around the LLM provider (NVIDIA/OpenAI compatible)."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        
        if self.settings.llm_provider == "openai":
            if not self.settings.openai_api_key:
                logger.warning("LLM provider set to openai but no API key found.")
                return
            
            # Initialize OpenAI client (supports OpenAI, NVIDIA, Groq, Ollama depending on base_url)
            self.client = OpenAI(
                base_url=self.settings.llm_base_url,
                api_key=self.settings.openai_api_key,
            )
            logger.info(f"Initialized LLMClient with provider {self.settings.llm_provider} and model {self.settings.llm_model}")

    def is_enabled(self) -> bool:
        return self.client is not None

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Generates a text response from the LLM."""
        if not self.is_enabled():
            return ""
            
        try:
            completion = self.client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=1024,
                stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return ""

    def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> dict:
        """Generates a JSON response from the LLM. 
        Expects the LLM to return valid JSON (NVIDIA models might need explicit instructions)."""
        if not self.is_enabled():
            return {}
            
        system_prompt += "\n\nYou MUST return ONLY valid JSON. Do not wrap it in markdown block quotes like ```json ... ```. Just the raw JSON string."
        
        try:
            # Some providers like native OpenAI support response_format={"type": "json_object"}
            # But since we are using NVIDIA API (or others), we rely on strict prompting.
            completion = self.client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=512,
                stream=False
            )
            content = completion.choices[0].message.content
            
            # Clean up potential markdown formatting
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            return json.loads(content.strip())
        except Exception as e:
            logger.error(f"LLM JSON generation failed: {e}")
            return {}
