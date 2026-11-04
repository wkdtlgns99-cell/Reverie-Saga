# Material Ambiguity — Director Clarification Policy

Approved by direct director instruction2026-11-03. Part of the canonical
[ENGINEERING_RULES Preflight](../ENGINEERING_RULES.md#preflight),not a separate every-turn checklist.

- Before asking,inspect current instructions,canonical contracts,actual sources and prior answers.
- If materially different plausible interpretations would change player experience,product scope,
  public/save contracts,irreversible effects,or substantial rework,ask the director before dependent
  design/implementation. Never silently omit,downgrade or replace a requested capability.
- State the ambiguity,a recommended interpretation and its concrete effect. Group related issues
  when useful;honor an explicit request to ask one decision at a time.
- Proceed autonomously with reversible local technical choices within settled contracts;report
  material assumptions. Reuse prior answers and delegation;do not ask again without new conflicting
  evidence or a materially different decision outside that delegation.
- While awaiting a required answer,continue independent authorized work. Do not execute the
  dependent branch or treat silence as approval. If no independent work remains,wait for the answer.
- A question rule is not an every-turn question requirement. Subjective uncertainty alone is not
  the trigger;the materially different outcomes above are. Existing scope,permission and pause limits remain.

Examples:live conversation versus prepared lines,initial-world scope,generation delay and expansion
semantics need product clarification when unresolved. Local helper naming,settled codec reuse,
ordinary test selection and routine error diagnosis do not require renewed permission.
