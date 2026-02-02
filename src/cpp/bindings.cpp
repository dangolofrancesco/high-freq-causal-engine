#include <pybind11/pybind11.h>
#include "order_book.hpp"
#include "pair_strategy.hpp"

namespace py = pybind11;

// This defines the python module "engine_core"
PYBIND11_MODULE(engine_core, m) {
    m.doc() = "High-Frequency C++ Trading Engine";

    // Bind OrderBook class
    py::class_<OrderBook>(m, "OrderBook")
        .def(py::init<>())
        .def("add_order", &OrderBook::add_order)
        .def("get_imbalance", &OrderBook::get_imbalance)
        .def("clear", &OrderBook::clear)
        .def("get_bid_count", &OrderBook::get_bid_count)
        .def("get_ask_count", &OrderBook::get_ask_count);

    // Bind PairStrategy class
    py::class_<PairStrategy>(m, "PairStrategy")
        .def(py::init<double>())
        .def("on_market_data", &PairStrategy::on_market_data)
        .def("check_signals", &PairStrategy::check_signals)
        .def("get_leader_imbalance", &PairStrategy::get_leader_imbalance);
}