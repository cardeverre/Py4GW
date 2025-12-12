"""
VQ Regent Valley Bot
====================
Travels to Fort Ranik -> exits to Regent Valley -> follows 111 waypoints.
Uses shared base for consumables, DP monitor, wipe recovery.
Loops forward/reverse until VQ complete via FSM jump.
"""
from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ConsoleLog, Console
import Py4GW
import os
import sys

base_path = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "Prophecies")
if base_path not in sys.path:
    sys.path.insert(0, base_path)
from vq_prophecies_base import check_title, setup_bot_common, add_combat_coroutines

BOT_VERSION = "2.6"
BOT_NAME = "VQ Regent Valley"

Py4GW.Console.Log(BOT_NAME, f"Module loaded v{BOT_VERSION}", Py4GW.Console.MessageType.Warning)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")

REGENT_VALLEY_MAP_ID = 101
FORT_RANIK_OUTPOST_ID = 29

EXIT_PATH: list[tuple[float, float]] = [
    (7936, -28412),
    (7194, -31058),
    (7208, -32163),
]
EXIT_PORTAL_COORDS = (7208, -32863)

# 111 waypoints from Master Vanquisher
Vanquish_Path: list[tuple[float, float]] = [
    (21699, 3672), (20836, 1939), (18455, -1521), (17643, -2863),
    (20445, -5550), (21478, -4761), (18234, -3211), (14919, -3146),
    (16498, -9490), (15206, -10527), (12313, -10774), (11070, -10965),
    (9864, -10115), (7000.60, -5542.55), (9864, -10115), (9939, -12556),
    (5221, -12945), (4344, -13179), (1334, -11871), (528, -10483),
    (1403, -8861), (-1971, -7535), (-4702, -7478), (-6217, -6654),
    (-7577, -10113), (-9999, -10387), (-11608, -10839), (-12279, -13028),
    (-16213.01, -10971.41), (-16174, -12648), (-18280.89, -8908.74),
    (-14366.40, -5257.85), (-18280.89, -8908.74), (-19732, -12366),
    (-21211, -11417), (-22943, -11033), (-23156, -8099), (-24782, -7465),
    (-22058, -3958), (-21328, -2190), (-17648.23, 418.00), (-21291.44, 889.61),
    (-17648.23, 418.00), (-21328, -2190), (-23692, -3505), (-25476, -2187),
    (-26016, 788), (-24702, 3184), (-24410, 6415), (-22838, 10491),
    (-19955, 10804), (-17822, 10732), (-16417.85, 9620.00), (-15218.41, 11461.83),
    (-15860, 13862), (-13860, 14310), (-8907, 12192), (-5661, 11764),
    (-3382, 8429), (21, 6773), (589, 9675), (3661, 6260),
    (6283, 5235), (7652, 3790), (8490, 3320), (7126, 829),
    (11115, 1954), (13905, 1320), (16783, 5522), (16466, 9848),
    (14816, 8630), (17357, 6712), (15704, 2851), (10740, 2036),
    (6667, -751), (6999, -3284), (7050, -5761), (4608, -1723),
    (3481, 20), (766, -197), (-3665, -340), (-7683, -533),
    (-7077, -2634), (-7537, -5424), (-6601, -2790), (-3759, -3592),
    (-1058, -4608), (-3888, -3514), (-6660, -1623), (-9148, 185),
    (-11547, 1738), (-12293, 2438), (-13322, 3119), (-13857, 1901),
    (-16212, -764), (-15176, -4550), (-16699, -2440), (-17656, 589),
    (-15195, 889), (-17768, 5880), (-14062, 3681), (-11469, 5019),
    (-11593, 6730), (-12250, 7507), (-12982, 3408), (-12820.18, -712.43),
    (-13150.19, 1175.47), (-9548, 4840), (-6728, 5698), (-6347, 6169),
    (-11819, 9584),
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
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=FORT_RANIK_OUTPOST_ID)

    bot.States.AddHeader("Title Check")
    bot.States.AddCustomState(lambda: check_title(BOT_NAME), "CheckTitle")

    bot.Party.SetHardMode(True)

    for x, y in EXIT_PATH:
        bot.Move.XY(x, y)
    bot.Move.XYAndExitMap(EXIT_PORTAL_COORDS[0], EXIT_PORTAL_COORDS[1], REGENT_VALLEY_MAP_ID)
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
