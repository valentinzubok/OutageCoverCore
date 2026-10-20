# OutageCover

<p align="center">
  <img src="assets/logo.png" alt="OutageCover" width="120" />
</p>

<p align="center">
  <strong>Outage insurance that pays when validators agree the provider's own status page reported the incident.</strong>
</p>

<p align="center">
  <a href="https://valentinzubok.github.io/OutageCover/"><img src="https://img.shields.io/badge/Live-Console-f87171?style=flat-square" alt="Live console" /></a>
  <a href="https://github.com/valentinzubok/OutageCoverCore/actions/workflows/ci.yml"><img src="https://github.com/valentinzubok/OutageCoverCore/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/GenLayer-Studio%20Dev%2061997-f87171?style=flat-square" alt="Studio Dev" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="MIT" /></a>
</p>

---

## The trust problem

Parametric insurance is supposed to pay on a fact instead of a claims adjuster. The weak spot is
who reports the fact. A price oracle cannot read "API major outage, 47 minutes" off a status page,
and an insurer that decides for itself whether the outage counted is a claims adjuster again.

**OutageCover makes "did the provider's own status page report a qualifying incident inside the
cover period?" a consensus question**, and lets the answer move the money. Everything that
decides it is fixed when the pool opens.

## What a policyholder trusts

Read this before buying cover; the console shows the same thing next to the buy button.

| Pool | What it means | What you rely on |
|---|---|---|
| **VERIFIED** | The provider site publishes `/.well-known/genlayer-status.json` listing this status page and this service. Validators read it when the pool opens **and again in every settlement round**. | Whoever controls the provider's site. A page on another host is refused at `open_pool`; if the attestation disappears or stops listing the page, that round is `inconclusive`. |
| **UNVERIFIED** | The provider publishes no attestation. Allowed, and the flag is stored with the pool. | The underwriter's choice of page. Check that the page really is the provider's before you buy. |

`buy_cover` takes the pool's **terms hash** (provider site, page, rule, verified flag, dates,
multiple, schedule). A buyer cannot end up covered on terms they did not confirm.

```
open_pool(pool_id, service, provider_site, status_url, incident_rule, sales_close_in,
          cover_length, multiple, settle_interval, rounds_required)       PAYABLE, >= 1 GEN
buy_cover(pool_id, confirmed_terms_hash)                                  PAYABLE
settle(pool_id)       anyone, after cover ends and strictly BEFORE settle_deadline
                      validators freeze the page and agree on one finding:
                        incident      -> proposes or confirms "incident"
                        clean         -> counts only if the whole page was read
                        inconclusive  -> nothing proposed or overturned
                      a different answer restarts the count;
                      rounds_required agreeing rounds -> TRIGGERED or CLEAN
expire(pool_id)       anyone, AT or after settle_deadline: VOID, every premium back
claim / withdraw_underwriter / withdraw_credit                            pull payments
get_round(pool_id, n) the full evidence of round n, kept for good
list_pools(offset, limit)                                                 paged registry
```

### Why it fails the way it does

