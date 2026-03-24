--- STEAMODDED HEADER
--- MOD_ID: live_state_exporter
--- MOD_NAME: Live State Exporter
--- MOD_AUTHOR: [luiga]
--- MOD_DESCRIPTION: Writes compact live Balatro state snapshots to ai/live_state.json for external agents.
--- PREFIX: live_state_exporter
--- VERSION: 0.1.0

local EXPORT_DIR = "ai"
local EXPORT_FILE = "live_state.json"
local EXPORT_PATH = EXPORT_DIR .. "/" .. EXPORT_FILE
local EXPORT_INTERVAL_SECONDS = 0.05
local EXPORT_MAX_HAND_CARDS = 20
local EXPORT_MAX_JOKERS = 8
local EXPORT_MAX_STRING = 80
local unpack_fn = table.unpack or unpack

local function now()
  if love and love.timer and love.timer.getTime then
    return love.timer.getTime()
  end
  return os.clock()
end

local function trim_text(value, limit)
  local text = tostring(value or "")
  if #text <= limit then
    return text
  end
  return text:sub(1, math.max(0, limit - 3)) .. "..."
end

local function safe_tostring(value)
  if value == nil then
    return nil
  end
  local ok, result = pcall(tostring, value)
  if ok then
    return result
  end
  return nil
end

local function safe_number(value)
  if type(value) == "number" then
    return value
  end
  if type(value) == "table" then
    local direct = value[1]
    if type(direct) ~= "number" then
      direct = value.value
    end
    if type(direct) ~= "number" then
      direct = value.n
    end
    if type(direct) == "number" then
      return direct
    end
  end
  local text = safe_tostring(value)
  if text and string.match(text, "^%-?%d+$") then
    return tonumber(text)
  end
  return nil
end

local function first_non_nil(...)
  for i = 1, select("#", ...) do
    local value = select(i, ...)
    if value ~= nil then
      return value
    end
  end
  return nil
end

local function safe_table(value)
  if type(value) == "table" then
    return value
  end
  return nil
end

local function is_array(tbl)
  if type(tbl) ~= "table" then
    return false
  end
  local count = 0
  for key, _ in pairs(tbl) do
    if type(key) ~= "number" then
      return false
    end
    count = count + 1
  end
  return count > 0
end

local function escape_json_string(value)
  local replacements = {
    ['\\'] = '\\\\',
    ['"'] = '\\"',
    ["\b"] = "\\b",
    ["\f"] = "\\f",
    ["\n"] = "\\n",
    ["\r"] = "\\r",
    ["\t"] = "\\t",
  }

  return value:gsub('[%z\1-\31\\"]', function(char)
    return replacements[char] or string.format("\\u%04x", char:byte())
  end)
end

