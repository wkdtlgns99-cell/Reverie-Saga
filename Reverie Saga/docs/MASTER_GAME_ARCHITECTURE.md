# [MASTER GAME ARCHITECTURE] QUILLTALE v2 — AI-PRODUCED HD-2D / 2.5D TURN-BASED RPG

> **문서 목적**  
> 본 문서는 Quilltale v2의 제품 정체성, 게임플레이 목표, AI 제작 파이프라인, 런타임 구조, 비주얼/오디오 방향, 패키징, 성능 및 개발 원칙을 정의하는 최상위 제품 명세다.  
> Astra, Sol, Claude, GPT 또는 이후의 어떤 AI 에이전트가 읽더라도 **“무슨 게임을 만드는지”와 “인간과 AI가 어떤 역할로 이 게임을 제작하는지”**를 동일하게 이해해야 한다.

---

# 현재 프로젝트 정정 — 2026-10-02

Reverie Saga의 주 작업 에이전트는 **GPT-6.1 Sol**이다. 설계·구현·테스트·통합·일상 검토를 담당하며, Astra는 필요할 때 가끔 사용하는 설계·감사 조언자다. 아래에서 Astra에게만 부여한 기술 결정 책임은 현재 주 작업 에이전트가 수행하며, Astra 참여를 필수 단계로 요구하지 않는다.

개발·통합 환경은 §11.0의 실제 노트북을 기준으로 한다. 현재 Windows 11은 임시 개발 OS이므로 OS 전용 구현은 배포 단계로 미룬다. 우선 휴대 가능한 결정론적 코어와 실제 노트북의 RAM·VRAM·저장 공간을 고려한다. 기존 데스크톱 제품 목표와 MIN-SPEC은 개발 기기 사양과 별도로 관리한다.

사용자 보고는 결과·핵심 결정·다음 작업만 짧게 전달한다. 설계 전용 요청에서 생산 구현을 시작하지 않는 제한은 유지한다.

# 0. 최상위 제품 정의

## 0.1 게임 정체성

Quilltale v2는 **텍스트 TRPG가 아니다.**

최종 제품은 다음을 목표로 한다.

- **장르:** Procedural HD-2D / 2.5D Turn-Based RPG
- **플랫폼:** Windows 11 기반 standalone desktop / Steam-style distribution
- **비주얼:** 3D low-poly/modular assets + pixel/toon rendering을 이용한 입체 도트 그래픽
- **카메라:** 게임/연출이 요구하는 범위에서 자유 회전, 360° 시점 대응
- **전투:** 그래픽 UI 기반 턴제 전투
- **월드:** 절차적 생성 + 장기 상태 변화 + NPC 자율 행동 + 지연 인과관계
- **조작:** Keyboard / Gamepad / UI 기반 typed command
- **런타임 핵심:** deterministic simulation
- **LLM:** 권위 있는 게임 상태를 직접 결정하지 않음

아트 방향의 대표 참고점은 다음과 같다.

- **Octopath Traveler:** 3D 조명/심도 + 고전 도트 감성
- **Threads of Time:** 입체 도트와 자유로운 카메라
- **Dead Cells:** 3D 기반 모델/애니메이션을 픽셀 스타일로 표현하는 접근
- **Baldur's Gate / Disco Elysium:** 필드 표현과 고품질 대화 초상화의 역할 분리

이 작품의 핵심은 “LLM이 매 턴 소설을 써주는 텍스트 게임”이 아니라, **AI로 제작된 그래픽 턴제 RPG**다.

---

## 0.2 프로젝트의 근간 — AI Game Factory

Quilltale의 개발 철학은 다음과 같다.

> **Human = Game Director / Planner / Approver**  
> **AI Systems = Production Workforce**

인간 개발자는 가능한 한 다음 작업을 직접 제작하지 않는다.

- production code 손코딩
- 픽셀 아트 수작업
- 3D 모델링 수작업
- 애니메이션 수작업
- 음악 작곡 수작업
- SFX 제작 수작업
- 대량 NPC/퀘스트/아이템 데이터 수작업

인간의 주 역할은 다음이다.

1. 게임 기획과 방향 결정
2. 시스템 요구사항 정의
3. 스타일/품질 기준 정의
4. AI 산출물 승인/거부
5. 플레이테스트 기반 우선순위 결정

