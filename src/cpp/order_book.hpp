#pragma once // Previene che il file venga incluso due volte (Header Guard)
#include <vector>
#include <memory>
#include <mutex>

// Structure for a single order
struct Order {
    double price;
    double quantity;
    Order(double p, double q) : price(p), quantity(q) {}
};

class OrderBook {
    private:
        std::vector<std::unique_ptr<Order>> bids;
        std::vector<std::unique_ptr<Order>> asks;
        mutable std::mutex mtx;

    public:
        OrderBook(); // Constructor definition
        
        void add_order(double price, double quantity, bool is_bid);
        double get_imbalance();
        void clear();
        int get_bid_count();
        int get_ask_count();
};