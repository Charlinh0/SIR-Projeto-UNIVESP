from detentos.services import verificar_assinatura_pdf

caminho = r'C:\Users\space\OneDrive\Documentos\DOCs PESSOAIS\BACHARELADO T.I\PI 2\Plano de Ação\PLANO_DE_ACAO_PI_GRUPO_10-final_assinado.pdf'
estado, nome = verificar_assinatura_pdf(caminho)
print(f"Estado: {estado} | Assinante: {nome}")