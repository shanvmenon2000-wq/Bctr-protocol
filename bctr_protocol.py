"""
BCTR Protocol v1.1 - Fixed Python Reference Implementation
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Dict, List, Optional, Tuple


class DebtType(Enum):
    ENTRY = "entry"
    CONTINUITY = "continuity"
    TRANSFORMATION = "transformation"
    RECONSTRUCTION = "reconstruction"
    RETURN = "return"


class Verdict(Enum):
    STABLE = "stable"
    MONITOR = "monitor"
    BREAK = "break"
    DISCOVERY = "discovery"


@dataclass(frozen=True)
class RungInfo:
    name: str
    pressure: int
    math: str
    verbal: str


PRESSURE_MAP: Dict[int, RungInfo] = {
    0: RungInfo("Pre-number", 1, "More/less", "Phoneme→word"),
    1: RungInfo("Number & word", 2, "1+1=2", "Letter→word"),
    2: RungInfo("Make-ten", 5, "5+6=11", "Sentence boundaries"),
    3: RungInfo("Grouping", 5, "4×3=12", "Paragraph topic"),
    4: RungInfo("Place value", 6, "Tens/ones", "Main idea"),
    5: RungInfo("Fraction & inference", 7, "1/2 = 2/4", "Reading between lines"),
    6: RungInfo("Negative & counterargument", 8, "5-8=-3", "Opposing view"),
    7: RungInfo("Variable & complex sentence", 7, "x+3=7", "Because/although"),
    8: RungInfo("Equation & argument", 7, "2x+3=11", "Claim+evidence"),
    9: RungInfo("Function & purpose", 7, "f(3)=7", "Author's purpose"),
    10: RungInfo("Slope & implication", 7, "Rise/run", "If...then"),
    11: RungInfo("Systems & perspectives", 7, "x+y=10", "Synthesize sources"),
    12: RungInfo("Quadratics & flaws", 8, "x²-5x+6=0", "Logical flaws"),
    13: RungInfo("Data & probability", 7, "Mean/median", "Statistical evidence"),
    14: RungInfo("Ratio & proportion", 6, "2:5=6:x", "Essay proportion"),
    15: RungInfo("Geometry & spatial", 7, "Area=πr²", "Diagram matching"),
    16: RungInfo("Permutation & modality", 8, "3!=6", "Must/may/cannot"),
    17: RungInfo("Text completion", 7, "", "Context→word"),
    18: RungInfo("Reading comprehension", 8, "", "One-sentence summary"),
    19: RungInfo("Issue essay", 8, "", "Timed structure"),
    20: RungInfo("Argument essay", 9, "", "Flaw detection"),
    21: RungInfo("Data interpretation", 7, "Chart→number", "Visual+text"),
    22: RungInfo("Word problems", 8, "Story→equation", "Explanation"),
}


@dataclass
class Packet:
    packet_id: str
    rung: int
    debt_type: DebtType
    steps: List[str]
    pre_rung: Optional[str] = None


@dataclass
class Attempt:
    learner_hash: str
    rung: int
    debt_type: str
    packet_id: str
    crossed: bool
    retest_delay_hours: int
    timestamp: str


def hash_learner_id(learner_id: str) -> str:
    return hashlib.sha256(learner_id.encode("utf-8")).hexdigest()[:16]


class ThothMemory:
    def __init__(self) -> None:
        self.attempts: List[Attempt] = []
        self.packets: Dict[str, Packet] = {}

    def register_packet(self, packet: Packet) -> None:
        self.packets[packet.packet_id] = packet

    def record_attempt(
        self,
        learner_id: str,
        rung: int,
        debt_type: DebtType,
        packet_id: str,
        crossed: bool,
        retest_delay_hours: int = 24,
    ) -> None:
        self.attempts.append(
            Attempt(
                learner_hash=hash_learner_id(learner_id),
                rung=rung,
                debt_type=debt_type.value,
                packet_id=packet_id,
                crossed=crossed,
                retest_delay_hours=retest_delay_hours,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

    def get_packet_success_rate(self, rung: int, debt_type: DebtType) -> Tuple[Optional[str], float]:
        relevant = [a for a in self.attempts if a.rung == rung and a.debt_type == debt_type.value]
        if not relevant:
            return None, 0.0

        stats: Dict[str, Tuple[int, int]] = {}
        for attempt in relevant:
            total, crossed = stats.get(attempt.packet_id, (0, 0))
            stats[attempt.packet_id] = (total + 1, crossed + int(attempt.crossed))

        best_packet: Optional[str] = None
        best_rate = 0.0
        for packet_id, (total, crossed) in stats.items():
            rate = crossed / total
            if rate > best_rate:
                best_packet = packet_id
                best_rate = rate
        return best_packet, best_rate


class BCTRAgent:
    def __init__(self, name: str, thoth: Optional[ThothMemory] = None) -> None:
        self.name = name
        self.thoth = thoth or ThothMemory()
        self.failure_history: Dict[Tuple[str, int, DebtType], int] = {}

    def get_rung_info(self, rung: int) -> RungInfo:
        return PRESSURE_MAP.get(rung, RungInfo("Unknown", 5, "", ""))

    def classify_error(self, rung: int, wrong_answer: str, explanation: str = "") -> DebtType:
        if "9+7=15" in wrong_answer:
            return DebtType.CONTINUITY
        if "x+3=7" in wrong_answer and "10" in wrong_answer:
            return DebtType.CONTINUITY
        if len(explanation.strip()) < 20:
            return DebtType.RECONSTRUCTION
        return DebtType.ENTRY

    def get_verdict(self, learner_id: str, rung: int, debt_type: DebtType) -> Verdict:
        learner_hash = hash_learner_id(learner_id)
        fail_count = self.failure_history.get((learner_hash, rung, debt_type), 0)
        if fail_count >= 2:
            return Verdict.BREAK
        _, success_rate = self.thoth.get_packet_success_rate(rung, debt_type)
        if success_rate < 0.3 and fail_count >= 1:
            return Verdict.DISCOVERY
        if fail_count >= 1:
            return Verdict.MONITOR
        return Verdict.STABLE

    def process_attempt(self, learner_id: str, rung: int, wrong_answer: str, explanation: str = "") -> dict:
        debt_type = self.classify_error(rung, wrong_answer, explanation)
        learner_hash = hash_learner_id(learner_id)
        key = (learner_hash, rung, debt_type)
        self.failure_history[key] = self.failure_history.get(key, 0) + 1

        verdict = self.get_verdict(learner_id, rung, debt_type)
        rung_info = self.get_rung_info(rung)
        return {
            "learner_id": learner_hash,
            "rung": rung,
            "rung_name": rung_info.name,
            "debt_type": debt_type.value,
            "pressure": rung_info.pressure,
            "verdict": verdict.value,
            "message": self.get_verdict_message(verdict, rung, debt_type),
        }

    def record_outcome(self, learner_id: str, rung: int, debt_type: DebtType, packet_id: str, crossed: bool) -> None:
        self.thoth.record_attempt(learner_id, rung, debt_type, packet_id, crossed)
        if crossed:
            self.failure_history[(hash_learner_id(learner_id), rung, debt_type)] = 0

    @staticmethod
    def get_verdict_message(verdict: Verdict, rung: int, debt_type: DebtType) -> str:
        if verdict == Verdict.STABLE:
            return f"Stable at Rung {rung} ({debt_type.value}). Continue normal path."
        if verdict == Verdict.MONITOR:
            return f"Monitor Rung {rung} ({debt_type.value}). Deploy recommended packet and watch next attempt."
        if verdict == Verdict.BREAK:
            return f"BREAK at Rung {rung} ({debt_type.value}). Insert pre-rung."
        if verdict == Verdict.DISCOVERY:
            return f"New pattern at Rung {rung} ({debt_type.value}). Create or test a new packet."
        return ""


if __name__ == "__main__":
    agent = BCTRAgent("Math-Tutor")
    print(json.dumps(agent.process_attempt("L001", 2, "9+7=15", ""), indent=2))
