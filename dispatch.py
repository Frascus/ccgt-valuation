"""
CCGT dispatch: clean spark spread, state transitions under minimum
up/down-time, and the dynamic-programming solver for the optimal on/off
profile. Also a Monte Carlo wrapper over synthetic price years.
"""

import numpy as np

def compute_spark_spread(*, pun_price, ttf_price, heat_rate, emission_factor, co2_price):
    """
    Clean spark spread (EUR/MWh): power price net of fuel and carbon cost.

        spark_spread = pun_price - heat_rate * ttf_price - emission_factor * co2_price

    Accepts scalars or aligned array-likes.
    """
    return pun_price - heat_rate * ttf_price - emission_factor * co2_price




def update_state(
        *,
        current_state,
        switching,
        min_on_time,
        min_off_time
    ):
    """
    Return the state one hour ahead, given the current state and the
    switch decision.

    A state is (status, hours_in_status), the hour counter capped at the
    minimum up/down-time. Switching is only legal once that minimum is met.
    """
    if current_state[0]=="ON":
        if switching:
            assert current_state[1]>=min_on_time, (
                f"switching not possible from {current_state}: "
                f"minimum on-time is {min_on_time}"
            )
            new_state=("OFF", 1)
        else:
            if current_state[1]<min_on_time:
                new_state=("ON", current_state[1]+1)
            else:
                new_state=current_state
    else:
        if switching:
            assert current_state[1]>=min_off_time, (
                f"switching not possible from {current_state}: "
                f"minimum off-time is {min_off_time}"
            )
            new_state=("ON", 1)
        else:
            if current_state[1]<min_off_time:
                new_state=("OFF", current_state[1]+1)
            else:
                new_state=current_state

    return new_state

def compute_allowed_switch_choices(
        *,
        current_state,
        min_on_time,
        min_off_time
    ):
    """
    Return the legal switch decisions from the current state: [False]
    while the minimum up/down-time is not yet met, [False, True] once
    switching is allowed.
    """

    if current_state[0]=="ON":
        if current_state[1]<min_on_time:
            return [False]
        else:
            return [False, True]

    else:
        if current_state[1]<min_off_time:
            return [False]
        else:
            return [False, True]


def compute_optimal_choice_and_profit(
        *,
        current_state,
        min_on_time,
        min_off_time,
        spark_spread,
        next_time_best_revenue_onward,
        switch_on_cost,
        ccgt_power,
    ):

    """
    Bellman step for one state at one hour: return (best value-to-go,
    switch decision).

    For each legal choice, add this hour's margin (spark_spread * power if
    the resulting status is ON, else 0), less the start-up cost when the
    plant switches on, to the best value-to-go of the successor state, and
    keep the choice with the highest total.
    """

    allowed_switch_choices=compute_allowed_switch_choices(
        current_state=current_state,
        min_on_time=min_on_time,
        min_off_time=min_off_time
        )

    possible_revenues_onward=[]

    for switch in allowed_switch_choices:
        new_state=update_state(
            current_state=current_state,
            switching=switch,
            min_on_time=min_on_time,
            min_off_time=min_off_time
            )

        hourly_revenue=(
            spark_spread*ccgt_power
            if new_state[0]=="ON" else 0
        )
        switch_on_cost_hourly = (
            switch_on_cost if current_state[0]=="OFF" and switch
            else 0
        )
        revenue_onward=(
            hourly_revenue
            + next_time_best_revenue_onward[new_state]
            - switch_on_cost_hourly
        )

        possible_revenues_onward.append((revenue_onward, switch))

    return max(
                possible_revenues_onward,
                key=lambda x: x[0]
            )


def compute_possible_states(*, min_on_time, min_off_time):
    """
    Enumerate the reachable states (status, hours_in_status), with the
    hour counter capped at the minimum required time in that status: the
    capped state is absorbing, since beyond the minimum only "switching
    allowed" matters.
    """
    possible_states=[
    ]

    for i in range (1, min_on_time+1):
        possible_states.append(("ON", i))

    for i in range (1, min_off_time+1):
        possible_states.append(("OFF", i))

    return possible_states


