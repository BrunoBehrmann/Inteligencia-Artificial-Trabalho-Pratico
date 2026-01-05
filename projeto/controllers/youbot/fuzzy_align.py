class FuzzyAlign:
    def __init__(self, image_width):
        self.image_width = image_width

    def compute(self, error_px):
        """
        Retorna apenas omega.
        """
        norm_error = error_px / (self.image_width / 2)  # -1 .. 1

        if abs(norm_error) < 0.05:
            return 0.0

        if norm_error > 0.5:
            return 0.25
        elif norm_error > 0.2:
            return 0.15
        elif norm_error > 0.05:
            return 0.08

        if norm_error < -0.5:
            return -0.25
        elif norm_error < -0.2:
            return -0.15
        elif norm_error < -0.05:
            return -0.08

        return 0.0
