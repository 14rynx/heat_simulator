from math import ceil


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
                next_cycle_precise = start
                next_cycle_round = start
                while next_cycle_round < end + self.cycle_time and next_cycle_round < tick:
                    next_cycle_precise += self.cycle_time
                    next_cycle_round = ceil(next_cycle_precise)

                if next_cycle_round == tick:
                    return True
                else:
                    return False

        return False

    @property
    def last_activity(self):
        return self.pairs[-1][1] + 1


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
            factor_dict = {
                8: 0.82,
                7: 0.79,
                6: 0.76,
                5: 0.71,
                4: 0.63,
                3: 0.50,
                2: 0.25,
                1: 1
            }

            self.attenuation = factor_dict[self.slots]
        else:
            self.attenuation = attenuation

    def simulate(self):
        rack_heat = self.start_rack_heat
        chance_statistics = [DiscreteChance()] * self.slots

        for tick in range(1, max([m.last_activity for m in self.modules])):
            # Do heat dissipation # TODO: Does immediate heat also get dissipated ?
            rack_heat *= 0.99

            # And generate heat by active modules
            for module in self.modules:  # TODO Optimise activity calculation
                if module.active_at(tick - 1):
                    rack_heat += module.heat_generation * self.ship_heat_generation_modifier
            rack_heat = min(1.00, rack_heat)  # Limit rack heat to 1.0
            print(f"Tick: {tick}, Rack Heat: {rack_heat:.3f}", end=" ")

            # Now calculate damage probabilities
            for module_position, module in enumerate(self.modules):
                if module.ending_cycle_at(tick):
                    for chance_position, chance_statistic in enumerate(chance_statistics):
                        position_chance_modifier = self.attenuation ** (abs(module_position - chance_position))
                        damage_chance = rack_heat * position_chance_modifier * self.ship_chance_modifier * self.filled_chance_modifier

                        # Adjust damage chance to module being burnt out
                        damage_chance *= chance_statistic.chance_under(40)

                        chance_statistic.add(damage_chance, module.heat_damage)

            # Display some basic readout
            for chance_position, chance_statistic in enumerate(chance_statistics):
                print(f"Slot {chance_position + 1}: Alive for {chance_statistic.chance_under(40) * 100:.1f}%", end=" ")
            print()  # Newline


module1 = Module()
module1.set_activity([(0, 200)])

module2 = Module()
module2.set_activity([(0, 200)])

rack = Rack([module1, module2])
rack.simulate()
