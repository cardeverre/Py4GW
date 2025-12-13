"""
VQ The Breach Bot
=================
Travels to Piken Square -> exits to The Breach -> follows waypoints.
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
BOT_NAME = "VQ The Breach"

Py4GW.Console.Log(BOT_NAME, f"Module loaded v{BOT_VERSION}", Py4GW.Console.MessageType.Warning)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")

THE_BREACH_MAP_ID = 102
PIKEN_SQUARE_OUTPOST_ID = 40

EXIT_PATH: list[tuple[float, float]] = [
    (20234, 8055),
]
EXIT_PORTAL_COORDS = (20385, 7095)

# 161 waypoints - VQ + carto
Vanquish_Path: list[tuple[float, float]] = [
    (20242, 6574), (17487, 6500), (17819, 7942), (16805, 6346), (15300, 5988),
    (15639, 7295), (16721, 8390), (16084, 10343), (14946, 9493), (14663, 8402),
    (14626, 8155), (13722, 8017), (12634, 6996), (11778, 8381), (10454, 8694),
    (8554, 9920), (8515, 10782), (6677, 9819), (4573, 9274), (3887, 9886),
    (3489, 10945), (3886, 8568), (2386, 7973), (1165, 9549), (-184, 10740),
    (-1550, 10893), (-3240, 10494), (-3789, 9915), (-4658, 10294), (-6616, 10047),
    (-7876, 9262), (-9829, 10064), (-11211, 9587), (-12354, 10433), (-13108, 8435),
    (-13509, 6090), (-14669, 4989), (-16042, 3927), (-17742, 4225), (-15583, 3960),
    (-14398, 4729), (-12293, 4893), (-11574, 4447), (-11588, 2205), (-10491, 1491),
    (-8523, 1305), (-7089, 2140), (-6908, 4865), (-5938, 7016), (-5309, 9038),
    (-3883, 7898), (-2516, 6034), (-1018, 5964), (1772, 7430), (-725, 6128),
    (-1495, 4501), (-541, 4089), (419, 3500), (1683, 4415), (4045, 4914),
    (5785, 4927), (6339, 6270), (8008, 8663), (6444, 6359), (7072, 4611),
    (7953, 5006), (9324, 3228), (11764, 2988), (12311, 3489), (12182, 6685),
    (12616, 2004), (14530, 1842), (16407, 1340), (17114, 1730), (18811, 501),
    (20390, 1879), (21039, 3813), (19576, 3606), (20704, 2521), (19112, 59),
    (18964, -902), (20099, -845), (21010, -821), (21914, -1636), (20933, -479),
    (21890, 296), (19119, -1792), (19761, -4491), (20294, -6015), (21498, -8374),
    (22306, -10484), (18694, -6224), (17415, -7994), (15738, -7512), (16171, -6231),
    (15902, -5045), (17977, -2068), (16822, -1680), (15595, -3104), (14864, -4678),
    (13246, -2599), (14021, -1342), (14887, -1329), (16211, -1067), (12698, -2046),
    (12799, -4447), (12667, -6079), (11164, -6926), (10367, -5758), (10203, -3837),
    (10387, -2117), (8546, -2427), (7319, -2993), (5754, -2968), (4658, -3223),
    (3389, -2482), (1969, -2727), (1285, -1884), (887, -1348), (-1677, -963),
    (-2235, -3381), (-3342, -5459), (-4433, -6692), (-7109, -8088), (-8314, -8310),
    (-9246, -8348), (-10553, -6511), (-13641, -8953), (-14859, -6687), (-17163, -7119),
    (-14567, -6016), (-13078, -1504), (-13990, -5728), (-11302, -2752), (-11590, -6256),
    (-10006, -3808), (-8038, -4192), (-8757, -1254), (-7413, -6150), (-6927, -7119),
    (-5055, -8560), (-3855, -8656), (-3135, -7984), (-4086, -5618), (-2833, -3895),
    (-1153, -2215), (190, -4711), (1870, -4711), (2014, -6535), (3886, -6727),
    (4126, -4903), (6574, -5623), (6766, -8119), (5035, -6457), (3451, -7703),
    (4171, -8903), (6765, -8892), (7107, -5037), (6922, -688), (8828, -174),
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
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=PIKEN_SQUARE_OUTPOST_ID)

    bot.States.AddHeader("Title Check")
    bot.States.AddCustomState(lambda: check_title(BOT_NAME), "CheckTitle")

    bot.Party.SetHardMode(True)

    for x, y in EXIT_PATH:
        bot.Move.XY(x, y)
    bot.Move.XYAndExitMap(EXIT_PORTAL_COORDS[0], EXIT_PORTAL_COORDS[1], THE_BREACH_MAP_ID)
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
