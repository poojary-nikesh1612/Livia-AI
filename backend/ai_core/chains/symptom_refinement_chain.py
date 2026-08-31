"""ai_core/chains/symptom_refinement_chain.py"""

from ai_core.llm_config import reasoning_llm
from ai_core.system_prompts.symptom_refinement_prompt import SYMPTOM_REFINEMENT_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from schemas.ai_models import SymptomRefinementOutput

symptom_refinement_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYMPTOM_REFINEMENT_PROMPT),
        ("human", "Synthesize the new observation into the updated symptom profile."),
    ]
)

# LCEL Chain with structured output guarantee
symptom_refinement_chain = (
    symptom_refinement_prompt
    | reasoning_llm.with_structured_output(SymptomRefinementOutput)
)
