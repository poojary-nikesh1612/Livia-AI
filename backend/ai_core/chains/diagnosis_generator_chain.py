"""ai_core/chains/diagnosis_generator_chain.py"""

from ai_core.llm_config import reasoning_llm
from ai_core.system_prompts.diagnosis_generator_prompt import DIAGNOSIS_SYSTEM_PROMPT
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

diagnosis_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", DIAGNOSIS_SYSTEM_PROMPT),
        ("human", "Please provide the voice advisory script for the farmer."),
    ]
)

diagnosis_chain = diagnosis_prompt | reasoning_llm | StrOutputParser()