실제 생산은 전문 역할을 가진 AI/도구가 담당한다.

```text
Human Director
    |
    v
Production Brief / Acceptance Criteria
    |
    v
AI Production Orchestrator
    |
    +-- Architecture / Audit AI
    |     -> architecture, boundaries, review, repair specifications
    |
    +-- Coding AI
    |     -> runtime code, tools, importers, tests
    |
    +-- Content / Data LLM
    |     -> NPC data, quests, item data, world content, dialogue data
    |
    +-- 2D Image Pipeline
    |     -> SD 1.5 + LoRA + ADetailer
    |
    +-- 3D / Model Asset AI
    |     -> paid AI/service-based pre-generation
    |
    +-- Animation Pipeline
    |     -> Mixamo / AI-assisted / compatible pre-generated clips
    |
    +-- Audio Production AI
    |     -> BGM / SFX / gibberish voice / short voice assets
    |
    +-- QA / Validation
          -> schema, import, build, visual/audio/technical checks
    |
    v
Validated + Approved Assets / Code / Data
    |
    v
Game Project Import / Build
    |
    v
Playable Quilltale Build
```

AI 산출물은 “생성되었다”는 이유만으로 완성으로 간주하지 않는다.

모든 산출물은 가능한 범위에서 다음 단계를 거친다.

```text
PLANNED
 -> GENERATED
 -> VALIDATED
 -> APPROVED
 -> IMPORTED
 -> BUILD_VERIFIED
```

실패한 산출물은 `REJECTED`, `RETRY`, `NEEDS_REVIEW` 등의 상태를 가진다.

---

## 0.3 Production AI와 Runtime AI의 분리

두 종류의 AI 사용을 혼동하지 않는다.

### A. Production-time AI

게임을 **개발할 때** 사용한다.

- code generation
- game data generation
- 2D image generation
- 3D/model generation
- animation assistance
- BGM/SFX/voice generation
- QA/review

이 산출물은 개발 중 미리 생성하고 검수한 뒤 게임에 포함한다.

**3D, image, music, SFX, voice를 플레이 도중 계속 생성하지 않는다.**

### B. Optional Runtime LLM

게임이 실행 중일 때 LLM을 사용할 경우에도 매 턴 소설을 생성하는 구조를 기본으로 하지 않는다.

허용되는 기본 방향:

- New Game / World Generation
- Chapter Transition
- Loading / Preparation Window
- 특정 대규모 콘텐츠 생성 단계

이때 LLM은 자유 형식 서사를 곧바로 게임에 적용하는 것이 아니라 **구조화된 game data**를 생성한다.

```text
Runtime Generation Request
 -> LLM Structured Output
 -> Schema Validation
 -> World/Game Rule Validation
 -> Accept / Reject
 -> Cache / Persist
 -> Normal Gameplay Uses Accepted Data
```

정상 턴 처리에는 LLM 호출이 필수가 아니다.

---

# 1. 핵심 게임 비전

## 1.1 절차적 세계

매 플레이마다 다음 요소가 달라질 수 있다.

- 세계/대륙/권역 구조
- 국가와 세력 관계
- 정주지/시설
- 도로와 이동망
- 던전/위험 지역
- NPC 성격/관계/기억
- 지역 경제
- 날씨/환경
- 퀘스트와 사건
- 역사적 변화
- 장기적인 butterfly effect

세계는 단순한 랜덤 맵이 아니라 **상태와 인과관계가 지속되는 시뮬레이션 월드**를 목표로 한다.

---

## 1.2 6계층 Macro -> Micro World Stack

기본 세계 계층 개념은 유지한다.

```text
L0 Cosmology
 -> L1 Continent
   -> L2 Region
     -> L3 Nation
       -> L4 Settlement
         -> L5 Facility
```

상위 계층은 하위 계층에 영향을 주고, 하위 계층에서 일어난 사건도 상위 상태에 영향을 줄 수 있다.

예:

```text
지역 가뭄
 -> 식량 생산 감소
 -> 정주지 물가 상승
 -> 주민 불만 증가
 -> 도적/반란 위험 증가
 -> 국가 세수/군사력 변화
```

기존 v1의 수량 예시는 scale reference일 뿐 v2의 고정 수량이 아니다.

---

