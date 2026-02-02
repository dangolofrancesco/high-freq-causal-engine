#include "pair_strategy.hpp"

// Constructor implementation
PairStrategy::PairStrategy(double threshold) : entry_threshold(threshold) {}

void PairStrategy::on_market_data(int symbol_type, double price, double quantity, bool is_bid) {
    if (symbol_type == 0) leader_book->add_order(price, quantity, is_bid);
    else if (symbol_type == 1) follower_book->add_order(price, quantity, is_bid);
}

int PairStrategy::check_signals() {
    double leader_obi = leader_book->get_imbalance();

    // Lead-Lag logic: Leader imbalance predicts Follower movement 
    if (leader_obi > entry_threshold) return 1;  // Signal to buy Follower
    else if (leader_obi < -entry_threshold) return -1; // Signal to sell Follower
    return 0; // No signal
}

double PairStrategy::get_leader_imbalance() {
    return leader_book->get_imbalance();
}
