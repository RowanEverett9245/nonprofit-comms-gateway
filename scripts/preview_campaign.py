from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nonprofit_comms.request_models import (
    CampaignSnapshot,
    CommunicationsRequest,
    Donation,
    VolunteerShift,
)
from nonprofit_comms.service import get_sender


def main() -> None:
    request = CommunicationsRequest(
        donation=Donation(donor_name="Jordan Lee", amount=Decimal("125"), goods_value=Decimal("25")),
        volunteer=VolunteerShift(
            volunteer_name="Sam Rivera",
            shift_name="Saturday pantry setup",
            hours_until_shift=18,
        ),
        campaign=CampaignSnapshot(
            campaign_name="Summer Pantry",
            raised=Decimal("18400"),
            target=Decimal("25000"),
            donor_count=143,
        ),
    )
    plan, draft = get_sender().preview(request)
    print(f"receipt_status={plan.receipt_status}")
    print(f"reminder_priority={plan.reminder_priority}")
    print(draft)


if __name__ == "__main__":
    main()