## 1.3 핵심 세계 시뮬레이션 능력

아래는 제품 능력 요구다. **각 항목이 반드시 별도 engine file이어야 한다는 뜻은 아니다.**

### 물리 / 환경

- object/material interaction
- 공격 물리
- 거리/사거리
- 파괴/붕괴
- 조도/시야
- 소음/은신
- 온도/체온
- 날씨
- 산소/밀폐 공간
- 환경 위험

### 전투 / 생존

- turn-based combat
- stamina / poise
- status / injury
- toxicology / disease
- food / ration / spoilage
- sleep / fatigue
- equipment weight / encumbrance
- harvesting / body-part consequences where enabled

### NPC / 사회

- personality
- emotion/stress
- interpersonal attitude
- goals / intent
- memory
- faction/social relationships
- rumor propagation
- trade/economy
- autonomous off-screen behavior

기존 v1에서 검증한 NPC cognition 개념은 v2 재설계 시 참고 자산으로 유지한다.

- 12-axis traits
- 10-factor interpersonal attitude
- 20-factor deep persona
- BDI-style belief/desire/intention concepts
- 5-level semantic memory
- high-priority permanent memory anchors

단, 이 수치 체계 자체가 v2의 클래스/모듈 구조를 강제하지는 않는다. Astra는 같은 제품 능력을 더 유지보수하기 쉬운 데이터 모델로 재구성할 수 있다.

### 공간 / 인프라

- hierarchical world locations
- road/network graph
- settlement/facility structure
- dungeons
- routes
- time/calendar
- quest/event consequences

이 기능들은 실제 플레이테스트와 제품 필요성에 따라 병합/분리될 수 있다.

기존 v1의 content-scale reference:

- 57 cosmology entries
- 120 continent templates
- 304 region templates

이 숫자는 v2의 고정 목표가 아니라 현재 데이터 자산/스케일 참고값이다.

---

# 2. Runtime Architecture — Brain & Body

## 2.1 Authoritative Brain

게임의 실제 진실은 로컬 deterministic Brain이 소유한다.

현재 기본 구현 방향은 Python이다.

Brain 책임:

- authoritative WorldState
- turn resolution
- combat rules
- world simulation
- NPC state
- event scheduling
- persistence
- save migration
- procedural generation rules
- validated generated-content ingestion

클라이언트는 게임 결과를 마음대로 만들어내면 안 된다.

```text
Player Input
 -> Typed GameCommand
 -> Brain Validation
 -> Deterministic Simulation
 -> StateDelta / WorldEvent
 -> COMMIT
 -> PresentationEvent / StateDiff
 -> Graphical Client
```

`COMMIT` 이전의 presentation은 authoritative truth가 아니다.

---

## 2.2 Graphical Body / Client

최종 제품은 그래픽 클라이언트를 사용한다.

클라이언트 기술은 Astra가 비교 후 provisional하게 선택할 수 있다.

후보 예:

- Unity
- Godot
- Unreal Engine
- 기타 적합한 엔진

중요한 것은 특정 엔진 이름보다 결과 조건이다.

클라이언트는 다음을 지원해야 한다.

- HD-2D / 3D-to-pixel presentation
- modular 3D assets
- turn-based combat presentation
- animation/VFX/UI
- free/360° camera where required
- gamepad/keyboard input
- dialogue portrait UI
- BGM/SFX/gibberish audio
- MIN-SPEC budget

Brain의 domain logic은 클라이언트 엔진 타입에 종속되면 안 된다.

---

## 2.3 Player Input

정상 게임 플레이는 자연어 문장 입력을 기본으로 하지 않는다.

```text
Keyboard / Gamepad / UI
 -> Client Input Mapping
 -> GameCommand
 -> Brain
```

예:

- Attack
- Skill
- Guard
- Item
- Move
- Interact
- Talk
- Inspect
- Travel

추후 natural-language command가 추가되더라도 optional adapter로만 존재하고 동일한 `GameCommand`로 변환되어야 한다.

---

# 3. Runtime Determinism & Causality

## 3.1 Single Source of Truth

WorldState 또는 그 후속 v2 authoritative state model이 유일한 진실 공급원이다.

- UI는 상태를 그린다.
- Animation은 상태를 표현한다.
- LLM은 구조화 콘텐츠를 제안할 수 있다.
- Asset AI는 파일을 만든다.

