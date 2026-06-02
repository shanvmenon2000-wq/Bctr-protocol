// BCTR Protocol v1.1 - Fixed JavaScript Reference Implementation

const crypto = require("crypto");

const DebtType = Object.freeze({
    ENTRY: "entry",
    CONTINUITY: "continuity",
    TRANSFORMATION: "transformation",
    RECONSTRUCTION: "reconstruction",
    RETURN: "return"
});

const Verdict = Object.freeze({
    STABLE: "stable",
    MONITOR: "monitor",
    BREAK: "break",
    DISCOVERY: "discovery"
});

const PRESSURE_MAP = Object.freeze({
    0: { name: "Pre-number", pressure: 1, math: "More/less", verbal: "Phoneme→word" },
    1: { name: "Number & word", pressure: 2, math: "1+1=2", verbal: "Letter→word" },
    2: { name: "Make-ten", pressure: 5, math: "5+6=11", verbal: "Sentence boundaries" },
    3: { name: "Grouping", pressure: 5, math: "4×3=12", verbal: "Paragraph topic" },
    4: { name: "Place value", pressure: 6, math: "Tens/ones", verbal: "Main idea" },
    5: { name: "Fraction & inference", pressure: 7, math: "1/2 = 2/4", verbal: "Reading between lines" },
    6: { name: "Negative & counterargument", pressure: 8, math: "5-8=-3", verbal: "Opposing view" },
    7: { name: "Variable & complex sentence", pressure: 7, math: "x+3=7", verbal: "Because/although" },
    8: { name: "Equation & argument", pressure: 7, math: "2x+3=11", verbal: "Claim+evidence" },
    9: { name: "Function & purpose", pressure: 7, math: "f(3)=7", verbal: "Author's purpose" },
    10: { name: "Slope & implication", pressure: 7, math: "Rise/run", verbal: "If...then" },
    11: { name: "Systems & perspectives", pressure: 7, math: "x+y=10", verbal: "Synthesize sources" },
    12: { name: "Quadratics & flaws", pressure: 8, math: "x²-5x+6=0", verbal: "Logical flaws" },
    13: { name: "Data & probability", pressure: 7, math: "Mean/median", verbal: "Statistical evidence" },
    14: { name: "Ratio & proportion", pressure: 6, math: "2:5=6:x", verbal: "Essay proportion" },
    15: { name: "Geometry & spatial", pressure: 7, math: "Area=πr²", verbal: "Diagram matching" },
    16: { name: "Permutation & modality", pressure: 8, math: "3!=6", verbal: "Must/may/cannot" },
    17: { name: "Text completion", pressure: 7, math: "", verbal: "Context→word" },
    18: { name: "Reading comprehension", pressure: 8, math: "", verbal: "One-sentence summary" },
    19: { name: "Issue essay", pressure: 8, math: "", verbal: "Timed structure" },
    20: { name: "Argument essay", pressure: 9, math: "", verbal: "Flaw detection" },
    21: { name: "Data interpretation", pressure: 7, math: "Chart→number", verbal: "Visual+text" },
    22: { name: "Word problems", pressure: 8, math: "Story→equation", verbal: "Explanation" }
});

function hashLearnerId(learnerId) {
    return crypto.createHash("sha256").update(String(learnerId)).digest("hex").slice(0, 16);
}

class Packet {
    constructor(packetId, rung, debtType, steps, preRung = null) {
        this.packet_id = packetId;
        this.rung = rung;
        this.debt_type = debtType;
        this.steps = steps;
        this.pre_rung = preRung;
    }

    toDict() {
        return { ...this };
    }
}

class ThothMemory {
    constructor() {
        this.attempts = [];
        this.packets = new Map();
    }

    registerPacket(packet) {
        this.packets.set(packet.packet_id, packet);
    }

    recordAttempt(learnerId, rung, debtType, packetId, crossed, retestDelayHours = 24) {
        this.attempts.push({
            learner_hash: hashLearnerId(learnerId),
            rung,
            debt_type: debtType,
            packet_id: packetId,
            crossed,
            retest_delay_hours: retestDelayHours,
            timestamp: new Date().toISOString()
        });
    }

