#include <iostream>
#include "bctr_protocol.h"

int main() {
    BCTR::BCTRAgent agent("Math-Tutor");
    auto result = agent.process_attempt("L001", 2, "9+7=15", "");
    std::cout << "{\n"
              << "  \"learner_id\": \"" << result.learner_id << "\",\n"
              << "  \"rung\": " << result.rung << ",\n"
              << "  \"rung_name\": \"" << result.rung_name << "\",\n"
              << "  \"debt_type\": \"" << BCTR::debt_type_to_string(result.debt_type) << "\",\n"
              << "  \"pressure\": " << result.pressure << ",\n"
              << "  \"verdict\": \"" << BCTR::verdict_to_string(result.verdict) << "\",\n"
              << "  \"message\": \"" << result.message << "\"\n"
              << "}\n";
}