| Risk | What stops it |
|---|---|
| An attacker's page under a provider's name | The page must be under the declared provider site. For a VERIFIED pool the provider's own site must list the page; an attestation that does not list it, or names another service, leaves the pool UNVERIFIED and says so. |
| The provider site changes hands or drops the page | The attestation is re-read every round: missing or no longer listing the page → `inconclusive` (`attestation_missing`), no verdict. |
| "Clean" decided from part of a long page | `clean` only counts when the validators read the whole page (`covers_whole_document`). A clean answer from excerpts is stored as `inconclusive` (`clean_from_incomplete_page`). A pool that never gets a complete reading ends VOID, premiums back. |
| A late keeper choosing the outcome | `settle` is refused at or after the deadline, `expire` before it. `get_schedule` never offers both. |
| Evidence lost when the page changes | Every round stores provider site, URL, fetch status, time, SHA-256 of the page, total chars, completeness, the exact excerpts read with their hash, the attestation, the model's answer and the finding. |
| A registry that fills up | No pool cap. Pools, policies, rounds and credits are `TreeMap`s keyed by id with a `DynArray` index; a pool costs at least 1 GEN of collateral; `list_pools` is paged. |
| A refused payment shown as success | The console checks chain state after every call; a refusal is shown as "NOT opened" / "NOT covered" with the credit and a button to take it back. |
| The insurer deciding the outage "did not count" | Nobody decides. `settle` takes a pool id only; no owner, no setters. |
| Buying cover after the outage started | Sales close before cover starts. |
| One wrong reading pays or denies | `rounds_required` agreeing rounds, a full interval apart; a different answer restarts the count. |
| The status page steering the model | Page text is fenced as untrusted data, instruction-like phrasing flagged and stored. Only the JSON literals `"incident"`, `"clean"`, `"inconclusive"` are accepted. |
| A refused call stranding money | Payable methods never raise once value is attached: what they cannot escrow is credited. |

## Live

| | |
|---|---|
| Console | **https://valentinzubok.github.io/OutageCover/** (reads work with no wallet) |
| Network | GenLayer Studio Dev / Studio Next — chain `61997` |
| Contract (v2) | [`0x9A42C69cB0d0136065998d37Eb4bf00593686615`](https://explorer-studio-dev.genlayer.com/address/0x9A42C69cB0d0136065998d37Eb4bf00593686615) — CI checks the deployed code equals [`contracts/OutageCover.py`](contracts/OutageCover.py) |
| Deploy record | [`STUDIO_DEV_DEPLOY.md`](STUDIO_DEV_DEPLOY.md) — 22 transactions: an attacker's page, a dust pool, wrong terms, an incomplete page, an incident confirmed over two rounds, a settle refused after the deadline, expiry, and the evidence still readable after the page was deleted |
| v1 | `0xF99E…991B`, [its run](docs/STUDIO_DEV_V1_RUN.md) |

## Demo provider sites

Folders in this repository, served by `raw.githubusercontent.com`:

- [`providers/harbor`](fixtures/providers/harbor) publishes
  [`.well-known/genlayer-status.json`](fixtures/providers/harbor/.well-known/genlayer-status.json)
  listing `history.html` (a long incident history) and `calm.html` (no incidents; the console's
  default page, so a reviewer can open a VERIFIED pool). `api.html` reported the demo's outage and
  was deleted after settlement.
- [`providers/nobody`](fixtures/providers/nobody) publishes no attestation, so pools on
  it open UNVERIFIED.

## The console

[`web/`](https://github.com/valentinzubok/OutageCover/tree/main/web/) — Next.js 16 + `genlayer-js` + MetaMask, exported statically to Pages. Pools load
20 at a time. Each pool shows its trust badge, a "before you buy" card with the provider site, the
page and what you rely on, the settlement deadline, and every round with its evidence. Success is
decided by reading the contract after the call ([`outcome.ts`](https://github.com/valentinzubok/OutageCover/tree/main/web/src/lib/outcome.ts)).

The console lives in [OutageCover](https://github.com/valentinzubok/OutageCover/); this repository holds the contract, its tests and the deploy record.

## Tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest -q      # 59 tests
sh scripts/lint_current_sdk.sh
```

[`tests/test_outagecover.py`](tests/test_outagecover.py) is grouped by the review points: source
authenticity (attacker host, look-alike domain, an attestation that does not list the page or
names another service, ownership change between rounds, an altered report, an unreachable
provider), the deadline boundary (one second before, at, after; schedule never offers both),
incomplete evidence (clean from excerpts → inconclusive, incident from excerpts still counts),
history (every round kept, readable after the page is edited and deleted), the registry (more pools
than the old cap, paging), refused payables credited, malformed answers, injection, and the books
balancing through a random run.

## License

[MIT](LICENSE) © 2026 Valentyn Zubok
