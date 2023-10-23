from math import ceil, exp


class Module:
    """Holds all data related to one in-game module.
    It's heat related values, cycle time as well as when in the simulation it is active = overheated"""

    def __init__(self, hp=40, heat_damage=2.7, heat_generation=0.01, cycle_time=3.75):
        self.hp = hp
        self.heat_damage = heat_damage
        self.heat_generation = heat_generation
        self.cycle_time = cycle_time
        self.pairs = []

    def set_green(self, pairs=None):
        if not pairs:
            pairs = []

        self.pairs = pairs

    def green_at(self, tick):
        for start, end in self.pairs:
            if start <= tick <= end:
                return True
        return False

    def active_at(self, tick):
        for start, end in self.pairs:
            if start <= tick <= self.cycle_time * ceil(end / self.cycle_time):
                return True
        return False

    def ending_cycle_at(self, tick):
        for start, end in self.pairs:
            if start + 1 <= tick <= self.cycle_time * ceil(end / self.cycle_time):
                cycle_end = (tick - start) % self.cycle_time
                return cycle_end < 1
        return False

    @property
    def last_activity(self):
        if len(self.pairs) > 0:
            return int(ceil(self.pairs[-1][1])) + 1
        else:
            return 0


class DiscreteChance:
    """Represents the chances on one discrete variable.

       E.g. if you play a game with a six sided dice,
       where you are out if you roll two times six,
       that might be modeled as following:

       Every time you roll, you get a 1 in 6 chance of getting a strike,
       two strikes and you are out. Now to calculate this chance after n rolls,
       you would do

       d = DiscreteChance(max_level=2) # we are interested in max 2 strikes, anything higher can be lumped together
       for roll_nr in range(rolls):
           d.add(1 / 6, 1) # With the chance of 1/6 add a strike
           print(d.chance_under(2)) # Print the chance that you are still under two strikes total
    """

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

    def chance_under(self, level):
        """Returns the probability that the level is under some level."""
        return sum([c for l, c in self.points.items() if l < level])

    def chance_over(self, level):
        """Returns the probability that the level is over some level."""
        return sum([c for l, c in self.points.items() if l > level])

    def expected(self):
        """Returns the expected damage value."""
        return sum([l * c for l, c in self.points.items()])

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

    def simulate(self, print_callback=None):
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

            if print_callback:
                print_callback(tick, rack_heat, chance_statistics)
