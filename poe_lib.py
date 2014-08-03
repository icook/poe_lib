import json
import struct
import base64
import re


class PassiveNode(object):
    def __init__(self, data):
        # The unique id of the passive node
        self.id = None
        # The path the the node image in the image map
        self.icon = ""
        # Keystone (boolean)
        self.ks = False
        # Notable (boolean)
        self.notable = False
        # Display Name
        self.dn = "Unnamed"
        # Orbit and Orbit Index (probably for positioning)
        self.o = None
        self.oidx = None
        # Skill description
        self.sd = []
        # Start Position Class
        self.spc = []
        # Dex/Str/Int increase
        self.da = 0
        self.sa = 0
        self.ia = 0
        # Mastery
        self.m = False
        # Group
        self.g = None
        self.in_nodes = {}
        self.out_nodes = {}

        self.__dict__.update(data)
        self.notable = data['not']
        self.effects = []
        for s in self.sd:
            eff = Effect(s)
            eff.source = self
            self.effects.append(eff)

        if self.spc:
            PoE.character_types[self.spc[0]].start_node = self.id

    def __str__(self):
        return "Passive Node " + self.dn

    @classmethod
    def print_passives(cls, passives):
        for node in passives:
            print "{}{}{}".format(
                node.dn,
                " [N]" if node.notable else "",
                " [KS]" if node.ks else "")
            for s, effect in zip(node.sd, node.effects):
                print "\t- {}".format(effect.__dict__)

    @classmethod
    def decode_passive(cls, b64):
        raw = base64.b64decode(b64.replace("-", "+").replace("_", "/"))
        version = struct.unpack(">I", raw[:4])[0]
        char_type = struct.unpack(">H", raw[4:6])[0]
        checksum = struct.unpack(">B", raw[6:7])[0]
        assert checksum == 1

        new = Character()
        new.char_type = PoE.character_types[char_type]
        for start in xrange(6, len(raw), 2):
            new.allocated_nodes.add(struct.unpack(">H", raw[start:start + 2])[0])

        assert version == 2
        return new

    def neighbor_nodes(self):
        for out_node in self.out_nodes:
            yield out_node
        for in_node in self.in_nodes:
            yield in_node


class CharacterTypes(object):
    def __init__(self, data):
        self.start_node = None
        self.__dict__.update(data)

    def __str__(self):
        return "<{} instance at {}, id {}, spc {}>".format(self.__class__.__name__, id(self), self.id, self.start_node)
    __repr__ = __str__