하지만 이들 중 어느 것도 authoritative gameplay result를 직접 덮어쓰지 않는다.

---

## 3.2 Deterministic Replay

같은 world seed, accepted content package, player command trace를 입력하면 authoritative state 결과는 재현 가능해야 한다.

관리 대상:

- RNG seed
- turn index
- event ordering
- generated-content package hash
- state schema version
- deterministic clocks

실시간 LLM 호출은 golden replay의 입력이 되지 않는다.

LLM으로 생성된 콘텐츠가 게임에 사용된다면 먼저 저장/승인되고, replay에서는 해당 accepted package를 고정 입력으로 사용한다.

---

## 3.3 Delayed Causality / Butterfly Effect

지연 사건을 first-class event로 취급한다.

예:

```text
Turn 10: bandit quest ignored
Turn 20: merchant route disrupted
Turn 30: settlement supply drops
Turn 40: prices rise / security falls
Turn 60: faction response or settlement collapse
```

플레이어가 보지 않는 곳에서도 세계 변화는 이어질 수 있다.

단, 전체 세계를 매 턴 full-resolution으로 계산하지 않는다.

---

## 3.4 Off-screen Simulation LOD

상태 중요도에 따라 simulation resolution을 나눈다.

예시:

- **Tier A / strict:** 영속적 핵심 상태. 재현성/인과성 강하게 보장.
- **Tier B / bounded:** 군중/소문/일부 encounter처럼 제한적 오차 허용.
- **Tier C / derived:** 시각 캐시, 연출, 다시 생성 가능한 데이터.

플레이어 복귀 시 catch-up으로 세계를 동기화한다.

---

# 4. AI Production Factory

## 4.1 생산 오케스트레이션

AI Game Factory는 프로젝트의 부가 기능이 아니라 개발 방식 자체다.

모든 production job은 가능한 한 다음 정보를 가진다.

- task/job id
- input brief
- acceptance criteria
- dependencies
- assigned AI/tool role
- output location
- validation rules
- approval state
- provenance

대규모 산출물은 한 모델이 모든 일을 하는 방식보다 역할을 분리한다.

---

## 4.2 Code / Architecture Pipeline

현재 역할 분담:

```text
GPT-6.1 Sol
 -> architecture / dependency design / implementation / tests / integration / routine review

Astra (optional)
 -> occasional architecture advice / audit / repair specification

Independent reviewer
 -> architecture/code audit
```

Astra가 production implementation을 대량으로 직접 수행하는 것을 기본 워크플로로 삼지 않는다.

Sol은 Director 요구를 bounded work order로 구체화하고 구현한다. Astra 작업 지시서나 검토를 필수 선행 단계로 요구하지 않는다. 독립 검토와 Sol 자체 검증은 구분한다.

---

## 4.3 Structured Game Content AI

LLM은 다음과 같은 bulk data 제작에 사용할 수 있다.

- NPC personality data
- dialogue data
- quests
- item descriptions/data
- factions
- locations
- lore
- encounter data
- world templates
- procedural content templates

출력은 가능한 한 JSON/typed schema로 받는다.

```text
Content Brief
 -> LLM Structured Generation
 -> Schema Validation
 -> Duplicate / Rule Validation
 -> Review
 -> Approved Game Data
```

자유 형식 텍스트를 production truth로 바로 저장하지 않는다.

---

## 4.4 2D Image Pipeline — FIXED

대화창 portrait/illustration의 기본 파이프라인은 다음을 유지한다.

**SD 1.5 + LoRA + ADetailer**

목적:

- 고정된 판타지 화풍
- 캐릭터 portrait
- dialogue illustration
- 필요 시 UI용 2D assets

개발 단계에서 미리 생성하고 검수한 뒤 게임 빌드에 포함하는 것을 기본으로 한다.

런타임 실시간 이미지 생성을 정상 gameplay requirement로 두지 않는다.

### 기본 생산 흐름

```text
Character Visual Spec
 -> Prompt/Tag Builder
 -> SD 1.5 + Project LoRA
 -> ADetailer
 -> Automated Technical Check
 -> Style/Identity Review
 -> Approved Portrait
 -> Import
```

관리해야 할 메타데이터 예:

