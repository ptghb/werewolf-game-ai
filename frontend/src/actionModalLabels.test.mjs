import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const actionModalSource = await readFile(new URL("./components/ActionModal.jsx", import.meta.url), "utf8");
const chatPanelSource = await readFile(new URL("./components/ChatPanel.jsx", import.meta.url), "utf8");

assert.match(actionModalSource, /hunter_shot:\s*["']猎人开枪["']/);
assert.match(chatPanelSource, /hunter_shot:\s*["']猎人开枪["']/);
