class WhatsAppAPIError(Exception):
    """Erro de chamada à Meta Cloud API — preserva status HTTP e corpo bruto.

    Espelha AsaasAPIError. A notificação é best-effort (UC15): o
    whatsapp_service captura este erro e loga, nunca propaga para o fluxo
    principal (pagamento, check-in, cancelamento).
    """

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Meta WhatsApp {status_code}: {detail}")
