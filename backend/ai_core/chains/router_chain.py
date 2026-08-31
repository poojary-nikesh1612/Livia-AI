"""ai_core/chains/router_chain.py"""

from ai_core.llm_config import lightweight_llm
from ai_core.system_prompts.router_prompt import ROUTER_SYSTEM_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from schemas.ai_models import RouteDecision

router_prompt = ChatPromptTemplate.from_messages(
    [("system", ROUTER_SYSTEM_PROMPT), ("human", "{user_text}")]
)

router_chain = router_prompt | lightweight_llm.with_structured_output(RouteDecision)
