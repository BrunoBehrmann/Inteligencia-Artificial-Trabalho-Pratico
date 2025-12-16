import controller
from controller import Robot, Motor
import time

def execute_robot_actions():
    # Inicialização do robô e do passo de tempo (timestep)
    robot = Robot()
    timestep = int(robot.getBasicTimeStep())

    # Inicialização dos motores das rodas
    wheel_motors = []
    wheel_motor_names = ['wheel1', 'wheel2', 'wheel3', 'wheel4']
    for motor_name in wheel_motor_names:
        motor = robot.getDevice(motor_name)
        motor.setPosition(float('inf'))
        wheel_motors.append(motor)

    # Inicialização dos motores do braço (Lengan)
    arm_motor_names = ['arm1', 'arm2', 'arm3', 'arm4', 'arm5']
    arm_motors = []
    for motor_name in arm_motor_names:
        motor = robot.getDevice(motor_name)
        arm_motors.append(motor)

    # Função para mover o robô para trás com uma velocidade e duração específicas
    def move_backward(duration, speed):
        end_time = robot.getTime() + duration
        while robot.getTime() < end_time:
            for motor in wheel_motors:
                motor.setVelocity(-speed)
            robot.step(timestep)
        for motor in wheel_motors:
            motor.setVelocity(0)

    # Função para mover o robô para frente com uma velocidade e duração específicas
    def move_forward(duration, speed):
        end_time = robot.getTime() + duration
        while robot.getTime() < end_time:
            for motor in wheel_motors:
                motor.setVelocity(speed)
            robot.step(timestep)
        for motor in wheel_motors:
            motor.setVelocity(0)

    # Função para mover o robô para a esquerda com uma velocidade e duração específicas
    def move_left(duration, speed):
        end_time = robot.getTime() + duration
        while robot.getTime() < end_time:
            wheel_motors[0].setVelocity(speed)
            wheel_motors[1].setVelocity(-speed)
            wheel_motors[2].setVelocity(-speed)
            wheel_motors[3].setVelocity(speed)
            robot.step(timestep)
        for motor in wheel_motors:
            motor.setVelocity(0)

    # Função para mover o robô para a direita com uma velocidade e duração específicas
    def move_right(duration, speed):
        end_time = robot.getTime() + duration
        while robot.getTime() < end_time:
            wheel_motors[0].setVelocity(-speed)
            wheel_motors[1].setVelocity(speed)
            wheel_motors[2].setVelocity(speed)
            wheel_motors[3].setVelocity(-speed)
            robot.step(timestep)
        for motor in wheel_motors:
            motor.setVelocity(0)
            
    # Função para olhar o objeto
    def look_at_object():
        new_positions = [0.0, -0.350, -0.251, -1.068, 0.0]
        for i in range(len(arm_motors)):
            arm_motors[i].setPosition(new_positions[i])
        target_time = robot.getTime() + 3.0
        while robot.getTime() < target_time:
            robot.step(timestep)

    # Função para pegar o objeto (distância de 10 cm, presumivelmente)
    def grab_object():
        new_positions = [0.0, -1.132, -0.775, -1.232, 0.0]
        for i in range(len(arm_motors)):
            arm_motors[i].setPosition(new_positions[i])
        target_time = robot.getTime() + 2.0
        while robot.getTime() < target_time:
            robot.step(timestep)

    # Função para colocar o objeto na base
    def place_object_on_base():
        new_positions = [0.0, 0.597, 1.097, 1.104, 0.0]
        for i in range(len(arm_motors)):
            arm_motors[i].setPosition(new_positions[i])
        target_time = robot.getTime() + 2.0
        while robot.getTime() < target_time:
            robot.step(timestep)
            
    # Chama as funções para executar as ações do robô
    move_backward(5.0, 5.0)  # Mover para trás por 5 segundos com velocidade 5.0
    move_forward(5.0, 5.0)   # Mover para frente por 5 segundos com velocidade 5.0
    move_left(10.0, 10.0)    # Mover para a esquerda por 10 segundos com velocidade 10.0
    move_right(10.0, 10.0)   # Mover para a direita por 10 segundos com velocidade 10.0
    look_at_object()         # Olhar para o objeto
    grab_object()            # Pegar o objeto
    place_object_on_base()   # Colocar o objeto na base
    move_left(10.0, 10.0)
    move_forward(5.0, 2.0)
    move_right(10.0, 10.0)
    move_backward(5.0, 3.0)
    
# Chama a função principal para executar as ações do robô
execute_robot_actions()