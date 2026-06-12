"""Serviço para envio de emails via SMTP."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from loguru import logger

from app.core.config import settings


async def enviar_codigo_recuperacao_senha(email_destino: str, codigo: str, nome_usuario: str) -> bool:
    """
    Envia um email com código de recuperação de senha.

    Args:
        email_destino: Email do usuário
        codigo: Código de 6 dígitos para recuperação
        nome_usuario: Nome do usuário para personalização do email

    Returns:
        True se o email foi enviado com sucesso, False caso contrário
    """
    try:
        # Criar mensagem
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Recuperação de Senha - PampaTickets"
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = email_destino

        # Corpo do email em HTML
        html = f"""\
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #333; text-align: center;">Recuperação de Senha</h2>
                    <p style="color: #666; font-size: 16px;">
                        Olá <strong>{nome_usuario}</strong>,
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        Recebemos uma solicitação para recuperar sua senha no PampaTickets. 
                        Use o código abaixo para validar sua identidade:
                    </p>
                    <div style="background-color: #f0f0f0; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #007bff; font-size: 36px; letter-spacing: 5px; margin: 0;">{codigo}</h1>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        <strong>O código expira em 15 minutos.</strong>
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        Se você não solicitou esta recuperação de senha, ignore este email.
                    </p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        © 2026 PampaTickets. Todos os direitos reservados.
                    </p>
                </div>
            </body>
        </html>
        """

        # Versão em texto
        text = f"""\
        Recuperação de Senha - PampaTickets
        
        Olá {nome_usuario},
        
        Recebemos uma solicitação para recuperar sua senha no PampaTickets. 
        Use o código abaixo para validar sua identidade:
        
        {codigo}
        
        O código expira em 15 minutos.
        
        Se você não solicitou esta recuperação de senha, ignore este email.
        
        © 2026 PampaTickets. Todos os direitos reservados.
        """

        # Adicionar partes ao email
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        # Conectar ao servidor SMTP e enviar
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        # Sem o endereço no log (PII) — o request_id do middleware já correlaciona.
        logger.info("Email de recuperação de senha enviado")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Falha na autenticação SMTP. Verifique credenciais de email.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Erro ao enviar email via SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar email: {e}")
        return False
