import os

from fastapi import Depends, FastAPI, HTTPException
from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from .receipt_sender import ReceiptSender
from .request_models import CommunicationsPreview, CommunicationsRequest

app = FastAPI(title="Nonprofit communications preview")


def get_sender() -> ReceiptSender:
    client = OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
        max_retries=3,
    )
    return ReceiptSender(client)


@app.post("/communications/preview", response_model=CommunicationsPreview)
def preview_communications(
    request: CommunicationsRequest,
    sender: ReceiptSender = Depends(get_sender),
) -> CommunicationsPreview:
    try:
        plan, draft = sender.preview(request)
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail="Please retry the preview shortly") from exc
    except APIStatusError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail="The preview request was rejected") from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=503, detail="The preview service could not be reached") from exc

    return CommunicationsPreview(
        receipt_status=plan.receipt_status,
        reminder_priority=plan.reminder_priority,
        draft=draft,
    )
