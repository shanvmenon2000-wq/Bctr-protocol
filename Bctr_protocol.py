"""
BCTR Protocol v1.0 - Reference Implementation
License: MIT
Author: BCTR Community
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json
import hashlib


# ============================================================
# ENUMS AND TYPES
# ============================================================

class DebtType(Enum):
    ENTRY = "entry"
    CONTINUITY = "continuity"
    TRANSFORMATION = "transformation"
    RECONSTRUCTION = "reconstruction"
    RETURN = "return"


class Verdict(Enum):
    STABLE = "stable"      # Packet worked, keep sequence
    MONITOR = "monitor"    # First failure, watch
    BREAK = "break"        # Two failures, insert pre-rung
    DISCOVERY = "discovery" # New pattern, needs new packet


# ============================================================
# PRESSURE MAP (Rungs 0-22)
# ============================================================

PRESSURE_MAP = {
    0: {"name": "Pre-number", "pressure": 1, "math": "More/less", "verbal": "Phoneme→word"},
    1: {"name": "Number & word", "pressure": 2, "math": "1+1=2", "verbal": "Letter→word"},
    2: {"name": "Make-ten", "pressure": 5, "math": "5+6=11", "verbal": "Sentence boundaries"},
    3: {"name": "Grouping", "pressure": 5, "math": "4×3=12", "verbal": "Paragraph topic"},
    4: {"name": "Place value", "pressure": 6, "math": "Tens/ones", "verbal": "Main idea"},
    5: {"name": "Fraction & inference", "pressure": 7, "math": "1/2 = 2/4", "verbal": "Reading between lines"},
    6: {"name": "Negative & counterargument", "pressure": 8, "math": "5-8=-3", "verbal": "Opposing view"},
    7: {"name": "Variable & complex sentence", "pressure": 7, "math": "x+3=7", "verbal": "Because/although"},
    8: {"name": "Equation & argument", "pressure": 7, "math": "2x+3=11", "verbal": "Claim+evidence"},
    9: {"name": "Function & purpose", "pressure": 7, "math": "f(3)=7", "verbal": "Author's purpose"},
    10: {"name": "Slope & implication", "pressure": 7, "math": "Rise/run", "verbal": "If...then"},
    11: {"name": "Systems & perspectives", "pressure": 7, "math": "x+y=10", "verbal": "Synthesize sources"},
    12: {"name": "Quadratics & flaws", "pressure": 8, "math": "x²-5x+6=0", "verbal": "Logical flaws"},
    13: {"name": "Data & probability", "pressure": 7, "math": "Mean/median", "verbal": "Statistical evidence"},
    14: {"name": "Ratio & proportion", "pressure": 6, "math": "2:5=6:x", "verbal": "Essay proportion"},
    15: {"name": "Geometry & spatial", "pressure": 7, "math": "Area=πr²", "verbal": "Diagram matching"},
    16: {"name": "Permutation & modality", "pressure": 8, "math": "3!=6", "verbal": "Must/may/cannot"},
    17: {"name": "Text completion", "pressure": 7, "math": "", "verbal": "Context→word"},
    18: {"name": "Reading comprehension", "pressure": 8, "math": "", "verbal": "One-sentence summary"},
    19: {"name": "Issue essay", "pressure": 8, "math": "", "verbal": "Timed structure"},
    20: {"name": "Argument essay", "pressure": 9, "math": "", "verbal": "Flaw detection"},
    21: {"name": "Data interpretation", "pressure": 7, "math": "Chart→number", "verbal": "Visual+text"},
    22: {"name": "Word problems", "pressure": 8, "math": "Story→equation", "verbal": "Explanation"},
}

# Debt type to pressure adjustment
DEBT_PRESSURE = {
    DebtType.ENTRY: 4,
    DebtType.CONTINUITY: 6,
    DebtType.TRANSFORMATION: 7,
    DebtType.RECONSTRUCTION: 8,
    DebtType.RETURN: 5,
}


# ============================================================
# PACKET CLASS
# ============================================================

@dataclass
class Packet:
    """A 5-step bridge packet."""
    packet_id: str
    rung: int
    debt_type: DebtType
    steps: List[str]
    pre_rung: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "packet_id": self.packet_id,
            "rung": self.rung,
            "debt_type": self.debt_type.value,
            "steps": self.steps,
            "pre_rung": self.pre_rung
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Packet':
        return cls(
            packet_id=data["packet_id"],
            rung=data["rung"],
            debt_type=DebtType(data["debt_type"]),
            steps=data["steps"],
            pre_rung=data.get("pre_rung")
        )


# ============================================================
# THOTH MEMORY (Shared Learning)
# ============================================================

class ThothMemory:
    """Shared memory of what works. Can be implemented as a database."""
    
    def __init__(self):
        self.attempts: List[Dict] = []
        self.packets: Dict[str, Packet] = {}
    
    def register_packet(self, packet: Packet):
        """Add a packet to the Crossing Library."""
        self.packets[packet.packet_id] = packet
    
    def record_attempt(self, learner_id: str, rung: int, debt_type: DebtType, 
                       packet_id: str, crossed: bool, retest_delay_hours: int = 24):
        """Record a traversal attempt."""
        # Hash learner ID for privacy
        learner_hash = hashlib.sha256(learner_id.encode()).hexdigest()[:16]
        
        self.attempts.append({
            "learner_hash": learner_hash,
            "rung": rung,
            "debt_type": debt_type.value,
            "packet_id": packet_id,
            "crossed": crossed,
            "retest_delay_hours": retest_delay_hours,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_packet_success_rate(self, rung: int, debt_type: DebtType) -> Tuple[Optional[str], float]:
        """Return (best_packet_id, success_rate) for a given rung and debt type."""
        relevant = [a for a in self.attempts 
                   if a["rung"] == rung and a["debt_type"] == debt_type.value]
        
        if not relevant:
            return None, 0.0
        
        # Count successes per packet
        packet_stats = {}
        for a in relevant:
            pid = a["packet_id"]
            if pid not in packet_stats:
                packet_stats[pid] = {"total": 0, "crossed": 0}
            packet_stats[pid]["total"] += 1
            if a["crossed"]:
                packet_stats[pid]["crossed"] += 1
        
        # Find best packet
        best_packet = None
        best_rate = 0.0
        for pid, stats in packet_stats.items():
            rate = stats["crossed"] / stats["total"] if stats["total"] > 0 else 0
            if rate > best_rate:
                best_rate = rate
                best_packet = pid
        
        return best_packet, best_rate
    
    def get_population_insights(self) -> Dict:
        """Return aggregate insights."""
        total = len(self.attempts)
        if total == 0:
            return {"message": "No data yet"}
        
        crossed_count = sum(1 for a in self.attempts if a["crossed"])
        
        # Most common debt type
        debt_counts = {}
        for a in self.attempts:
            d = a["debt_type"]
            debt_counts[d] = debt_counts.get(d, 0) + 1
        most_common_debt = max(debt_counts, key=debt_counts.get) if debt_counts else None
        
        # Rungs with lowest cross rate
        rung_stats = {}
        for a in self.attempts:
            r = a["rung"]
            if r not in rung_stats:
                rung_stats[r] = {"total": 0, "crossed": 0}
            rung_stats[r]["total"] += 1
            if a["crossed"]:
                rung_stats[r]["crossed"] += 1
        
        weak_rungs = [(r, stats["crossed"]/stats["total"]) 
                     for r, stats in rung_stats.items()
                     if stats["total"] > 0]
        weak_rungs.sort(key=lambda x: x[1])
        
        return {
            "total_attempts": total,
            "crossed_count": crossed_count,
            "overall_cross_rate": crossed_count / total if total > 0 else 0,
            "most_common_debt": most_common_debt,
            "weakest_rungs": weak_rungs[:5],  # Top 5 weakest
        }


# ============================================================
# BCTR AGENT (Main Protocol Implementation)
# ============================================================

class BCTRAgent:
    """An intelligence (human or AI) that speaks BCTR."""
    
    def __init__(self, name: str, thoth: Optional[ThothMemory] = None):
        self.name = name
        self.thoth = thoth or ThothMemory()
        self.failure_history: Dict[Tuple[str, int, DebtType], int] = {}  # (learner, rung, debt) -> count
    
    def get_rung_info(self, rung: int) -> Dict:
        """Get information about a rung."""
        if rung not in PRESSURE_MAP:
            return {"error": f"Rung {rung} not in pressure map (0-22)"}
        return PRESSURE_MAP[rung]
    
    def classify_error(self, rung: int, wrong_answer: str, explanation: Optional[str] = None) -> DebtType:
        """Classify a wrong answer into a debt type."""
        # This is the core diagnostic logic
        # In production, this would be more sophisticated
        
        rung_data = PRESSURE_MAP.get(rung, {})
        rung_name = rung_data.get("name", "")
        
        # Simple classification rules (example)
        if "can't explain" in wrong_answer.lower() or (explanation and len(explanation) < 10):
            return DebtType.RECONSTRUCTION
        
        if "doesn't feel related" in wrong_answer.lower() or "different topic" in wrong_answer.lower():
            return DebtType.CONTINUITY
        
        if rung_name == "Place value" and "inverted" in wrong_answer.lower():
            return DebtType.TRANSFORMATION
        
        if rung_name == "Make-ten" and ("15" in wrong_answer or "16" in wrong_answer):
            return DebtType.CONTINUITY
        
        if rung_name == "Borrowing" and explanation and "borrow" in explanation.lower():
            # Got the borrowing right but maybe not the reduction
            return DebtType.RECONSTRUCTION
        
        # Default
        return DebtType.ENTRY
    
    def calculate_pressure(self, rung: int, debt_type: DebtType) -> int:
        """Calculate effective pressure including debt adjustment."""
        base_pressure = PRESSURE_MAP.get(rung, {}).get("pressure", 5)
        debt_adjustment = DEBT_PRESSURE.get(debt_type, 0)
        return min(10, base_pressure + (debt_adjustment - 5) // 2)  # Normalize
    
    def get_verdict(self, learner_id: str, rung: int, debt_type: DebtType) -> Verdict:
        """Determine if transition is stable or needs pre-rung."""
        key = (learner_id, rung, debt_type)
        self.failure_history[key] = self.failure_history.get(key, 0)
        
        if self.failure_history[key] >= 2:
            return Verdict.BREAK
        
        # Check Thoth memory for population patterns
        best_packet, success_rate = self.thoth.get_packet_success_rate(rung, debt_type)
        if success_rate < 0.3 and self.failure_history[key] >= 1:
            return Verdict.DISCOVERY
        
        if self.failure_history[key] >= 1:
            return Verdict.MONITOR
        
        return Verdict.STABLE
    
    def recommend_packet(self, rung: int, debt_type: DebtType) -> Tuple[Optional[Packet], str]:
        """Recommend a packet from Thoth memory or generate a default."""
        # First, check Thoth for what worked for others
        best_packet_id, success_rate = self.thoth.get_packet_success_rate(rung, debt_type)
        
        if best_packet_id and best_packet_id in self.thoth.packets:
            return self.thoth.packets[best_packet_id], f"Recommended based on {success_rate:.0%} success rate"
        
        # Default packet generation (the 5-step template)
        default_packet = self._generate_default_packet(rung, debt_type)
        return default_packet, "Generated from default template (no Thoth data yet)"
    
    def _generate_default_packet(self, rung: int, debt_type: DebtType) -> Packet:
        """Generate a default 5-step packet from the template."""
        rung_data = PRESSURE_MAP.get(rung, {})
        rung_name = rung_data.get("name", f"Rung {rung}")
        
        steps = [
            f"Step 1 (Do it): Solve a basic problem at {rung_name}",
            f"Step 2 (Check it): Verify your answer using the inverse operation",
            f"Step 3 (Make one): Create your own {rung_name} problem",
            f"Step 4 (Explain it): Write one sentence explaining the invariant",
            f"Step 5 (Transfer it): Solve a problem in a different representation (words, diagram, or real-world context)"
        ]
        
        pre_rung = None
        # Check if pressure jump suggests a pre-rung
        if rung > 0:
            prev_pressure = PRESSURE_MAP.get(rung-1, {}).get("pressure", 0)
            curr_pressure = rung_data.get("pressure", 0)
            if curr_pressure - prev_pressure >= 3:
                pre_rung = f"Rung {rung-0.5}: {rung_name} with concrete anchors only"
        
        packet_id = f"GEN_{rung}_{debt_type.value[:3].upper()}"
        
        return Packet(
            packet_id=packet_id,
            rung=rung,
            debt_type=debt_type,
            steps=steps,
            pre_rung=pre_rung
        )
    
    def suggest_pre_rung(self, rung: int) -> str:
        """Suggest a pre-rung when BREAK occurs."""
        rung_data = PRESSURE_MAP.get(rung, {})
        rung_name = rung_data.get("name", f"Rung {rung}")
        return f"Insert pre-rung at {rung-0.5}: {rung_name} with concrete anchors only (no symbols)"
    
    def process_attempt(self, learner_id: str, rung: int, wrong_answer: str, 
                        explanation: Optional[str] = None) -> Dict:
        """Main entry point: process a learner attempt and return BCTR response."""
        
        # 1. Classify error
        debt_type = self.classify_error(rung, wrong_answer, explanation)
        
        # 2. Update failure history
        key = (learner_id, rung, debt_type)
        self.failure_history[key] = self.failure_history.get(key, 0) + 1
        
        # 3. Get verdict
        verdict = self.get_verdict(learner_id, rung, debt_type)
        
        # 4. Calculate pressure
        pressure = self.calculate_pressure(rung, debt_type)
        
        # 5. Recommend packet
        packet, recommendation_note = self.recommend_packet(rung, debt_type)
        
        # 6. Build response
        response = {
            "learner_id": learner_id[:8] + "...",  # Partial for privacy
            "rung": rung,
            "rung_name": PRESSURE_MAP.get(rung, {}).get("name", "Unknown"),
            "debt_type": debt_type.value,
            "pressure": pressure,
            "verdict": verdict.value,
            "recommended_packet": packet.to_dict() if packet else None,
            "recommendation_note": recommendation_note,
            "message": self._get_verdict_message(verdict, rung, debt_type)
        }
        
        return response
    
    def record_outcome(self, learner_id: str, rung: int, debt_type: DebtType, 
                       packet_id: str, crossed: bool):
        """Record whether the learner crossed after the packet."""
        self.thoth.record_attempt(learner_id, rung, debt_type, packet_id, crossed)
        
        # Reset failure history if crossed
        if crossed:
            key = (learner_id, rung, debt_type)
            self.failure_history[key] = 0
    
    def _get_verdict_message(self, verdict: Verdict, rung: int, debt_type: DebtType) -> str:
        """Human-readable message based on verdict."""
        if verdict == Verdict.STABLE:
            return f"First failure at Rung {rung} ({debt_type.value}). Deploy recommended packet and retest."
        elif verdict == Verdict.MONITOR:
            return f"Second failure at Rung {rung} ({debt_type.value}). Deploy packet again. If fails again, insert pre-rung."
        elif verdict == Verdict.BREAK:
            return f"BREAK: Repeated failure at Rung {rung} ({debt_type.value}). Insert pre-rung: {self.suggest_pre_rung(rung)}"
        else:  # DISCOVERY
            return f"New failure pattern at Rung {rung} ({debt_type.value}). Create new packet and add to Crossing Library."
    
    def speak(self, message: str) -> str:
        """AI-to-AI communication using BCTR protocol."""
        # Parse incoming BCTR message (simplified)
        # In production, this would parse JSON
        return f"[BCTR Agent {self.name}] Acknowledged. Sending response in BCTR format."


# ============================================================
# DEMO AND TESTING
# ============================================================

def demo():
    """Demonstrate the BCTR protocol in action."""
    
    print("=" * 60)
    print("BCTR Protocol v1.0 - Reference Implementation Demo")
    print("=" * 60)
    
    # Create Thoth memory (shared across agents)
    thoth = ThothMemory()
    
    # Register some packets
    thoth.register_packet(Packet(
        packet_id="PK007",
        rung=7,
        debt_type=DebtType.CONTINUITY,
        steps=[
            "Solve □ + 3 = 7 using a box",
            "Replace □ with x and solve again",
            "Create your own box equation",
            "Explain what x means",
            "Solve a word problem using x"
        ],
        pre_rung="Rung 6.5: Box as placeholder only"
    ))
    
    # Create two agents that speak BCTR
    math_agent = BCTRAgent("Math-Tutor", thoth)
    pedagogy_agent = BCTRAgent("Pedagogy-Specialist", thoth)
    
    # Scenario: A learner fails at Rung 7 (variables)
    learner = "Student_A"
    wrong_answer = "x + 3 = 7 → x = 10"
    explanation = "I added 3 to both sides?"  # Weak explanation
    
    print("\n--- SCENARIO: Learner fails at Rung 7 ---")
    print(f"Wrong answer: {wrong_answer}")
    print(f"Explanation: {explanation}")
    print()
    
    # Math agent processes the attempt
    result = math_agent.process_attempt(learner, 7, wrong_answer, explanation)
    
    print("--- Math Agent Response ---")
    print(f"Rung: {result['rung']} ({result['rung_name']})")
    print(f"Debt type: {result['debt_type']}")
    print(f"Pressure: {result['pressure']}/10")
    print(f"Verdict: {result['verdict'].upper()}")
    print(f"Message: {result['message']}")
    print(f"Recommended packet: {result['recommended_packet']['packet_id'] if result['recommended_packet'] else 'None'}")
    
    # Math agent talks to pedagogy agent
    print("\n--- AI-to-AI Communication ---")
    math_msg = json.dumps({
        "protocol": "BCTR",
        "from": math_agent.name,
        "to": pedagogy_agent.name,
        "status": {
            "learner": learner,
            "rung": 7,
            "debt_type": "continuity",
            "crossed": False
        }
    })
    print(f"{math_agent.name}: {math_msg}")
    
    response = pedagogy_agent.speak(math_msg)
    print(f"{pedagogy_agent.name}: {response}")
    
    # Record outcome after retest
    print("\n--- Recording Outcome ---")
    math_agent.record_outcome(learner, 7, DebtType.CONTINUITY, "PK007", crossed=True)
    print("Recorded: learner crossed after packet PK007")
    
    # Show Thoth insights
    print("\n--- Thoth Memory Insights ---")
    insights = thoth.get_population_insights()
    print(json.dumps(insights, indent=2))
    
    # Show pressure map for a few rungs
    print("\n--- Pressure Map Sample ---")
    for rung in [0, 5, 10, 15, 20, 22]:
        info = math_agent.get_rung_info(rung)
        print(f"Rung {rung}: {info['name']} (Pressure: {info['pressure']}/10)")


if __name__ == "__main__":
    demo()
