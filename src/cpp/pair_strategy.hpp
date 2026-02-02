#pragma once
#include "order_book.hpp"
#include <memory>

class OrderBook; // Forward declaration

class PairStrategy {
    private:
        std::unique_ptr<OrderBook> leader_book = std::make_unique<OrderBook>();
        std::unique_ptr<OrderBook> follower_book = std::make_unique<OrderBook>();
        double entry_threshold;

    public:
        PairStrategy(double threshold);
        
        // Update market data. symbol_type; 0:leader, 1:follower
        void on_market_data(int symbol_type, double price, double quantity, bool is_bid);

        // Check for trading signals based on imbalance
        int check_signals();

        double get_leader_imbalance();
};

