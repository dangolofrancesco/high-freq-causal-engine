#include "order_book.hpp"
#include <numeric>

// Construtor implementation
OrderBook::OrderBook() {}

void OrderBook::add_order(double price, double quantity, bool is_bid) {
    std::lock_guard<std::mutex> lock(mtx);
    auto new_order = std::make_unique<Order>(price, quantity);

    if (is_bid) bids.push_back(std::move(new_order));
    else asks.push_back(std::move(new_order));
}

double OrderBook::get_imbalance() {
    std::lock_guard<std::mutex> lock(mtx);
    double total_bid_vol = 0.0, total_ask_vol = 0.0;

    for (const auto& bid : bids) total_bid_vol += bid->quantity;
    for (const auto& ask : asks) total_ask_vol += ask->quantity;
    double total_vol = total_bid_vol + total_ask_vol;

    if (total_vol == 0) return 0.0; // Avoid division by zero
    return (total_bid_vol - total_ask_vol) / total_vol;
}

void OrderBook::clear() {
    std::lock_guard<std::mutex> lock(mtx);
    bids.clear();
    asks.clear();
}   

int OrderBook::get_bid_count() {
    std::lock_guard<std::mutex> lock(mtx);
    return bids.size();
}

int OrderBook::get_ask_count() {
    std::lock_guard<std::mutex> lock(mtx);
    return asks.size();
}