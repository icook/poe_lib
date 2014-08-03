import parsley
import poe_lib

x = parsley.makeGrammar(
    """
    float = <('+' | '-')?>:sign <digit+>:a <('.' <digit+>)?>:b -> float((sign or "+") + a + (b or ""))

    amount = float:t -> (int(t), int(t))
    range = float:lower ws '-' ws float:upper -> (int(lower), int(upper))
    effect_metric = (amount | range):effect_value <'%'?>:perc -> (effect_value, 'perc' if perc else 'flat')

    word = ws letter+ ws
    effect = ws effect_metric:eff <word*>:extra ws -> dict(effect_type=eff[0], effect_value=eff[1], extra=extra)

    conditions = 'spells cast by totems' | 'attacks used by totems' | 'trap damage penetrates'
    conjunction = 'have'
    conditional = condition ws conjunction? -> condition
    conditionals = conditionals*

    expr = (conditionals:cond effect:effect -> dict(conditionals=cond, **effect))
           | (letterOrDigit | ' ')+ end -> dict(type="Unknown")
    #expr = (ws mod ws '.')*
    """, {})

for passive in poe_lib.PoE.passive_nodes.itervalues():
    for effect in passive.effects:
        print effect.orig_text
        print x(effect.orig_text.lower()).expr()