- source character/spec id
- LoRA/model version
- generation parameters reference
- output hash
- resolution
- approval status
- target character/entity

---

## 4.5 3D / Model Asset Pipeline

3D 모델과 환경 에셋은 **개발 단계에서 suitable paid AI/services를 이용해 미리 생성**하는 것을 기본 방향으로 한다.

예:

- character body bases
- hair
- armor/clothes
- weapons
- furniture
- buildings
- dungeon props
- landmark objects
- rocks/trees/environment pieces

정확한 서비스 공급자는 architecture에 hard-code하지 않는다.

가능한 경우 provider adapter / standardized import contract를 사용한다.

### 생산 흐름

```text
Asset Brief
 -> Paid 3D AI / Service
 -> Mesh Download
 -> Technical Validation
 -> Retopo/optimization stage if required
 -> Material/texture validation
 -> Rig compatibility validation if character
 -> Approval
 -> Game-engine import
```

검사 대상:

- polygon budget
- mesh scale
- pivots
- normals
- material count
- texture resolution
- skeleton compatibility
- collision requirements
- file format
- license/provenance

일반 자산에 무료/CC0 라이브러리를 보조적으로 사용하는 것은 허용하지만, **핵심 제작 정책은 AI 기반 사전 생성 + 검수 + import**다.

---

## 4.6 Animation Pipeline

애니메이션은 직접 keyframe 수작업을 기본으로 하지 않는다.

후보:

- Mixamo
- AI motion generation
- marketplace/prebuilt animation libraries
- compatible paid animation services

캐릭터 skeleton contract를 먼저 정의한 뒤, animation clip은 그 규격에 맞춰 생산한다.

검증:

- skeleton mapping
- root motion policy
- loop behavior
- clip length
- event timing
- weapon/hand alignment
- import success

---

## 4.7 Audio / BGM / SFX / Gibberish Voice Pipeline

음향 역시 **미리 생성하고 게임에 넣어둔 library를 런타임에서 선택/재생하는 방식**을 기본으로 한다.

### BGM

- paid AI/music service 등을 이용해 개발 단계에서 생성
- region/combat/event tags를 부여
- 게임에는 audio file library로 포함
- 런타임에서는 tag 기반으로 선택하고 crossfade

예:

```text
Region: frozen_tundra
Mood: exploration_calm
Danger: low
 -> BGM tag resolver
 -> pre-generated track selection
 -> crossfade playback
```

### SFX

- combat impact
- weapon
- footsteps
- environment
- magic
- UI
- creature

등을 AI/service 또는 라이브러리로 사전 제작하고 import한다.

### Gibberish / Short Voice

Full sentence speech TTS를 기본으로 하지 않는다.

목표는 Octopath / Zelda / Animal Crossing 계열의 짧은 음소/의성어/chatter다.

기본 생산 방식:

- paid voice/TTS/voice-generation AI로 미리 여러 음소/감탄사 생성
- 캐릭터/성격/종족 태그 부여
- 런타임에서 캐릭터에 맞는 clip 선택
- 필요하면 pitch / tempo / EQ / reverb variation 적용

즉:

```text
Pre-generated Voice Library
 + Runtime Selection
 + Small Pitch/Reverb Variation
```

방식을 사용한다.

오디오 생성 AI가 게임 실행 중 매 대사를 생성하는 구조가 아니다.

---

## 4.8 Artifact Manifest / Provenance

생성된 production artifact는 추적 가능해야 한다.

권장 manifest field:

```text
artifact_id
artifact_type
source_brief_id
source_spec_hash
provider/tool
model/version
input_dependencies
output_hash
license/provenance
validation_status
approval_status
import_target
importer_version
build_version
```

AI가 만든 결과가 어디서 왔는지 모르는 상태로 repository에 쌓이지 않게 한다.

---

# 5. HD-2D / 3D-to-Pixel Rendering

## 5.1 기본 접근

최종 필드 표현은 “2D sprite를 모든 방향으로 수작업”하는 방식보다 **3D asset을 실시간으로 pixel-style rendering**하는 방식을 지향한다.

```text
Pre-generated 3D Asset Pool
 -> Modular Assembly
 -> Runtime Lighting
 -> Low-resolution Render Target
 -> Point Sampling
 -> Toon Quantization
 -> Pixel Outline
 -> HD-2D / 3D-to-Pixel Presentation
```

