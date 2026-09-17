"""Tests for Phase 3: Conversational layer, multi-turn memory, field extraction, and clarifying logic."""

import pytest
from fastapi.testclient import TestClient
from daaruka.main import app
from daaruka.chat.extractor import extract_site_assessment_from_text
from daaruka.chat.session_store import InMemorySessionStore, session_store
from daaruka.chat.turn_handler import handle_chat_turn, merge_assessment_inputs
from daaruka.reasoning.models import SiteAssessmentInput

client = TestClient(app)


def test_free_text_field_extraction_various_inputs():
    """Verify that unstructured natural language is correctly parsed into structured SiteAssessmentInput fields."""
    # Test case 1: Soil carbon, rainfall, monoculture wheat
    text1 = "My soil organic carbon is 0.8%, rainfall is low and erratic, and it's monoculture wheat."
    extracted1 = extract_site_assessment_from_text(text1)
    assert extracted1.soc_pct == 0.8
    assert "cropland" in (extracted1.current_land_use or "").lower()
    assert "wheat" in (extracted1.current_land_use or "").lower()
    assert "low" in (extracted1.rainfall_pattern or "").lower() or "erratic" in (extracted1.rainfall_pattern or "").lower()

    # Test case 2: pH, semi-arid, conventional tillage
    text2 = "We have soil pH 7.2 in a semi-arid climate using conventional tillage."
    extracted2 = extract_site_assessment_from_text(text2)
    assert extracted2.ph == 7.2
    assert extracted2.biome == "semi-arid"
    assert "tillage" in (extracted2.tillage_practice or "").lower()

    # Test case 3: Declining biodiversity / agroecosystem
    text3 = "Biodiversity is declining on my land with degraded soil."
    extracted3 = extract_site_assessment_from_text(text3)
    assert extracted3.biome is not None

    # Test case 4: Coordinates
    text4 = "Site located at lat: 31.5, lon: -100.2"
    extracted4 = extract_site_assessment_from_text(text4)
    assert extracted4.latitude == 31.5
    assert extracted4.longitude == -100.2


def test_merge_assessment_inputs_preserves_previous_data():
    """Verify state merging preserves previously collected fields and updates new ones."""
    state1 = SiteAssessmentInput(
        biome="agricultural landscape / degraded agroecosystem",
        region="North America",
    )
    update = SiteAssessmentInput(
        soc_pct=0.8,
        biome="semi-arid",
        current_land_use="cropland / wheat cultivation",
    )

    merged = merge_assessment_inputs(state1, update)
    assert merged.region == "North America"
    assert merged.soc_pct == 0.8
    assert merged.biome == "semi-arid"
    assert merged.current_land_use == "cropland / wheat cultivation"


def test_session_memory_persistence():
    """Verify that InMemorySessionStore remembers conversation history and variables."""
    store = InMemorySessionStore()
    session = store.get_or_create("test-session-123")
    
    session.add_message(role="user", content="Hello!")
    session.accumulated_assessment.soc_pct = 1.1
    store.save(session)

    # Re-retrieve
    retrieved = store.get("test-session-123")
    assert retrieved is not None
    assert len(retrieved.messages) == 1
    assert retrieved.accumulated_assessment.soc_pct == 1.1


def test_hackathon_brief_exact_two_turn_conversation():
    """Integration test replicating the exact brief's conversation:
    Turn 1: 'Biodiversity is declining on my land' -> asks clarifying question
    Turn 2: Provide missing values -> returns recommendations without repeating questions.
    """
    session_id = "test-brief-eval-session"
    session_store.clear(session_id)

    # --- Turn 1 ---
    turn1_msg = "Biodiversity is declining on my land"
    resp1 = handle_chat_turn(message=turn1_msg, session_id=session_id)

    assert resp1.is_asking_clarification is True
    assert resp1.recommendations is None
    assert resp1.session_id == session_id
    # Must ask for missing context (soil, climate, or land use)
    assert any(term in resp1.response_text.lower() for term in ["soil", "land use", "climate", "rainfall", "crop", "carbon"])

    # --- Turn 2 ---
    turn2_msg = "My soil organic carbon is 0.8%, rainfall is low and erratic in a semi-arid zone, and it is cropland wheat with conventional tillage."
    resp2 = handle_chat_turn(message=turn2_msg, session_id=session_id)

    assert resp2.is_asking_clarification is False
    assert resp2.recommendations is not None
    assert len(resp2.recommendations) >= 1
    assert resp2.session_id == session_id

    # Verify session retained Turn 1 context and merged Turn 2
    session = session_store.get(session_id)
    assert session is not None
    assert len(session.messages) == 4  # 2 user messages + 2 assistant messages
    assert session.accumulated_assessment.soc_pct == 0.8
    assert session.accumulated_assessment.biome == "semi-arid"
    assert "cropland" in (session.accumulated_assessment.current_land_use or "").lower()

    # Verify recommendations have grounded page citations
    for rec in resp2.recommendations:
        assert len(rec.sources) >= 1
        for src in rec.sources:
            assert src.page is not None or src.section_title is not None
            assert src.document_title != ""


def test_api_chat_endpoint_multi_turn():
    """Verify FastAPI /api/v1/chat endpoint handles multi-turn calls and session inspection."""
    # Turn 1
    t1_payload = {"message": "I want to restore biodiversity on my farm"}
    r1 = client.post("/api/v1/chat", json=t1_payload)
    assert r1.status_code == 200
    d1 = r1.json()
    sess_id = d1["session_id"]
    assert d1["is_asking_clarification"] is True

    # Turn 2 using same session_id
    t2_payload = {
        "session_id": sess_id,
        "message": "Topsoil organic carbon is 0.5%, pH is 6.8, climate is semi-arid with low rainfall, land use is monoculture wheat.",
    }
    r2 = client.post("/api/v1/chat", json=t2_payload)
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["is_asking_clarification"] is False
    assert len(d2["recommendations"]) >= 1

    # Verify GET session endpoint
    r_sess = client.get(f"/api/v1/chat/sessions/{sess_id}")
    assert r_sess.status_code == 200
    s_data = r_sess.json()
    assert s_data["session_id"] == sess_id
    assert len(s_data["messages"]) == 4
