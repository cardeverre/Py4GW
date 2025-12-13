"""
VQ Traveler's Vale Bot
======================
Travels to Yak's Bend -> exits to Traveler's Vale -> follows 49 waypoints.
Uses shared base for consumables, DP monitor, wipe recovery.
Loops forward/reverse until VQ complete via FSM jump.
"""
from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ConsoleLog, Console
import Py4GW
import os
import sys

base_path = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish")
if base_path not in sys.path:
    sys.path.insert(0, base_path)
from vq_base_class import check_title, setup_bot_common, add_combat_coroutines

BOT_VERSION = "1.1"
BOT_NAME = "VQ Travelers Vale"

Py4GW.Console.Log(BOT_NAME, f"Module loaded v{BOT_VERSION}", Py4GW.Console.MessageType.Warning)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")

TRAVELERS_VALE_MAP_ID = 99
YAKS_BEND_OUTPOST_ID = 134

EXIT_PATH: list[tuple[float, float]] = [
    (9303, 4208),
]
EXIT_PORTAL_COORDS = (9275, 4000)

Vanquish_Path: list[tuple[float, float]] = [
    (8207, -333), (11417, -2899), (10010, -6296), (9963, -10398),
    (10306, -13417), (8917, -14510), (5683, -16716), (2951, -14883),
    (338, -13873), (-866, -15697), (-3456, -16785), (-1283, -15970),
    (-3080, -12849), (-5949, -12463), (-8216, -11267), (-4301, -12607),
    (-2184, -13157), (947, -11275), (2561, -9659), (3322, -12900),
    (4254, -7633), (7700, -6871), (3990, -7655), (2096, -6324),
    (3341, -3666), (7534, -1623), (3439, -2328), (-374, -1352),
    (-1550, -2966), (-1776, -6295), (-1550, -737), (-3184, 1337),
    (-2571, 6561), (-801, 8248), (-3679, 11100), (-6869, 13503),
    (-8547, 12819), (-6371, 16077), (-3117, 17801), (-2035, 16561),
    (278, 16481), (239, 15300), (832, 13347), (-1633, 12227),
    (-1227, 8598), (1825, 6460), (2915, 4653), (1299, 3860),
    (5094, 7017),
]

bot = Botting(BOT_NAME, upkeep_honeycomb_active=False)

LOOP_HEADER = "VQ Loop"
pass_count = 0


def _log_vq_progress():
    """Log current VQ progress."""
    killed = GLOBAL_CACHE.Map.GetFoesKilled()
    remaining = GLOBAL_CACHE.Map.GetFoesToKill()
    total = killed + remaining
    pct = (killed / total * 100) if total > 0 else 0
    ConsoleLog(BOT_NAME, f"VQ: {killed}/{total} ({pct:.0f}%)", Console.MessageType.Info)


def _check_vq_and_loop(bot: Botting):
    """Check if VQ complete. If not, jump back to loop start."""
    global pass_count
    pass_count += 1

    if not Routines.Checks.Map.MapValid():
        return

    if GLOBAL_CACHE.Map.GetIsVanquishComplete():
        killed = GLOBAL_CACHE.Map.GetFoesKilled()
        ConsoleLog(BOT_NAME, f"VQ complete! {killed} foes in {pass_count} pass(es)", Console.MessageType.Success)
        return

    _log_vq_progress()
    ConsoleLog(BOT_NAME, f"Starting pass {pass_count + 1}...", Console.MessageType.Warning)
    bot.config.FSM.jump_to_state_by_name(f"[H]{LOOP_HEADER}")


def bot_routine(bot: Botting) -> None:
    global pass_count
    pass_count = 0

    ConsoleLog(BOT_NAME, f"Starting v{BOT_VERSION}", Console.MessageType.Info)

    setup_bot_common(bot, BOT_NAME)
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=YAKS_BEND_OUTPOST_ID)

    bot.States.AddHeader("Title Check")
    bot.States.AddCustomState(lambda: check_title(BOT_NAME), "CheckTitle")

    bot.Party.SetHardMode(True)

    for x, y in EXIT_PATH:
        bot.Move.XY(x, y)
    bot.Move.XYAndExitMap(EXIT_PORTAL_COORDS[0], EXIT_PORTAL_COORDS[1], TRAVELERS_VALE_MAP_ID)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Combat")
    add_combat_coroutines(bot, BOT_NAME)

    Carto_Path = list(reversed(Vanquish_Path))

    bot.States.AddHeader(LOOP_HEADER)
    bot.Move.FollowAutoPath(Vanquish_Path, "Forward")
    bot.Wait.UntilOutOfCombat()
    bot.Move.FollowAutoPath(Carto_Path, "Reverse")
    bot.Wait.UntilOutOfCombat()
    bot.States.AddCustomState(lambda: _check_vq_and_loop(bot), "CheckVQ")

    bot.States.AddHeader("Cartography")
    bot.Move.FollowPath(Carto_Path, "Carto Final")

    ConsoleLog(BOT_NAME, "VQ + Carto complete - verify and resign manually", Console.MessageType.Success)


bot.SetMainRoutine(bot_routine)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)


if __name__ == "__main__":
    main()
