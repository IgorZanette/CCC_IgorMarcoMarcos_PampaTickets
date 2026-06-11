// Setup global da suíte: matchers do jest-dom no expect do Vitest e cleanup
// do DOM entre testes (o auto-cleanup da Testing Library depende de globals,
// que mantemos desativados — imports explícitos nos testes).
import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});
