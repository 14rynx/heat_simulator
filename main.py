from math import ceil, floor, exp


class Module:
    """Just a simple dataclass, data might come from another source like pyfa"""

    def __init__(self, hp=40, heat_damage=2.7, heat_generation=0.01, cycle_time=3.75):
        self.hp = hp
        self.heat_damage = heat_damage
        self.heat_generation = heat_generation
        self.cycle_time = cycle_time
        self.pairs = None

    def set_activity(self, pairs=None):
        if not pairs:
            pairs = []

        self.pairs = pairs

    def active_at(self, tick):
        for start, end in self.pairs:
            if start <= tick <= end:
                return True
        return False

    def ending_cycle_at(self, tick):
        for start, end in self.pairs:
            if start <= tick <= end:
                cycle_end = (tick - start) % self.cycle_time
                return cycle_end < 1
        return False

    @property
    def last_activity(self):
        if len(self.pairs) > 0:
            return self.pairs[-1][1] + 1
        else:
            return 0


class DiscreteChance:
    """Represents the Chances on one discrete variable"""

    def __init__(self, max_level=40):
        self.points = {0: 1}
        self.max_level = max_level

    def add(self, transition_chance, transition_amount):
        """Adds one transition with a chance and amount to the Statistic"""
        new_points = {}
        for current_level, current_chance in self.points.items():
            remain_chance = current_chance * (1 - transition_chance)
            remain_level = current_level

            switch_chance = current_chance * transition_chance
            switch_level = min(current_level + transition_amount, self.max_level)

            if remain_level in new_points:
                new_points[remain_level] += remain_chance
            else:
                new_points[remain_level] = remain_chance

            if switch_level in new_points:
                new_points[switch_level] += switch_chance
            else:
                new_points[switch_level] = switch_chance

        self.points = new_points

    def chance_under(self, value):
        return sum([chance for level, chance in self.points.items() if level < value])

    def chance_over(self, value):
        return sum([chance for level, chance in self.points.items() if level > value])

    def __str__(self):
        ret = []
        for level, chance in self.points.items():
            ret.append(f"{level:.2f}: {chance:.4f}")
        return "\n".join(ret)


class Rack:
    def __init__(self, modules, start_rack_heat=0.0, attenuation=None, filled_chance_modifier=1.0,
                 ship_chance_modifier=1.0, ship_heat_generation_modifier=1.0):
        self.modules = modules
        self.slots = len(modules)

        self.filled_chance_modifier = filled_chance_modifier
        self.ship_chance_modifier = ship_chance_modifier
        self.ship_heat_generation_modifier = ship_heat_generation_modifier

        self.start_rack_heat = start_rack_heat

        if not attenuation:
            if self.slots > 1:
                self.attenuation = 0.25 ** (1 / (self.slots - 1))
            else:
                self.attenuation = 0
        else:
            self.attenuation = attenuation

    def simulate(self):
        rack_heat = self.start_rack_heat
        chance_statistics = [DiscreteChance() for _ in range(self.slots)]

        for tick in range(1, max([m.last_activity for m in self.modules])):
            heat_influx = 0
            for module in self.modules:  # TODO Optimise activity calculation
                if module.active_at(tick - 1):
                    heat_influx += module.heat_generation * self.ship_heat_generation_modifier

            # Do heat dissipation, with factoring in new heat generation
            # https://wiki.eveuniversity.org/Overheating 1% exponential decay

            # h'(t) = u -0.01 * h(t), h(0) = k
            # -> h(t) = e^(-0.01 * t) * (k - 100 u) + 100 u
            # -> h(1) = e^(-0.01) * (k - 100 u) + 100 u
            # h: rack_heat
            # u: heat_influx
            # k: previous rack_heat
            # (https://www.wolframalpha.com/input?i2d=true&i=h%27%5C%2840%29t%5C%2841%29+%3D+u+-0.01+h%5C%2840%29t%5C%2841%29%5C%2844%29+h%5C%2840%290%5C%2841%29+%3D+k)
            rack_heat = exp(-0.01) * (rack_heat - 100 * heat_influx) + 100 * heat_influx

            # Limit rack heat to 1.0
            rack_heat = min(1.00, rack_heat)

            # Now calculate damage probabilities
            for module_position, module in enumerate(self.modules):
                if module.ending_cycle_at(tick):
                    for chance_position, chance_statistic in enumerate(chance_statistics):
                        position_chance_modifier = self.attenuation ** (abs(module_position - chance_position))
                        damage_chance = rack_heat * position_chance_modifier * self.ship_chance_modifier * self.filled_chance_modifier
                        if module_position == chance_position:
                            # Module damages itself which implies it is not burnt
                            chance_statistic.add(damage_chance, module.heat_damage)
                        else:
                            # Module damages another module, the chance that that can happen depends on this module being burnt as well
                            damage_chance *= chance_statistics[module_position].chance_under(40)
                            chance_statistic.add(damage_chance, module.heat_damage)
            # End of main simulation calculation

            if self.modules[0].ending_cycle_at(tick): # Only display if slot 1 cycles
                print(f"Tick: {tick:04d}, Rack Heat: {rack_heat:.3f}", end="    ")
                print(f"Cycle: {floor(tick / self.modules[0].cycle_time)}", end="    ")

                # Display some specific readout for slot 1
                print(f"Slot 1 chance of 2.5 HP damage {chance_statistics[0].chance_over(2.5) * 100:.3f}%", end="    ")
                print(f"Slot 1 chance of 5 HP damage {chance_statistics[0].chance_over(5) * 100:.3f}%", end="    ")
                print(f"Slot 1 chance of 7.5 HP damage {chance_statistics[0].chance_over(7.5) * 100:.3f}%", end="    ")
                print(f"Slot 1 chance of 10 HP damage {chance_statistics[0].chance_over(10) * 100:.3f}%", end="    ")

                for chance_position, chance_statistic in enumerate(chance_statistics):
                    print(f"Slot {chance_position + 1} alive chance {chance_statistic.chance_under(40) * 100:.1f}%", end="    ")
                print()  # Newline


module1 = Module()
module1.set_activity([(0, 500)])

module2 = Module()
module2.set_activity([])

module3 = Module()
module3.set_activity([])

module4 = Module()
module4.set_activity([])

rack = Rack([module1, module2, module3, module4])
rack.simulate()
