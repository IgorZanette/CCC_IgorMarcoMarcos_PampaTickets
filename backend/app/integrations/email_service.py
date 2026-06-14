"""Serviço para envio de emails via SMTP."""

import smtplib
from email.mime.application import MIMEApplication
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


async def enviar_confirmacao_email(email_destino: str, codigo: str, nome_usuario: str) -> bool:
    """Envia email com código de confirmação de conta."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Confirme seu cadastro - PampaTickets"
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = email_destino

        html = f"""\
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #333; text-align: center;">Confirme seu cadastro</h2>
                    <p style="color: #666; font-size: 16px;">
                        Olá <strong>{nome_usuario}</strong>,
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        Bem-vindo ao PampaTickets! Use o código abaixo para confirmar seu e-mail e ativar sua conta:
                    </p>
                    <div style="background-color: #f0f0f0; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #007bff; font-size: 36px; letter-spacing: 5px; margin: 0;">{codigo}</h1>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        <strong>O código expira em 24 horas.</strong>
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        Se você não criou esta conta, ignore este email.
                    </p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        © 2026 PampaTickets. Todos os direitos reservados.
                    </p>
                </div>
            </body>
        </html>
        """

        text = f"""\
        Confirme seu cadastro - PampaTickets

        Olá {nome_usuario},

        Bem-vindo ao PampaTickets! Use o código abaixo para confirmar seu e-mail:

        {codigo}

        O código expira em 24 horas.

        Se você não criou esta conta, ignore este email.

        © 2026 PampaTickets. Todos os direitos reservados.
        """

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Email de confirmação de conta enviado")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Falha na autenticação SMTP. Verifique credenciais de email.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Erro ao enviar email de confirmação via SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar email de confirmação: {e}")
        return False


async def enviar_ingresso_por_email(
    email_destino: str,
    nome_usuario: str,
    nome_evento: str,
    data_evento_str: str,
    pdf_bytes: bytes,
    nome_pdf: str,
) -> bool:
    """Envia email com PDF do ingresso em anexo."""
    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"Seu ingresso para {nome_evento} - PampaTickets"
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = email_destino

        html = f"""\
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #333; text-align: center;">Seu ingresso está aqui! 🎉</h2>
                    <p style="color: #666; font-size: 16px;">
                        Olá <strong>{nome_usuario}</strong>,
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        Seu pagamento foi confirmado. Segue em anexo o ingresso para o evento:
                    </p>
                    <div style="background-color: #f0f0f0; padding: 16px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0; font-size: 16px; font-weight: bold; color: #333;">{nome_evento}</p>
                        <p style="margin: 4px 0 0 0; font-size: 14px; color: #666;">{data_evento_str}</p>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        Apresente o QR Code do ingresso na entrada do evento.
                        Você também pode acessar seus ingressos pelo site a qualquer momento.
                    </p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        © 2026 PampaTickets. Todos os direitos reservados.
                    </p>
                </div>
            </body>
        </html>
        """

        text = f"""\
        Seu ingresso está aqui!

        Olá {nome_usuario},

        Seu pagamento foi confirmado. Segue em anexo o ingresso para:

        {nome_evento}
        {data_evento_str}

        Apresente o QR Code do ingresso na entrada do evento.

        © 2026 PampaTickets. Todos os direitos reservados.
        """

        corpo = MIMEMultipart("alternative")
        corpo.attach(MIMEText(text, "plain"))
        corpo.attach(MIMEText(html, "html"))
        msg.attach(corpo)

        anexo = MIMEApplication(pdf_bytes, Name=nome_pdf)
        anexo["Content-Disposition"] = f'attachment; filename="{nome_pdf}"'
        msg.attach(anexo)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Email com ingresso enviado")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Falha na autenticação SMTP. Verifique credenciais de email.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Erro ao enviar email de ingresso via SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar email de ingresso: {e}")
        return False
