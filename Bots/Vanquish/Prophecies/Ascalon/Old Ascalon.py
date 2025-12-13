"""
VQ Old Ascalon Bot
==================
Travels to Ascalon City -> exits to Old Ascalon -> follows waypoints.
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

BOT_VERSION = "1.0"
BOT_NAME = "VQ Old Ascalon"

Py4GW.Console.Log(BOT_NAME, f"Module loaded v{BOT_VERSION}", Py4GW.Console.MessageType.Warning)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")

OLD_ASCALON_MAP_ID = 33
ASCALON_CITY_OUTPOST_ID = 81

EXIT_PATH: list[tuple[float, float]] = [
    (2806, 1505), (-8, 1869),
]
EXIT_PORTAL_COORDS = (-1038, 1763)

# 236 waypoints - 100% VQ + wall-crawled for exploration
Vanquish_Path: list[tuple[float, float]] = [
    (16653, 10591), (15347, 11167), (14248, 12572), (15178, 13296), (15605, 13676),
    (16452, 13499), (17406, 13562), (17169, 12522), (16588, 12221), (15659, 13995),
    (15495, 14946), (14182, 15660), (13770, 16571), (14118, 17013), (13796, 17856),
    (13479, 16879), (12430, 16987), (11483, 17076), (11522, 17848), (11451, 16434),
    (11591, 14158), (10574, 15846), (9687, 16907), (9472, 17676), (10468, 18345),
    (9542, 18536), (8928, 19221), (8305, 18880), (7809, 18814), (7200, 19424),
    (5181, 19349), (4996, 18238), (3710, 17725), (3239, 19515), (3201, 19285),
    (3270, 17937), (2111, 17374), (829, 17792), (-1443, 17769), (-2532, 17395),
    (-2591, 16751), (-1793, 15776), (-1611, 14548), (-3015, 14754), (-3835, 13988),
    (-4864, 13961), (-5815, 14362), (-6460, 15121), (-6980, 16196), (-6339, 17162),
    (-6651, 16685), (-7406, 16815), (-8113, 16452), (-8847, 16208), (-9386, 16222),
    (-9968, 17049), (-10823, 16948), (-11776, 15955), (-13298, 15382), (-13298, 15382),
    (-15574, 16121), (-17932, 17527), (-18971, 17779), (-20672, 18108), (-21152, 18748),
    (-21648, 16930), (-22224, 15402), (-22298, 11446), (-21661, 10447), (-20926, 12114),
    (-19668, 13600), (-18699, 14451), (-17270, 15598), (-16065, 15561), (-14720, 15400),
    (-13527, 14681), (-14842, 12888), (-15429, 12005), (-15588, 10331), (-17542, 10104),
    (-19053, 10117), (-19061, 9177), (-19424, 8268), (-19782, 7741), (-20635, 5348),
    (-21497, 3904), (-22843, 4599), (-22060, 3971), (-21382, 2548), (-20304, 3280),
    (-19817, 3433), (-19170, 1937), (-19681, 1213), (-19885, -720), (-20348, -3043),
    (-19969, -3884), (-21746, -3799), (-22407, -4137), (-22021, -4852), (-22984, -6010),
    (-23574, -6591), (-22187, -6572), (-22492, -7263), (-22731, -7847), (-23513, -7560),
    (-22073, -8061), (-21300, -9023), (-22049, -10399), (-20302, -10822), (-19049, -13701),
    (-18993, -15674), (-17738, -16387), (-16989, -15138), (-15894, -14596), (-15118, -14833),
    (-12733, -16065), (-12343, -14018), (-13683, -11556), (-14582, -10935), (-18993, -12808),
    (-17834, -14646), (-13528, -14950), (-11104, -14042), (-9408, -16172), (-8467, -14400),
    (-5257, -12990), (-5854, -12205), (-5193, -11229), (-4428, -10554), (-2735, -10382),
    (-2802, -9280), (-6562, -10799), (-7233, -8648), (-3389, -6991), (-3684, -5975),
    (-1042, -7834), (894, -5745), (-682, -8922), (1842, -9738), (1188, -10703),
    (2317, -10284), (3551, -12475), (6554, -13752), (3531, -12324), (2850, -10341),
    (3192, -9965), (1314, -8099), (2355, -6049), (3558, -5067), (4732, -7521),
    (6757, -9907), (8152, -12092), (9043, -12912), (8053, -12004), (6420, -9399),
    (5442, -6364), (5243, -5166), (6500, -4218), (6611, -2481), (6553, -1805),
    (9976, -1038), (11435, -49), (13241, -731), (15257, -3003), (15918, -3901),
    (15459, -5674), (15195, -7951), (12884, -8397), (15350, -7333), (16542, -3802),
    (17686, -3497), (19416, -2427), (18246, -151), (19792, 1258), (19948, 4070),
    (20761, 6287), (19527, 6837), (17928, 6715), (17982, 7513), (17712, 4782),
    (17136, 2560), (14219, 1917), (13107, 2183), (11647, 3353), (8907, 4953),
    (11619, 6761), (12538, 7039), (14901, 7912), (11673, 9510), (8473, 11462),
    (5970, 11694), (4725, 9864), (2976, 10611), (4000, 12907), (2507, 14223),
    (187, 12456), (-1646, 11291), (-3521, 10796), (-3913, 12309), (-2281, 10125),
    (-1995, 7708), (-4553, 7941), (-6220, 9175), (-5417, 9914), (-6217, 8134),
    (-5948, 6212), (-10211, 4532), (-12674, 5888), (-14323, 8020), (-13676, 4048),
    (-14126, 3533), (-15667, 2023), (-16373, -1220), (-14419, 507), (-12860, 1961),
    (-12204, 3460), (-7045, 5180), (-1259, 3468), (611, 2981), (1220, 5394),
    (2284, 5904), (3581, 4940), (5183, 6678), (6556, 8260), (8760, 5395),
    (7602, 2384), (5823, 990), (4676, 282), (4676, 282), (2509, -755),
    (-882, 84), (-3369, 971), (-4877, -1845), (-5242, -3996), (-3833, -4877),
    (-884, -4030), (137, -1666),
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
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=ASCALON_CITY_OUTPOST_ID)

    bot.States.AddHeader("Title Check")
    bot.States.AddCustomState(lambda: check_title(BOT_NAME), "CheckTitle")

    bot.Party.SetHardMode(True)

    for x, y in EXIT_PATH:
        bot.Move.XY(x, y)
    bot.Move.XYAndExitMap(EXIT_PORTAL_COORDS[0], EXIT_PORTAL_COORDS[1], OLD_ASCALON_MAP_ID)
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
