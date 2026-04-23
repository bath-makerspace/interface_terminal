def Calculate_Personal_Cost(Weight_String: str) -> float:
    try:
        # Convert the string from the Entry box to a number
        Weight = int(Weight_String)

        tier_1_threshold = 70
        tier_1_cost_per_gram = 0.06
        tier_2_cost_per_gram = 0.04

        if Weight <= tier_1_threshold:
            return round(Weight * tier_1_cost_per_gram, 2)
        else:
            tier_1_cost = tier_1_threshold * tier_1_cost_per_gram
            tier_2_cost = (Weight - tier_1_threshold) * tier_2_cost_per_gram
            return round(tier_1_cost + tier_2_cost, 2)
    except ValueError:
        return 0.0  # Return 0 if the input isn't a valid number


def calculate_markforged_cost(onyx_cc, fiber_type, fiber_cc, hours):
    """
    Calculates the total cost for a Markforged print.

    onyx_cc: float/int - Volume of base Onyx
    fiber_type: string - 'Carbon Fibre', 'Kevlar', or 'None'
    fiber_cc: float/int - Volume of reinforcement fiber
    hours: float/int - Total print time
    """

    # --- PLACEHOLDER PRICE CONSTANTS ---
    ONYX_PRICE_PER_CC = 0.50  # e.g., £0.50 per cc
    CARBON_FIBER_PRICE_PER_CC = 1.50  # e.g., £1.50 per cc
    KEVLAR_PRICE_PER_CC = 1.20  # e.g., £1.20 per cc
    TIME_PRICE_PER_HOUR = 2.00  # e.g., £2.00 per hour for machine wear
    # -----------------------------------

    try:
        # Convert inputs to floats in case they come in as strings from Entry widgets
        v_onyx = float(onyx_cc)
        v_fiber = float(fiber_cc)
        t_hours = float(hours)
    except (ValueError, TypeError):
        return 0.0

    # Calculate Base Onyx Cost
    base_cost = v_onyx * ONYX_PRICE_PER_CC

    # Calculate Fiber Cost
    if fiber_type == "Carbon Fibre":
        fiber_cost = v_fiber * CARBON_FIBER_PRICE_PER_CC
    elif fiber_type == "Kevlar":
        fiber_cost = v_fiber * KEVLAR_PRICE_PER_CC
    else:
        fiber_cost = 0.0

    # Calculate Time Cost
    time_cost = t_hours * TIME_PRICE_PER_HOUR

    total = 1.4*(base_cost + fiber_cost + time_cost)

    return round(total, 2)