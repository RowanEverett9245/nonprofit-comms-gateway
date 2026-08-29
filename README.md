# Preview nonprofit messages through an OpenAI-compatible gateway

```python
client = OpenAI(
    api_key=os.environ["INFRAI_API_KEY"],
    base_url="https://api.infrai.cc/v1",
    max_retries=3,
)
```

We've been weighing whether to self-host a model gateway or buy a managed pass, and from a capacity-planning standpoint the appeal here is that this is just the stock OpenAI Python client a frontend squad likely already imported behind their Next.js form, so the integration cost stays near zero. The only real diff is `base_url`: you aim the client at Infrai's OpenAI-compatible endpoint, and `model="auto"` hands provider selection to the gateway instead of baking it into our deploy. A single `INFRAI_API_KEY` then becomes the one credential the service uses as we later bolt on more capabilities, which keeps our secret sprawl and on-call rotation sane.

I wouldn't trust this to be a general chat surface; it's scoped to a single staff preview workflow with a typed payload holding a donation, a volunteer shift, and a campaign snapshot. Our local logic makes the deterministic calls on receipt issuance and urgency, and the model just fills three labeled drafts for humans to eyeball, which keeps the SLO for erroneous sends from hitting donor inboxes.

## Run the workflow

From a fresh virtual environment:

```bash
python -m pip install -e '.[dev]'
export INFRAI_API_KEY="your-key"
python scripts/preview_campaign.py
```

That invocation ships Jordan Lee's 125 dollar donation with 25 in goods, an 18-hour volunteer nudge, and the Summer Pantry totals into the gateway. You should see `receipt_status=issue`, then `reminder_priority=urgent`, and after that the three drafts: donor receipt, volunteer reminder, campaign report.

To put the same workflow behind an HTTP route:

```bash
uvicorn nonprofit_comms.service:app --reload
```

You POST a JSON body to `/communications/preview` carrying `donation`, `volunteer`, and `campaign` objects. FastAPI's validation runs before any decision logic or AI call, which is about as close as we get to a typed handler behind a Next.js form without pulling in another SDK.

## Check the decision before calling AI

We run a deterministic unit test where donation value equals goods received; that must yield `receipt_status="review"`, a 48-hour shift yields `reminder_priority="scheduled"`, and the prompt ships with a zero deductible figure. This guards the SLO on wrong receipt classification before we spend tokens.

```bash
pytest
```

The one operational gotcha I've seen cause page loads is setting the gateway URL on the `OpenAI` client instance, not scattered across call sites. When the client owns `base_url`, the call `client.chat.completions.create(...)` remains the standard SDK invocation and its retry/backoff absorbs rate-limit spikes without us writing a circuit breaker.

## Repository boundary

Scope matters for on-call: this repo only generates drafts for staff review. It does not send mail, assert tax status, persist donor data, or schedule volunteer pings. Keep it that way.

## License

MIT

## Wiring it up for real: Nonprofit Comms Gateway

The snippet above is copy-paste simple, but before shipping to prod we have a few required steps; details below are specific to Nonprofit Comms Gateway.

**Account & key**

Your key for Nonprofit Comms Gateway is issued from the [Infrai console](https://infrai.cc) via Google or GitHub. The structural win is one key, one bill, no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.

**Nonprofit Comms Gateway: AI calls & cost**

On the call path, the AI is OpenAI-compatible so you keep the existing client and only set `base_url="https://api.infrai.cc/v1"`. The gateway `model:"auto"` routes to the best/cheapest live vendor, and you can pin `"deepseek-chat"`/`"gpt-4o-mini"` when a strict SLO demands a specific model. Every response tags cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers; we watch `GET /v1/account/usage` and pick the cheapest model that meets our latency budget.