class Effect(object):
    top_level_rules = [
        {"exp": "^(Adds )?(Can set up to )?(?P<amount>[\+-]?[0-9\.]+)(?P<perc>\%)?(-(?P<upper_amount>[\+-]?[0-9\.]+)(\%)?)? (?P<stat>[a-zA-Z\s]+)$",
         "callables": ("number_parse",),
         "mixins": ["effect_type", "clean_toof"]},
        {"exp": "^(?P<require>((Minions)|(Totems))) ((have)|(gain)|(deal)) (?P<amount>[\+-]?[0-9\.]+)(?P<perc>\%)? (?P<stat>[a-zA-Z\s]+)$",
         "callables": ("number_parse",),
         "mixins": ["effect_type", "clean_toof"]},
        {"exp": "^(?P<stat>[a-zA-Z\s]+)$"}
    ]

    mixin_rules = {
        "effect_type": {"exp": "^(?:(?P<add>increased|additional)|(?P<subt>decreased|reduced)|(?P<multi>more|less)) (?P<stat>[a-zA-Z\s]+)$", "callables": ("parse_effect_type",)},
        "clean_toof": {"exp": "^((to)|(of)) (?P<stat>[a-zA-Z\s]+)$"},
    }

    stat_rules = [
        {"exp": "^(?P<stat>[a-zA-Z\s]+) ((on)|(with)|(while)|(while holding a)|(of)|(from)|(for)) (?P<require>[a-zA-Z\s]+)$"},
        {"exp": "^(?P<stat>[a-zA-Z\s]+) (per) (?P<require>[a-zA-Z]+ Charge)$", "category": "attack"},

        {"exp": "^(?P<require>[a-zA-Z\s]+) (?P<stat>Leeched as ((Mana)|(Life)))$"},
        {"exp": "^(?P<one>[a-zA-Z\s]+) and (?P<two>[a-zA-Z\s]+)$", "callables": ("dual",)},
        {"exp": "^(chance to Avoid )((Elemental Status Ailments)|(Dodge Attacks)|(being [a-zA-Z]+))$", "category": "defense"},
        {"exp": "^(?P<resistance_type>[a-zA-Z\s]+) (Resistance[s]?)$", "callables": ("resistance",)},
        {"exp": "^([a-zA-Z\s]+) ((Damage)|(Duration))$", "category": "attack"},
        {"exp": "^([a-zA-Z\s]+) ((Life)|(Mana)|(Energy Shield))$", "category": "defense"},
        {"exp": "^(((Life)|(Mana)|(Energy Shield))) ((Reserved)|(Cooldown Recovery)|(Regeneration Rate)|(Regenerated per Second)|(Cost))$", "category": "defense"},
        {"exp": "^(?P<require>((Melee)|(Projectile)) )?(?P<stat>((Attack)|(Casting)) (Speed))$", "category": "attack"},
        {"exp": "^Movement Speed$", "category": "misc"},
        {"exp": "^(?P<require>((Weapon)|(Global)) )?(Critical Strike)([a-zA-Z\s]+)$", "category": "attack"},
        {"exp": "((Evasion Rating)|(Armour)|(Block)|(Stun Recovery))", "category": "defense"},
        {"exp": "^((Chance to Block)|(Accuracy Rating)|(Intelligence)|(Strength)|(Dexterity))$", "category": "defense"},
    ]

    def dual(self):
        self.effects = [self.last_match['one'], self.last_match['two']]
        self.stat = ''

    def resistance(self):
        if self.last_match['resistance_type'] == "all Elemental":
            self.effects = ["Fire Resistance", "Lightning Resistance", "Ice Resistance"]
        else:
            self.effects = [self.last_match['resistance_type'] + " Resistance"]
        self.stat = ""

    def number_parse(self):
        if self.last_match['perc']:
            self.amount_appl = "perc"
        else:
            self.amount_appl = "flat"

        self.lower_amount = float(self.last_match['amount'])
        if 'upper_amount' in self.last_match and self.last_match['upper_amount']:
            self.upper_amount = float(self.last_match['upper_amount'])
        else:
            self.upper_amount = float(self.last_match['amount'])

    def parse_effect_type(self):
        """ Handles more/less and increase/decrease (sometimes written
        additional/reduced) percentage modifiers """
        # ignore flat modifiers
        if self.amount_appl != "perc":
            return

        if self.last_match['add']:
            self.effect = float(self.lower_amount) / 100
        elif self.last_match['subt']:
            self.effect = (100.0 - float(self.lower_amount)) / 100

        if self.last_match['multi']:
            self.amaount_appl = "prec_mult"
            if self.last_match['multi'] == "more":
                self.effect = (100.0 + float(self.lower_amount)) / 100
            else:
                self.effect = (100.0 - float(self.lower_amount)) / 100

    def __init__(self, s):
        self.requires = []
        self.effects = []
        self.category = "Unknown"
        self.orig_text = s
        self.rules = []
        self.raw_match = {}
        self.last_match = {'stat': s}

        # Try to match to a top level rule
        s = s.strip()
        for i, rule in enumerate(self.top_level_rules):
            if self.parse(rule):
                self.rules.append("top{}".format(i))
                break
        else:
            # If we don't match any of the rules, then info can't be determined
            self.stat = "Unknown"
            del self.last_match
            return

        # Do a whole second round of parsing for the stat. This won't be
        # chopping down the "Stat" field, but just adding properties to be used
        # later
        for i, rule in enumerate(self.stat_rules):
            self.last_match = {'stat': self.stat}
            if self.parse(rule):
                self.rules.append("{}".format(i))

        # If we still have stat information left, it's an effect
        if self.stat and self.stat != "Unknown":
            self.effects.append(self.stat)

        # Avoid dumb collisions with things like whitespace and casing
        self.requires = [r.lower().strip() for r in self.requires]
        self.effects = [r.lower().strip() for r in self.effects]
        # Some effects/requirements have different names. Replace them all to
        # the same names
        subs = {"evasion": "evasion rating"}
        for start, finish in subs.iteritems():
            if start in self.requires:
                self.requires[self.requires.index(start)] = finish
            if start in self.effects:
                self.effects[self.effects.index(start)] = finish

        del self.stat
        del self.raw_match
        del self.last_match

    @property
    def effect_pretty(self):
        if not hasattr(self, 'lower_amount'):
            return "unknown"
        s = str(self.lower_amount)
        if self.upper_amount != self.lower_amount:
            s = "{}-{}".format(self.lower_amount, self.upper_amount)
        if self.amount_appl == "perc":
            s += "% additive"
        elif self.amount_appl == "flat":
            s += " flat"
        elif self.amount_appl == "perc_mult":
            s += "% multiplicative"
        if self.upper_amount != self.lower_amount:
            s += " (avg {})".format(((self.upper_amount - self.lower_amount) / 2) + self.lower_amount)
        return s

    def tabulate(self):
        return [str(s) for s in (self.effect_pretty, ", ".join(self.requires), ", ".join(self.effects), self.source, self.orig_text)]

    def __str__(self):
        return ("amount {}; requires {}; effects {}; source {}; \"{}\""
                .format(self.effect_pretty, self.requires, self.effects, self.source, self.orig_text))

    @property
    def hash_rules(self):
        return "|".join(self.rules)

    @property
    def hash_requires(self):
        return "|".join(sorted(s.lower() for s in self.requires))

    @property
    def hash_effects(self):
        return "|".join(sorted(s.lower() for s in self.requires))

    def parse(self, rule):
        match_string = self.last_match['stat']  # default to matching the whole string
        # If they specified a previous match that they're going to compare
        # against
        if 'match' in rule:
            # if the match they wan't doesn't exist, skip
            if rule['match'] not in self.last_match:
                return False
            # change the match string to something from previous matches
            match_string = self.last_match[rule['match']]

        # Compile the regexp if not compiled
        if isinstance(rule['exp'], basestring):
            rule['exp'] = re.compile(rule['exp'], flags=re.I)

        # Try and match the regexp
        res = rule['exp'].match(match_string)
        if res is not None:
            self.last_match = res.groupdict()
            self.raw_match.update(self.last_match)
            if 'stat' in self.last_match:
                self.stat = self.last_match['stat']
            # Run specified callables to perform logic on the matched data
            for cal in rule.get('callables', []):
                getattr(self, cal)()

            # Allow putting basic effect info in the rule information
            if 'category' in rule:
                self.category = rule['category']
            if 'requires' in rule:
                self.requires.extend(rule['requires'])
            if 'require' in self.last_match and self.last_match['require']:
                self.requires.append(self.last_match['require'])
            if 'effects' in rule:
                self.effects.extend(rule['effects'])
            if 'effect' in self.last_match and self.last_match['effect']:
                self.effects.append(self.last_match['effects'])

            # Now run the extra rules for this match
            for name in rule.get('mixins', []):
                self.parse(self.mixin_rules[name])

            return True
        return False

    def group(self):
        return "-".join([str(getattr(self, attr))
                         for attr in ['hash_effects', 'hash_requires', 'effect_type']
                         if hasattr(self, attr)])


