from math import floor

from sim import Module, Rack

# Example 1: Heat a Leshak's gun for 500 cycles and plot the damage on the 4 slots next to it
print("\nEXAMPLE 1\n")
gun = Module(hp=40, heat_damage=2.7, heat_generation=0.01, cycle_time=3.75)
gun.set_green([(0, 500)])

smartbomb = Module()
rep1 = Module()
rep2 = Module()
rep3 = Module()

rack = Rack(
    [gun, smartbomb, rep1, rep2, rep3],
    ship_heat_generation_modifier=0.5,
    filled_chance_modifier=17 / 20
)


def print_callback1(tick, rack_heat, chance_statistics):
    if gun.ending_cycle_at(tick):  # Only display if slot 1 cycles
        print(f"Tick: {tick:04d}, Rack Heat: {rack_heat:.3f}", end="    ")
        print(f"End of cycle: {floor(tick / gun.cycle_time)}", end="    ")

        # Display some specific readout for slot 1
        print(f"Slot 1 chance of 2.5 HP damage {chance_statistics[0].chance_over(2.5) * 100:.3f}%", end="    ")
        print(f"Slot 1 chance of 5 HP damage {chance_statistics[0].chance_over(5) * 100:.3f}%", end="    ")
        print(f"Slot 1 chance of 7.5 HP damage {chance_statistics[0].chance_over(7.5) * 100:.3f}%", end="    ")
        print(f"Slot 1 chance of 10 HP damage {chance_statistics[0].chance_over(10) * 100:.3f}%", end="    ")

        for chance_position, chance_statistic in enumerate(chance_statistics):
            print(f"Slot {chance_position + 1} alive chance {chance_statistic.chance_under(40) * 100:.1f}%", end="    ")
        print()  # Newline


rack.simulate(print_callback=print_callback1)


# Example 2: Heat an Osprey Navy Issues RLML launchers for 20 cycles, wait for reload and heat again
print("\nEXAMPLE 2\n")

rlml_cycle_time = 3.49
rlml_reload = 35
rlml_activity = [(0, rlml_cycle_time * 20), (rlml_cycle_time * 20 + rlml_reload, rlml_cycle_time * 40 + rlml_reload)]

rlml1 = Module(hp=40, heat_damage=1.05, heat_generation=0.02, cycle_time=rlml_cycle_time)
rlml1.set_green(rlml_activity)

neut1 = Module()

rlml2 = Module(hp=40, heat_damage=1.05, heat_generation=0.02, cycle_time=rlml_cycle_time)
rlml2.set_green(rlml_activity)

neut2 = Module()

rlml3 = Module(hp=40, heat_damage=1.05, heat_generation=0.02, cycle_time=rlml_cycle_time)
rlml3.set_green(rlml_activity)

rack = Rack(
    [rlml1, neut1, rlml2, neut2, rlml3],
    ship_heat_generation_modifier=0.75,
    filled_chance_modifier=15 / 18
)


def print_callback2(tick, rack_heat, chance_statistics):
    if rlml1.ending_cycle_at(tick):  # Only display if slot 1 cycles
        print(f"Tick: {tick:04d}, Rack Heat: {rack_heat:.3f}", end="    ")
        rlml_active_tick = tick - rlml_reload * floor(tick / (rlml_cycle_time * 20 + rlml_reload))
        print(f"End of cycle: {floor(rlml_active_tick / rlml1.cycle_time)}", end="    ")

        for name, chance_statistic in zip(["RLML1", "NEUT1", "RLML2", "NEUT2", "RLML3"], chance_statistics):
            print(f"{name} alive chance {chance_statistic.chance_under(40) * 100:.1f}%", end="    ")
        print()  # Newline


rack.simulate(print_callback=print_callback2)


# Example 3a: On a Vargur with Grapple and MWD, heat grapple first for 20s, then MWD for 20s
print("\nEXAMPLE 3a\n")

any1 = Module()
any2 = Module()
grapple = Module(hp=40, heat_damage=3.75, heat_generation=0.02, cycle_time=2)
grapple.set_green([(0, 20)])
mwd = Module(hp=40, heat_damage=6.15, heat_generation=0.04, cycle_time=10)
mwd.set_green([(20, 40)])
any3 = Module()
any4 = Module()

rack = Rack(
    [any1, any2, grapple, mwd, any3, any4],
    ship_heat_generation_modifier=0.5,
    filled_chance_modifier=19 / 21
)


def print_callback3(tick, rack_heat, chance_statistics):
    print(f"Tick: {tick:04d}, Rack Heat: {rack_heat:.3f}", end="    ")
    print(f"Grapple expected heat damage {chance_statistics[2].expected():.1f}", end="    ")
    print(f"MWD expected heat damage {chance_statistics[3].expected():.1f}", end="    ")
    print()

rack.simulate(print_callback=print_callback3)

# Example 3a: On a Vargur with Grapple and MWD, heat the other way around!
print("\nEXAMPLE 3b\n")

grapple.set_green([(20, 40)])
mwd.set_green([(0, 20)])

rack = Rack(
    [any1, any2, grapple, mwd, any3, any4],
    ship_heat_generation_modifier=0.5,
    filled_chance_modifier=19 / 21
)
rack.simulate(print_callback=print_callback3)
