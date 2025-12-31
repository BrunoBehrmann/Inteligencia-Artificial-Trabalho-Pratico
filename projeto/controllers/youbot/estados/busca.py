import image_processing as img_proc


def executar(base, camera):
    """
    Lógica de varredura: Gira até que um objeto seja detectado.
    """
    # Realiza o processamento da imagem atual
    dados_visao = img_proc.processar_imagem(camera)

    if dados_visao["detected"]:
        # CORREÇÃO: Usar reset() em vez de stop()
        base.reset()
        print(
            f"Objeto {dados_visao['class']} detectado! Indo para APROXIMACAO.")
        return "APROXIMACAO"

    # CORREÇÃO: Usar move(vx, vy, omega) em vez de set_velocity
    # vx=0, vy=0, omega=0.1 (Giro suave para evitar que a câmera perca o frame)
    base.move(0.0, 0.0, 0.1)

    return "BUSCA_CUBO"
