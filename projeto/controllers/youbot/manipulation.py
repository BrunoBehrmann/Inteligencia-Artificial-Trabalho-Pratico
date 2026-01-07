
from arm import ArmHeight


class ManipulationManager:
    def __init__(self, arm, gripper):
        self.arm = arm
        self.gripper = gripper
        self.timer = 0
        self.step = 0

    def reset_sequence(self):

        self.timer = 0
        self.step = 0

    def run_pickup_sequence(self):

        self.timer += 1

        if self.step == 0:

            self.arm.set_height(ArmHeight.FRONT_FLOOR)
            self.gripper.release()
            if self.timer > 60:
                self.step = 1
                self.timer = 0

        elif self.step == 1:

            self.gripper.grip()
            if self.timer > 40:
                self.step = 2
                self.timer = 0

        elif self.step == 2:

            self.arm.set_height(ArmHeight.FRONT_PLATE)
            if self.timer > 50:
                return True

        return False

    def run_deposit_sequence(self):

        self.timer += 1

        if self.step == 0:

            self.arm.set_height(ArmHeight.FRONT_CARDBOARD_BOX)
            if self.timer > 50:
                self.step = 1
                self.timer = 0

        elif self.step == 1:

            self.gripper.release()
            if self.timer > 30:
                self.step = 2
                self.timer = 0

        elif self.step == 2:

            self.arm.set_height(ArmHeight.RESET)
            if self.timer > 40:
                return True

        return False
