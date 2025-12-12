"""
VQ Regent Valley Bot
====================
Setup:
  - Travels to Fort Ranik outpost
  - Auto-sets Tyrian Vanquisher title (warns if fails)
  - Enables Hard Mode
  - Walks exit path to Regent Valley

Combat:
  - Follows 111 waypoints from Master Vanquisher route
  - Pauses when enemies in Earshot range
  - Upkeeps pcons + food buffs every 10s
  - Monitors death penalty (logs when detected/cleared)

Events:
  - Party wipe recovery (pauses FSM, resumes on revive)

Post-VQ:
  - Waits for 100% foes killed
  - Runs cartography reverse pass
  - Prompts manual resign

TODO:
  - Auto-use honeycomb/clovers for DP
  - Auto-resign/loop
"""
from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Range, Utils, ConsoleLog, Console, TitleID, TITLE_NAME
import Py4GW
import os

BOT_VERSION = "2.3"
BOT_NAME = "VQ Regent Valley"
REQUIRED_TITLE = TitleID.VanquisherTyria

Py4GW.Console.Log(BOT_NAME, f"Module loaded v{BOT_VERSION}", Py4GW.Console.MessageType.Warning)

VQ_DANGER_RANGE = 1000  # Earshot - guarantees engagement
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

_last_danger_log = 0
_last_dp_status = False


_title_warned = False


def _check_and_set_title(bot: "Botting") -> bool:
    """Check title, try to set in outpost. Returns True when OK or gives up."""
    global _title_warned

    active_title = GLOBAL_CACHE.Player.GetActiveTitleID()
    if active_title == REQUIRED_TITLE:
        if _title_warned:
            ConsoleLog(BOT_NAME, f"Title OK: {TITLE_NAME.get(active_title, 'Unknown')}", Console.MessageType.Success)
        _title_warned = False
        return True

    active_name = TITLE_NAME.get(active_title, "None") if active_title != -1 else "None"
    required_name = TITLE_NAME.get(REQUIRED_TITLE, "Unknown")

    # Only try to set title in outpost
    if Routines.Checks.Map.IsOutpost():
        if not _title_warned:
            ConsoleLog(BOT_NAME, f"Setting title: {active_name} -> {required_name}", Console.MessageType.Warning)
            GLOBAL_CACHE.Player.SetActiveTitle(REQUIRED_TITLE)
            _title_warned = True
        return False
    else:
        # In explorable - can't change title, just warn once and continue
        if not _title_warned:
            ConsoleLog(BOT_NAME, f"Wrong title ({active_name}), need {required_name} - set manually next run", Console.MessageType.Error)
            _title_warned = True
        return True  # Return True to not block


def _wait_for_correct_title(bot: "Botting"):
    """Coroutine that tries to set title in outpost, warns in explorable."""
    global _title_warned
    _title_warned = False

    attempts = 0
    while not _check_and_set_title(bot):
        yield from bot.Wait._coro_for_time(2000)
        attempts += 1
        if attempts > 3:
            # Give up in outpost too after 6 seconds
            ConsoleLog(BOT_NAME, "Title change failed - continuing anyway", Console.MessageType.Error)
            return


def _vq_danger_check() -> bool:
    """Pause when enemies in earshot range or party member dead/casting."""
    global _last_danger_log
    import time

    if Routines.Checks.Party.IsPartyMemberDead():
        if time.time() - _last_danger_log > 3:
            _last_danger_log = time.time()
            ConsoleLog(BOT_NAME, "Party member dead", Console.MessageType.Warning)
        return True

    if Routines.Checks.Skills.InCastingProcess():
        return True

    # Simple check: enemies in close range = danger
    if Routines.Checks.Agents.InDanger(Range.Earshot):
        return True

    return False


