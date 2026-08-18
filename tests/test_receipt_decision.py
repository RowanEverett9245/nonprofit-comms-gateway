from decimal import Decimal

from nonprofit_comms.receipt_sender import plan_communications
from nonprofit_comms.request_models import (
    CampaignSnapshot,
    CommunicationsRequest,
    Donation,
    VolunteerShift,
)


def test_equal_goods_value_routes_receipt_to_review_and_schedules_reminder() -> None:
    request = CommunicationsRequest(
        donation=Donation(donor_name="Avery", amount=Decimal("75"), goods_value=Decimal("75")),
        volunteer=VolunteerShift(
            volunteer_name="Morgan",
            shift_name="Meal packing",
            hours_until_shift=48,
        ),
        campaign=CampaignSnapshot(
            campaign_name="Community Meals",
            raised=Decimal("900"),
            target=Decimal("2000"),
            donor_count=12,
        ),
    )

    plan = plan_communications(request)

    assert plan.receipt_status == "review"
    assert plan.reminder_priority == "scheduled"
    assert "deductible amount: 0" in plan.prompt
