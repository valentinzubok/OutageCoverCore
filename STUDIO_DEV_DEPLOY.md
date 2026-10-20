# OutageCover v2 — Studio Dev (chain 61997) deploy record

| | |
|---|---|
| **Network** | GenLayer Studio Dev / Studio Next — chain `61997` |
| **Contract** | [`0x9A42C69cB0d0136065998d37Eb4bf00593686615`](https://explorer-studio-dev.genlayer.com/address/0x9A42C69cB0d0136065998d37Eb4bf00593686615) |
| **Deploy tx** | [`0x9e09b6d1…6e58cc`](https://explorer-studio-dev.genlayer.com/tx/0x9e09b6d16bbf8eef4d5e6d91dcbfcdce5161f449d577b308bbb9abfead6e58cc) from `0x06721Ec34a405d7bbfeF398fdD320EDBEE9C976F`, which has no role in the contract |
| **Source** | [`contracts/OutageCover.py`](contracts/OutageCover.py) — runner `py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng` |
| **Source sha256** | `bb36860c6fcc0728daab97bf41a00684bf7510c2b9398e8834aa97a1595e22fd` |
| **Previous deployment** | `0xF99E82326c4971d36dC71Bec29985c358939991B` — [its run](docs/STUDIO_DEV_V1_RUN.md) |

## What v2 changes, point by point

| Review point | v2 |
|---|---|
| **Source authenticity** | `open_pool` takes a `provider_site` (https origin + optional path). The status page must be under it, checked in code. Validators read `provider_site + /.well-known/genlayer-status.json`; the pool is **VERIFIED** only if it lists the page and names the service, which only whoever controls the site can publish. It is re-read in every settlement round: if it disappears, that round is `inconclusive` (`attestation_missing`) and no model is asked. UNVERIFIED pools are allowed but carry the flag, and `buy_cover` requires the pool's `terms_hash` (site, page, rule, verified flag, dates, multiple), so a buyer confirms the source they are trusting. The trust model is stated at the top of the contract, in the README and in the console. |
| **Settlement deadline** | `settle` is accepted only strictly before `settle_deadline`; `expire` only at or after it; `get_schedule` never offers both. A late round is refused before any fetch. |
| **Incomplete evidence** | Three findings: `incident`, `clean`, `inconclusive`. `clean` counts only when the validators read the whole page (`covers_whole_document`); a clean answer from excerpts becomes `inconclusive` (`clean_from_incomplete_page`). Inconclusive rounds propose and overturn nothing. A pool that never gets a complete clean reading ends VOID with every premium returned. |
| **Historical evidence** | Every round is stored in `rounds_log[pool#n]` and never truncated: provider site, page URL, fetch status, SHA-256 of the whole page, total chars, completeness, the exact excerpts the validators read and their SHA-256, the attestation read in that round, the model's answer, the finding, the reason, the outcome. `get_round(pool, n)` returns it. |
| **Registry capacity** | No global cap. Pools, policies, rounds and credits live in `TreeMap`s keyed by id (`genlayer.storage`), with a `DynArray` index; a write touches one entry, not the whole registry. Opening a pool costs at least 1 GEN of collateral. `list_pools(offset, limit)` pages the index (limit ≤ 50); the console loads 20 at a time, newest first. |
| **Refused payable operations in the console** | Success is decided from chain state after the call, never from the receipt: a pool counts as opened only if `get_pool` returns it with this underwriter; a purchase only if `get_policies` lists the buyer. A refusal is shown as "NOT opened" / "NOT covered", with the credit and a "take it back" button. `web/src/lib/outcome.ts` holds that logic and `outcome.test.ts` tests it (11 tests, in CI). |

## Verify the source yourself

```bash
curl -s -X POST https://studio-dev.genlayer.com/api -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"gen_getContractCode","params":["0x9A42C69cB0d0136065998d37Eb4bf00593686615"]}' \
  | python3 -c "import sys,json,base64,hashlib; print(hashlib.sha256(base64.b64decode(json.load(sys.stdin)['result'])).hexdigest())"
shasum -a 256 contracts/OutageCover.py
# both print bb36860c6fcc0728daab97bf41a00684bf7510c2b9398e8834aa97a1595e22fd
```

## Lint

`sh scripts/lint_current_sdk.sh` — `genvm-lint lint`, `check`, `typecheck`: passed, in CI. `check` runs
on a copy with the public runner `1jb45aa8…` because Studio Dev accepts only `5jycge4q…`, which is
in no public GenVM release.

## The run

| Role | Address |
|---|---|
| underwriter | `0xBB10E67f1aCcCE9DcCD3bEe7F24A8F5F1f36f48d` |
| Ann (buyer) | `0x2eC378B4E55dafe222c76Ed5a2d61AC0d6B7Ec68` |
| Ben (buyer who confirms the wrong terms) | `0x46417a947e661dd47BbD4a523436bE88758b2d07` |
| Cat (underwriter of the unverified pool, buyer) | `0xAF068A87D5E08d65A886A95eFD9935bd18e17D82` |
| stranger (attacker, keeper) | `0x5197B12a00443D272c171528851C74C9a8c6E45e` |

Demo provider sites are folders of this repository served by `raw.githubusercontent.com`:
`https://raw.githubusercontent.com/valentinzubok/OutageCover/main/web/public/fixtures/providers/harbor` publishes [`.well-known/genlayer-status.json`](https://github.com/valentinzubok/OutageCover/blob/main/web/public/fixtures/providers/harbor/.well-known/genlayer-status.json);
`https://raw.githubusercontent.com/valentinzubok/OutageCover/main/web/public/fixtures/providers/nobody` publishes none. During the cover period the provider published a major outage on
`api.html` by commit [`a9f14b4`](https://github.com/valentinzubok/OutageCover/commit/a9f14b48d013fbf7d0832aad576a3c5644c44504) (15:49:49 UTC).

| # | Call | Sender | Result | What happened | Tx |
|---|------|--------|--------|---------------|----|
| 1 | `open_pool(api-2)` value 4 GEN | underwriter | SUCCESS | `api-2`: 4 GEN, provider site `…/providers/harbor`, page `…/harbor/api.html`, ×4, 2 rounds 60 s apart. Validators read the provider's attestation: lists the page and the service → **VERIFIED** | [`0xc76898f8…c252cf`](https://explorer-studio-dev.genlayer.com/tx/0xc76898f867f6bb13d2797c75c9e120212b9addd1814e9d105b25cb88a2c252cf) |
| 2 | `open_pool(hist-1)` value 2 GEN | underwriter | SUCCESS | `hist-1`: 2 GEN, page `…/harbor/history.html` (8 842 chars of incident history), 1 round → **VERIFIED** | [`0x37d0b336…45869b`](https://explorer-studio-dev.genlayer.com/tx/0x37d0b336dea4f92f58ec6b8be14d64584e8e43ba83e36fb51a359c386d45869b) |
| 3 | `open_pool(mirror-1)` value 1 GEN | Cat | SUCCESS | `mirror-1`: 1 GEN, site `…/providers/nobody` which publishes no attestation → opened **UNVERIFIED**, flag stored and in the terms hash | [`0x7e5cd67f…c975a5`](https://explorer-studio-dev.genlayer.com/tx/0x7e5cd67fe3ab5fcb27d30fbe85511d82cd5577068cf62cb18a2e6e9a9dc975a5) |
| 4 | `open_pool(fake-1)` value 2 GEN | **stranger** | SUCCESS | `fake-1`: status page `https://attacker.example/harbor-status` under the Harbor site name → refused in the return value: `the status page must be under the provider site`; 2 GEN credited | [`0x36aee382…845473`](https://explorer-studio-dev.genlayer.com/tx/0x36aee382dc7219f76df1bff4b9629d0297b9a2e69416b2cee103c174f5845473) |
| 5 | `open_pool(dust-1)` value 0.5 GEN | **stranger** | SUCCESS | `dust-1`: 0.5 GEN → refused: `collateral is below the minimum of 1000000000000000000 wei`; credited | [`0x593fa3e8…fcae19`](https://explorer-studio-dev.genlayer.com/tx/0x593fa3e82011bd420d4fd952c5f788d587ecda3ca096254c4175bd2dcafcae19) |
| 6 | `buy_cover(api-2)` value 0.5 GEN | Ann | SUCCESS | 0.5 GEN with the pool's terms hash → covered, pays 2 GEN | [`0x7fa47678…8b52d5`](https://explorer-studio-dev.genlayer.com/tx/0x7fa47678d34d2d71242f0b9e1403698c1d7c1033da283c01ab1b8c970f8b52d5) |
| 7 | `buy_cover(api-2)` value 0.5 GEN | **Ben** | SUCCESS | 0.5 GEN with a wrong terms hash → refused: `the confirmed terms do not match this pool's terms`; credited, no policy recorded | [`0x5e43ce0a…43446e`](https://explorer-studio-dev.genlayer.com/tx/0x5e43ce0a03435c40e81030a19fc9490a0624ce92aece4b1c489b25151743446e) |
| 8 | `buy_cover(hist-1)` value 0.5 GEN | Cat | SUCCESS | `hist-1`: 0.5 GEN → covered | [`0x8b8cc7c0…7b6f44`](https://explorer-studio-dev.genlayer.com/tx/0x8b8cc7c09397f3b53a653fee45025ef9a9e942240ec6e954912eba12de7b6f44) |
| 9 | `buy_cover(mirror-1)` value 0.2 GEN | Ann | SUCCESS | `mirror-1`: 0.2 GEN → covered | [`0xd625d64e…6c9163`](https://explorer-studio-dev.genlayer.com/tx/0xd625d64ea308670b1149b7182ea93014b77b5577c25296fdaed1ff6ed26c9163) |
| 10 | `settle(hist-1)` | stranger | SUCCESS | `hist-1` round 1: validators read 2 710 of 8 842 chars (`complete: false`) and answered **inconclusive** (`validators_inconclusive`). Nothing proposed; a clean answer here would also have been downgraded | [`0xbb20e3c5…e545d5`](https://explorer-studio-dev.genlayer.com/tx/0xbb20e3c55e6d91fd3009ff96c8c118f454c247531c84f7c54218337454e545d5) |
| 11 | `settle(mirror-1)` | stranger | SUCCESS | FINALIZED. `mirror-1`: short page read whole, **clean** → final CLEAN (1 round) | [`0x16e83cd1…c9e61d`](https://explorer-studio-dev.genlayer.com/tx/0x16e83cd113d3120bdc452a553c53730b3a657b8f5841f592962406f40bc9e61d) |
| 12 | `settle(api-2)` | stranger | SUCCESS | `api-2` round 1: page with the outage published during cover read whole, attestation re-read and valid → **incident**, proposed | [`0x180f2bf2…cf2f9c`](https://explorer-studio-dev.genlayer.com/tx/0x180f2bf2fb4d40f2c66937cf9c98a3cf66c4bc08f8d3387a02c0810256cf2f9c) |
| 13 | `settle(api-2)` | stranger | SUCCESS | FINALIZED. `api-2` round 2: **incident** confirmed → TRIGGERED | [`0x4f62536d…6d86df`](https://explorer-studio-dev.genlayer.com/tx/0x4f62536d9502d1f419ca6ac9368cde24b8f86b70fa929638341325612c6d86df) |
| 14 | `claim(api-2)` | Ann | SUCCESS | FINALIZED. claim 2 GEN | [`0x1e9dc5ff…f32571`](https://explorer-studio-dev.genlayer.com/tx/0x1e9dc5ff2895525ad19de6305e772497931fc3f2e9ed4e897d141cf3dbf32571) |
| 15 | `withdraw_underwriter(api-2)` | underwriter | SUCCESS | FINALIZED. `api-2` remainder: 4 + 0.5 − 2 = 2.5 GEN | [`0xa43546c8…a5c5a9`](https://explorer-studio-dev.genlayer.com/tx/0xa43546c8617be59e97cb78c57ab7865f86cb8ae8e7654ae61a0855b29aa5c5a9) |
| 16 | `withdraw_credit()` | Ben | SUCCESS | FINALIZED. the refused 0.5 GEN back | [`0x7aba00a8…380d93`](https://explorer-studio-dev.genlayer.com/tx/0x7aba00a8f70f48793d5f643ed902b44c725a960fdb1a418cf1c852b5ff380d93) |
| 17 | `withdraw_credit()` | stranger | SUCCESS | FINALIZED. the refused 2.5 GEN back | [`0xbb288ca0…b255a0`](https://explorer-studio-dev.genlayer.com/tx/0xbb288ca0696e22d05fb193dd8a314fe0377ea122e7a269aa843ae4428eb255a0) |
| 18 | `settle(hist-1)` | stranger | **ERROR** | sent after `hist-1`'s deadline (chain time 1792511958 ≥ 1792511776): **UserError** `the settlement deadline has passed at 1792511776; only expire is accepted` | [`0xc4943450…f09fd4`](https://explorer-studio-dev.genlayer.com/tx/0xc49434507a7e1199ae661ec8ad255ffb5c44f3994ec9004a4677929dd2f09fd4) |
| 19 | `expire(hist-1)` | stranger | SUCCESS | `expire`: `hist-1` → VOID | [`0x1b2d35b5…9eff65`](https://explorer-studio-dev.genlayer.com/tx/0x1b2d35b5721394a29ea10a6e57e5c269b6ce865b8f2f3fe18c35a35a909eff65) |
| 20 | `claim(hist-1)` | Cat | SUCCESS | FINALIZED. VOID: the 0.5 GEN premium back | [`0x386c0fc4…e08fee`](https://explorer-studio-dev.genlayer.com/tx/0x386c0fc4ace1f21c21f7ce74e2d65634b07482478f377a1b093e6346b3e08fee) |
| 21 | `withdraw_underwriter(hist-1)` | underwriter | SUCCESS | FINALIZED. VOID: the 2 GEN collateral back | [`0x1d36edbe…1d4295`](https://explorer-studio-dev.genlayer.com/tx/0x1d36edbe995e3918f5c0969f0c2b90dfe9b75db0243a6d909a64d3dbef1d4295) |
| 22 | `withdraw_underwriter(mirror-1)` | Cat | SUCCESS | FINALIZED. `mirror-1` CLEAN: collateral + premium, 1.2 GEN | [`0xf43fd7a2…2f38b0`](https://explorer-studio-dev.genlayer.com/tx/0xf43fd7a2dafacab85fae9023cfc4b9a2b2fbaa618946b5f5ae1c1c350c2f38b0) |

### Evidence after the page is gone

After settlement the status page was deleted by commit
[`65adf36`](https://github.com/valentinzubok/OutageCover/commit/65adf3613b2d3447b1b952e82b5ba486a1796d27). `get_round("api-2", 1)` still returns, from
chain: retrieved at 1792511660, URL `…/harbor/api.html`, page SHA-256
`9a1c5bf7e95358f301e3dd880a8a03e16905736c72f017e8393bf29750d0d2a8`, excerpts SHA-256
`398ba16c71bb61f13dcde88b9a2c50983d8ff2b673810e8b82f1a1b3e9a5d2fe`, and the 534 characters the validators read (the
whole page, raw HTML as served: `… Current status: Operational. The incident below is resolved. … 2026-10-20
15:49:49 UTC - Major outage - the API returned errors for every request …`).

### What this run did not show

Between the two `api-2` rounds a postmortem line was committed
([`debabff`](https://github.com/valentinzubok/OutageCover/commit/debabffbde43da5c8448065f038b50318a8cd9b9)), but `raw.githubusercontent.com` was still
serving the cached page 65 s later, so both rounds recorded the same page hash. Rounds that read
different page versions are covered by `test_an_altered_report_is_judged_on_what_the_page_says_at_settlement`
and `test_evidence_survives_the_page_being_edited_and_deleted`.

End state: `list_pools(0, 10)` → `api-2 triggered`, `hist-1 void`, `mirror-1 clean`;
`get_balance` → `{"balance":"0","credits":"0","held":"0"}`.
