class FuzzyControl:
    def __init__(self):
        self.target_distance = 0.22
        self.max_speed = 0.3

    def compute(self, error_pixels, distance, image_width):
        kp_omega = 0.002
        omega = error_pixels * kp_omega
        omega = max(-0.4, min(0.4, omega))

        dist_error = distance - self.target_distance

        if dist_error > 0.6:
            vx = self.max_speed
        elif dist_error > 0.2:
            vx = 0.15
        elif dist_error > 0.02:
            vx = 0.05
        elif dist_error < -0.05:
            vx = -0.05
        else:
            vx = 0.0

        return vx, omega
