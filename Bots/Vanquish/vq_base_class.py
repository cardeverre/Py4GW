"""
Shared base utilities for Prophecies VQ bots.
Provides common coroutines, checks, and event handlers.
"""
from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, Range, ConsoleLog, Console, TitleID, TITLE_NAME

REQUIRED_TITLE = TitleID.VanquisherTyria


def check_title(bot_name: str):
    """One-time title check. Logs status, tries to set if in outpost."""
    active = GLOBAL_CACHE.Player.GetActiveTitleID()
    required = TITLE_NAME.get(REQUIRED_TITLE, "Tyrian Vanquisher")

    if active == REQUIRED_TITLE:
        ConsoleLog(bot_name, f"Title OK: {required}", Console.MessageType.Success)
        return

    active_name = TITLE_NAME.get(active, "None") if active != -1 else "None"
    if Routines.Checks.Map.IsOutpost():
        ConsoleLog(bot_name, f"Setting title: {active_name} -> {required}", Console.MessageType.Warning)
        GLOBAL_CACHE.Player.SetActiveTitle(REQUIRED_TITLE)
    else:
        ConsoleLog(bot_name, f"Wrong title ({active_name}), need {required}", Console.MessageType.Error)


def vq_danger_check() -> bool:
    """Returns True if should pause (enemies nearby, dead party member, casting)."""
    if Routines.Checks.Party.IsPartyMemberDead():
        return True
    if Routines.Checks.Skills.InCastingProcess():
        return True
    if Routines.Checks.Agents.InDanger(Range.Earshot):
        return True
    return False


def monitor_death_penalty(bot: "Botting", bot_name: str):
    """Coroutine: logs DP when detected, clears when removed."""
    has_dp = False
    while True:
        yield from bot.Wait._coro_for_time(2000)
        if not Routines.Checks.Map.MapValid() or Routines.Checks.Map.IsOutpost():
            continue

        morale = GLOBAL_CACHE.Player.GetMorale()
        dp_now = morale < 0

        if dp_now and not has_dp:
            ConsoleLog(bot_name, f">>> DEATH PENALTY: {abs(morale)}% <<<", Console.MessageType.Error)
            has_dp = True
        elif not dp_now and has_dp:
            ConsoleLog(bot_name, "Death penalty cleared", Console.MessageType.Success)
            has_dp = False


def upkeep_consumables(bot: "Botting"):
    """Coroutine: maintains pcons and food buffs."""
    first = True
    while True:
        if not first:
            yield from bot.Wait._coro_for_time(10000)
        first = False

        if not Routines.Checks.Map.MapValid() or Routines.Checks.Map.IsOutpost():
            continue
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            continue

        yield from Routines.Yield.Upkeepers.Upkeep_EssenceOfCelerity()
        yield from Routines.Yield.Upkeepers.Upkeep_GrailOfMight()
        yield from Routines.Yield.Upkeepers.Upkeep_ArmorOfSalvation()
        yield from Routines.Yield.Upkeepers.Upkeep_BirthdayCupcake()
        yield from Routines.Yield.Upkeepers.Upkeep_GoldenEgg()
        yield from Routines.Yield.Upkeepers.Upkeep_CandyCorn()
        yield from Routines.Yield.Upkeepers.Upkeep_CandyApple()
        yield from Routines.Yield.Upkeepers.Upkeep_SliceOfPumpkinPie()
        yield from Routines.Yield.Upkeepers.Upkeep_DrakeKabob()
        yield from Routines.Yield.Upkeepers.Upkeep_BowlOfSkalefinSoup()
        yield from Routines.Yield.Upkeepers.Upkeep_PahnaiSalad()
        yield from Routines.Yield.Upkeepers.Upkeep_WarSupplies()


def wait_for_vq_complete(bot: "Botting", bot_name: str):
    """Coroutine: waits until VQ is 100% complete."""
    while True:
        if not Routines.Checks.Map.MapValid():
            return

        killed = GLOBAL_CACHE.Map.GetFoesKilled()
        remaining = GLOBAL_CACHE.Map.GetFoesToKill()

        if GLOBAL_CACHE.Map.GetIsVanquishComplete():
            ConsoleLog(bot_name, f"VQ complete! {killed} foes", Console.MessageType.Success)
            return

        total = killed + remaining
        pct = (killed / total * 100) if total > 0 else 0
        ConsoleLog(bot_name, f"VQ: {killed}/{total} ({pct:.0f}%)", Console.MessageType.Warning)
        yield from bot.Wait._coro_for_time(5000)


def is_vq_complete() -> bool:
    """Check if vanquish is complete."""
    return GLOBAL_CACHE.Map.GetIsVanquishComplete()


def log_vq_progress(bot_name: str):
    """Log current VQ progress."""
    killed = GLOBAL_CACHE.Map.GetFoesKilled()
    remaining = GLOBAL_CACHE.Map.GetFoesToKill()
    total = killed + remaining
    pct = (killed / total * 100) if total > 0 else 0
    ConsoleLog(bot_name, f"VQ: {killed}/{total} ({pct:.0f}%)", Console.MessageType.Info)


def on_party_wipe_handler(bot: "Botting"):
    """Coroutine: waits for revive after wipe, then resumes FSM."""
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return
    bot.config.FSM.resume()


def on_party_wipe(bot: "Botting", bot_name: str):
    """Event callback for party wipe."""
    ConsoleLog(bot_name, "Party wipe", Console.MessageType.Warning)
    bot.config.FSM.pause()
    bot.config.FSM.AddManagedCoroutine("OnWipe", lambda: on_party_wipe_handler(bot))


def setup_bot_common(bot: "Botting", bot_name: str):
    """Common bot setup: events, templates, danger check."""
    bot.Events.OnPartyWipeCallback(lambda: on_party_wipe(bot, bot_name))
    bot.States.AddHeader(bot_name)
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_inventory_management")
    bot.config._set_pause_on_danger_fn(vq_danger_check)


def add_combat_coroutines(bot: "Botting", bot_name: str):
    """Adds standard combat-phase coroutines (consumables, DP monitor)."""
    bot.States.AddManagedCoroutine("Consumables", lambda: upkeep_consumables(bot))
    bot.States.AddManagedCoroutine("DP Monitor", lambda: monitor_death_penalty(bot, bot_name))
