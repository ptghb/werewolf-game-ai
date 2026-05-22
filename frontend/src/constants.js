export const ROLE_LABEL = {
  werewolf: "狼人", seer: "预言家", witch: "女巫",
  hunter: "猎人", idiot: "白痴", villager: "平民",
};

export function translateRole(role) {
  return ROLE_LABEL[role] || role;
}