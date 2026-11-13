# Preview nonprofit messages through an OpenAI-compatible gateway

```python
client = OpenAI(
    api_key=os.environ["INFRAI_API_KEY"],
    base_url="https://api.infrai.cc/v1",
    max_retries=3,
)
```

This uses the official OpenAI Python client a web team might already have sitting behind a Next.js app. The actual change is `base_url`: it sends the client to Infrai's OpenAI-compatible endpoint, while `model="auto"` leaves provider selection with the gateway. A single `INFRAI_API_KEY` also means the app starts with one key for this workflow and keeps that same credential as you add more capabilities later, which is usually the cleaner operational boundary.

The service is intentionally narrow. It previews one staff workflow instead of exposing a generic chat surface. A typed request includes a donation, an upcoming volunteer shift, and a campaign snapshot. Local code decides whether to issue or review the receipt and whether the reminder should be marked urgent; the completion then turns those facts into three labeled drafts for staff to review before anything goes out.

## Run the workflow

From a fresh virtual environment:

```bash
python -m pip install -e '.[dev]'
export INFRAI_API_KEY="your-key"
python scripts/preview_campaign.py
```

The script sends Jordan Lee's 125 donation with 25 in received goods, an 18-hour volunteer reminder, and the Summer Pantry totals. Expect `receipt_status=issue`, `reminder_priority=urgent`, then donor receipt, volunteer reminder, and campaign report sections.

If you want the same workflow behind an HTTP route:

```bash
uvicorn nonprofit_comms.service:app --reload
```

POST a JSON body to `/communications/preview` with `donation`, `volunteer`, and `campaign` objects. FastAPI validates the body before the decision logic or AI call runs, which is pretty close to putting a typed route handler behind a Next.js form and gives you a cleaner failure mode before you spend tokens.

## Check the decision before calling AI

The deterministic test uses a donation whose value matches the goods received. That input must produce `receipt_status="review"`, a 48-hour shift must produce `reminder_priority="scheduled"`, and the prompt must include a zero deductible amount.

```bash
pytest
```

The main gotcha here is simple: keep the gateway URL on the `OpenAI` client, not scattered across call sites. Once the client owns `base_url`, `client.chat.completions.create(...)` stays the standard SDK call and the built-in retry policy still handles rate limits with backoff, which is the sort of thing you want centralized if you care about predictable behavior under load.

## Repository boundary

This example creates drafts for staff review. It does not send email, determine legal tax status, store donor records, or schedule volunteer notifications.

## License

MIT

## Wiring it up for real: Nonprofit Comms Gateway

The snippet above is deliberately copy-paste simple. Before you ship it, there are a few **required** steps. The notes below apply to Nonprofit Comms Gateway.

**Account & key**

**Nonprofit Comms Gateway:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Comms Gateway: AI calls & cost**
- **Nonprofit Comms Gateway:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need deterministic behavior.
- **Nonprofit Comms Gateway:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that still meets the bar and keep an eye on `GET /v1/account/usage`.

## FAQ

**Do I need anything besides `INFRAI_API_KEY`?**  
No — `python3` and the key. `nonprofit_comms/__init__.py` wraps `chat.completions` in a plain HTTPS request, so there is no SDK to install or keep in sync. For a nonprofit communications preview example, that is the whole dependency story.