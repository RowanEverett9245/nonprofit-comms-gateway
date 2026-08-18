from dataclasses import dataclass
from decimal import Decimal

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    @dataclass
    class Donation:
        donor_name: str
        amount: Decimal
        goods_value: Decimal = Decimal("0")

    @dataclass
    class VolunteerShift:
        volunteer_name: str
        shift_name: str
        hours_until_shift: int

    @dataclass
    class CampaignSnapshot:
        campaign_name: str
        raised: Decimal
        target: Decimal
        donor_count: int

    @dataclass
    class CommunicationsRequest:
        donation: Donation
        volunteer: VolunteerShift
        campaign: CampaignSnapshot

    @dataclass
    class CommunicationsPreview:
        receipt_status: str
        reminder_priority: str
        draft: str
else:
    class Donation(BaseModel):
        donor_name: str = Field(min_length=1)
        amount: Decimal = Field(gt=0)
        goods_value: Decimal = Field(default=Decimal("0"), ge=0)

    class VolunteerShift(BaseModel):
        volunteer_name: str = Field(min_length=1)
        shift_name: str = Field(min_length=1)
        hours_until_shift: int = Field(ge=0)

    class CampaignSnapshot(BaseModel):
        campaign_name: str = Field(min_length=1)
        raised: Decimal = Field(ge=0)
        target: Decimal = Field(gt=0)
        donor_count: int = Field(ge=0)

    class CommunicationsRequest(BaseModel):
        donation: Donation
        volunteer: VolunteerShift
        campaign: CampaignSnapshot

    class CommunicationsPreview(BaseModel):
        receipt_status: str
        reminder_priority: str
        draft: str
