#ifndef BCTR_PROTOCOL_H
#define BCTR_PROTOCOL_H

#include <chrono>
#include <iomanip>
#include <map>
#include <optional>
#include <sstream>
#include <string>
#include <tuple>
#include <vector>

namespace BCTR {

enum class DebtType { ENTRY, CONTINUITY, TRANSFORMATION, RECONSTRUCTION, RETURN };
enum class Verdict { STABLE, MONITOR, BREAK, DISCOVERY };

inline std::string debt_type_to_string(DebtType d) {
    switch (d) {
        case DebtType::ENTRY: return "entry";
        case DebtType::CONTINUITY: return "continuity";
        case DebtType::TRANSFORMATION: return "transformation";
        case DebtType::RECONSTRUCTION: return "reconstruction";
        case DebtType::RETURN: return "return";
    }
    return "unknown";
}

inline std::string verdict_to_string(Verdict v) {
    switch (v) {
        case Verdict::STABLE: return "stable";
        case Verdict::MONITOR: return "monitor";
        case Verdict::BREAK: return "break";
        case Verdict::DISCOVERY: return "discovery";
    }
    return "unknown";
}

struct RungInfo {
    std::string name;
    int pressure;
    std::string math;
    std::string verbal;
};

inline const std::map<int, RungInfo> PRESSURE_MAP = {
    {0, {"Pre-number", 1, "More/less", "Phoneme→word"}},
    {1, {"Number & word", 2, "1+1=2", "Letter→word"}},
    {2, {"Make-ten", 5, "5+6=11", "Sentence boundaries"}},
    {3, {"Grouping", 5, "4×3=12", "Paragraph topic"}},
    {4, {"Place value", 6, "Tens/ones", "Main idea"}},
    {5, {"Fraction & inference", 7, "1/2 = 2/4", "Reading between lines"}},
    {6, {"Negative & counterargument", 8, "5-8=-3", "Opposing view"}},
    {7, {"Variable & complex sentence", 7, "x+3=7", "Because/although"}},
    {8, {"Equation & argument", 7, "2x+3=11", "Claim+evidence"}},
    {9, {"Function & purpose", 7, "f(3)=7", "Author's purpose"}},
    {10, {"Slope & implication", 7, "Rise/run", "If...then"}},
    {11, {"Systems & perspectives", 7, "x+y=10", "Synthesize sources"}},
    {12, {"Quadratics & flaws", 8, "x²-5x+6=0", "Logical flaws"}},
    {13, {"Data & probability", 7, "Mean/median", "Statistical evidence"}},
    {14, {"Ratio & proportion", 6, "2:5=6:x", "Essay proportion"}},
    {15, {"Geometry & spatial", 7, "Area=πr²", "Diagram matching"}},
    {16, {"Permutation & modality", 8, "3!=6", "Must/may/cannot"}},
    {17, {"Text completion", 7, "", "Context→word"}},
    {18, {"Reading comprehension", 8, "", "One-sentence summary"}},
    {19, {"Issue essay", 8, "", "Timed structure"}},
    {20, {"Argument essay", 9, "", "Flaw detection"}},
    {21, {"Data interpretation", 7, "Chart→number", "Visual+text"}},
    {22, {"Word problems", 8, "Story→equation", "Explanation"}}
};

struct Packet {
    std::string packet_id;
    int rung;
    DebtType debt_type;
    std::vector<std::string> steps;
    std::optional<std::string> pre_rung;
};

struct Attempt {
    std::string learner_hash;
    int rung;
    DebtType debt_type;
    std::string packet_id;
    bool crossed;
    int retest_delay_hours;
    std::string timestamp;
};

inline std::string hash_learner_id(const std::string& learner_id) {
    // Demo-safe stable hash. Replace with SHA-256 in production.
    std::hash<std::string> hasher;
    std::stringstream ss;
    ss << std::hex << hasher(learner_id);
    std::string out = ss.str();
    return out.substr(0, 16);
}

inline std::string current_timestamp() {
    auto now = std::chrono::system_clock::now();
    auto t = std::chrono::system_clock::to_time_t(now);
    std::tm tm = *std::gmtime(&t);
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
    return oss.str();
}

class ThothMemory {
private:
    std::vector<Attempt> attempts;
    std::map<std::string, Packet> packets;

public:
    void register_packet(const Packet& packet) { packets[packet.packet_id] = packet; }

    void record_attempt(const std::string& learner_id, int rung, DebtType debt_type,
                        const std::string& packet_id, bool crossed, int retest_delay_hours = 24) {
        attempts.push_back({hash_learner_id(learner_id), rung, debt_type, packet_id, crossed, retest_delay_hours, current_timestamp()});
    }

