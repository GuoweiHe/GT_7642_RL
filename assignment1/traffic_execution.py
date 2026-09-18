import time

import gymnasium as gym

import rl_planners

from traffic_environment import TrafficEnv

rewards = {'state': 0}

env = TrafficEnv(rewards=rewards, max_steps=100)

rl_algo = "Value Iteration"

if rl_algo == "Value Iteration":
    agent = rl_planners.ValueIterationPlanner(env)

observation, info = env.reset(seed=42), {}

RED, GREEN = 0, 1

terminated, truncated = False, False
while not terminated and not truncated:

    action = agent.choose_action(observation)
    observation, reward, terminated, truncated, info = env.step(action)
    
    ns, ew, light = observation
    print(f"Step: {env.current_step}, NS: {ns}, EW: {ew}, "
          f"Light: {'RED' if light == RED else 'GREEN'}, Reward: {reward}, "
          f"Terminated: {terminated}, Truncated: {truncated}")

    env.render()
    time.sleep(0.1)

    if terminated or truncated:
        observation, info = env.reset(), {}
        terminated, truncated = False, False


env.render(close=True)
