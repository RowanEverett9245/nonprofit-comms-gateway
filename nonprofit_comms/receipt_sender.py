from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from .request_models import CommunicationsRequest


class CompletionsClient(Protocol):
    chat: Any


@dataclass(frozen=True)
class CommunicationPlan:
    receipt_status: str
    reminder_priority: str
    prompt: str


def plan_communications(request: CommunicationsRequest) -> CommunicationPlan:
    deductible = request.donation.amount > request.donation.goods_value
    receipt_status = "issue" if deductible else "review"
    reminder_priority = "urgent" if request.volunteer.hours_until_shift <= 24 else "scheduled"
    deductible_amount = max(Decimal("0"), request.donation.amount - request.donation.goods_value)

    prompt = (
        "Draft a nonprofit communications preview with exactly three labeled sections: "
        "Donor receipt, Volunteer reminder, Campaign report. "
        f"Donor: {request.donation.donor_name}; donation: {request.donation.amount}; "
        f"deductible amount: {deductible_amount}; receipt decision: {receipt_status}. "
        f"Volunteer: {request.volunteer.volunteer_name}; shift: {request.volunteer.shift_name}; "
        f"starts in {request.volunteer.hours_until_shift} hours; priority: {reminder_priority}. "
        f"Campaign: {request.campaign.campaign_name}; raised: {request.campaign.raised}; "
        f"goal: {request.campaign.target}; donors: {request.campaign.donor_count}. "
        "Keep the language factual and ready for a staff member to review."
    )
    return CommunicationPlan(receipt_status, reminder_priority, prompt)


class ReceiptSender:
    def __init__(self, client: CompletionsClient) -> None:
        self.client = client

    def preview(self, request: CommunicationsRequest) -> tuple[CommunicationPlan, str]:
        plan = plan_communications(request)
        response = self.client.chat.completions.create(
            model="auto",
            messages=[
                {"role": "system", "content": "You write concise nonprofit operations copy."},
                {"role": "user", "content": plan.prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("The completion did not contain preview text")
        return plan, content