    getPacketSuccessRate(rung, debtType) {
        const relevant = this.attempts.filter(a => a.rung === rung && a.debt_type === debtType);
        if (relevant.length === 0) return { bestPacket: null, successRate: 0 };

        const stats = new Map();
        for (const a of relevant) {
            const stat = stats.get(a.packet_id) || { total: 0, crossed: 0 };
            stat.total += 1;
            if (a.crossed) stat.crossed += 1;
            stats.set(a.packet_id, stat);
        }

        let bestPacket = null;
        let successRate = 0;
        for (const [packetId, stat] of stats.entries()) {
            const rate = stat.crossed / stat.total;
            if (rate > successRate) {
                bestPacket = packetId;
                successRate = rate;
            }
        }
        return { bestPacket, successRate };
    }
}

class BCTRAgent {
    constructor(name, thoth = new ThothMemory()) {
        this.name = name;
        this.thoth = thoth;
        this.failureHistory = new Map();
    }

    failureKey(learnerId, rung, debtType) {
        return `${hashLearnerId(learnerId)}|${rung}|${debtType}`;
    }

    getRungInfo(rung) {
        return PRESSURE_MAP[rung] || { name: "Unknown", pressure: 5, math: "", verbal: "" };
    }

    classifyError(rung, wrongAnswer, explanation = "") {
        if (wrongAnswer.includes("9+7=15")) return DebtType.CONTINUITY;
        if (wrongAnswer.includes("x+3=7") && wrongAnswer.includes("10")) return DebtType.CONTINUITY;
        if (explanation.trim().length < 20) return DebtType.RECONSTRUCTION;
        return DebtType.ENTRY;
    }

    getVerdict(learnerId, rung, debtType) {
        const failCount = this.failureHistory.get(this.failureKey(learnerId, rung, debtType)) || 0;
        if (failCount >= 2) return Verdict.BREAK;
        const { successRate } = this.thoth.getPacketSuccessRate(rung, debtType);
        if (successRate < 0.3 && failCount >= 1) return Verdict.DISCOVERY;
        if (failCount >= 1) return Verdict.MONITOR;
        return Verdict.STABLE;
    }

    processAttempt(learnerId, rung, wrongAnswer, explanation = "") {
        const debtType = this.classifyError(rung, wrongAnswer, explanation);
        const key = this.failureKey(learnerId, rung, debtType);
        this.failureHistory.set(key, (this.failureHistory.get(key) || 0) + 1);

        const verdict = this.getVerdict(learnerId, rung, debtType);
        const rungInfo = this.getRungInfo(rung);
        return {
            learner_id: hashLearnerId(learnerId),
            rung,
            rung_name: rungInfo.name,
            debt_type: debtType,
            pressure: rungInfo.pressure,
            verdict,
            message: this.getVerdictMessage(verdict, rung, debtType)
        };
    }

    recordOutcome(learnerId, rung, debtType, packetId, crossed) {
        this.thoth.recordAttempt(learnerId, rung, debtType, packetId, crossed);
        if (crossed) this.failureHistory.set(this.failureKey(learnerId, rung, debtType), 0);
    }

    getVerdictMessage(verdict, rung, debtType) {
        switch (verdict) {
            case Verdict.STABLE:
                return `Stable at Rung ${rung} (${debtType}). Continue normal path.`;
            case Verdict.MONITOR:
                return `Monitor Rung ${rung} (${debtType}). Deploy recommended packet and watch next attempt.`;
            case Verdict.BREAK:
                return `BREAK at Rung ${rung} (${debtType}). Insert pre-rung.`;
            case Verdict.DISCOVERY:
                return `New pattern at Rung ${rung} (${debtType}). Create or test a new packet.`;
            default:
                return "";
        }
    }
}

module.exports = { DebtType, Verdict, PRESSURE_MAP, ThothMemory, Packet, BCTRAgent, hashLearnerId };

if (require.main === module) {
    const agent = new BCTRAgent("Math-Tutor");
    console.log(JSON.stringify(agent.processAttempt("L001", 2, "9+7=15", ""), null, 2));
}