이 방식은 다음 요구와 잘 맞는다.

- 360° camera
- equipment swapping
- modular outfits
- lighting changes
- procedural environments
- AI-generated 3D assets

---

## 5.2 핵심 렌더링 요구

### 1. Draw-call / Mesh optimization

캐릭터/건물에 작은 sub-mesh가 과도하게 쌓이면 draw call이 폭증한다.

따라서 selected engine에 맞는:

- mesh combining
- material atlasing
- batching
- GPU instancing

등을 사용한다.

특정 API 이름 자체는 requirement가 아니다.

### 2. Point Filtering

저해상도 Render Texture를 확대할 때 blur가 생기지 않도록 point/nearest sampling을 사용한다.

### 3. Pixel Snapping / Temporal Stability

3D 움직임에서 pixel crawl/jitter가 과도하게 보이지 않도록 pixel grid stabilization을 적용한다.

### 4. Toon Quantization

부드러운 PBR gradient를 그대로 쓰기보다 제한된 명암 단계로 양자화한다.

예:

- light
- mid
- shadow

### 5. Pixel Outline

Depth/Normal 또는 적합한 screen-space 방식으로 얇은 pixel outline을 제공할 수 있다.

---

## 5.3 Lighting / Depth

HD-2D 느낌을 위해 사용할 수 있는 요소:

- point lights
- torch lights
- moonlight
- fog
- depth of field
- bloom (절제)
- volumetric/light shafts where performance allows

단, pixel readability가 우선이다.

---

# 6. Character Visual System

## 6.1 Field Character

필드 캐릭터는 modular 3D 기반으로 구성할 수 있다.

예:

- body base
- race/body proportions
- hair
- face texture/details
- upper/lower clothing
- armor
- cloak
- weapon
- accessories

World/NPC data의 visual tags를 실제 visual component selection으로 매핑한다.

월드/엔티티 데이터에는 UI 요약, 콘텐츠 규칙, procedural generation, visual mapping에 사용할 수 있는 범용 tag/trait 개념을 유지한다. 기존 `traits: list[str]` 관례는 v2 schema에서 동등한 역할을 보존하되, 정확한 클래스 형태는 Astra가 재설계할 수 있다.

---

## 6.2 Dialogue Portrait

필드 모델이 모든 얼굴 디테일을 보여줄 필요는 없다.

대화 UI에서는 SD 1.5 + LoRA + ADetailer로 사전 생성된 고품질 portrait를 보여준다.

```text
NPC visual profile
 -> portrait asset id
 -> pre-generated approved image
 -> dialogue UI display
```

동일 NPC의 portrait identity consistency가 중요하다.

---

# 7. Runtime Content Generation & BYOK

## 7.1 기본 원칙

Runtime LLM은 선택적 기능이다.

사용 목적 예:

- new-world content package
- chapter-specific quests
- NPC background variations
- dialogue data bundles
- world-event content

매 전투 행동이나 이동마다 LLM을 호출하지 않는다.

---

## 7.2 BYOK

Runtime LLM generation이 최종 게임에 포함될 경우 기본 비즈니스 방향은 BYOK다.

- player provides own supported LLM API key
- developer does not proxy every request through a paid central API relay
- exact provider/model quota is not a fixed product promise

“하루 1,500턴”, “평생 무제한 무료” 같은 숫자는 architecture requirement가 아니다.

실제 사용량은 당시 provider/model/tier quota를 기준으로 계산한다.

---

## 7.3 Generation Window UX

예:

```text
Start New Game
 -> Generate / load world content package
 -> Validate
 -> Save package
 -> Enter game
```

또는:

```text
Chapter End
 -> Loading / transition
 -> Generate next chapter content package
 -> Validate / cache
 -> Continue
```

실패 시 fake success를 만들지 않는다.

- retry
- deferred generation
- cached content fallback
- explicit error/status

중 하나를 사용한다.

---

# 8. Memory / NPC Data / Retrieval

NPC memory가 필요한 경우 authoritative memory와 retrieval index를 분리한다.

### Authoritative

- relationship facts
- memories/events
- personality state
- goals
- trauma/stress
- faction relation

### Derived retrieval

- full-text search index
- embeddings
- semantic rerank
- cached summaries

