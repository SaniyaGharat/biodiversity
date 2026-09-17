"""Turn handler orchestrating conversational memory, field extraction, gap detection, and reasoning."""

import logging
from typing import Optional, Dict, Any

from daaruka.chat.models import ChatSession, ChatResponse, SessionStateSummary
from daaruka.chat.session_store import session_store
from daaruka.chat.extractor import extract_site_assessment_from_text
from daaruka.chat.question_generator import select_clarifying_question
from daaruka.chat.formatter import format_conversational_recommendations
from daaruka.reasoning.gap_detector import detect_gaps
from daaruka.reasoning.engine import default_reasoning_engine
from daaruka.reasoning.models import SiteAssessmentInput

logger = logging.getLogger(__name__)


def merge_assessment_inputs(current: SiteAssessmentInput, updates: SiteAssessmentInput) -> SiteAssessmentInput:
    """Merge newly extracted fields into accumulated state without losing previous turns' data."""
    current_data = current.model_dump()
    update_data = updates.model_dump(exclude_none=True)

    for field, val in update_data.items():
        if val is not None:
            current_data[field] = val

    return SiteAssessmentInput(**current_data)


def handle_chat_turn(message: str, session_id: Optional[str] = None) -> ChatResponse:
    """Process a single conversational turn in the biodiversity intelligence workflow.
    
    1. Retrieves or creates session state.
    2. Extracts structured variables from user natural language message.
    3. Merges extracted variables into accumulated site state.
    4. Evaluates missing ecological gaps.
    5. Returns ONE single prioritized clarifying question if gaps remain.
    6. Returns scientifically grounded conversational recommendations once sufficient data is provided.
    """
    # 1. Retrieve or create session
    session: ChatSession = session_store.get_or_create(session_id=session_id)

    # 2. Extract structured fields from free text
    extracted_input = extract_site_assessment_from_text(message)
    extracted_dict = extracted_input.model_dump(exclude_none=True)

    # 3. Merge into accumulated assessment
    session.accumulated_assessment = merge_assessment_inputs(
        session.accumulated_assessment, extracted_input
    )

    # 4. Record user message
    session.add_message(role="user", content=message, metadata={"extracted_fields": extracted_dict})

    # 5. Run gap detection on accumulated state
    gap_result = detect_gaps(session.accumulated_assessment)

    # 6. Check if we should ask a clarifying question
    has_minimum_actionable_profile = (
        (session.accumulated_assessment.soc_pct is not None or session.accumulated_assessment.moisture_level is not None or session.accumulated_assessment.ph is not None)
        and (session.accumulated_assessment.current_land_use is not None or session.accumulated_assessment.cropping_pattern is not None)
        and (session.accumulated_assessment.biome is not None or session.accumulated_assessment.rainfall_pattern is not None)
    )

    clarification_tuple = None
    if not has_minimum_actionable_profile and gap_result.data_completeness_score < 0.6:
        clarification_tuple = select_clarifying_question(
            assessment=session.accumulated_assessment,
            gap_result=gap_result,
            asked_categories=session.asked_categories,
        )

    # Prepare summary
    accumulated_dict = session.accumulated_assessment.model_dump(exclude_none=True)
    summary = SessionStateSummary(
        session_id=session.session_id,
        accumulated_fields=accumulated_dict,
        data_completeness_score=gap_result.data_completeness_score,
        missing_categories=gap_result.missing_categories,
        present_categories=gap_result.present_categories,
        total_messages=len(session.messages),
    )

    if clarification_tuple:
        category, question_text = clarification_tuple
        session.record_question(category, question_text)
        session.add_message(role="assistant", content=question_text, metadata={"asking_clarification": True, "category": category})
        session_store.save(session)

        return ChatResponse(
            session_id=session.session_id,
            response_text=question_text,
            session_state_summary=summary,
            is_asking_clarification=True,
            recommendations=None,
            extracted_in_this_turn=extracted_dict,
        )

    # 7. Evaluate reasoning engine and format conversational recommendations
    assessment_output = default_reasoning_engine.evaluate(session.accumulated_assessment)
    response_text = format_conversational_recommendations(assessment_output)

    session.add_message(role="assistant", content=response_text, metadata={"recommendation_count": len(assessment_output.recommendations)})
    session_store.save(session)

    return ChatResponse(
        session_id=session.session_id,
        response_text=response_text,
        session_state_summary=summary,
        is_asking_clarification=False,
        recommendations=assessment_output.recommendations,
        extracted_in_this_turn=extracted_dict,
    )
