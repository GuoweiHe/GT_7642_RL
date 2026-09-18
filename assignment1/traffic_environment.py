import sys
from typing import Optional

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from traffic_simulator import TrafficRenderer, TrafficSim


RED, GREEN = 0, 1

class TrafficEnv(gym.Env):
    metadata = {"render.modes": ["human", "rgb_array"]}

    def __init__(
        self,
        max_cars_dir: int = 20,
        max_cars_total: int = 30,
        lambda_ns: float = 2.0,
        lambda_ew: float = 3.0,
        cars_leaving: int = 5,
        rewards=None,
        max_steps=1000,
    ):
        self.max_cars_dir = max_cars_dir
        self.max_cars_total = max_cars_total
        self.lambda_ns = lambda_ns
        self.lambda_ew = lambda_ew

        self.rewards = rewards

        self.max_steps = max_steps
        self.current_step = 0

        self.nS = (self.max_cars_dir + 1) ** 2 * 2
        self.nA = 2

        self.action_space = spaces.Discrete(self.nA)
        sizes = [self.max_cars_dir + 1, self.max_cars_dir + 1, 2]
        self.observation_space = spaces.MultiDiscrete(sizes)

        self.isd = np.indices(sizes).reshape(len(sizes), -1).T

        self.s = (0, 0, 1)

        self.sim = TrafficSim(
            max_cars_dir=self.max_cars_dir,
            lambda_ns=self.lambda_ns,
            lambda_ew=self.lambda_ew,
            cars_leaving=cars_leaving,
            ns=self.s[0],
            ew=self.s[1],
            light=self.s[2],
        )

        self.renderer = TrafficRenderer(self.sim, mode="human")

        print("Building transition matrix...")
        self.P = self._build_transition_prob_matrix()
        print("Transition matrix built.")

    def _build_transition_prob_matrix(self):
        P = {}
        for ns in range(self.max_cars_dir + 1):
            for ew in range(self.max_cars_dir + 1):
                for light in [RED, GREEN]:
                    state = (ns, ew, light)
                    P[state] = {action: [] for action in range(self.nA)}
                    for action in range(self.nA):
                        transitions = []
                        for appr_ns in range(8):
                            for appr_ew in range(8):
                                next_light = abs(light - action)
                                next_ns, next_ew, prob_next_state = (
                                    self.sim.get_updated_wait_cars(
                                        ns, ew, next_light, appr_ns, appr_ew
                                    )
                                )

                                reward = self.get_rewards(next_ns, next_ew, next_light)
                                done = self.is_terminal(next_ns, next_ew)
                                next_state = (next_ns, next_ew, next_light)
                                transitions.append(
                                    (prob_next_state, next_state, reward, done)
                                )
                        total_prob = sum([t[0] for t in transitions])
                        transitions = [
                            (prob / total_prob, next_state, reward, done)
                            for prob, next_state, reward, done in transitions
                        ]
                        P[state][action] = transitions
        return P

    def get_rewards(self, ns, ew, light):
        if self.rewards is None:
            return -1 * (ns + ew)
        if (ns, ew, light) not in self.rewards:
            return -1 * (ns + ew)
        else:
            return self.rewards[ns, ew, light]

    def is_terminal(self, ns, ew):
        return ns + ew > self.max_cars_total

    def is_truncated(self):
        return self.current_step >= self.max_steps

    def step(self, action):
        assert self.action_space.contains(action), "Invalid action"

        transitions = self.P[self.s][action]
        probs, next_states, rewards, dones = zip(*transitions)
        next_state_idx = np.random.choice(len(next_states), p=probs)
        next_state = next_states[next_state_idx]
        reward = rewards[next_state_idx]
        done = dones[next_state_idx]

        self.s = next_state
        self.current_step += 1

        return next_state, reward, done, self.is_truncated(), {}

    def reset(self,
              *,
              seed: Optional[int] = None,
              return_info: bool = False,
              options: Optional[dict] = None
              ):
        super().reset(seed=seed)
        random_index = np.random.choice(len(self.isd))
        self.s = tuple(self.isd[random_index])
        self.sim.reset(self.s[0], self.s[1], self.s[2])
        self.current_step = 0
        if return_info:
            return self.s, {}
        else:
            return self.s

    def render(self, close=False):
        if close and self.renderer is not None:
            self.renderer.close()
            return
    
        if self.renderer is not None:
            return self.renderer.render(*self.s)