def compute_optimal_dispatch(*, hourly_prices, constraints):
    """
    Solve the optimal dispatch by backward induction.

    Parameters
    ----------
    hourly_prices : DataFrame with a 'spark_spread' column (EUR/MWh), one
        row per hour in chronological order.
    constraints : dict with keys 'min_on_time', 'min_off_time',
        'switch_on_cost' (EUR) and 'ccgt_power' (MW).

    Returns
    -------
    (is_on_dispatch, optimal_value) : the optimal on/off profile as a bool
        array (True = ON) and the corresponding total margin (EUR).
    """
    min_on_time=constraints["min_on_time"]
    min_off_time=constraints["min_off_time"]
    switch_on_cost=constraints["switch_on_cost"]
    ccgt_power=constraints["ccgt_power"]

    possible_states=compute_possible_states(
        min_off_time=min_off_time,
        min_on_time=min_on_time,
        )

    total_hours=len(hourly_prices)

    # value-to-go for every (hour, state); one extra slot for the terminal boundary
    max_profit_onward=[
        {state:None for state in possible_states}
        for _ in range(total_hours+1)
    ]

    # terminal condition: nothing left to earn after the last hour
    max_profit_onward[total_hours]={
        state:0 for state in possible_states
    }

    # optimal switch decision for every (hour, state)
    is_switching=[
        {state:None for state in possible_states}
        for _ in range(total_hours)
    ]

    spark = hourly_prices["spark_spread"].to_numpy()

    for t in reversed(range(total_hours)):
        for state in possible_states:
            max_profit_onward[t][state], is_switching[t][state] = (
                compute_optimal_choice_and_profit(
                    current_state=state,
                    min_on_time=min_on_time,
                    min_off_time=min_off_time,
                    spark_spread=spark[t],
                    next_time_best_revenue_onward=max_profit_onward[t+1],
                    switch_on_cost=switch_on_cost,
                    ccgt_power=ccgt_power
                )
            )

    # reconstruct the optimal on/off path forward from the initial state
    is_on_dispatch=[]
    current_state=("OFF",min_off_time)
    is_on=False

    for t in range(total_hours):
        is_on = not(is_on) if is_switching[t][current_state] else is_on
        is_on_dispatch.append(is_on)
        current_state=update_state(
            current_state=current_state,
            switching=is_switching[t][current_state],
            min_on_time=min_on_time,
            min_off_time=min_off_time,
        )

    optimal_real_revs=max_profit_onward[0][("OFF",min_off_time)]

    is_on_dispatch = np.array(is_on_dispatch, dtype=bool)

    return is_on_dispatch, optimal_real_revs


def count_startups(is_on_dispatch):
    """
    Count start-ups (OFF -> ON transitions) in a dispatch profile; the
    plant is assumed OFF before the first hour.
    """
    is_on_dispatch_extended=np.concatenate(([False], is_on_dispatch))

    return (
        ((~is_on_dispatch_extended)[:-1] & is_on_dispatch_extended[1:])
        .sum()
    )


def monte_carlo_profits(*, year_generator, constraints, n_scenarios):
    """
    Run n_scenarios: for each, generate a synthetic price year, solve the
    optimal dispatch, and collect its optimal profit and start-up count.

    Returns (profits, n_startups), two lists of length n_scenarios.
    """
    profits=[]
    n_startups=[]
    for _ in range(n_scenarios):
        synthetic_year=year_generator()
        is_on_dispatch, optimal_profit=compute_optimal_dispatch(
            hourly_prices=synthetic_year,
            constraints=constraints
        )
        profits.append(optimal_profit)
        n_startups.append(count_startups(is_on_dispatch))
    return profits, n_startups