retrieval 기술은 제품 목표를 만족하는 한 Astra가 선택할 수 있다.

플레이어가 별도 DB server나 Docker를 설치해야 하는 구조를 normal shipping requirement로 두지 않는다.

---

# 9. Persistence / Save / Generated Content Packages

Save에는 최소한 다음을 고려한다.

- core WorldState
- scheduled events
- RNG/replay metadata
- content-package IDs/hashes
- accepted runtime-generated structured data
- version/schema metadata

Production-time images/3D/audio binary는 일반 save에 복제하지 않고 game build asset으로 관리한다.

Save migration은 versioned migration path를 사용한다.

partial commit을 방지한다.

---

# 10. Standalone Packaging

## 10.1 Player UX

Steam에서 게임을 실행했을 때 플레이어가:

- Python console
- database service
- Docker
- manual server setup

을 볼 필요가 없어야 한다.

```text
Steam / Executable
 -> Game Client
 -> Brain/runtime startup if separate
 -> Game Window
```

패키징 기술은 Astra가 비교해 결정할 수 있다.

후보:

- PyInstaller
- Nuitka
- embedded Python/runtime
- other justified Windows packaging

---

## 10.2 Process Lifecycle

Brain과 client가 separate process라면:

- start
- heartbeat/liveness
- normal exit
- Alt+F4
- crash
- Task Manager kill
- Steam forced termination

을 다뤄야 한다.

orphan process가 남아서는 안 된다.

---

# 11. Performance Goals

## 11.0 실제 주 개발·통합 노트북

- Laptop: Lenovo LOQ-E 15.6 inch (ARP10e)
- CPU: AMD Ryzen 7 7735HS
- GPU: NVIDIA GeForce RTX 4050 Laptop GPU, 6GB VRAM
- RAM: 16GB DDR5
- Storage: 512GB NVMe SSD
- Current development OS: Windows 11 (임시 사용)

초기 개발 예산은 **TARGET**으로 개발 도구·job 합산 private commit 12GB 이하, 로컬 생성 VRAM 4.5GB 이하, 재생성 가능한 모델·처리 cache 30GB 이하를 둔다. 실제 성능·모델 적합성은 **UNVERIFIED**이며, 대표 작업에서 메모리·VRAM·cache 크기와 도구 버전을 기록하여 검증한다.

무거운 로컬 AI·에셋 처리는 기본적으로 순차 실행한다. 이미지 생성·대형 로컬 LLM·그래픽 편집기를 동시에 실행하는 자원 예산을 가정하지 않는다. SD 1.5 + LoRA + ADetailer는 실제 기기 검증 후 batch 크기를 정하며, 예산 초과 시 batch 축소·도구 unload·외부 제작 job을 사용한다. 승인 원본과 provenance는 재생성 cache와 분리한다.

이 개발 예산은 아래 MIN-SPEC 출시 기준을 대체하지 않는다.

## 11.1 MIN-SPEC

기본 release minimum 방향:

- 4-core CPU
- 8GB RAM
- iGPU-class hardware

정확한 FPS/turn/memory budget은 architecture 단계에서 TARGET으로 정하고 prototype에서 측정한다.

핵심 원칙:

- AI production cost는 runtime cost가 아니다.
- 미리 만든 3D/audio/image를 로드하는 것은 runtime AI inference가 아니다.
- runtime simulation은 LLM latency와 분리해서 성능을 측정한다.

---

# 12. Development / AI Agent Rules

## 12.1 Runtime Truth

- simulation truth는 deterministic Brain이 소유
- client는 result를 invent하지 않음
- generated content는 validate/accept 후 ordinary data로 취급
- live LLM response를 곧바로 authoritative state mutation으로 사용 금지

---

## 12.2 AI Production Rules

AI-generated code/assets/data는 다음을 만족해야 한다.

1. output path가 명확할 것
2. provenance가 있을 것
3. validation rule이 있을 것
4. completion evidence가 있을 것
5. duplicate production을 피할 것
6. human approval이 필요한 범위를 명확히 할 것

---

## 12.3 Current Development Workflow

기본 워크플로:

```text
Human Director
 -> MASTER / requirements
 -> GPT-6.1 Sol architecture / bounded work orders
 -> GPT-6.1 Sol implementation / tests / integration
 -> optional Astra advice / independent review
 -> GPT-6.1 Sol repair / verification
```

