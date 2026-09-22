// SPDX-License-Identifier: GPL-2.0-or-later
#include "engine.hpp"
#include <iostream>
#include <iomanip>
#include <string>
int main(int argc, char** argv) {
    try {
        const auto tracking = argc == 2 ? std::stoi(argv[1]) : 4;
        double x, y;
        std::cout << std::setprecision(12);
        while (std::cin >> x >> y) {
            auto moved = mac_reference::apply(x, y, tracking);
            std::cout << moved.x << ' ' << moved.y << '\n';
        }
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