class Item(object):
    def __init__(self, data):
        self.__dict__.update(data)
        self.mods = []
        for m in self.explicitMods + getattr(self, 'implicitMods', []):
            eff = Effect(m)
            eff.source = self
            self.mods.append(eff)

    def __str__(self):
        return "Item " + self.name + " (" + self.typeLine + ")"

    @classmethod
    def print_items(cls, items):
        for item in items:
            print "{}".format(item.typeLine)
            for mod in item.explicitMods + getattr(item, 'implicitMods', []):
                print "\t- {}".format(mod)
            for mod in item.mods:
                print "\t- {}".format(mod.__dict__)


class Character(object):
    def __init__(self):
        self.items = []
        self.char_type = None
        self.allocated_nodes = set()
        self.can_allocate_skills = set()

    def refresh_can_allocate(self, e):
        self.can_allocate_skills = set()
        for node in self.allocated_nodes:
            for neighbor in node.neighbor_nodes:
                # Is the node already allocated? Then skip
                if neighbor.id in self.allocated_nodes:
                    continue
                # Is it the actual start node
                if node.id == self.char_type.start_node.id:
                    self.can_allocate_skills.add(node.id)
                    continue
                # Is one of the nodes pointing to this node active, or is one
                # of the nodes pointing the start node
                for out_node in node.out_nodes:
                    if out_node.id in self.allocated_nodes or out_node.id == self.char_type.start_node.id:
                        self.can_allocate_skills.add(node.id)
                        continue

    def print_passives(self):
        PassiveNode.print_passives([PoE.passive_nodes[p] for p in self.allocated_nodes])

    def print_items(self):
        Item.print_items(self.items)

    @property
    def effects(self):
        for item in self.items:
            for effect in item.mods:
                yield effect

        for passive in self.allocated_nodes:
            passive = PoE.passive_nodes[passive]
            for effect in passive.effects:
                yield effect


class PoE(object):
    character_data = {
        "1": {
            "base_str": 32,
            "base_dex": 14,
            "base_int": 14
        },
        "3": {
            "base_str": 14,
            "base_dex": 14,
            "base_int": 32
        },
        "0": {
            "base_str": 20,
            "base_dex": 20,
            "base_int": 20
        },
        "2": {
            "base_str": 14,
            "base_dex": 32,
            "base_int": 14
        },
        "4": {
            "base_str": 23,
            "base_dex": 23,
            "base_int": 14
        },
        "6": {
            "base_str": 14,
            "base_dex": 23,
            "base_int": 23
        },
        "5": {
            "base_str": 23,
            "base_dex": 14,
            "base_int": 23
        }
    }
    passive_nodes = {}
    character_types = {}

    def __init__(self):
        for char_id, data in self.character_data.iteritems():
            data['id'] = char_id
            self.character_types[int(char_id)] = CharacterTypes(data)

        passive_data = json.load(open("passives.json"))
        for data in passive_data['nodes']:
            self.passive_nodes[data['id']] = PassiveNode(data)

        # Convert the simple integer ids in the out node list to actual objects
        for node in self.passive_nodes.itervalues():
            for node_hash in node.out:
                # change our list of hashes into a dict of Passive objects
                node.out_nodes[node_hash] = self.passive_nodes[node_hash]
                # set the outgoing nodes incoming pointer
                self.passive_nodes[node_hash].in_nodes = node

        print "Loaded {} passives".format(len(self.passive_nodes))
        print "Loaded character classes {}".format(self.character_types.values())

PoE = PoE()
