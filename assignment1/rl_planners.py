import numpy as np

class ValueIterationPlanner:

    def __init__(self, env, gamma=0.9, theta=1e-6):
        self.env = env
        self.gamma = gamma
        self.theta = theta
        sizes = [self.env.max_cars_dir + 1, self.env.max_cars_dir + 1, 2]
        self.all_states = np.indices(sizes).reshape(len(sizes), -1).T
        self.state_to_index = {
            tuple(state): index for index, state in enumerate(self.all_states)
        }
        self.policy = np.random.choice(
            [0, 1], size=np.array(sizes).prod()
        )
        self.value_function = np.zeros(np.array(sizes).prod())
        self.value_iteration()

    def value_iteration(self):

        while True:
            delta = 0
            Q = np.zeros(
                (len(self.all_states), self.env.action_space.n), dtype=np.float64
            )

            for state_index, state_array in enumerate(self.all_states):
                state = tuple(state_array)

                for action in range(self.env.action_space.n):
                    for prob, next_state, reward, done in self.env.P[state][action]:
                        next_state_index = self.state_to_index[next_state]
                        Q[state_index, action] += prob * (
                            reward + self.gamma * self.value_function[next_state_index] * (not done)
                        )

                best_action_value = np.max(Q[state_index])
                delta = max(delta, abs(best_action_value - self.value_function[state_index]))
                self.value_function[state_index] = best_action_value

            if delta < self.theta:
                break

        for state_index in range(len(self.all_states)):
            self.policy[state_index] = np.argmax(Q[state_index])

    def choose_action(self, state):
        state_index = self.state_to_index[tuple(state)]
        return self.policy[state_index]