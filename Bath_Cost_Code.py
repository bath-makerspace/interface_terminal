def Calculate_Personal_Cost(Weight):
    tier_1_threshold = 70
    tier_1_cost_per_gram = 0.06
    tier_2_cost_per_gram = 0.04

    if Weight <= tier_1_threshold:
        return round(Weight * tier_1_cost_per_gram, 2)
    else:
        tier_1_cost = tier_1_threshold * tier_1_cost_per_gram
        tier_2_cost = (Weight - tier_1_threshold) * tier_2_cost_per_gram
        return round(tier_1_cost + tier_2_cost, 2)
    return 