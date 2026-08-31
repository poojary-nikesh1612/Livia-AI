"""ai_core/chains/general_chat_chain.py"""

from ai_core.llm_config import lightweight_llm
from ai_core.system_prompts.general_chat_prompt import GENERAL_CHAT_SYSTEM_PROMPT
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [("system", GENERAL_CHAT_SYSTEM_PROMPT), ("human", "{user_text}")]
)

general_chat_chain = prompt | lightweight_llm | StrOutputParser()