    std::pair<std::string, double> get_packet_success_rate(int rung, DebtType debt_type) const {
        std::map<std::string, std::pair<int, int>> stats;
        for (const auto& a : attempts) {
            if (a.rung == rung && a.debt_type == debt_type) {
                auto& stat = stats[a.packet_id];
                stat.first++;
                if (a.crossed) stat.second++;
            }
        }

        std::string best_packet;
        double best_rate = 0.0;
        for (const auto& [packet_id, stat] : stats) {
            double rate = stat.first > 0 ? static_cast<double>(stat.second) / stat.first : 0.0;
            if (rate > best_rate) {
                best_packet = packet_id;
                best_rate = rate;
            }
        }
        return {best_packet, best_rate};
    }
};

struct AttemptResponse {
    std::string learner_id;
    int rung;
    std::string rung_name;
    DebtType debt_type;
    int pressure;
    Verdict verdict;
    std::string message;
};

inline std::string verdict_message(Verdict verdict, int rung, DebtType debt_type) {
    std::ostringstream oss;
    switch (verdict) {
        case Verdict::STABLE: oss << "Stable at Rung "; break;
        case Verdict::MONITOR: oss << "Monitor Rung "; break;
        case Verdict::BREAK: oss << "BREAK at Rung "; break;
        case Verdict::DISCOVERY: oss << "New pattern at Rung "; break;
    }
    oss << rung << " (" << debt_type_to_string(debt_type) << ").";
    if (verdict == Verdict::MONITOR) oss << " Deploy recommended packet and watch next attempt.";
    if (verdict == Verdict::BREAK) oss << " Insert pre-rung.";
    if (verdict == Verdict::DISCOVERY) oss << " Create or test a new packet.";
    if (verdict == Verdict::STABLE) oss << " Continue normal path.";
    return oss.str();
}

class BCTRAgent {
private:
    std::string name;
    ThothMemory thoth;
    std::map<std::tuple<std::string, int, DebtType>, int> failure_history;

public:
    explicit BCTRAgent(const std::string& agent_name, const ThothMemory& shared_thoth = ThothMemory())
        : name(agent_name), thoth(shared_thoth) {}

    RungInfo get_rung_info(int rung) const {
        auto it = PRESSURE_MAP.find(rung);
        if (it != PRESSURE_MAP.end()) return it->second;
        return {"Unknown", 5, "", ""};
    }

    DebtType classify_error(int, const std::string& wrong_answer, const std::string& explanation = "") const {
        if (wrong_answer.find("9+7=15") != std::string::npos) return DebtType::CONTINUITY;
        if (wrong_answer.find("x+3=7") != std::string::npos && wrong_answer.find("10") != std::string::npos) return DebtType::CONTINUITY;
        if (explanation.length() < 20) return DebtType::RECONSTRUCTION;
        return DebtType::ENTRY;
    }

    Verdict get_verdict(const std::string& learner_id, int rung, DebtType debt_type) const {
        auto key = std::make_tuple(hash_learner_id(learner_id), rung, debt_type);
        auto it = failure_history.find(key);
        int fail_count = it == failure_history.end() ? 0 : it->second;
        if (fail_count >= 2) return Verdict::BREAK;
        auto [best_packet, success_rate] = thoth.get_packet_success_rate(rung, debt_type);
        if (success_rate < 0.3 && fail_count >= 1) return Verdict::DISCOVERY;
        if (fail_count >= 1) return Verdict::MONITOR;
        return Verdict::STABLE;
    }

    AttemptResponse process_attempt(const std::string& learner_id, int rung, const std::string& wrong_answer, const std::string& explanation = "") {
        DebtType debt_type = classify_error(rung, wrong_answer, explanation);
        auto key = std::make_tuple(hash_learner_id(learner_id), rung, debt_type);
        failure_history[key]++;
        Verdict verdict = get_verdict(learner_id, rung, debt_type);
        RungInfo info = get_rung_info(rung);
        return {hash_learner_id(learner_id), rung, info.name, debt_type, info.pressure, verdict, verdict_message(verdict, rung, debt_type)};
    }

    void record_outcome(const std::string& learner_id, int rung, DebtType debt_type, const std::string& packet_id, bool crossed) {
        thoth.record_attempt(learner_id, rung, debt_type, packet_id, crossed);
        if (crossed) failure_history[std::make_tuple(hash_learner_id(learner_id), rung, debt_type)] = 0;
    }
};

} // namespace BCTR

#endif
