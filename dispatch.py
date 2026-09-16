import numpy as np

def compute_spark_spread(*, pun_price, ttf_price, heat_rate, emission_factor, co2_price):
    """
    function that computes hourly spark spread
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
    Compute and return the new state starting from current one and based 
    on the decision about switching or not
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
    Returns a list of legal choices about switching or not the state
    based on current state
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
    compute and return the best possible revenue onward and the 
    corresponding switching decision
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
    computes the list of possible states, each one defined by status
    ON or OFF and by the time spent in that status (capped at its minimum
    required time in that status before switching is possible)
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
    Return a tuple containing the optimal ON/OFF status profile for the turbine,
    as a list of boolean (True for ON, False for OFF),
    and the corresponding optimal value extracted,
    given hourly prices and physical costraints.
    """
    min_on_time=constraints["min_on_time"]
    min_off_time=constraints["min_off_time"]
    switch_on_cost=constraints["switch_on_cost"]
    ccgt_power=constraints["ccgt_power"]

    possible_states=compute_possible_states(
        min_off_time=min_on_time, 
        min_on_time=min_off_time,
        )

    total_hours=len(hourly_prices)

    #creating list of dict
    max_profit_onward=[
        {state:None for state in possible_states}
        for _ in range(total_hours+1)
    ]

    #initializing the final+1 hour
    max_profit_onward[total_hours]={
        state:0 for state in possible_states
    }

    #creating list of dict
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
    compute the number of startups, for cost estimation purpose, 
    fron the optimal profile
    """
    is_on_dispatch_extended=np.concatenate(([False], is_on_dispatch))
    
    return (
        ((~is_on_dispatch_extended)[:-1] & is_on_dispatch_extended[1:])
        .sum()
    )

    



