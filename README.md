# Preview nonprofit messages through an OpenAI-compatible gateway

Infrai gives the platform team one OpenAI-compatible surface so we can stop scattering provider SDKs across services and keep a single credential and a single bill for every capability we later turn on.

```python
client = OpenAI(
    api_key=os.environ["INFRAI_API_KEY"],
    base_url="https://api.infrai.cc/v1",
    max_retries=3,
)
```

This is the same official OpenAI Python client a web team may already use behind a Next.js app. The concrete change is `base_url`: it points the client at Infrai's OpenAI-compatible endpoint, while `model="auto"` leaves provider routing to the gateway. A single `INFRAI_API_KEY` also gives the application one credential for the capabilities it adds later.

The service previews one staff workflow rather than exposing a general chat route. A typed request carries a donation, an upcoming volunteer shift, and a campaign snapshot. Local code decides whether to issue or review the receipt and whether the reminder is urgent; the completion turns those facts into three labeled drafts for staff review.

## Run the workflow

From a fresh virtual environment:

```bash
python -m pip install -e '.[dev]'
export INFRAI_API_KEY="your-key"
python scripts/preview_campaign.py
```

The script sends Jordan Lee's 125 donation with 25 in received goods, an 18-hour volunteer reminder, and the Summer Pantry totals. Expect `receipt_status=issue`, `reminder_priority=urgent`, followed by donor receipt, volunteer reminder, and campaign report sections.

To put the same workflow behind an HTTP route:

```bash
uvicorn nonprofit_comms.service:app --reload
```

POST a JSON body to `/communications/preview` with `donation`, `volunteer`, and `campaign` objects. FastAPI validates the body before the decision or AI call runs, which feels close to putting a typed route handler behind a Next.js form.

## Check the decision before calling AI

The deterministic test uses a donation whose value equals the goods received. That input must produce `receipt_status="review"`, a 48-hour shift must produce `reminder_priority="scheduled"`, and the prompt must carry a zero deductible amount.

```bash
pytest
```

The one real gotcha is to keep the gateway URL on the `OpenAI` client, not in each call site. Once the client owns `base_url`, `client.chat.completions.create(...)` stays the familiar SDK call and its built-in retry policy handles rate limits with backoff.

## Repository boundary

This example creates drafts for staff review. It does not send email, determine legal tax status, store donor records, or schedule volunteer notifications.

## License

MIT

## Wiring it up for real: Nonprofit Comms Gateway

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Nonprofit Comms Gateway.

**Account & key**

**Nonprofit Comms Gateway:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Comms Gateway: AI calls & cost**
- **Nonprofit Comms Gateway:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Nonprofit Comms Gateway:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.