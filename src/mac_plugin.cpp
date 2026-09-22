// SPDX-License-Identifier: GPL-2.0-or-later
// Hook/config integration adapted from windows-pointer-linux (BSD-3-Clause).
// Copyright (c) 2026, windows-pointer-linux contributors.
// Retained notice: vendor/windows-pointer-linux/LICENSE.
// Reference data/corresponding source: vendor/libpointing-sequoia/.
#include "mac/engine.hpp"
#include <hyprland/src/config/ConfigManager.hpp>
#include <hyprland/src/config/values/types/StringValue.hpp>
#include <hyprland/src/devices/IPointer.hpp>
#include <hyprland/src/event/EventBus.hpp>
#include <hyprland/src/managers/input/InputManager.hpp>
#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/plugins/PluginSystem.hpp>
#include <algorithm>
#include <charconv>
#include <cmath>
#include <limits>
#include <sstream>
#include <stdexcept>

namespace {
HANDLE handle = nullptr;
CFunctionHook* hook = nullptr;
SP<SHyprCtlCommand> command;
SP<Config::Values::CStringValue> trackingOption;
CHyprSignalListener reloadListener;
int tracking = 4;
uint64_t processed = 0, passthrough = 0;
using Original = void (*)(CInputManager*, IPointer::SMotionEvent);

[[noreturn]] void fail(const std::string& message) {
    throw std::runtime_error("Pointer Feel Mac: " + message);
}
int parseTracking(const std::string& text) {
    int value = 0;
    const auto parsed = std::from_chars(text.data(), text.data()+text.size(), value);
    if (parsed.ec != std::errc{} || parsed.ptr != text.data()+text.size() || value < 1 || value > 10)
        return 0;
    return value;
}
bool supported(double value) {
    return std::isfinite(value) && value >= std::numeric_limits<int32_t>::min()
        && value <= std::numeric_limits<int32_t>::max() && std::abs(value-std::round(value)) < 1e-9;
}
void onMouseMoved(CInputManager* manager, IPointer::SMotionEvent event) {
    if (event.device && event.mouse && !event.device->m_isTouchpad && !event.device->isVirtual()
        && supported(event.unaccel.x) && supported(event.unaccel.y)) {
        const auto moved = mac_reference::apply(event.unaccel.x, event.unaccel.y, tracking);
        event.delta = Vector2D{moved.x, moved.y};
        ++processed;
    } else {
        ++passthrough;
    }
    // Preserve unaccelerated relative motion, timestamps, and the paired report.
    reinterpret_cast<Original>(hook->m_original)(manager, event);
}
void readSettings() {
    const auto parsed = parseTracking(trackingOption->value());
    if (parsed) tracking = parsed;
}
int luaLoaded(lua_State*) { return 0; }
}

APICALL EXPORT std::string PLUGIN_API_VERSION() { return HYPRLAND_API_VERSION; }
APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE pluginHandle) {
    handle = pluginHandle;
    if (std::string{__hyprland_api_get_hash()} != __hyprland_api_get_client_hash())
        fail("Hyprland changed; rebuild this module for the running compositor.");
    for (const auto* plugin : g_pPluginSystem->getAllPlugins()) {
        if (plugin->m_name == "windows-pointer-linux")
            fail("Unload windows-pointer-linux before selecting Mac.");
    }
    Config::Values::SStringValueOptions options{
        .validator = [](const Config::STRING& value) -> std::expected<void, std::string> {
            if (!parseTracking(value)) return std::unexpected("Tracking speed must be an integer from 1 to 10.");
            return {};
        },
    };
    trackingOption = makeShared<Config::Values::CStringValue>(
        "plugin:pointer-feel-mac:tracking-speed", "Sequoia reference tracking level (1..10).", "4", std::move(options));
    if (!HyprlandAPI::addConfigValueV2(handle, trackingOption)) fail("Could not register settings.");
    readSettings();
    reloadListener = Event::bus()->m_events.config.reloaded.listen(readSettings);
    if (Config::mgr()->type() == Config::CONFIG_LUA &&
        !HyprlandAPI::addLuaFunction(handle, "pointer_feel_mac", "loaded", luaLoaded))
        fail("Could not register the Lua namespace.");
    command = HyprlandAPI::registerHyprCtlCommand(handle, SHyprCtlCommand{
        .name = "pointer-feel-mac",
        .exact = true,
        .fn = [](eHyprCtlOutputFormat, std::string) {
            std::ostringstream out;
            out << "{\"model\":\"sequoia-15.3.2\",\"experimental\":true,\"tracking_speed\":" << tracking
                << ",\"processed\":" << processed << ",\"passthrough\":" << passthrough << "}\n";
            return out.str();
        },
    });
    if (!command) fail("Could not register status readback.");
    const auto functions = HyprlandAPI::findFunctionsByName(handle, "onMouseMoved");
    const auto target = std::ranges::find_if(functions, [](const SFunctionMatch& candidate) {
        return candidate.demangled.contains("CInputManager::onMouseMoved(IPointer::SMotionEvent)");
    });
    if (target == functions.end()) fail("Could not find the matching mouse motion entry point.");
    hook = HyprlandAPI::createFunctionHook(handle, target->address, reinterpret_cast<void*>(onMouseMoved));
    if (!hook || !hook->hook()) fail("Could not attach the mouse motion hook.");
    return {"pointer-feel-mac", "Experimental macOS Sequoia measured pointer reference", "Pointer Feel contributors", "0.3.0"};
}
APICALL EXPORT void PLUGIN_EXIT() {
    reloadListener.reset();
    if (command) { HyprlandAPI::unregisterHyprCtlCommand(handle, command); command.reset(); }
    if (hook) { HyprlandAPI::removeFunctionHook(handle, hook); hook = nullptr; }
    trackingOption.reset();
    handle = nullptr;
}
