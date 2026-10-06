# RS-P1-CORE / CORE-05 — Durable Turns, Receipt Recovery and Save Slots

Date: 2026-10-05 (Asia/Seoul) | Executor/reviewer: Sol | Instruction: EXECUTED | Implementation: ACCEPTED/DONE

Current execution acceptance is §11; §§1–10 retain the exact instruction and historical authoring evidence. Director authorized execution with "다음꺼 ㄱ". Parent remains IN_PROGRESS pending a separate representative-slice review.

Historical authoring context: Director requested the next item after [CORE-04 acceptance](RS-P1-CORE_04_EVENTS_NPC.md#10-core-04-execution--acceptance--2026-10-05). This delivery authors the next instruction and independent expectations; it does not implement persistence. Self-review is not independent-person review. Parent RS-P1-CORE remains IN_PROGRESS; CORE-01/02/03/04 DONE. NEXT: execute this order.

Authority: current director instructions; [coding template](../prompts/SOL_CODING_WORK_ORDER.md); [parent slice](RS-P1-CORE_VERTICAL_SLICE.md); [B01](../../architecture/BLOCK_01.md) ownership/dependencies; [B02](../../architecture/BLOCK_02.md) COMMIT/publication; [B03](../../architecture/BLOCK_03.md) canonical CORE/protocol/queues; [B04](../../architecture/BLOCK_04.md) A7/A9; [B05](../../architecture/BLOCK_05.md) A10/A12. Preserve [MASTER](../MASTER_GAME_ARCHITECTURE.md) product outcomes and [primary prompt](../ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md) invariants. No governance/CI/dependency/primary-spec/engine/oracle change is authorized.

## 1. Work Order / Decisions

| Field | Concrete contract |
|---|---|
| task_id/title | RS-P1-CORE / CORE-05: persist one prepared turn, resolve uncertain commits, export/load validated slots |
| goal | The accepted watch gameplay path survives process exit without changing CORE/pending/protocol, retries or replay; SQLite commits before the existing single head publication |
| non_goals | New gameplay, emotion/persona/BDI/memory, client/IPC/supervisor, cloud saves, concurrent readers/writers, provider/content generation, package-blob support, historical migration transforms, performance/release/power-loss qualification |
| prerequisites | CORE-01–04 accepted; refreshed 1009-test baseline, Ruff and strict mypy; source/hash checks; stdlib SQLite profile/probes in §9 |
| baseline | HEAD/main `efd2478ff8a6ed93ee833c3f8464a0efdd8a181a`; 117 entry raw hashes and tool results in [vectors](RS-P1-CORE_05_REFERENCE_VECTORS.json); dirty inventory §2 |
| read_files | Exact existing callers/owners in §2; B04 A9 plus linked accepted orders; reference artifact is READ after authoring |
| allowed_edit_paths | Exactly §3, NEW/MODIFY as stated; implementation must preserve all old assertions and bytes |
| public_contract | Frozen checkpoint/request/recovery/slot DTOs and typed commit port; optional Driver/_restore commit injection; app durable session and explicit attachment tokens in §4 |
| behavior/edge_policy | §§5–7: changed-row transaction, full causal queue, bounded receipts/segments, proven recovery, atomic slot publication, exact version/pin rejection |
| examples | §8 and independently derived artifact; old six fixture byte/hash expectations remain READ |
| algorithms/wiring | §9, one existing Driver; no evaluate-then-save wrapper or second simulation/state owner |
| performance | Brain ≤512 MiB; durable turn p95≤100 ms/p99≤250 ms and local Ruff+six goldens≤20 s remain TARGET. This order measures local feedback only; no full snapshot per ordinary turn and bounded SQL row writes are inspectable acceptance |
| baseline/verification_commands | §9; actual authoring results §10; future runtime checks NOT_RUN |
| test_responsibilities | §8/§9: real DB, real engines/Driver, filesystem/process faults only at adapter boundary; no mocked domain outcomes or regenerated oracle |
| acceptance | §9: sparse durable/live turn, old compatibility, complete old/new recovery, exact queue/receipt identity, safe slot load, version rejection, rotation and source-layer checks |
| stop_conditions | Unexpected source/hash changes, unsupported package/rule migration, need for another edit path, ambiguous durable head, unexplained baseline failure or overlapping user edit. Inspect safe in-scope alternatives, then report actual evidence and the needed decision |
| delivery | Record actual file paths/callers, commands/results, crash boundaries, limits and self-review; update five delivery docs. No task deletion, agent, install, commit/push or external write |

Fixed choices:

- Embedded stdlib SQLite; format_version=1 is the first Reverie Saga save format, separate from replay fixture version 1 and Quilltale/v1. Current accepted gameplay pins do not change.
- One attachment owns a working database and one Driver. SQLite stores committed representation; engines receive their existing typed observed reads and never SQL/paths/bytes.
- Changed component/queue/protocol rows plus one receipt, compact replay step and header commit together. Keep 1024 receipts, all ≤16 stream cursors/tombstones, ≤4096 pending events and ≤4096 committed steps per retained replay segment.
- Slots `slot01`…`slot08`, one current and at most one previous validated generation per slot. Load into a new private working file; never replace an open working database or reconstruct current state by rerunning commands.
- Supported save versions exactly `(1,)`; forward migration registry is empty because no older Reverie save format exists. Older unsupported/future/legacy rejection is required now. Actual migration edges require a later source-specific instruction and independent fixtures.
- Current registered selections and six golden checkpoints have empty accepted package/build pins. Reject nonempty pins with SAVE_PACKAGE_UNAVAILABLE; do not claim package preservation support, silently drop dependencies, read providers or invent package blobs. Preserve this required later capability in the backlog.

## 2. Actual Source / Entry Evidence

Tracked dirty: `docs/ASTRA_ENGINE_ARCHITECTURE_PROMPT_v2.6_AI_PRODUCED_RPG_EN.md`, `docs/MASTER_GAME_ARCHITECTURE.md` (preexisting). Untracked prior work: BACKLOG/SESSION_HANDOFF, architecture/order/reference documents, config/lock, src/{app,contracts,domain,engines,orchestration}, tests/{unit,integration,replay}. `git status --short` records directories; artifact raw hashes identify actual files. Preserve all prior work. No root AGENTS.md found; archived AGENTS_v1 is historical evidence. Remote freshness unchecked.

Existing READ contracts/callers:

- `src/contracts/turn.py`: GameCommand, CommitReceipt, StoredReceipt, ProtocolSnapshot, TurnPublication and unchanged TurnOutcome union. Stream high-water and retention already work; no new command ID or receipt shape.
- `src/contracts/state_io.py` and `src/orchestration/serialization.py`: selected registered StateIO; strict component/pending/protocol codecs, `hash_core_document`, receipt validation, world/pin identity and event-policy rights. Reuse; add no watch dispatch to generic persistence.
- `src/orchestration/turn.py:Driver.__init__/_submit`: validates candidate and prepared effects, then currently assigns `_head = _Head(candidate, next_protocol)` inside a broad candidate-exception handler. This exact boundary needs durable injection and recovery-aware error handling; memory-only callers must preserve behavior.
- `src/app/headless.py:_restore`: constructs that Driver under one selected IO. `restore_checkpoint` and `_CheckpointFactory` currently create memory-only owners. Extend only `_restore` with optional injection; existing public bootstrap/restore/replay defaults remain memory-only.
- `src/orchestration/replay.py:Runner`: accepts ReplayStep.expected_witness=None and compares all four hashes/outcome. `decode_fixture` deliberately requires complete witnesses. Durable compact segments use typed ReplayTrace/Runner directly; do not weaken fixture codec or existing full witnesses.
- `src/app/watch.py:_bootstrap/bootstrap_watch`, `src/app/watch_registry.py:watch_bundle`: representative ten-record owner, trusted future wake and fixed gameplay pins. No source edits here; compose bootstrap snapshot/protocol with the durable app constructor.
- `src/domain/canonical.py`, `src/domain/state_types.py`, `src/domain/primitives.py`, `src/orchestration/events.py:queued_sort_key`, scheduler/RNG/read views, all feature engines/codecs, all prior tests/config/lock/specs/oracles: READ.

Observed gap: no current SQL owner, commit port, disk format, slot coordinator, recovery lifecycle or attachment token. A wrapper that calls `submit` and subsequently writes a checkpoint would expose non-durable success and lose causal/receipt atomicity; forbidden.

Tool evidence: CPython 3.13.12, bundled SQLite 3.50.4, Ruff 0.16.6, mypy 2.4.0, pytest 9.1.1; 13-package dev lock unchanged. Python baseline ≥3.12; SQLite ≥3.37 required for STRICT tables. Only the installed Python/SQLite pair is probed, not every supported minor/platform. Existing Python launcher location stderr is non-failing. SQLite is a bundled stdlib capability, not a new pip dependency.

## 3. Exact Future Implementation Scope

NEW production (all absent at authoring; namespace `adapters` follows existing layer direction, no new __init__ file):

```text
C:\Reverie Saga\src\contracts\persistence.py
C:\Reverie Saga\src\orchestration\persistence.py
C:\Reverie Saga\src\adapters\sqlite_store.py
C:\Reverie Saga\src\adapters\save_slots.py
C:\Reverie Saga\src\app\durable.py
```

MODIFY production, only optional commit/lifecycle injection and named helper wiring:

```text
C:\Reverie Saga\src\orchestration\turn.py
C:\Reverie Saga\src\app\headless.py
```

NEW tests/helpers:

```text
C:\Reverie Saga\tests\unit\durability_fixtures.py
C:\Reverie Saga\tests\unit\test_save_codec.py
C:\Reverie Saga\tests\integration\test_durable_turn.py
C:\Reverie Saga\tests\integration\test_sqlite_recovery.py
C:\Reverie Saga\tests\integration\test_save_slots.py
C:\Reverie Saga\tests\replay\test_durable_replay.py
```

Two NEW canonical JSON expectation fixtures, copied from this order's independent artifact, never from production/Recorder:

```text
C:\Reverie Saga\tests\replay\fixtures\durable_watch_v1.json
C:\Reverie Saga\tests\replay\fixtures\durable_watch_passive_v1.json
```

They contain the `main` and `passive` projection/vector objects respectively, not SQLite file bytes and not the old ReplayFixture format. SQLite binary hashes are export observations only, not cross-version golden or gameplay identity.

Canonical UTF8 fixture SHA256 (no trailing newline): durable_watch_v1.json=`4c9dcfea46c1f1ba0c08b0fc94d9a13211fb7e32fd52a43eaf7bdf0233425472`; durable_watch_passive_v1.json=`f0adc9c19bbb94fd4fe3f6e1a70bf95e63a1221e7f354b3a09a237c592616951`.

MODIFY delivery docs only: this order's execution/acceptance section, `C:\Reverie Saga\BACKLOG.md`, `C:\Reverie Saga\SESSION_HANDOFF.md`, `C:\Reverie Saga\docs\work_orders\RS-P1-CORE_VERTICAL_SLICE.md`, `C:\Reverie Saga\docs\work_orders\PHASE0_CONTRACTS.md` (dated API supersession; preserve historical evidence). Reference artifact becomes READ. All other source/tests/config/lock/fixtures/specs/policies/tools/CI/C:\Quilltale paths forbidden. Existing Ruff permits adapter SQLite/Path calls without modifying config; `time`, global RNG, environment APIs and mocks remain restricted as before. Filesystem/OS adapter functions are not engine imports.

Authoring scope NOW: NEW this order and its vectors; MODIFY only BACKLOG, SESSION_HANDOFF and parent slice. No production/test/init/config/architecture edit.

## 4. Public Contracts / Callers

`contracts/persistence.py` imports existing domain/contracts types. Frozen/slotted DTOs below; field names/order exact; no Any/object/open payload dict, filesystem path or SQLite handle crosses this contract. SaveError(RuntimeError) has exact constructor `__init__(self, code: str, detail: str) -> None`, storing both attributes; SaveUnavailable, CommitUncertain and WorldUnavailable inherit that constructor. SaveUnavailable means absence proved, CommitUncertain means result unresolved, WorldUnavailable means admission blocked. Do not convert CommitUncertain/WorldUnavailable into generic ENGINE_EXCEPTION.

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from contracts.replay import ReplayTrace
from contracts.turn import CommitReceipt, GameCommand, ProtocolSnapshot, TurnPublication
from domain.state_types import CoreSnapshot

@dataclass(frozen=True, slots=True)
class DurableCheckpoint:
    core: CoreSnapshot
    protocol: ProtocolSnapshot

@dataclass(frozen=True, slots=True)
class DurableTurn:
    previous: DurableCheckpoint
    next: DurableCheckpoint
    command: GameCommand
    publication: TurnPublication

@dataclass(frozen=True, slots=True)
class RecoveryCommitted:
    checkpoint: DurableCheckpoint
    receipt: CommitReceipt

@dataclass(frozen=True, slots=True)
class RecoveryAbsent:
    checkpoint: DurableCheckpoint

type RecoveryResult = RecoveryCommitted | RecoveryAbsent

@dataclass(frozen=True, slots=True)
class SaveSegment:
    checkpoint: DurableCheckpoint
    trace: ReplayTrace

@dataclass(frozen=True, slots=True)
class SaveExportReceipt:
    slot_id: str
    revision: int
    core_hash: str
    protocol_hash: str
    file_sha256: str
    directory_synced: bool

@dataclass(frozen=True, slots=True)
class SaveLoadReceipt:
    slot_id: str
    revision: int
    core_hash: str
    protocol_hash: str
    attachment_id: str

class DurableCommitPort(Protocol):
    def persist(self, turn: DurableTurn) -> CommitReceipt: ...
    def recover(self, turn: DurableTurn) -> RecoveryResult: ...
```

Exact modified signatures:

- `Driver.__init__(..., *, io: StateIO, commit_port: DurableCommitPort | None = None) -> None`; all existing parameters/order retained. No port means existing memory-only path with identical hashes/publications/errors.
- `app.headless._restore(..., *, io: StateIO | None = None, commit_port: DurableCommitPort | None = None) -> _Session`; forward port to Driver. No other old public function/Protocol signature changes.
- `Driver.recover_pending() -> TurnPublication`: only with a retained uncertain DurableTurn; successful resolution publishes once or returns absence abort; no pending request raises SaveError(NO_RECOVERY_PENDING). Failure leaves blocked lifecycle and raises WorldUnavailable(SAVE_UNCERTAIN). `Driver.detach() -> None`: quiescent owner operation, permanently blocks submit/reject_malformed/recovery; repeated detach is harmless. Immutable historical snapshot/protocol reads remain permissible.
- Driver ordinary submit/reject_malformed reject blocked/detached owner with WorldUnavailable, before malformed/admission/duplicate logic. Never return stale last_publication as the unresolved request's result.

`orchestration/persistence.py` public boundaries:

- `checkpoint_document(checkpoint: DurableCheckpoint, *, io: StateIO) -> JsonObject` / `decode_checkpoint(document: JsonObject, *, io: StateIO) -> DurableCheckpoint`.
- Closed checkpoint body exactly `{core, protocol, header}`; header is the existing ReplayHeader document pinned to this checkpoint. It has initial hashes, world/seed/pins and empty build_artifacts; reuse existing types and hash tags. Decode validates all fields/pins/CORE/protocol before returning typed data.
- `prepare_turn(turn: DurableTurn, *, io: StateIO) -> SaveRowPlan`: pure, private frozen row DTOs implement the exact SQL mapping in §5. Compare canonical old/new row bytes to produce only changed/deleted addresses; include compact committed replay step, next metadata/hashes, optional rotation checkpoint and exact base revision/CORE/protocol hashes. Plan DTO is orchestration→adapter only, never an engine argument.
- `decode_segment(checkpoint: DurableCheckpoint, bodies: tuple[bytes, ...], *, io: StateIO) -> SaveSegment`: validate exact compact step schema, canonical bytes/digests/command/outcome/branch and contiguous committed revision chain; construct ReplayStep with witness=None. Runner executes this optional verification separately; startup loads current rows without rerunning gameplay.

`adapters/sqlite_store.py:SqliteCommitStore` implements DurableCommitPort:

- `@classmethod create(cls, path: Path, checkpoint: DurableCheckpoint, *, io: StateIO) -> SqliteCommitStore`; exclusively create a new working store; existing destination is SAVE_EXISTS, zero overwrite.
- `@classmethod open(cls, path: Path, *, io: StateIO) -> SqliteCommitStore`; existing file only, lock then recover/validate before attachment. Missing path is SAVE_NOT_FOUND, not empty creation.
- `load() -> DurableCheckpoint`, `retained_segment() -> SaveSegment`, `persist(turn) -> CommitReceipt`, `recover(turn) -> RecoveryResult`, `backup_to(destination: Path) -> None`, `close() -> None`.
- Adapter functions `validate_save(path: Path, *, io: StateIO) -> DurableCheckpoint` and `read_segment(path: Path, *, io: StateIO) -> SaveSegment` inspect immutable closed slot backups read-only, without lifetime working attachment. Never URI immutable=1 on a potentially hot working store. Recover uncertain work by reopening the locked working DB in normal mode, allowing SQLite journal recovery.

`adapters/save_slots.py:SqliteSlots(store: SqliteCommitStore, root: Path, *, io: StateIO)` owns `export(slot_id: str) -> SaveExportReceipt` and `stage_load(slot_id: str) -> SqliteCommitStore`. stage_load returns a fully validated, attached private working store, not a published Driver. Ownership transfers to the caller, which closes it on failure. Slot root is application-approved local directory, default `<working-parent>/slots`; slot IDs never accept paths.

`app/durable.py` owns a new `DurableSession` (not a widened old HeadlessSession):

- `create_durable(path: Path, checkpoint: DurableCheckpoint, *, bundles: tuple[FeatureBundle, ...]) -> DurableSession` and `resume_durable(path: Path, *, bundles: tuple[FeatureBundle, ...]) -> DurableSession`. Compile one selected IO; no infer/default registry from stored bytes.
- `attachment_id: str` and `working_path: Path` properties (app boundary only); `snapshot() -> CoreSnapshot`, `protocol() -> ProtocolSnapshot`, `last_publication() -> TurnPublication`.
- `submit(command: GameCommand, *, attachment_id: str) -> TurnPublication`, `submit_json(body: bytes, *, attachment_id: str) -> TurnPublication`; exact body cap/decode/retry priorities as headless; attachment checked before decoding and before owner submission.
- `export(slot_id: str) -> SaveExportReceipt`, `load(slot_id: str) -> SaveLoadReceipt`, `recover() -> TurnPublication`, `retained_segment() -> SaveSegment`, `close() -> None`, context manager enter/exit.
- No public raw Driver/connection access: app methods route the active attachment. A new opaque 32-lowercase-hex token from app-owned `secrets.token_hex(16)` on create/resume/successful load invalidates queued old-world requests even if branch/revision was rewound. Tokens are excluded from CORE/protocol/save/replay/RNG. Old internal Driver aliases are detached after successful swap. Unknown token raises SaveError(STALE_ATTACHMENT) without mutation; closed session raises WorldUnavailable(SESSION_CLOSED).
- `main(argv: Sequence[str] | None = None) -> int`, live CLI: `python -m app.durable --working PATH --create` or `--working PATH` to resume; no create fallback on resume failure. Create uses existing WatchBootstrapSpec(zero seed/branch, ones stream), bootstrap_watch and its checkpoint, explicit `(watch_bundle(),)`.
- CLI emits canonical startup `{kind:"attached",attachment_id,working_path,revision,core_hash,protocol_hash}`, with the resolved absolute app-owned path as UTF8 text. Subsequent stdin is closed envelopes `{kind:"command",attachment_id,command}` / `{kind:"export",slot_id}` / `{kind:"load",slot_id}` / `{kind:"recover"}`. Envelope cap 32768 bytes; contained command canonical bytes cap 16384. Unknown/malformed envelope yields canonical `{kind:"save_error",code:"INVALID_REQUEST"}` without simulation. Commands emit existing encoded TurnPublication; export emits `{kind:"exported",receipt:{...exact DTO fields...}}`; load emits `{kind:"loaded",working_path,receipt:{...exact DTO fields...}}`; recover emits resolved publication. Save/WorldUnavailable errors emit `{kind:"save_error",code}` (no exception filesystem details/token echoes), session remains able to recover/close; startup error exits1. Graceful EOF closes handles. Old four CLIs remain unchanged.

## 5. Save Format / Sparse SQL Transaction

The artifact `sqlite_ddl` is normative exact DDL for seven STRICT tables. Canonical bodies are UTF8 BLOBs, never SQLite coercion-derived numbers or Python repr. SQL names/constants trusted; bind all values. Require application_id=`0x52535632` (decimal1381193266), user_version=1, no unexpected tables/views/triggers/indexes beyond DDL auto-indexes. Compare column names/types/PK/unique/CHECK definitions against the accepted schema; `integrity_check` alone cannot establish a compatible format.

| Table | Rows / mapping / validation |
|---|---|
| save_head | Exactly singleton1; format_version1; core_meta=existing CORE document without components/pending; protocol_meta=existing protocol document without streams/receipts; current hashes; checkpoint_revision |
| components | Key `(schema.kind, schema.version, entity_id)`; body is the complete existing `{schema,entity_id,fields}` component document; SHA tag component/v1. Key/body must agree; sorted tuple reconstructs exact CORE |
| pending | Full existing queued document, keyed by header.event_id; ordinal preserves queued_sort_key sequence; SHA pending-event/v1. Keys/ordinals exactly match body/order, unique contiguous0..n−1, n≤4096; no event/cause rewriting |
| streams | Key stream_id; body is complete existing StreamCursor document; reconstruct sorted by ID; ≤16 includes retired |
| receipts | Key command_id, unique revision; body complete existing StoredReceipt document; ≤1024 ordered by revision/ID; fingerprint/actor/branch/sequence/latest hash validate through StateIO |
| checkpoint | Exactly singleton1; full closed checkpoint_document body; SHA save-checkpoint/v1. Creation/rotation/export only; no full checkpoint rewrite on an ordinary turn |
| replay | Key commit revision; compact body exactly `{command,outcome,core_hash,protocol_hash,facts_hash,diff_hash}`; SHA save-step/v1; committed new receipts only, no rejected/aborted/duplicate entry; ≤4096 |

Reconstruct current canonical documents from rows, decode via selected StateIO, validate checkpoint, then recompute BOTH hashes and compare header. No repair/default/drop/reordering to hide a malformed save. All BLOBs must equal canonical_json(decode_json(body)); reject float/bool-for-int/duplicate keys/non-NFC/unknown/missing fields. Enforce existing exact world/pin/hash/event/RNG/rules/schedule identities; accepted gameplay/build packages must be empty in this unit. Bound replay and protocol cardinalities before allocating collections; check database page_count×page_size ≤1 GiB, row body≤64 MiB, checkpoint body≤128 MiB and aggregate materialized canonical row bytes≤256 MiB, command body≤16 KiB. These prototype safety caps are fixed, not a measured memory envelope; SAVE_LIMIT preserves old head.

SQLite profile: page_size4096 for NEW files; verify accepted files match; max_page_count262144; journal_mode=DELETE; synchronous=FULL (2); foreign_keys=ON; trusted_schema=OFF; busy_timeout=0; detect_types=0; check_same_thread=True. No WAL, executescript within transaction, pickle, external DB/service, JSON dump of the full CORE/protocol per ordinary durable commit.

Source-specific transaction refinement to B04 A9.1: `connect(..., autocommit=True, timeout=0)` allows PRAGMA setup outside transactions and explicit SQL `BEGIN IMMEDIATE` before optimistic base checks; use SQL COMMIT/ROLLBACK exclusively. Python Connection.commit()/rollback() are no-ops with autocommit=True and MUST NOT be used. This preserves B04's explicit transaction/single-owner guarantees while replacing its proposed autocommit=False profile, which opens a DEFERRED transaction automatically and conflicts with a subsequent BEGIN IMMEDIATE. Actual probe confirms this distinction. No claim of broad OS durability follows from it. [Python transaction control](https://docs.python.org/3.13/library/sqlite3.html#transaction-control) defines these modes.

Lifetime attachment: a second SQLite handle owns `<resolved-working-path>.lock.sqlite`, fixed singleton attachment table, DELETE journal and busy_timeout0, BEGIN EXCLUSIVE held until close. Never delete/recreate the sidecar on attach/recovery or decide staleness from a PID/mtime. SQLite/OS releases the lock on process termination; subsequent open recovers normally. Two attachment attempts serialize sidecar schema creation and lock acquisition; SQLITE_BUSY maps to SAVE_LOCKED. Only one successful owner proceeds to main DB. Handle/path identity is resolved once; reject symlink/reparse indirection and working/slot/sidecar path alias, require regular local files under app-approved root. Hostile filesystem races/network shares are unsupported, not a sandbox guarantee. Failure after acquiring one handle closes all partial resources. Primitive lock probe passed; application process attachment tests remain required.

Creation: exclusively reserve working path with filesystem create-if-absent; acquire sidecar; configure/schema-create/insert initial rows/header/checkpoint in one transaction; validate before attaching Driver. Failed creation does not overwrite any existing file; owned incomplete file is not auto-resumed as valid. Close/reopen persists initial pending/genesis/protocol exactly.

Existing open must classify signature/application_id/user_version/page profile before any journal-mode/schema-setting write. For a working file that needs hot-journal recovery, inspect its fixed SQLite header first (application_id and user_version are stable in this current-only format), then allow normal SQLite recovery and revalidate the recovered metadata/schema before configuring mutable PRAGMAs. A foreign/newer/unsupported original is never converted or reconfigured. Read-only slots are classified/validated without any write; no homemade journal repair.

Turn algorithm:

1. Existing Driver admits/simulates once, closes views, composes net deltas, creates candidate+next_protocol+prepared no-cue publication, validates all through selected IO. Build DurableTurn from pinned previous and candidate heads. No persistence for reject/abort/exact retry.
2. Pure prepare_turn independently validates both checkpoints, unchanged world/seed/pins/branch/stream membership/actors/status, revision+1, latest receipt/command fingerprint/high-water/retention and prepared facts/diff. It uses prepared facts to compute existing turn-facts/v1 and turn-diff/v1 hashes; no cues or presentation errors enter SQL.
3. BEGIN IMMEDIATE; compare stored previous revision AND CORE/protocol hashes with turn.previous. Mismatch with confirmed rollback is SAVE_STALE (session becomes unavailable until explicit reopen), never overwrite a fresher head. Do not infer success from revision alone.
4. Upsert/delete only changed component rows. Update pending bodies by event ID and ordinal changes; delete only consumed/removed IDs. If surviving ordinals move, lift ONLY affected survivors temporarily to `old_ordinal+4096`, then assign final ordinals, preventing unique-key swaps; check final contiguous ordinals before COMMIT. Unchanged component/queue bodies are not rewritten.
5. Update changed stream cursor, insert one StoredReceipt and deterministically delete evicted oldest receipts; no clear/reinsert of all retained receipts/streams. If previous segment has4096 steps, replace checkpoint with turn.previous, set checkpoint_revision=previous revision, clear only old replay rows, then insert new step. At4096th commit there is no rotation;4097th makes checkpoint revision4096 and segment count1. All rotates/writes belong to this same transaction.
6. Update header to validated next tick/revision/meta/hash plus checkpoint revision; validate final counts/constraints. SQL COMMIT. Receipt returned must equal prepared.receipt, including command ID/base/new revision/tick/hash.
7. Driver publishes one `_Head(candidate,next_protocol)` and prepared publication; existing presentation runs afterward. Postcommit presentation failure retains receipt/full facts/diff/queue and PRESENTATION_FAILED exactly as before.

Load checks checkpoint/header/replay range: checkpoint protocol.revision equals save_head.checkpoint_revision; first step checkpoint_revision+1; contiguous new receipts through current revision; last step CORE/protocol hashes equal current head; each outcome receipt.command_id/base/revision/tick/core_hash matches its command/expected hashes. Zero segment is legal only when checkpoint equals current head. Reject corrupted compact row/digest/chain before creating a Driver. Optional `retained_segment` returns the validated segment; a fresh memory-only Runner verifies game semantics offline. Startup recovery does not need full replay history or re-evaluate commands.

## 6. Durable Failure / Recovery Lifecycle

Only the existing Driver owns memory publication. Internal states ACTIVE → RECOVERING → ACTIVE or UNAVAILABLE; DETACHED terminal. Status is lifecycle, excluded from CORE/protocol/replay. Retain at most one uncertain DurableTurn/prepared effects; all view epochs already closed. Ports may not publish/re-evaluate gameplay themselves.

| Boundary / evidence | Required result |
|---|---|
| Candidate validation/engine/queue failure before persistence | Existing TurnAborted/error priority; no SQL turn, old head/protocol/queue |
| BEGIN/write/constraint/busy/limit error + rollback and validated old head | SaveUnavailable(SAVE_UNAVAILABLE), TurnAborted with empty effects; old memory/disk pair |
| Base mismatch | SAVE_STALE boundary error; block attachment, preserve both heads; explicit resume required |
| COMMIT raises, unexpected port exception, returned receipt mismatch, or failure after possible durability | Mark RECOVERING, retain request, clear current submission publication; close/reopen connection under same attachment; inspect validated durable receipt+head, never generic abort/retry |
| Recovery matches exact prepared next CORE+protocol/hash+receipt/fingerprint | RecoveryCommitted; install exact prepared next once, then normal postcommit presentation; return original receipt; action not rerun |
| Recovery matches exact previous CORE+protocol/hash, candidate receipt absent, segment/header unchanged | RecoveryAbsent; return SAVE_UNAVAILABLE abort, old pair; action not rerun automatically |
| Receipt missing by itself / newer unrelated revision / mixed heads / mismatched fingerprint / cannot reopen/validate | WorldUnavailable(SAVE_UNCERTAIN); block every command/query/export/load; allow recover/close only; do not claim confirmed abort/success |
| After durable commit/process kill before head or client reply | Next startup opens current rows; original retry returns retained receipt without evaluation or new SQL step |
| After head before reply / presenter error | Committed pair retained, retries follow existing no-republish/resync rules |

Recover must prove full previous or full next, not merely lookup=None. Candidate sequence is within newly prepared retained window, so matching next implies its receipt is present. HEAD can remain internally previous during unreadable recovery but is not exposed as an active world; app snapshot/protocol/last_publication raise WorldUnavailable while unresolved. `recover_pending` retries validation on the retained request, not engines; any recovery failure remains blocked and emits no finalized ReplayStep. Independent process restart has no request cache: validate current DB, restore accepted latest head, then normal retry receipt/high-water semantics resolve client uncertainty.

Move durable exceptions outside the existing broad candidate abort interpretation or add explicit typed exception handling that preserves the same effect. Unexpected failures after persist begins ALWAYS undergo resolution; only proven rollback/absence permits finalized SAVE_UNAVAILABLE. In particular, commit success followed by injected exception must not return ENGINE_EXCEPTION while disk is new and memory old.

[SQLite atomic commit](https://www.sqlite.org/atomiccommit.html) describes rollback-journal recovery subject to filesystem/device assumptions. Application process-kill fault tests qualify these named boundaries; they cannot establish physical power-loss behavior, Windows packaging/lifecycle or MIN-SPEC performance. Never remove a hot journal to make validation pass.

## 7. Slot Export / Load / Compatibility

Operations run only at a quiescent ACTIVE owner boundary. Pause admission for the duration; repeated/concurrent call fails SAVE_BUSY. CLOSED/DETACHED/RECOVERING owners cannot export/load. Export and load do not advance tick/revision or draw gameplay RNG.

Export:

1. Validate exact slot ID regex `slot0[1-8]`; resolve `<root>/<slot>.sqlite`, `<slot>.previous.sqlite` and unique same-directory temp filenames. No arbitrary paths, separator, case folding, trim or implicit default slot.
2. Pin current committed DB/header; store.backup_to an exclusively created temporary destination using SQLite Connection.backup(pages=128). Backup is not byte-copy of a live DB. The lifetime owner prevents concurrent turns; compare resulting checkpoint hashes/revision against the pin.
3. Validate schema/application/user versions, integrity/foreign keys, all selected IO pins/current rows/queued causes/protocol/replay segment, page/byte limits. Close all destination SQLite handles, fsync file. Invalid temp cannot replace a slot. [SQLite backup API](https://www.sqlite.org/backup.html) is the snapshot mechanism.
4. If current slot exists, validate it first; a corrupt existing slot is SAVE_CORRUPT and remains untouched until a separate repair decision. Back it up to another validated/fsynced temp and replace previous generation. Then os.replace new temp→current on same filesystem. No working DB/lock-sidecar replacement; at most current+previous remain as accepted generations.
5. Sync parent directory where supported and return receipt with actual directory_synced bool and SHA256 of final closed file. Windows prototype may return false; this explicitly qualifies file flush/process-atomic replacement only, not fully durable directory metadata/power-loss save. No fictitious fsync success. A failure after replace is SAVE_EXPORT_UNCERTAIN and must inspect/validate final file; never claim the old slot necessarily remains.
6. Failure BEFORE final replace returns SAVE_EXPORT_FAILED (or precise invalid/validation code), current slot unchanged; previous generation may already have advanced to the same old current file. Temps are never auto-promoted. Close and remove only files exclusively created by this operation; startup does not delete unknown leftovers/user files.

Load:

1. Validate slot read-only while existing world remains attached. New selected IO must match all pins; reject corruption/rules/versions/packages before owner creation. No silent fallback to previous, another bundle, new game or provider regeneration.
2. Consistent backup into a unique `<working-parent>/.loaded-<token>.sqlite`, never raw live copy, acquire its own lifetime attachment, validate fully. Permit at most8 such managed working files per approved directory, including the prospective file; count regular matching files before exclusive creation, fail SAVE_LIMIT on a ninth. Unknown crash leftovers are counted and never auto-promoted/deleted. Current singleton owner is serialized; broader directory multi-owner management remains unsupported. Failure closes staging handles and removes only its exclusively created staging file/sidecar after closing, leaving old driver/token/CORE/protocol/store/slot unchanged.
3. Construct fresh Driver with same selected bundle/IO, exact saved seed/world/tick/pending/protocol and new commit port, with no simulation. Allocate new attachment token. Publish active app session/store/driver/token as one prepared owner swap at quiescence; detach previous Driver and close previous store afterward. No mutable session objects leaked before swap.
4. Old queued requests/token/Driver aliases cannot submit to new owner; branch and protocol receipts remain unchanged. CLI loaded result reports the new attachment token/revision/hashes and actual working_path outside the DTO. Original caller-owned working file and source slot remain retained. After a subsequent successful load, remove a superseded clone only if this SAME live session exclusively created it, all its handles are closed and resolved file/sidecar targets remain under the approved directory; never infer ownership from filename alone or delete an original/resumed user file. Retain the active clone on close for restart. Later `--working` resume uses the returned actual path; eight-clone cap bounds leftovers across restarts. Cleanup UI/automatic retention of caller-owned saves is later work.
5. Reset app-held publication/read aliases on load; absent submission last_publication has existing no-submission error. DERIVED UI/retrieval caches are not currently present; no fake cache-reset subsystem. Domain records/queued IDs/order/hashes remain identical and next wake fires once at its original due tick.

Load compatibility priority: validate regular file/SQLite signature and application ID first; foreign application IDs (including0)→UNSUPPORTED_LEGACY_SAVE; matching ID with user_version>1→NEWER_SAVE_VERSION; user_version≤0→UNSUPPORTED_SAVE_VERSION; current schema mismatch/malformed data→SAVE_CORRUPT; schema/rules/schedule/RNG/hash/catalog pin mismatch→UNSUPPORTED_RULESET; nonempty accepted packages/build pins→SAVE_PACKAGE_UNAVAILABLE. Missing path→SAVE_NOT_FOUND. No original-source writes/migrations on reject. Local capacity/attachment contention→SAVE_LIMIT/SAVE_LOCKED. Current format only, empty migration chain; future explicit forward edges must copy to staging and preserve original before validation/publication.

## 8. Independent Examples / Test Responsibilities

Artifact reference_source imports only hashlib/json/struct; it projects independently authored CORE-04 requirement documents into full canonical row bodies, tagged digests and sparse row differences. It never calls Driver/StateIO/Recorder/production or Quilltale. Previous six golden expectations and gameplay formulas remain READ. New scalar/component/pending leaves are independently recomputed using u32 framing; alternate `length.to_bytes(4,"big")` recomputation must agree.

- Initial head: ten component rows, one future Wake due2, one actor-bound stream/high-water0, zero receipts/replay, checkpoint revision0. Initial CORE/protocol hashes equal CORE-04's literals; stored canonical rows reconstruct their full documents byte-for-byte.
- Main13 input publications contain exactly nine NEW commits at input indices `[0,1,2,3,8,9,10,11,12]`. Duplicate step4 returns its revision2 receipt with current tick6/revision4 and RESYNC_REQUIRED; stale/conflict/invalid-target inputs5/6/7 add no SQL/replay/receipt row. Sparse row differences for each case are literal in vectors.
- Final main head: tick27/revision9, CORE `fcd439a74234d1d51a79d06fd029850afa43bf64d5c1eb5331fe25e84d5035df`; future Wake due28 with exact cause/event ID, nine retained receipts/one stream/ten components, nine compact replay rows/checkpoint0. Restore then wait1 delivers due28 once and queues due30; compare with an uninterrupted fresh owner using independent gameplay requirements, not a saved production trace.
- Passive wait16: one outer commit/revision1, all eight NPC pulses and next Wake due18 retained, charge3; full CORE/pending/protocol/publication match CORE-04 independent passive fixture. Persistence writes final changed component rows, not one row per second/fact.
- Receipt boundaries: commits1024→receipts1..1024;1025→2..1025;1030→7..1030 with high-water1030. Exact retained ID recovers original receipt; evicted ID≤high-water returns RETRY_WINDOW_EXPIRED. Do not use 1025 expensive gameplay commands merely to derive expectations; independently calculate retention, then also exercise an actual owner around a legal high-water checkpoint boundary.
- Segment boundaries:4096→checkpoint0/4096 steps;4097→checkpoint4096/1 step;8192→checkpoint4096/4096;8193→checkpoint8192/1. Seed a genuinely validated complete compact segment/checkpoint, test actual transaction rotation/rollback/backup/Runner boundaries; never replace semantic gameplay with a fake success engine. Protocol latest receipt bounds still apply separately.
- Pending ordinal swap `[A0,B1]→[B0,A1]` must not violate temporary UNIQUE values; bodies/IDs unchanged. This generic adapter conformance example uses valid selected policy events/fresh IO, not illegal reordered watch checkpoint semantics. DDL row-level swap can be tested directly without claiming a new prototype event behavior.
- SQL staging faults retain complete old rows/header/receipt/queue; thrown-after-real-COMMIT wrapper resolves next, not abort; unreadable recovery blocks commands and publication until repaired/reopened; retries never invoke real engine twice.
- Export→close→fresh resume and slot load preserve BOTH hashes/protocol/queued causes and exact delayed next wake. Inject backup/validation/file flush/previous replace/final replace/directory flush failures at filesystem adapter boundary; distinguish pre-replace failure from post-replace uncertainty. Old world/token stays active on failed load; successful load rejects old token even for identical branch/revision.
- Malformed UTF8/duplicate keys/unknown fields/float/bool/row key/body mismatch/duplicate ordinal/stranded or invalid causal wake/non-NFC/package pins/wrong schema/version/missing stream/receipt/latest hash/corrupt replay chain fail before Driver factory restore. No source mutation/default success.

PLANNED tests:

| Path / names | Responsibility |
|---|---|
| unit/durability_fixtures.py | Fresh selected watch/toy/trial/encounter helpers; READ new independent literal vectors; independently calculated retention/rotation setups; no runtime-generated oracle |
| unit/test_save_codec.py | test_projection_matches_independent_rows, test_checkpoint_closed_codec, test_sparse_row_changes, test_strict_save_rows, test_segment_chain, test_retention_boundaries, test_pending_ordinal_swap |
| integration/test_durable_turn.py | test_real_main_durable_path, test_passive_wait_durable, test_old_memory_paths_unchanged, test_no_persist_for_reject_retry_abort, test_disk_precedes_head, test_confirmed_rollback_atomic, test_postcommit_presentation, test_generic_bundle_no_watch_dispatch |
| integration/test_sqlite_recovery.py | test_process_kill_matrix, test_uncertain_commit_old_or_new, test_unreadable_recovery_blocks, test_recover_without_evaluation, test_second_process_attachment, test_rollback_journal_reopen, test_receipt_eviction_after_resume, test_segment_rotation_atomic, test_sparse_sql_trace |
| integration/test_save_slots.py | test_export_previous_generation, test_export_fault_matrix, test_load_atomic_and_old_token, test_slot_id_and_path_bounds, test_version_pin_rejection, test_limits, test_real_durable_json_cli |
| replay/test_durable_replay.py | test_retained_segment_runner, test_rotation_checkpoint_runner, test_reopen_next_wake, test_corrupt_segment_before_restore, test_wrong_facts_hash_detected, test_fresh_world_isolation |

Process tests use subprocess handshake pipes and terminate only their owned test child; no long sleep, machine power cycling or arbitrary process kill. Production private filesystem/connection calls may be injected at the adapter boundary; real domain/engine/reducer/presenter math and existing assertion oracles remain untouched. Kill positions: after BEGIN, after components, pending, receipt, header, before SQL COMMIT; after COMMIT before head; after head before response. Recover a complete old/new validated state, never partial rows or replayed action. Stdlib authoring probe covers only before/after primitive COMMIT; full live matrix is NOT_RUN until implementation.

## 9. Ordered Execution / Verification / Acceptance

1. Refresh HEAD/status/hash inventory and actual sources. Explain expected three authoring delivery-doc differences; all114 other entry hashes must match. Baseline command results must reproduce or be explicitly diagnosed before editing.
2. Implement frozen contracts and pure checkpoint/row/segment codecs; copy two canonical projection fixtures from the artifact with literal hashes checked independently. No database game rules.
3. Implement exact DDL/profile/attachment/limits/validated create/open/sparse transaction/rollback/reopen recovery and backup adapter; actual SQLite/child-process tests before changing Driver publication.
4. Add optional commit_port and typed uncertain-recovery handling at existing sole head boundary, preserving memory-only flow/presentation/retry priorities; forward only through _restore. Audit every Driver/_restore caller and broad exception path. No evaluate-then-save wrapper.
5. Implement quiescent slot adapter, typed app session/attachment swap/CLI/recovery close. Use existing watch bootstrap/registered StateIO, not another rules/simulation path. Wire app→adapters→orchestration/contracts; orchestration must never import adapters/app/sqlite3/pathlib/secrets or watch IDs.
6. Execute independent normal/boundary/invalid/full live crash/slot/retry/segment replay tests; then existing complete suite/Ruff/strict mypy/six goldens. Diagnose in-scope failures; never edit old assertions, regenerate old oracles, add skip/xfail or weaken fixture codec.
7. Inspect all actual changed/untracked paths, raw protected input hashes, full wiring, SQL trace sparse row writes, canonical outputs and lifecycle/finally behavior. Update five delivery docs with actual evidence, qualify limits. Mark CORE-05 DONE only after acceptance; parent slice completion requires its own review against the representative goal, not full-game completion.

Commands (PowerShell; existing .venv; PYTHONIOENCODING=utf-8 for Unicode probes, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1):

```powershell
git -c safe.directory='C:/Reverie Saga' status --short
git -c safe.directory='C:/Reverie Saga' rev-parse HEAD
.venv/Scripts/python.exe -m pytest -q tests
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy --strict src tests
.venv/Scripts/python.exe -m pytest -q tests/unit/test_save_codec.py tests/integration/test_durable_turn.py tests/integration/test_sqlite_recovery.py tests/integration/test_save_slots.py tests/replay/test_durable_replay.py
.venv/Scripts/python.exe -m pytest -q tests/replay/test_golden.py tests/replay/test_registered_replay.py tests/replay/test_trial.py tests/replay/test_encounter.py tests/replay/test_watch.py
.venv/Scripts/python.exe -m pytest -q tests/replay/test_golden.py::test_core_trace tests/replay/test_trial.py::test_trial_core_trace tests/replay/test_encounter.py::test_encounter_core_trace tests/replay/test_encounter.py::test_encounter_death_trace tests/replay/test_watch.py::test_watch_core_trace tests/replay/test_watch.py::test_watch_passive_trace
git -c safe.directory='C:/Reverie Saga' diff --check
```

New focused test paths are PLANNED/absent now. Run them only on implementation. The listed replay modules cover full qualified compatibility plus negative assertions; do not claim they contain exactly six tests. Measure local Ruff+six explicit qualified golden nodes separately if reporting six-golden feedback. All old six fixture raw hashes must remain unchanged.

Acceptance: real CLI/API→same Driver→one durable SQL COMMIT→one head publication→existing presentation; independent complete main/passive CORE/protocol/publication/row transition and next-wake identity; old memory-only paths and all1009 existing assertions; sparse ordinary writes; bounded receipt/segment/queue; proper COMMIT uncertainty/recovery gating; process attachment/release and named old/new crash boundaries; safe backup/slot replace/load/token swap; current-only version/pin/package/limit rejection; compact Runner catches wrong facts even with equal CORE/protocol; no future migration/package/power-loss/independent-person claim; all necessary checks pass and exact scope holds. Performance/physical power loss/platform packaging remain UNVERIFIED, not acceptance-by-test-count.

## 10. Authoring Evidence / Readiness

Baseline actual: 1009 tests passed in110.88s, Ruff PASS, strict mypy75files PASS. No source/test/config edits. Installed Python3.13.12/SQLite3.50.4 queried directly; dev lock unchanged. Existing launcher diagnostic remained non-failing.

Independent artifact contains:117 entry raw hashes; retained READ CORE-04 main/passive requirement fixtures; stdlib-only executable reference_source;13 main row/publication projections including9 new commits; one passive projection;10 receipt/segment boundary vectors;10 crash-resolution contracts;5 version classifications;7 slot-ID cases; exact seven-table DDL. It recomputes CORE/protocol hashes from literals, full BLOB row bytes and tagged leaves; prospective fixtures do not use SQLite binary file hashes as goldens.

Actual one-off stdlib probes on owned temporary files: exact seven-table STRICT DDL created; DELETE/FULL2/foreign_keys1/trusted_schema0 verified; nine independently specified sparse transitions reached exact final main CORE hash; integrity_check=ok; SQL rollback retained checkpoint0; Connection.commit() with autocommit=True left transaction active, confirming required SQL COMMIT; 128-page backup hash matched; second exclusive sidecar attachment returned SQLITE_BUSY and reacquired after close. Two owned subprocesses killed before/after primitive COMMIT reopened checkpoint0/77 respectively. Probe files cleaned by their scoped TemporaryDirectory; no production module or checker created. These are primitive/schema probes, not live Driver/slots/recovery/crash-matrix execution.

Final authoring verification: reference_source reproduced exact main/passive objects; alternate length.to_bytes framing matched every initial/per-step CORE/protocol and component/pending leaf;10 retention/rotation vectors recomputed with an independent sequential state model; public Python declaration fence AST/compile PASS; actual Driver/_restore callers inspected, old parameter/default contracts retained and six qualified golden node names verified. Reference artifact557856bytes/SHA256=`5f1c69051d76b55d8d207e70d5ea9fe3aa2a23841dd10202956d01398fd4e988`; two prospective canonical fixture SHA values in §3. Final117-input scope check requires114 READ hashes identical and exactly BACKLOG/SESSION_HANDOFF/parent slice different; UTF8/fences/local links/trailing whitespace/Git diff checks recorded at delivery. Future implementation/CLI/new tests and full crash/power-loss/performance/package/migration support NOT_RUN/UNVERIFIED. Current-only save policy is deliberate, not a missing migration placeholder.

Decision: instruction READY; implementation NOT_STARTED. NEXT execute CORE-05 under this exact scope. CORE-01/02/03/04 DONE, parent RS-P1-CORE IN_PROGRESS. Self-review only; no agents/dependency/install/governance/CI/commit/push/external write.

Delivery checks (actual exit0): all117 entry hashes checked,114 READ unchanged and exactly three authorized delivery-doc changes; all prior source/test/config/spec/reference/six fixture bytes preserved. Four delivery documents pass UTF8/fence/Python AST/trailing-whitespace checks and60 local links resolve;15 exact prospective source/test/fixture paths checked against existence markers. Main/passive reference output, complete checkpoint byte/hash and both future fixture literal hashes reproduce. Artifact SHA is pinned in all four docs. `git diff --check` PASS (preexisting primary/MASTER LF→CRLF warnings only); HEAD/main unchanged. Authoring changed exactly this NEW order/NEW vector and MODIFY BACKLOG/SESSION_HANDOFF/parent; no production persistence path exists yet.

## 11. CORE-05 Execution / Acceptance — 2026-10-05

Director authorized implementation with "다음꺼 ㄱ". This section supersedes all authoring NOT_STARTED/NEXT execute statements above. ACCEPTED/DONE after the actual checks below; parent RS-P1-CORE IN_PROGRESS, NEXT separately review the representative slice.

Actual paths/wiring: five new modules from §3 exist; contracts/persistence defines the exact frozen DTOs/port, orchestration/persistence validates closed checkpoint/row/compact segment documents, adapters/sqlite_store owns exact DDL/profile/attachment/sparse transactions/proved recovery/backup, adapters/save_slots owns quiescent generations/private clones, app/durable owns the new app session/attachment swap and live JSON CLI. Driver adds optional commit_port=None plus recovery/detach at its sole head boundary; _restore only forwards it. Old defaults/public signatures/gameplay/pins/fixture format are unchanged. SQL values are bound. Orchestration imports no SQLite/filesystem/app/adapter or watch-specific rule IDs. The prepared head exists before persistence; only successful/proved durability publishes it, then the existing presenter runs. All partial connection/clone paths close owned handles; unknown leftover files are never promoted/deleted.

| Actual check | Result |
|---|---|
| Refreshed entry baseline | 1009 passed in117.91s; historical READ hashes checked before implementation |
| New five focused test modules | 102 passed in148.72s |
| Final complete suite | 1111 passed in 271.79s; 1009 prior assertions plus102 new |
| Ruff / strict mypy | PASS / PASS,86source files; existing configuration/lock unchanged |
| Six explicit old golden nodes | 6 passed in3.68s; local Ruff+six goldens4.5598222s |
| Independent full main/passive requirements | 13publications/9NEW SQL commits and passive wait16 match literal CORE/protocol/publications/component+pending row bytes and checksums |
| Sparse SQL / pending ordinal swap | Only changed rows/cursor/new receipt/compact step/header; no ordinary full checkpoint or stream/receipt rewrite; exact-DDL swap of two real policy-encoded row bodies passes without temporary UNIQUE collision |
| Receipt / segment boundaries | Actual commits1025..1030 retain7..1030; expired ID rejected,retained duplicate exact; independently validated4096/8192 segments rotate at4097/8193,rollback retains full previous segment,backup and fresh Runner pass |
| Live process crash / attachment | Eight owned-child kill positions: BEGIN/components/pending/receipt/header/beforeCOMMIT/afterCOMMIT/afterhead. Reopen complete previous or next head/protocol/queue, exact retry, lifetime sidecar lock released; second process blocked then reattached after close |
| Uncertain / stale / presentation | Throw after real SQL COMMIT resolves next; proved rollback returns SAVE_UNAVAILABLE; unreadable/mixed/mismatched proof blocks queries/commands/export/load until repaired,without NPC re-evaluation; SAVE_STALE blocks; real presenter failure preserves committed disk/head/receipt/facts/diff |
| Slots / CLI / generic selections | Current/previous generations,pre/post-replace fault matrix,staged backup/owner failure cleanup,old-world/token preservation,successful new-token swap and active-clone resume; real JSON CLI full main→export/load→passive path; trial/encounter/Gauge selections use the same durable path |
| Strict rejection | Canonical UTF8/duplicate/unknown/non-NFC/float/bool/key/body/hash/pending cause-rank-due-ordinal/stream/receipt/head/replay/schema/version/pin/package/limit cases fail before Driver restore; rejected source bytes unchanged |
| Replay semantics | Retained compact steps replay on fresh owners; altered facts hash with equal CORE/protocol reports exactly step1,$facts_hash; no recovery startup engine replay |
| Scope / bytes | 111of117 entry hashes unchanged; only six authorized historical files differ. Exact13new production/test/fixture paths; all six original fixtures/reference artifact/config/lock/old tests remain byte-identical |

Two new canonical fixture SHA256 values remain exactly §3's literals. Independent boundary helper derives Step0 core/protocol/receipt retention/compact fact+diff inputs using stdlib framing/JSON and existing READ toy rules; it does not invoke Driver/Recorder/production encoding for expected values. Three real replay steps separately validate this helper before boundary input use. The ordinal swap test is adapter DDL conformance in a rolled-back transaction; it does not claim an otherwise invalid two-wake watch checkpoint.

Execution refinements/diagnosis: SQL row-count preflight additionally bounds components to32768 to bound collection allocation,within the requested save-resource policy; no accepted fixture is affected. The adapter rejects hardlinked save files (st_nlink>1) as attachment aliases and closes a connection if PRAGMA initialization fails. Native hardlink creation was denied by this managed Windows filesystem (WinError5); a new adapter-metadata guard test preserves real stat attributes while injecting link count2,then resumes the actual file. Native hardlink/platform qualification remains UNVERIFIED. Initial default pytest tmp_path setup failed under the managed external TEMP location; all persistence/full checks use unique workspace-owned --basetemp='.pytest_cache/core05-...' directories,without config/assertion changes or escalation. New test setup field/stat-shape mistakes were corrected in new files and all102new cases rerun; no old assertion/oracle was weakened or skipped. Existing Python launcher-location stderr is non-failing.

Current-only save1 and empty forward migration chain are deliberate. Windows export directory_synced=False accurately reports unavailable directory fsync; file flush/atomic replacement/process termination checks do not establish physical power-loss durability. Accepted package blobs/older migration transformations,hostile path races/network shares,release packaging/MIN-SPEC/p95-p99/memory qualification and independent-person review remain UNVERIFIED/later work. No mandatory per-turn LLM or cognition/emotion system was added.

Acceptance: the representative accepted gameplay survives durable commit,process restart,receipt retry,validated slot load and compact replay with exact queued identity. All necessary live/unit/integration/replay/lint/type/source-scope checks PASS. SELF-REVIEW ACCEPTED; no full-game/parent-completion claim.

Final delivery checks (actual exit0): five UTF8 delivery docs,fence balance,Python declaration AST,68resolved local Markdown links and source/test/doc trailing whitespace PASS;117raw input hashes give111unchanged/exact six permitted differences;reference bytes and both fixture literal hashes PASS. Exact13new runtime/test/fixture paths checked against historical input inventory. Final Ruff/mypy PASS;git diff --check PASS (preexisting primary/MASTER LF→CRLF warnings only),HEAD/main unchanged. Source authoring statuses remain historical;this execution acceptance and current BACKLOG/SESSION_HANDOFF are authoritative.
