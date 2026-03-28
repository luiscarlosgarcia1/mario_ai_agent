local BlindKey = {}

local EXPECTED_STATE_BY_PHASE = {
  blind_select = "select",
  play_hand = "current",
  shop = "upcoming",
}

local function normalize_state(value)
  if type(value) ~= "string" then
    return nil
  end
  return string.lower(value)
end

function BlindKey.derive(interaction_phase, blind_choices)
  local expected_state = EXPECTED_STATE_BY_PHASE[interaction_phase]
  if expected_state == nil then
    return nil
  end
  if type(blind_choices) ~= "table" then
    return nil
  end

  for _, blind_choice in ipairs(blind_choices) do
    if type(blind_choice) == "table"
      and normalize_state(blind_choice.state) == expected_state
      and blind_choice.key ~= nil
    then
      return blind_choice.key
    end
  end

  return nil
end

return BlindKey
