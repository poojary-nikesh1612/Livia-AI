"""ai_core/chains/investigative_question_chain.py"""

from ai_core.llm_config import reasoning_llm
from ai_core.system_prompts.investigative_question_prompt import \
    INVESTIGATIVE_QUESTION_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from schemas.ai_models import InvestigativeQuestionOutput

# Create the prompt template
investigative_question_prompt = ChatPromptTemplate.from_messages([
    ("system", INVESTIGATIVE_QUESTION_PROMPT),
    ("human", "Generate the investigative question to help expand the symptom profile.")
])

# Build the LCEL Chain using structured output
investigative_question_chain = (
    investigative_question_prompt 
    | reasoning_llm.with_structured_output(InvestigativeQuestionOutput)
)
