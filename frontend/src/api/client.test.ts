// tokenExpMs decodifica o exp do JWT sem verificar assinatura (decisão de UI:
// só serve para saber QUANDO renovar; a validade real é decidida pelo backend).

import { describe, expect, it } from "vitest";

import { tokenExpMs } from "./client";

const fakeJwt = (payload: object): string =>
  `header.${btoa(JSON.stringify(payload))}.assinatura`;

describe("tokenExpMs", () => {
  it("devolve o exp em milissegundos", () => {
    expect(tokenExpMs(fakeJwt({ exp: 1_700_000_000 }))).toBe(1_700_000_000_000);
  });

  it("devolve null quando o payload não tem exp", () => {
    expect(tokenExpMs(fakeJwt({ sub: "u-1" }))).toBeNull();
  });

  it("devolve null para token ilegível", () => {
    expect(tokenExpMs("nao-e-um-jwt")).toBeNull();
    expect(tokenExpMs("a.b.c")).toBeNull();
    expect(tokenExpMs("")).toBeNull();
  });
});
