"""Conversational response formatter turning structured reasoning outputs into engaging dialogue."""

from typing import List
from daaruka.reasoning.models import ReasoningAssessmentOutput, Recommendation


def format_conversational_recommendations(assessment_output: ReasoningAssessmentOutput) -> str:
    """Format reasoning recommendations into rich, conversational markdown with scientific citations."""
    recs: List[Recommendation] = assessment_output.recommendations

    if not recs:
        return (
            "I've analyzed your site data, but need a few more site-specific constraints to produce high-confidence, "
            "grounded recommendations. Could you share details regarding your specific management goals or soil characteristics?"
        )

    lines = []
    lines.append("Based on the multi-variable ecological profile of your site, here are targeted, scientifically grounded recommendations:\n")

    if assessment_output.overall_confidence:
        lines.append(f"**Overall Assessment Confidence**: `{assessment_output.overall_confidence.upper()}`")
        if assessment_output.confidence_rationale:
            lines.append(f"*{assessment_output.confidence_rationale}*\n")
        else:
            lines.append("")

    for idx, rec in enumerate(recs, start=1):
        lines.append(f"### {idx}. {rec.action}")
        lines.append(f"**Ecological Mechanism**: {rec.mechanism}\n")
        
        if rec.variable_interactions:
            lines.append("**Cross-Variable Interactions & Synergies**:")
            for inter in rec.variable_interactions:
                lines.append(f"- *{inter}*")
            lines.append("")

        if rec.impacted_metrics:
            lines.append(f"**Impacted Metrics**: {', '.join(rec.impacted_metrics)}")

        lines.append(f"**Expected Outcome**: {rec.estimated_effect}")
        lines.append(f"**Implementation Horizon**: `{rec.time_horizon}` | **Scientific Confidence**: `{rec.confidence.upper()}`\n")

        if rec.sources:
            lines.append("**Scientific Evidence & Citations**:")
            for src in rec.sources:
                doc = src.document_title
                pub = src.publisher
                pg = f"p. {src.page}" if src.page else src.section_title
                url = f" ({src.url_or_doi})" if src.url_or_doi else ""
                lines.append(f"- [{pub}, {src.year}] *{doc}* ({pg}){url}")
            lines.append("")

    lines.append("---")
    lines.append("*These recommendations are grounded in peer-reviewed protocols from FAO, IPCC AR6 WGII, and the CBD Kunming-Montreal Framework.*")

    return "\n".join(lines)
