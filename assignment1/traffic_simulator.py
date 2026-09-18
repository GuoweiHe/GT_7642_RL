import os

import numpy as np
import pygame
import scipy.stats as stats


class TrafficSim:

    def __init__(self, max_cars_dir, lambda_ns, lambda_ew, cars_leaving, ns, ew, light):
        # set the main parameters
        self.max_cars_dir = max_cars_dir
        self.lambda_ns = lambda_ns
        self.lambda_ew = lambda_ew
        self.cars_leaving = cars_leaving

        self.cars_waiting_ns = ns
        self.cars_waiting_ew = ew
        self.light_ns = light

        self.prob_appr_cars = 1.0

    def get_approaching_cars(self):
        # sample the number of approaching cars from a Poisson distribution
        approaching_cars_ns = np.random.poisson(self.lambda_ns)
        approaching_cars_ew = np.random.poisson(self.lambda_ew)
        return approaching_cars_ns, approaching_cars_ew

    def get_updated_wait_cars(
        self, cars_wait_ns, cars_wait_ew, light, cars_appr_ns, cars_appr_ew
    ):
        updated_cars_wait_ns = min(
            max(cars_wait_ns + cars_appr_ns - light * self.cars_leaving, 0),
            self.max_cars_dir,
        )
        updated_cars_wait_ew = min(
            max(cars_wait_ew + cars_appr_ew - (1 - light) * self.cars_leaving, 0),
            self.max_cars_dir,
        )

        prob_appr_ns = stats.poisson.pmf(cars_appr_ns, self.lambda_ns)
        prob_appr_ew = stats.poisson.pmf(cars_appr_ew, self.lambda_ew)
        return updated_cars_wait_ns, updated_cars_wait_ew, prob_appr_ns * prob_appr_ew

    def advance(self, action):
        # get the number of approaching cars
        cars_appr_ns, cars_appr_ew = self.get_approaching_cars()

        self.light_ns = abs(self.light_ns - action)

        updated_cars_wait_ns, updated_cars_wait_ew, prob_appr_cars = (
            self.get_updated_wait_cars(
                self.cars_waiting_ns,
                self.cars_waiting_ew,
                self.light_ns,
                cars_appr_ns,
                cars_appr_ew,
            )
        )

        self.cars_waiting_ns = updated_cars_wait_ns
        self.cars_waiting_ew = updated_cars_wait_ew
        self.prob_appr_cars = prob_appr_cars

    def get_world_state(self):
        return (
            self.cars_waiting_ns,
            self.cars_waiting_ew,
            self.light_ns,
            self.prob_appr_cars,
        )

    def reset(self, ns, ew, light):
        self.cars_waiting_ns = ns
        self.cars_waiting_ew = ew
        self.light_ns = light
        self.prob_appr_cars = 1.0


class TrafficRenderer:

    def __init__(self, sim, mode):
        self.sim = sim
        self.mode = mode

        pygame.init()
        self.screen_width = 1082
        self.screen_height = 1084

        self.window = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )
        self.screen = pygame.Surface((self.screen_width, self.screen_height))

        self.background_image = pygame.image.load(
            os.path.join("images", "intersection.png")
        )
        self.car_im_ns = pygame.image.load(os.path.join("images", "car_ns.png"))
        self.car_im_sn = pygame.image.load(os.path.join("images", "car_sn.png"))
        self.car_im_ew = pygame.image.load(os.path.join("images", "car_ew.png"))
        self.car_im_we = pygame.image.load(os.path.join("images", "car_we.png"))
        self.traffic_light_green = pygame.image.load(
            os.path.join("images", "light_green.png")
        )
        self.traffic_light_red = pygame.image.load(
            os.path.join("images", "light_red.png")
        )
        self.end_image = pygame.image.load(
            os.path.join("images", "simulation_over.png")
        )

    def render(self, ns, ew, light):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.VIDEORESIZE:
                self.screen_width, self.screen_height = event.size
                self.window = pygame.display.set_mode(
                    (self.screen_width, self.screen_height), pygame.RESIZABLE
                )
                self.screen = pygame.Surface((self.screen_width, self.screen_height))

        self.screen.blit(self.background_image, (0, 0))
        y_offset = 415
        for i in range(ns // 2):
            self.screen.blit(
                self.car_im_ns, (515, y_offset - i * (self.car_im_ns.get_height() + 10))
            )

        y_offset = 625
        for i in range(ns - ns // 2):
            self.screen.blit(
                self.car_im_sn, (545, y_offset + i * (self.car_im_sn.get_height() + 10))
            )

        x_offset = 625
        for i in range(ew // 2):
            self.screen.blit(
                self.car_im_ew, (x_offset + i * (self.car_im_ew.get_width() + 10), 515)
            )

        x_offset = 415
        for i in range(ew - ew // 2):
            self.screen.blit(
                self.car_im_we, (x_offset - i * (self.car_im_we.get_width() + 10), 545)
            )

        position_light_ns = (415, 305)
        position_light_ew = (685, 600)
        if light == 1:
            self.screen.blit(self.traffic_light_green, position_light_ns)
            self.screen.blit(self.traffic_light_red, position_light_ew)
        else:
            self.screen.blit(self.traffic_light_red, position_light_ns)
            self.screen.blit(self.traffic_light_green, position_light_ew)

        if self.mode == "human":
            self.window.blit(self.screen, (0, 0))
            pygame.display.update()
        elif self.mode == "rgb_array":
            return pygame.surfarray.array3d(self.screen)

    def close(self):
        pygame.quit()
