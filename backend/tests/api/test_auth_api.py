"""Testes de API dos endpoints de autenticação (cadastro, login, me)."""

from app.integrations.asaas.exceptions import AsaasAPIError
from app.service import auth_service


def _cadastro(**overrides) -> dict:
    base = {
        "nome": "Novo Usuário",
        "email": "novo@test.com",
        "cpf_cnpj": "529.982.247-25",
        "celular": "54999407969",
        "senha": "senha-forte-123",
        "perfil": "PARTICIPANTE",
    }
    base.update(overrides)
    return base


class TestCadastro:
    async def test_cadastro_ok_201(self, client, mock_asaas_customers):
        resp = await client.post("/api/auth/cadastro", json=_cadastro())
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "novo@test.com"
        assert body["cpf_cnpj"] == "52998224725"
        mock_asaas_customers.assert_awaited_once()

    async def test_cadastro_email_duplicado_409(self, client, mock_asaas_customers):
        await client.post("/api/auth/cadastro", json=_cadastro())
        resp = await client.post("/api/auth/cadastro", json=_cadastro())
        assert resp.status_code == 409

    async def test_cadastro_cpf_invalido_422(self, client, mock_asaas_customers):
        resp = await client.post(
            "/api/auth/cadastro", json=_cadastro(cpf_cnpj="111.111.111-11")
        )
        assert resp.status_code == 422

    async def test_cadastro_asaas_erro_cliente_422(self, client, mock_asaas_customers):
        mock_asaas_customers.side_effect = AsaasAPIError(
            400, '{"errors":[{"description":"cpfCnpj inválido"}]}'
        )
        resp = await client.post("/api/auth/cadastro", json=_cadastro())
        assert resp.status_code == 422

    async def test_cadastro_asaas_erro_servidor_502(self, client, mock_asaas_customers):
        mock_asaas_customers.side_effect = AsaasAPIError(503, "indisponível")
        resp = await client.post("/api/auth/cadastro", json=_cadastro())
        assert resp.status_code == 502

    async def test_cadastro_senha_fraca_422(self, client, mock_asaas_customers):
        resp = await client.post(
            "/api/auth/cadastro", json=_cadastro(senha="somenteletras")
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_ok_200(self, client, mock_asaas_customers):
        await client.post("/api/auth/cadastro", json=_cadastro(email="login@test.com"))
        resp = await client.post(
            "/api/auth/login",
            json={"email": "login@test.com", "senha": "senha-forte-123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["usuario"]["email"] == "login@test.com"

    async def test_login_senha_errada_401(self, client, mock_asaas_customers):
        await client.post("/api/auth/cadastro", json=_cadastro(email="login2@test.com"))
        resp = await client.post(
            "/api/auth/login",
            json={"email": "login2@test.com", "senha": "senha-errada"},
        )
        assert resp.status_code == 401

    async def test_login_email_desconhecido_401(self, client):
        resp = await client.post(
            "/api/auth/login",
            json={"email": "ninguem@test.com", "senha": "qualquer-coisa"},
        )
        assert resp.status_code == 401


class TestMe:
    async def test_me_com_token_200(self, client, participante, auth_headers):
        resp = await client.get("/api/auth/me", headers=auth_headers(participante))
        assert resp.status_code == 200
        assert resp.json()["email"] == participante.email

    async def test_me_token_invalido_401(self, client):
        resp = await client.get(
            "/api/auth/me", headers={"Authorization": "Bearer token.invalido.aqui"}
        )
        assert resp.status_code == 401

    async def test_me_sub_nao_uuid_401(self, client):
        # Token assinado corretamente mas com 'sub' não-UUID deve dar 401, não 500.
        token = auth_service._gerar_token("nao-e-uuid")
        resp = await client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 401


class TestRateLimit:
    async def test_login_excede_limite_429(self, client):
        from app.core.rate_limit import limiter

        limiter.enabled = True
        codigos: list[int] = []
        try:
            for _ in range(25):
                resp = await client.post(
                    "/api/auth/login",
                    json={"email": "x@test.com", "senha": "senha-qualquer"},
                )
                codigos.append(resp.status_code)
        finally:
            limiter.enabled = False
        assert 429 in codigos
