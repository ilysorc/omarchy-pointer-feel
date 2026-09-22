// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
namespace mac_reference {
struct Motion { double x = 0; double y = 0; };
// Sampled Sequoia reference, using libpointing's unnormalised table semantics.
// The input report's two axes must be supplied together. No timing is invented.
Motion apply(double x, double y, int tracking);
double gain(unsigned magnitude, int tracking);
}
