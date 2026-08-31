"""ai_core/chains/safety_critic_chain.py"""

from ai_core.llm_config import reasoning_llm
from ai_core.system_prompts.safety_critic_prompt import SAFETY_CRITIC_SYSTEM_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from schemas.ai_models import CriticEvaluation

critic_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SAFETY_CRITIC_SYSTEM_PROMPT),
        ("human", "Evaluate the generated draft."),
    ]
)


safety_critic_chain = critic_prompt | reasoning_llm.with_structured_output(
    CriticEvaluation
)
