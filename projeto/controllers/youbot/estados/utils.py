def esperar(robot, segundos):
    """
    Substituto do time.sleep() para Webots.
    Mantém a simulação rodando enquanto espera.
    """
    inicio = robot.getTime()
    timestep = int(robot.getBasicTimeStep())

    # Loop que avança a física até o tempo passar
    while robot.step(timestep) != -1:
        if robot.getTime() - inicio > segundos:
            break
