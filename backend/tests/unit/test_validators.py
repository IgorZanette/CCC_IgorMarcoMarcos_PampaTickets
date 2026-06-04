"""Testes unitários do validador canônico de CPF/CNPJ (app/core/validators.py)."""

import pytest

from app.core.validators import validar_cnpj, validar_cpf, validar_cpf_cnpj


class TestValidarCpf:
    def test_cpf_valido_sem_mascara(self):
        assert validar_cpf("52998224725") == "52998224725"

    def test_cpf_valido_com_mascara_normaliza(self):
        assert validar_cpf("529.982.247-25") == "52998224725"

    def test_cpf_digitos_repetidos(self):
        with pytest.raises(ValueError):
            validar_cpf("11111111111")

    def test_cpf_digito_verificador_errado(self):
        with pytest.raises(ValueError):
            validar_cpf("52998224724")

    def test_cpf_tamanho_errado(self):
        with pytest.raises(ValueError):
            validar_cpf("123")


class TestValidarCnpj:
    def test_cnpj_valido_sem_mascara(self):
        assert validar_cnpj("11222333000181") == "11222333000181"

    def test_cnpj_valido_com_mascara(self):
        assert validar_cnpj("11.222.333/0001-81") == "11222333000181"

    def test_cnpj_digitos_repetidos(self):
        with pytest.raises(ValueError):
            validar_cnpj("00000000000000")

    def test_cnpj_digito_verificador_errado(self):
        with pytest.raises(ValueError):
            validar_cnpj("11222333000180")


class TestValidarCpfCnpj:
    def test_detecta_e_valida_cpf(self):
        assert validar_cpf_cnpj("529.982.247-25") == "52998224725"

    def test_detecta_e_valida_cnpj(self):
        assert validar_cpf_cnpj("11.222.333/0001-81") == "11222333000181"

    def test_tamanho_invalido(self):
        with pytest.raises(ValueError):
            validar_cpf_cnpj("123456")
