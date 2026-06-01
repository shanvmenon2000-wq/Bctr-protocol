# Bctr-protocol
BCTR: A protocol for intelligences (human or AI) to communicate learning state, failure modes, and bridges. Structure survives transformation.
# BCTR Protocol v1.0

**Bridgeability, Continuity, Transformation, Reconstruction**

*A protocol for intelligences (human or artificial) to communicate learning state, failure modes, and bridge requirements.*

**License:** MIT — free to use, modify, and implement.

**Version:** 1.0 | June 1, 2026

---

## One Sentence Summary

BCTR is a shared language that lets any intelligence — human or AI — say where it is on a learning ladder, why it's stuck, and what bridge it needs to cross.

---

## Core Concepts

| Term | Symbol | Meaning |
|------|--------|---------|
| Rung | N | Position on the abstraction ladder (0 to 22+) |
| Pressure | P | Derivative difficulty of this rung (1-10) |
| Integral | I | Cumulative pressure from Rung 0 to current rung |
| Debt type | D | Why traversal failed |
| Packet | PK | A 5-step bridge to cross the gap |
| Crossed | C | Successfully owned the invariant (i⁴) |
| Thoth | T | Shared memory of what works |

---

## Rungs (0-22)

| Rung | Math | Reading/Writing | Pressure |
|------|------|-----------------|----------|
| 0 | More/less | Phoneme → word | 1 |
| 1 | 1+1=2 | Letter → word | 2 |
| 2 | Make-ten (5+6=11) | Sentence boundaries | 5 |
| 3 | Multiplication as groups | Paragraph topic | 5 |
| 4 | Place value (tens/ones) | Main idea | 6 |
| 5 | Fractions | Inference | 7 |
| 6 | Negative numbers | Counterargument | 8 |
| 7 | Variable (x) | Complex sentence | 7 |
| 8 | Equation solving | Claim + evidence | 7 |
| 9 | Function machine | Author's purpose | 7 |
| 10 | Slope | Logical implication | 7 |
| 11 | System of equations | Multiple perspectives | 7 |
| 12 | Quadratics | Logical flaws | 8 |
| 13 | Data/Probability | Statistical evidence | 7 |
| 14 | Ratio/Proportion | Essay proportion | 6 |
| 15 | Geometry | Spatial logic | 7 |
| 16 | Permutation/Combination | Logical possibility | 8 |
| 17 | Text completion | Context → word | 7 |
| 18 | — | Reading comprehension | 8 |
| 19 | — | Issue essay | 8 |
| 20 | — | Argument essay | 9 |
| 21 | Data interpretation | Visual + text | 7 |
| 22 | Word problems | Story → equation | 8 |

---

## Debt Types

| Debt | Symbol | Meaning | Signal |
|------|--------|---------|--------|
| Entry | D₀ | No stable attachment point | Cannot enter the task |
| Continuity | D₁ | Doesn't feel related to prior knowledge | "This feels like a different topic" |
| Transformation | D₂ | Invariant fails across representations | Can do symbols but not words |
| Reconstruction | D₃ | Can follow but cannot rebuild | Correct answer but cannot explain |
| Return | D₄ | Cannot get back to primitive anchor | Could do it yesterday, not today |

---

## Packet Structure (5 Steps)

| Step | Action | What it tests |
|------|--------|---------------|
| 1 | **Do it** | Entry — can they perform the skill? |
| 2 | **Check it** | Continuity — do they understand inverse? |
| 3 | **Make one** | Reconstruction — can they generate a new example? |
| 4 | **Explain it** | Transformation — can they state the invariant? |
| 5 | **Transfer it** | Return — can they apply to a new domain? |

---

## Message Format (AI-to-AI)

```json
{
  "protocol": "BCTR",
  "version": "1.0",
  "sender": "AI-Math-v2",
  "recipient": "AI-Pedagogy",
  "status": {
    "learner_id": "L001",
    "current_rung": 9,
    "pressure": 7,
    "debt_type": "continuity",
    "crossed": false
  },
  "request": {
    "type": "packet",
    "target_rung": 9,
    "debt_type": "continuity"
  }
}