def bot_routine(bot: Botting) -> None:
    global Vanquish_Path, EXIT_PATH

    ConsoleLog(BOT_NAME, f"Starting v{BOT_VERSION}", Console.MessageType.Info)

    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_inventory_management")
    bot.config._set_pause_on_danger_fn(lambda: _vq_danger_check())

    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=FORT_RANIK_OUTPOST_ID)

    # Blocks until correct title is active
    bot.States.AddHeader("Title Check")
    bot.States.AddManagedCoroutine("WaitForTitle", lambda: _wait_for_correct_title(bot))

    bot.Party.SetHardMode(True)

    for x, y in EXIT_PATH:
        bot.Move.XY(x, y)
    bot.Move.XYAndExitMap(EXIT_PORTAL_COORDS[0], EXIT_PORTAL_COORDS[1], REGENT_VALLEY_MAP_ID)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Combat")
    bot.States.AddManagedCoroutine("Upkeep Consumables", lambda: _upkeep_consumables(bot))
    bot.States.AddManagedCoroutine("DP Monitor", lambda: _monitor_death_penalty(bot))

    bot.Move.FollowAutoPath(Vanquish_Path, "Kill Route")
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Waiting for VQ")
    bot.States.AddManagedCoroutine("WaitVQComplete", lambda: _wait_for_vq_complete(bot))

    bot.States.AddHeader("Cartography")
    Carto_Path = list(reversed(Vanquish_Path))
    bot.Move.FollowPath(Carto_Path, "Carto Reverse")

    ConsoleLog(BOT_NAME, "VQ + Carto complete - verify and resign manually", Console.MessageType.Success)


def _monitor_death_penalty(bot: "Botting"):
    """Log when DP detected, clear log when DP removed."""
    global _last_dp_status

    while True:
        yield from bot.Wait._coro_for_time(2000)

        if not Routines.Checks.Map.MapValid() or Routines.Checks.Map.IsOutpost():
            continue

        morale = GLOBAL_CACHE.Player.GetMorale()
        has_dp = morale < 0

        if has_dp and not _last_dp_status:
            # DP just detected
            ConsoleLog(BOT_NAME, f">>> DEATH PENALTY: {abs(morale)}% - Use Honeycomb/Clovers <<<", Console.MessageType.Error)
            _last_dp_status = True
        elif not has_dp and _last_dp_status:
            # DP cleared
            ConsoleLog(BOT_NAME, "Death penalty cleared", Console.MessageType.Success)
            _last_dp_status = False


def _upkeep_consumables(bot: "Botting"):
    """Maintain consumable buffs."""
    first_run = True
    while True:
        if not first_run:
            yield from bot.Wait._coro_for_time(10000)
        first_run = False

        if not Routines.Checks.Map.MapValid() or Routines.Checks.Map.IsOutpost():
            continue
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            continue

        # Pcons
        yield from Routines.Yield.Upkeepers.Upkeep_EssenceOfCelerity()
        yield from Routines.Yield.Upkeepers.Upkeep_GrailOfMight()
        yield from Routines.Yield.Upkeepers.Upkeep_ArmorOfSalvation()

        # Food buffs
        yield from Routines.Yield.Upkeepers.Upkeep_BirthdayCupcake()
        yield from Routines.Yield.Upkeepers.Upkeep_GoldenEgg()
        yield from Routines.Yield.Upkeepers.Upkeep_CandyCorn()
        yield from Routines.Yield.Upkeepers.Upkeep_CandyApple()
        yield from Routines.Yield.Upkeepers.Upkeep_SliceOfPumpkinPie()
        yield from Routines.Yield.Upkeepers.Upkeep_DrakeKabob()
        yield from Routines.Yield.Upkeepers.Upkeep_BowlOfSkalefinSoup()
        yield from Routines.Yield.Upkeepers.Upkeep_PahnaiSalad()
        yield from Routines.Yield.Upkeepers.Upkeep_WarSupplies()


def _wait_for_vq_complete(bot: "Botting"):
    """Wait until all foes killed."""
    while True:
        if not Routines.Checks.Map.MapValid():
            return

        foes_killed = GLOBAL_CACHE.Map.GetFoesKilled()
        foes_remaining = GLOBAL_CACHE.Map.GetFoesToKill()

        if GLOBAL_CACHE.Map.GetIsVanquishComplete():
            ConsoleLog(BOT_NAME, f"VQ complete! {foes_killed} foes", Console.MessageType.Success)
            return

        total = foes_killed + foes_remaining
        pct = (foes_killed / total * 100) if total > 0 else 0
        ConsoleLog(BOT_NAME, f"VQ: {foes_killed}/{total} ({pct:.0f}%)", Console.MessageType.Warning)

        yield from bot.Wait._coro_for_time(5000)


def _on_party_wipe(bot: "Botting"):
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog(BOT_NAME, "Party wipe", Console.MessageType.Warning)
    bot.config.FSM.pause()
    bot.config.FSM.AddManagedCoroutine("OnWipe", lambda: _on_party_wipe(bot))


bot.SetMainRoutine(bot_routine)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)


if __name__ == "__main__":
    main()
