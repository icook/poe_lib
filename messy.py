import json
import tabulate
import poe_lib
import pprint


def load_character():
    # Load my characters passive tree
    char = poe_lib.PassiveNode.decode_passive("AAAAAgAAAdwFLRHVFx0b-iXfMglAoEd-SshT31eXWNtfOWBBYEtlTWxGbmluqnJsdO14DXrvguSE2YTviq-QEZstm4OeuaQZqW618r6Kvqe-vMAPypDSTd3j")
    character_data = json.load(open("character.json"))

    for item in character_data['items']:
        if item['inventoryId'] not in ['MainInventory', 'Flask']:
            char.items.append(poe_lib.Item(item))

    data = [eff.tabulate() for eff in char.effects]
    print tabulate.tabulate(data, headers=["Effect Magnitude", "Requirement to Effect", "Effects", "Source", "Original Text"])


def group_unsorted():
    def show_stats(attrs, cond):
        attrs = {a: {'total': 0} for a in attrs}
        for p in poe_lib.PoE.passive_nodes.itervalues():
            for eff in p.effects:
                if cond(eff):
                    for attr, dct in attrs.iteritems():
                        a = getattr(eff, attr, '')
                        if isinstance(a, list):
                            a = "|".join(a)
                        if a:
                            dct.setdefault(a, 0)
                            dct[a] += 1
                            dct['total'] += 1
        pprint.pprint(attrs)

    print "Stats for category = Unknown"
    show_stats(["stat", "hash_rules"], lambda eff: eff.category == "Unknown")
    show_stats(["orig_text", "stat", "conditions", "type"], lambda eff: eff.stat.startswith("Maximum number") and eff.category == "Unknown")


def load_lots_of_items():
    char = poe_lib.Character()
    js = open("items.json").read().strip().decode('ascii', 'ignore')
    items = json.loads(js)

    weapon_types = {}
    words = {}
    for _, item, _ in items:
        if isinstance(item, dict):
            typ = item['typeLine'].lower()
            for word in typ.split(" "):
                words.setdefault(word, 0)
                words[word] += 1

            checks = ['sword', 'mace', 'stave', 'flask', 'shield', 'greaves', 'boots']
            for check in checks:
                if check in typ:
                    weapon_types.setdefault(check, 0)
                    weapon_types[check] += 1
                    break
            else:
                weapon_types.setdefault("unk", 0)
                weapon_types["unk"] += 1

    pprint.pprint(sorted(words.items(), key=lambda a: a[1]))
    pprint.pprint(sorted(weapon_types.items(), key=lambda a: a[1]))
    data = [eff.tabulate() for eff in char.effects]
    print tabulate.tabulate(data, headers=["Effect Magnitude", "Requirement to Effect", "Effects", "Source", "Original Text"])

load_lots_of_items()
