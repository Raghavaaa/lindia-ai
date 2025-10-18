"""
Prompt Template Manager
Manages configurable prompt templates for different RAG modes
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import os
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """
    Configurable prompt template
    """
    name: str
    system_prompt: str
    user_prompt_template: str
    description: str = ""
    variables: List[str] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []
    
    def format(self, **kwargs) -> str:
        """Format the user prompt with variables"""
        try:
            return self.user_prompt_template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable in prompt template: {e}")
            return self.user_prompt_template


class PromptManager:
    """
    Manages prompt templates for RAG pipeline
    Templates can be loaded from files or defined programmatically
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        self.templates: Dict[str, PromptTemplate] = {}
        self.template_dir = template_dir or os.getenv("RAG_PROMPT_TEMPLATE_DIR", "./prompts")
        
        # Load default templates
        self._load_default_templates()
        
        # Load custom templates from directory
        if Path(self.template_dir).exists():
            self._load_custom_templates()
    
    def _load_default_templates(self):
        """Load built-in default templates"""
        
        # Standard RAG template
        self.templates["standard"] = PromptTemplate(
            name="standard",
            system_prompt="""You are a helpful AI assistant specializing in legal information.
Your task is to answer questions based ONLY on the provided context documents.
If the context doesn't contain enough information to answer the question, clearly state that.
Always cite your sources using [1], [2], etc. to reference the documents.
Be precise, accurate, and cite relevant sections of the law or precedents.""",
            user_prompt_template="""Context Documents:
{context}

Question: {query}

Instructions:
1. Answer the question based on the context above
2. Cite sources using [1], [2], etc.
3. If you're uncertain, say so
4. Be concise but thorough

Answer:""",
            description="Standard RAG with citations",
            variables=["context", "query"]
        )
        
        # Legal analysis template
        self.templates["legal_analysis"] = PromptTemplate(
            name="legal_analysis",
            system_prompt="""You are an expert legal AI assistant with deep knowledge of Indian law.
Analyze legal questions with precision, citing relevant statutes, case law, and precedents.
Structure your analysis clearly and always distinguish between settled law and interpretation.
Cite all sources explicitly.""",
            user_prompt_template="""Legal Context:
{context}

Legal Question: {query}

Please provide a comprehensive legal analysis that includes:
1. **Relevant Law**: Cite applicable statutes, sections, and provisions
2. **Case Precedents**: Reference relevant case law if available
3. **Analysis**: Apply the law to the specific question
4. **Conclusion**: Provide a clear answer based on the analysis
5. **Caveats**: Note any limitations or areas requiring expert review

Analysis:""",
            description="Detailed legal analysis with structure",
            variables=["context", "query"]
        )
        
        # Conversational template
        self.templates["conversational"] = PromptTemplate(
            name="conversational",
            system_prompt="""You are a friendly AI legal assistant engaged in a conversation.
Maintain context from previous messages and provide helpful, conversational responses.
Always ground your answers in the provided documents and previous conversation.
Cite sources when making factual claims.""",
            user_prompt_template="""Previous Conversation:
{conversation_history}

Current Context:
{context}

User's Question: {query}

Respond naturally while:
- Referencing previous discussion if relevant
- Citing sources from the context
- Maintaining a conversational tone
- Asking clarifying questions if needed

Response:""",
            description="Multi-turn conversational RAG",
            variables=["conversation_history", "context", "query"]
        )
        
        # Summarization template
        self.templates["summarization"] = PromptTemplate(
            name="summarization",
            system_prompt="""You are an AI that creates concise, accurate summaries of legal documents.
Focus on key points, important dates, parties involved, and legal implications.
Preserve critical details while removing redundancy.""",
            user_prompt_template="""Documents to Summarize:
{context}

Create a summary that covers:
- Main topic/issue
- Key parties or entities
- Important dates and deadlines
- Critical legal points
- Outcome or current status (if applicable)

Summary:""",
            description="Document summarization",
            variables=["context"]
        )
        
        # Comparison template
        self.templates["comparison"] = PromptTemplate(
            name="comparison",
            system_prompt="""You are an AI that compares and contrasts multiple legal sources.
Identify similarities, differences, conflicts, and complementary aspects.
Present your comparison in a clear, structured format.""",
            user_prompt_template="""Sources to Compare:
{context}

Question: {query}

Provide a structured comparison:
1. **Common Ground**: What the sources agree on
2. **Differences**: Where sources diverge or conflict
3. **Hierarchy**: Which source takes precedence (if applicable)
4. **Synthesis**: Integrated understanding
5. **Implications**: What this means for the question

Comparison:""",
            description="Compare multiple sources",
            variables=["context", "query"]
        )
        
        # Follow-up questions template
        self.templates["follow_up"] = PromptTemplate(
            name="follow_up",
            system_prompt="""You generate relevant follow-up questions based on a query and answer.
Questions should help users explore the topic more deeply or clarify edge cases.""",
            user_prompt_template="""Original Query: {query}

Answer Provided: {answer}

Context Used: {context}

Generate 2 relevant follow-up questions that:
- Explore related aspects of the topic
- Help clarify potential ambiguities
- Guide further research
- Are natural next questions a user might ask

Format as JSON array:
[
  {{"question": "...", "reasoning": "...", "priority": 1}},
  {{"question": "...", "reasoning": "...", "priority": 2}}
]

Follow-up Questions:""",
            description="Generate follow-up questions",
            variables=["query", "answer", "context"]
        )
        
        logger.info(f"Loaded {len(self.templates)} default prompt templates")
    
    def _load_custom_templates(self):
        """Load custom templates from template directory"""
        try:
            template_path = Path(self.template_dir)
            for template_file in template_path.glob("*.json"):
                with open(template_file, 'r') as f:
                    data = json.load(f)
                    template = PromptTemplate(
                        name=data["name"],
                        system_prompt=data["system_prompt"],
                        user_prompt_template=data["user_prompt_template"],
                        description=data.get("description", ""),
                        variables=data.get("variables", [])
                    )
                    self.templates[template.name] = template
                    logger.info(f"Loaded custom template: {template.name}")
        except Exception as e:
            logger.warning(f"Failed to load custom templates: {e}")
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get template by name"""
        return self.templates.get(name)
    
    def register_template(self, template: PromptTemplate):
        """Register a new template"""
        self.templates[template.name] = template
        logger.info(f"Registered template: {template.name}")
    
    def list_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.templates.keys())
    
    def format_prompt(
        self,
        template_name: str,
        query: str,
        context: str,
        conversation_history: Optional[str] = None,
        answer: Optional[str] = None,
        **kwargs
    ) -> tuple[str, str]:
        """
        Format a prompt using a template
        
        Returns:
            (system_prompt, user_prompt)
        """
        template = self.get_template(template_name)
        if not template:
            logger.warning(f"Template '{template_name}' not found, using 'standard'")
            template = self.templates["standard"]
        
        # Prepare variables
        variables = {
            "query": query,
            "context": context,
            **kwargs
        }
        
        if conversation_history:
            variables["conversation_history"] = conversation_history
        
        if answer:
            variables["answer"] = answer
        
        # Format user prompt
        user_prompt = template.format(**variables)
        
        return template.system_prompt, user_prompt
    
    def save_template(self, template: PromptTemplate, filepath: str):
        """Save template to file"""
        try:
            data = {
                "name": template.name,
                "system_prompt": template.system_prompt,
                "user_prompt_template": template.user_prompt_template,
                "description": template.description,
                "variables": template.variables,
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved template '{template.name}' to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save template: {e}")

