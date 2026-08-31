"""ai_core/chains/alignment_chain.py"""

from ai_core.llm_config import reasoning_llm
from ai_core.system_prompts.alignment_prompt import ALIGNMENT_SYSTEM_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from schemas.ai_models import SymptomAlignment

# Prompt Template 
alignment_prompt = ChatPromptTemplate.from_messages([
    ("system", ALIGNMENT_SYSTEM_PROMPT),
    ("human", "User Text: {user_text}\n\nVisual Text: {visual_text}\n\nClarification History:\n{history}")
])

# Bind schema to reasoning model
structured_alignment_llm = reasoning_llm.with_structured_output(SymptomAlignment)

# Build the LCEL Chain
alignment_chain = alignment_prompt | structured_alignment_llm