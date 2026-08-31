"""ai_core/chains/follow_up_generator_chain.py"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ai_core.llm_config import reasoning_llm
from ai_core.system_prompts.follow_up_generator_prompt import FOLLOW_UP_SYSTEM_PROMPT

follow_up_prompt = ChatPromptTemplate.from_messages([
    ("system", FOLLOW_UP_SYSTEM_PROMPT),
    ("human", "{user_text}")
])

follow_up_chain = follow_up_prompt | reasoning_llm | StrOutputParser()