Asset/content production은 같은 원리로 역할 분리한다.

---

## 12.4 No Manual-Craft Dependency

한 사람이 직접 모든 art/code/audio를 만들어야만 프로젝트가 유지되는 구조를 피한다.

새 콘텐츠를 확장할 때 가능한 한:

- template
- generator
- AI production job
- importer
- validator

를 통해 scale한다.

---

# 13. Scope Gates / Development Order

AI-first 제작이라고 해서 시작부터 모든 AI asset을 대량 생산하지 않는다.

## Gate 0 — Architecture / Walking Skeleton

먼저 확인:

- deterministic runtime skeleton
- typed command
- state ownership
- replay
- client boundary
- build/test governance

## Gate 1 — Core Gameplay

- combat loop
- movement/interactions
- state/event system
- save/load
- representative NPC/world systems

## Gate 2 — Graphical Client Prototype

- provisional engine prototype
- 3D-to-pixel look
- camera
- one modular character
- one representative environment
- performance test

여기서 graphical client를 최종 확정한다.

## Gate 3 — AI Production Factory Integration

- artifact manifest
- content generation/import
- image import
- 3D import
- animation import
- audio import
- validation/reporting

## Gate 4 — Bulk Production

이후에:

- large 3D asset pool
- portraits
- BGM
- SFX
- voice/gibberish
- content libraries

를 AI pipeline으로 대량 제작한다.

## Gate 5 — Polish / Release

- optimization
- balancing
- QA
- packaging
- Steam release preparation

---

# 14. Technology Authority

이 MASTER는 **무엇을 만들어야 하는지**를 정의한다.

Astra architecture prompt는 **어떻게 만들지**를 결정한다.

따라서 다음과 같은 application/runtime infrastructure는 Astra가 비교해 바꿀 수 있다.

- Unity / Godot / UE / other client
- Named Pipe / loopback / embedded IPC
- SQLite / JSON / embedded DB
- local retrieval/index technology
- packaging technology

단, 아래는 현재 제품 요구로 유지한다.

- graphical HD-2D / 2.5D turn-based RPG
- deterministic authoritative simulation
- human-director + AI-production workflow
- pre-generated 3D/audio/voice asset policy
- SD 1.5 + LoRA + ADetailer 2D image direction
- Windows standalone target
- optional runtime LLM is not mandatory per-turn narration

---

# 15. Reference Decisions / Clarifications

## Q1. 이 게임은 텍스트 TRPG인가?

**아니다.**

v1의 text-TRPG 구조는 아이디어/실험/실패 사례의 참고 자료다.

v2 최종 제품은 그래픽 기반 턴제 RPG다.

---

## Q2. LLM이 전투 결과를 소설처럼 매 턴 묘사하는가?

**필수 구조가 아니다.**

전투 결과는 animation/VFX/UI/dialogue presentation으로 표현한다.

LLM은 필요하다면 특정 generation window에서 구조화 콘텐츠를 생성한다.

---

## Q3. 이미지/3D/BGM/SFX/TTS를 게임 실행 중 생성하는가?

기본적으로 **아니다.**

개발 단계에서 AI/services로 생성하고 검수하여 게임에 포함한다.

런타임은 해당 asset library를 로드/선택/재생/조합한다.

---

## Q4. 사운드 라이브러리 재생은 AI 사전 생성 정책과 충돌하는가?

아니다.

```text
Paid AI / service during development
 -> approved audio files
 -> packaged sound library
 -> runtime tag-based selection / crossfade / pitch variation
```

이 구조가 기본이다.

---

## Q5. 인간 개발자는 무엇을 하는가?

주로 다음을 한다.

- 기획
- 우선순위
- acceptance criteria
- 검수
- 플레이테스트
- 최종 승인

게임 제작의 반복 노동은 가능한 한 AI pipeline으로 넘긴다.

---

# 16. 최종 한 줄 정의

> **Quilltale v2는 인간이 게임 디렉터로서 기획과 승인을 담당하고, 전문 AI 파이프라인이 코드·콘텐츠·이미지·3D·애니메이션·오디오를 사전 제작·검증·통합하여 완성하는, 절차적 HD-2D / 2.5D 그래픽 턴제 RPG다.**
