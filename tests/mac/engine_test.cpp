// SPDX-License-Identifier: GPL-2.0-or-later
#include "engine.hpp"
#include <gtest/gtest.h>
#include <cmath>
#include <limits>
TEST(MacReference, PublishedSequoiaSamples) {
    EXPECT_NEAR(mac_reference::apply(1,0,4).x, 0.230339, 1e-9);
    EXPECT_NEAR(mac_reference::apply(10,0,4).x, 6.28665, 1e-9);
    EXPECT_NEAR(mac_reference::apply(127,0,4).x, 139.898, 1e-9);
}
TEST(MacReference, AxesAreOneReport) {
    auto output = mac_reference::apply(3,4,4);
    EXPECT_NEAR(output.x, 3 * (2.41855 / 5), 1e-9);
    EXPECT_NEAR(output.y, 4 * (2.41855 / 5), 1e-9);
}
TEST(MacReference, SignedAndFractionalMotion) {
    auto pos = mac_reference::apply(1,1,4);
    auto neg = mac_reference::apply(-1,-1,4);
    EXPECT_LT(pos.x, 1);
    EXPECT_DOUBLE_EQ(pos.x, -neg.x);
    EXPECT_DOUBLE_EQ(pos.y, -neg.y);
    EXPECT_DOUBLE_EQ(mac_reference::apply(0,0,4).x, 0);
}
TEST(MacReference, EndpointGainIsHeldOutsideMeasuredDomain) {
    EXPECT_NEAR(mac_reference::apply(254,0,4).x, 2 * 139.898, 1e-9);
}
TEST(MacReference, AllTrackingLevelsFiniteAcrossDirections) {
    for (int tracking=1; tracking<=10; ++tracking) {
        for (int x=-255; x<=255; ++x) {
            auto result = mac_reference::apply(x, 255-x, tracking);
            EXPECT_TRUE(std::isfinite(result.x));
            EXPECT_TRUE(std::isfinite(result.y));
            EXPECT_GE(result.x * x, 0);
        }
    }
}
TEST(MacReference, InvalidSettingsAndMotionRejected) {
    EXPECT_THROW(mac_reference::apply(1,0,0), std::invalid_argument);
    EXPECT_THROW(mac_reference::apply(1,0,11), std::invalid_argument);
    EXPECT_THROW(mac_reference::apply(std::numeric_limits<double>::quiet_NaN(),0,4), std::invalid_argument);
}
