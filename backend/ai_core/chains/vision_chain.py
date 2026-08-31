"""ai_core/chains/vision_chain.py"""

from ai_core.llm_config import vision_llm
from ai_core.system_prompts.vision_prompt import VISION_SYSTEM_PROMPT
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from schemas.ai_models import BatchVisionResult

# Prompt Template with MessagesPlaceholder
vision_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", VISION_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="human_message_with_images"),
    ]
)

# Bind the schema to the LLM
structured_vision_llm = vision_llm.with_structured_output(BatchVisionResult)

# LCEL Chain
vision_chain = vision_prompt | structured_vision_llm
