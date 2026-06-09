# Funcionalidade de Recuperação de Senha

## Visão Geral

Implementação completa de fluxo de recuperação de senha com envio de código de 6 dígitos por email. O usuário solicita recuperação, recebe um código no email (pampatickets@gmail.com), valida o código e redefine a senha.

## Arquitetura

### Backend (FastAPI)

#### 1. **Modelo de Dados** (`app/models/recuperacao_senha.py`)
```python
class RecuperacaoSenha(Base):
    - id: UUID (chave primária)
    - usuario_id: UUID (FK para usuarios.id)
    - codigo: str (6 dígitos)
    - token: str (token seguro único)
    - status: Enum (PENDENTE, VALIDADO, UTILIZADO, EXPIRADO)
    - criado_em: DateTime
    - expira_em: DateTime (15 minutos por padrão)
```

#### 2. **Configurações** (`app/core/config.py`)
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-app-password-do-gmail
EMAIL_FROM=seu-email@gmail.com
EMAIL_FROM_NAME=PampaTickets
PASSWORD_RESET_EXPIRE_MINUTES=15
```

#### 3. **Serviço de Email** (`app/integrations/email_service.py`)
- Envia email com código de 6 dígitos
- Template HTML personalizado com logo do PampaTickets
- Suporta SMTP com TLS

#### 4. **Repositório** (`app/repositories/recuperacao_senha_repo.py`)
- CRUD para gerenciar recuperações
- Busca por token e usuario_id
- Atualização de status

#### 5. **Serviço de Lógica** (`app/service/recuperacao_senha_service.py`)
```python
async def solicitar_recuperacao_senha(db, email)
    # Gera código + token, salva no banco, envia email

async def validar_codigo_recuperacao(db, email, codigo)
    # Valida código, marca como VALIDADO

async def redefinir_senha(db, email, codigo, nova_senha)
    # Redefine a senha após validação
```

#### 6. **Endpoints** (`app/api/routes/auth.py`)
```
POST /api/auth/forgot-password
  {email: "user@example.com"}
  → {mensagem: "Código enviado..."}

POST /api/auth/validate-reset-code
  {email: "user@example.com", codigo: "123456"}
  → {token: "...", mensagem: "Validado..."}

POST /api/auth/reset-password
  {email: "...", codigo: "...", nova_senha: "..."}
  → {mensagem: "Senha redefinida..."}
```

#### 7. **Migração Alembic**
- Arquivo: `backend/alembic/versions/d1a2b3c4e5f6_adiciona_tabela_recuperacao_senhas.py`
- Cria tabela `recuperacao_senhas` com constraints apropriadas

### Frontend (React + TypeScript)

#### 1. **Páginas**

**ForgotPasswordPage.tsx** (`/esqueci-senha`)
- Input para email
- Botão "Enviar Código"
- Feedback de sucesso com redirecionamento automático

**ValidateCodePage.tsx** (`/validar-codigo`)
- Input para código (6 dígitos, máscaras automáticas)
- Exibe email do usuário
- Redireciona para redefinir senha após validação

**ResetPasswordPage.tsx** (`/redefinir-senha`)
- Inputs para nova senha e confirmação
- Validações em tempo real
- Feedback de sucesso com redirecionamento para login

#### 2. **API Client** (`src/api/auth.ts`)
```typescript
solicitarRecuperacaoSenha(payload)
validarCodigoRecuperacao(payload)
redefinirSenha(payload)
```

#### 3. **Integração de Rotas** (`src/App.tsx`)
```
/esqueci-senha → ForgotPasswordPage
/validar-codigo → ValidateCodePage
/redefinir-senha → ResetPasswordPage
```

#### 4. **Link na Página de Login**
- Botão "Esqueci minha senha" adicionado ao formulário de login

## Fluxo de Uso

### Cenário Nominal

1. Usuário clica em "Esqueci minha senha" na página de login
2. Navega para `/esqueci-senha`
3. Insere seu email e clica "Enviar Código"
4. Backend gera código de 6 dígitos e envia por email
5. Frontend redireciona para `/validar-codigo`
6. Usuário copia o código do email e insere na página
7. Backend valida o código e marca como VALIDADO
8. Frontend redireciona para `/redefinir-senha`
9. Usuário insere nova senha e confirmação
10. Backend valida e redefine a senha
11. Usuário pode fazer login com a nova senha

### Cenários de Erro

- **Email inválido/não existe**: Retorna 404 com mensagem genérica (segurança)
- **Código expirado**: Token marcado como EXPIRADO, erro 400
- **Código inválido**: Erro 400 com mensagem clara
- **Senhas não conferem**: Validação no frontend
- **Senha fraca**: Validação (mínimo 8 chars, letras + números)

## Rate Limiting

- Solicitar recuperação: 5 req/min
- Validar código: 10 req/min
- Redefinir senha: 5 req/min

## Segurança

✅ **Implementado:**
- Emails não revelam se são válidos (proteção contra enumeration)
- Códigos são aleatórios (6 dígitos)
- Tokens são criptograficamente seguros
- Senhas hashadas com bcrypt
- Expiração automática de códigos
- HTTPS obrigatório em produção
- Rate limiting por IP

## Testando Localmente

1. **Configure o arquivo .env:**
```bash
cp .env.example .env
# Edite com as credenciais de email
```

2. **Suba os serviços:**
```bash
make up
```

3. **Acesse o fluxo:**
```
http://localhost:5173/login → Esqueci minha senha
```

4. **Monitore os logs:**
```bash
make logs-api
```

## Próximos Passos

- [ ] Adicionar testes unitários para o serviço de recuperação
- [ ] Adicionar testes E2E para o fluxo completo
- [ ] Implementar resend de código (retry)
- [ ] Dashboard do admin para ver tentativas de recuperação
- [ ] Notificações complementares via WhatsApp (UC15)

## Dependências Externas

- **SMTP Gmail**: Requer credenciais de APP PASSWORD (não senha da conta)
- **Biblioteca Python**: `smtplib` (stdlib), `email` (stdlib)

## Estrutura de Arquivos

```
backend/
├── app/
│   ├── models/
│   │   └── recuperacao_senha.py (novo)
│   ├── repositories/
│   │   └── recuperacao_senha_repo.py (novo)
│   ├── service/
│   │   └── recuperacao_senha_service.py (novo)
│   ├── integrations/
│   │   └── email_service.py (novo)
│   ├── api/routes/
│   │   └── auth.py (modificado)
│   └── core/
│       └── config.py (modificado)
└── alembic/versions/
    └── d1a2b3c4e5f6_adiciona_tabela_recuperacao_senhas.py (novo)

frontend/
├── src/
│   ├── api/
│   │   └── auth.ts (modificado)
│   ├── pages/auth/
│   │   ├── ForgotPasswordPage.tsx (novo)
│   │   ├── ValidateCodePage.tsx (novo)
│   │   ├── ResetPasswordPage.tsx (novo)
│   │   └── LoginPage.tsx (modificado)
│   └── App.tsx (modificado)
```

---

**Data de Implementação:** 07/06/2026  
**Responsável:** Igor Zanette
