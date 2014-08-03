# Skill gems
molten_strike_mana = 8
molten_strike_proj_dec = 0.6
molten_strike_phys_mult = 1.2 * 0.6  # 120% physical * 60% of physical converted to fire
lmp_proj_dec = 0.7
lmp_proj_inc = 0.10
lmp_mana_mult = 1.5
multistrike_att_dec = 0.64
multistrike_mana_mult = 1.8
wed_increase = 1.49
wed_mana_mult = 1.5
added_fire_perc = 0.29
added_fire_mana_mult = 1.3
conc_effect_more = 1.59
conc_effect_mana_mult = 1.6

# Passives
point_blank_more = 1.43

# Calculate projectiles per second
aps = 4.84
multistrike = 3
lmp_proj = 2
molten_strike_proj = 2
projectile_per_sec = aps * (molten_strike_proj + lmp_proj) * multistrike

# Calculate base mana cost
mana_cost = molten_strike_mana * lmp_mana_mult * multistrike_mana_mult

# Calculate our common more/less/increase/decrease bases
phys_att_damage = 150
combined_proj_inc = sum([lmp_proj_inc])
base_ball = phys_att_damage * molten_strike_phys_mult * (1 + combined_proj_inc)
combined_proj_less_more = molten_strike_proj_dec * lmp_proj_dec * multistrike_att_dec * point_blank_more

wed = base_ball * combined_proj_less_more * wed_increase
wed_mana = mana_cost * wed_mana_mult
print "weapon elemental damage: {} dpp, {} dps, {} mps".format(wed, wed * projectile_per_sec, wed_mana * aps)
afd = (base_ball + (added_fire_perc * phys_att_damage)) * combined_proj_less_more
afd_mana = mana_cost * added_fire_mana_mult
print "added fire damage: {} dpp, {} dps, {} mps".format(afd, afd * projectile_per_sec, afd_mana * aps)

raw_input()
