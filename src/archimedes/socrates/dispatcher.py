from __future__ import annotations

from dataclasses import dataclass

from archimedes.models.socrates import SocratesReviewContext


@dataclass(slots=True)
class DispatchMessage:
    context: SocratesReviewContext
    formatted_context: str
    recipients: list[str]


@dataclass(slots=True)
class DispatcherExecutor:
    """Formats the review context and broadcasts it to persona executors."""

    recipients: list[str]

    async def dispatch(self, context: SocratesReviewContext) -> DispatchMessage:
        return DispatchMessage(
            context=context,
            formatted_context=self.format_context(context),
            recipients=self.recipients,
        )

    @staticmethod
    def format_context(context: SocratesReviewContext) -> str:
        option_lines = []
        for option in context.architecture_options:
            option_id = option.get("option_id") or option.get("id") or option.get("name")
            summary = option.get("summary") or option.get("name") or "No summary"
            option_lines.append(f"- {option_id}: {summary}")

        business_need = (
            context.business_need.get("refined_statement")
            or context.business_need.get("raw_input")
            or "No business need supplied"
        )
        criteria = ", ".join(context.evaluation_criteria) or "standard architecture criteria"
        return (
            f"Business need: {business_need}\n"
            f"Evaluation criteria: {criteria}\n"
            "Options:\n"
            + "\n".join(option_lines)
        )
