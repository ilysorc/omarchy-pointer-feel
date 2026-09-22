// SPDX-License-Identifier: GPL-2.0-or-later
// Table lookup convention follows libpointing Interpolation::applyd(normalize=false).
// See vendor/libpointing-sequoia for GPL terms and upstream provenance.
#include "engine.hpp"
#include "mac_tables.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace mac_reference {
double gain(unsigned magnitude, int tracking) {
    if (tracking < 1 || tracking > 10) throw std::invalid_argument("Tracking speed must be 1..10");
    if (magnitude == 0) return 0;
    const auto index = std::min(magnitude, 127U);
    return samples[tracking - 1][index] / index;
}
Motion apply(double x, double y, int tracking) {
    if (!std::isfinite(x) || !std::isfinite(y)) throw std::invalid_argument("Non-finite motion");
    const double length = std::floor(std::hypot(x, y));
    const auto index = static_cast<unsigned>(std::min(length, 127.0));
    const auto factor = gain(index, tracking);
    return {x * factor, y * factor};
}
}