local function encode_json(value, seen)
  local kind = type(value)
  if kind == "nil" then
    return "null"
  end
  if kind == "boolean" then
    return value and "true" or "false"
  end
  if kind == "number" then
    if value ~= value or value == math.huge or value == -math.huge then
      return "null"
    end
    return tostring(value)
  end
  if kind == "string" then
    return '"' .. escape_json_string(value) .. '"'
  end
  if kind ~= "table" then
    return "null"
  end

  seen = seen or {}
  if seen[value] then
    return "null"
  end
  seen[value] = true

  local parts = {}
  if is_array(value) then
    local n = #value
    for i = 1, n do
      parts[#parts + 1] = encode_json(value[i], seen)
    end
    seen[value] = nil
    return "[" .. table.concat(parts, ",") .. "]"
  end

  local keys = {}
  for key, _ in pairs(value) do
    keys[#keys + 1] = key
  end
  table.sort(keys, function(a, b)
    return tostring(a) < tostring(b)
  end)

  for _, key in ipairs(keys) do
    local encoded_value = encode_json(value[key], seen)
    parts[#parts + 1] = '"' .. escape_json_string(tostring(key)) .. '":' .. encoded_value
  end
  seen[value] = nil
  return "{" .. table.concat(parts, ",") .. "}"
end

local function format_modifier(name, value, default)
  if value == nil or value == default then
    return nil
  end
  return tostring(name) .. "=" .. tostring(value)
end

local function summarize_card(card, area_name)
  if type(card) ~= "table" then
    return nil
  end

  local base = safe_table(card.base) or {}
  local save_fields = safe_table(card.save_fields) or {}
  local ability = safe_table(card.ability) or {}
  local edition = safe_table(card.edition) or {}

  local enhancement = safe_tostring(first_non_nil(ability.effect, card.enhancement))
  if enhancement == "Base" then
    enhancement = nil
  end

  local modifiers = {}
  local function add_modifier(name, value, default)
    local formatted = format_modifier(name, value, default)
    if formatted then
      modifiers[#modifiers + 1] = formatted
    end
  end

  add_modifier("bonus", first_non_nil(ability.bonus, card.bonus), 0)
  add_modifier("mult", first_non_nil(ability.mult, card.mult), 0)
  add_modifier("x_mult", first_non_nil(ability.x_mult, card.x_mult), 1)
  add_modifier("x_chips", first_non_nil(ability.x_chips, card.x_chips), 1)
  add_modifier("perma_bonus", first_non_nil(ability.perma_bonus, card.perma_bonus), 0)
  add_modifier("perma_mult", first_non_nil(ability.perma_mult, card.perma_mult), 0)
  add_modifier("perma_x_mult", first_non_nil(ability.perma_x_mult, card.perma_x_mult), 0)
  add_modifier("perma_x_chips", first_non_nil(ability.perma_x_chips, card.perma_x_chips), 0)
  add_modifier("h_mult", ability.h_mult, 0)
  add_modifier("h_chips", ability.h_chips, 0)
  add_modifier("h_x_mult", ability.h_x_mult, 0)
  add_modifier("h_x_chips", ability.h_x_chips, 1)
  add_modifier("h_dollars", ability.h_dollars, 0)
  add_modifier("p_dollars", ability.p_dollars, 0)
  add_modifier("t_mult", ability.t_mult, 0)
  add_modifier("t_chips", ability.t_chips, 0)
  add_modifier("d_size", ability.d_size, 0)
  add_modifier("h_size", ability.h_size, 0)

  if first_non_nil(card.debuffed, card.debuff) then
    modifiers[#modifiers + 1] = "debuffed"
  end

  if ability.played_this_ante then
    modifiers[#modifiers + 1] = "played_this_ante"
  end

  return {
    area = area_name,
    code = safe_tostring(first_non_nil(save_fields.card, card.card_key, card.key)),
    name = trim_text(
      safe_tostring(first_non_nil(base.name, card.label, ability.name, card.name, card.key)) or "card",
      EXPORT_MAX_STRING
    ),
    facing = safe_tostring(card.facing),
    enhancement = enhancement,
    edition = safe_tostring(first_non_nil(edition.type, edition.key, edition.name)),
    seal = safe_tostring(first_non_nil(card.seal, base.seal)),
    debuffed = not not first_non_nil(card.debuffed, card.debuff),
    modifiers = modifiers,
  }
end

local function summarize_joker(card)
  if type(card) ~= "table" then
    return nil
  end

  local ability = safe_table(card.ability) or {}
  local label = safe_tostring(first_non_nil(card.label, ability.name, ability.key, card.name, card.key))
  if not label then
    return nil
  end

  return trim_text(label, EXPORT_MAX_STRING)
end

local function collect_cards(area, limit, area_name)
  local result = {}
  local count = 0
  local cards = safe_table(area and area.cards) or {}
  for _, card in ipairs(cards) do
    count = count + 1
    if #result < limit then
      local summary = summarize_card(card, area_name)
      if summary then
        result[#result + 1] = summary
      end
    end
  end
  return result, count
end

local function collect_jokers(area, limit)
  local result = {}
  local count = 0
  local cards = safe_table(area and area.cards) or {}
  for _, card in ipairs(cards) do
    count = count + 1
    if #result < limit then
      local summary = summarize_joker(card)
      if summary then
        result[#result + 1] = summary
      end
    end
  end
  return result, count
end

local function infer_phase(root, game)
  local blind = safe_table(game.blind) or {}
  local current_round = safe_table(game.current_round) or {}
  local round_resets = safe_table(game.round_resets) or {}
  local round_blind = safe_table(round_resets.blind) or {}

  if blind.in_blind then
    return "play_hand"
  end

  if round_blind.name and current_round.hands_left ~= nil and current_round.discards_left ~= nil then
    return "blind_select"
  end

  local state_id = first_non_nil(root and root.STATE, game.state, game.current_round_state)
  if state_id ~= nil then
    return "state_" .. tostring(state_id)
  end

  return "unknown"
end

local function snapshot_game()
  local root = rawget(_G, "G")
  local game = root and root.GAME
  if type(game) ~= "table" then
    return nil
  end

  local hand_cards, hand_count = collect_cards(root and root.hand, EXPORT_MAX_HAND_CARDS, "hand")
  local jokers, joker_count = collect_jokers(root and root.jokers, EXPORT_MAX_JOKERS)

  local blind = safe_table(game.blind) or {}
  local current_round = safe_table(game.current_round) or {}
  local round_resets = safe_table(game.round_resets) or {}

  return {
    meta = {
      captured_at_seconds = now(),
      exporter_version = 1,
    },
    state = {
      source = "live_state_exporter",
      phase = infer_phase(root, game),
      state_id = safe_number(first_non_nil(root and root.STATE, game.state, game.current_round_state)),
      money = safe_number(first_non_nil(game.dollars, game.money)),
      hands_left = safe_number(first_non_nil(current_round.hands_left, round_resets.hands, game.hands_left, game.hands)),
      discards_left = safe_number(first_non_nil(current_round.discards_left, round_resets.discards, game.discards_left, game.discards)),
      blind_name = safe_tostring(first_non_nil(blind.name, game.blind_name)),
      blind_key = safe_tostring(first_non_nil(blind.config_blind, blind.key, game.blind_key)),
      current_score = safe_number(first_non_nil(game.chips, game.current_round_score, game.score)),
      score_to_beat = safe_number(first_non_nil(blind.chips, game.score_to_beat, game.target_score)),
      cards_in_hand = hand_count,
      jokers_count = joker_count,
      hand_cards = hand_cards,
      jokers = jokers,
      notes = {
        "exporter=live_state_exporter",
      },
    },
  }
end

local function make_signature(snapshot)
  if type(snapshot) ~= "table" then
    return "nil"
  end

  local state = safe_table(snapshot.state) or {}
  local parts = {
    safe_tostring(state.phase),
    safe_tostring(state.state_id),
    safe_tostring(state.money),
    safe_tostring(state.hands_left),
    safe_tostring(state.discards_left),
    safe_tostring(state.blind_name),
    safe_tostring(state.current_score),
    safe_tostring(state.score_to_beat),
    safe_tostring(state.cards_in_hand),
    safe_tostring(state.jokers_count),
  }

  local function add_card_summaries(items, field_name)
    local labels = {}
    for _, item in ipairs(items or {}) do
      if type(item) == "table" then
        labels[#labels + 1] = safe_tostring(item[field_name])
      else
        labels[#labels + 1] = safe_tostring(item)
      end
    end
    parts[#parts + 1] = table.concat(labels, "|")
  end

  add_card_summaries(state.hand_cards, "name")
  add_card_summaries(state.jokers, "name")
  return table.concat(parts, "::")
end

local function ensure_export_dir()
  if love and love.filesystem and love.filesystem.createDirectory then
    pcall(love.filesystem.createDirectory, EXPORT_DIR)
  end
end

local function write_snapshot(payload)
  ensure_export_dir()
  if love and love.filesystem and love.filesystem.write then
    local ok = pcall(love.filesystem.write, EXPORT_PATH, payload)
    if ok then
      return true
    end
  end
  return false
end

local Exporter = {
  last_write_at = 0,
  last_signature = nil,
}

function Exporter:flush(reason)
  local snapshot = snapshot_game()
  if not snapshot then
    return false
  end

  local signature = make_signature(snapshot)
  local current_time = now()
  if signature == self.last_signature and (current_time - self.last_write_at) < EXPORT_INTERVAL_SECONDS then
    return false
  end

  snapshot.meta.reason = reason or "update"
  local payload = encode_json(snapshot)
  if write_snapshot(payload) then
    self.last_write_at = current_time
    self.last_signature = signature
    return true
  end

  return false
end

function Exporter:tick(reason)
  local current_time = now()
  if (current_time - self.last_write_at) < EXPORT_INTERVAL_SECONDS and reason ~= "startup" then
    return false
  end
  return self:flush(reason)
end

local function wrap_update(target, method_name, reason)
  if type(target) ~= "table" or type(target[method_name]) ~= "function" then
    return false
  end
  if target["__live_state_exporter_wrapped_" .. method_name] then
    return false
  end

  local original = target[method_name]
  target["__live_state_exporter_wrapped_" .. method_name] = true
  target[method_name] = function(...)
    local result = { original(...) }
    Exporter:tick(reason)
    return unpack_fn(result)
  end
  return true
end

local function install_hooks()
  if not wrap_update(rawget(_G, "love"), "update", "love.update") then
    wrap_update(rawget(_G, "Game"), "update", "Game.update")
  end
end

install_hooks()
Exporter:tick("startup")
