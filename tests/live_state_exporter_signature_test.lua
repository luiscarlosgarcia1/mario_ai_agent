local Signature = dofile("mods/live_state_exporter/signature.lua")

local function assert_true(condition, message)
  if not condition then
    error(message or "assertion failed", 2)
  end
end

local function assert_not_equal(left, right, message)
  if left == right then
    error(message or ("expected values to differ, both were: " .. tostring(left)), 2)
  end
end

local function test_missing_scalar_fields_still_produce_signature()
  local signature = Signature.make({
    state = {
      phase = "shop",
      money = 4,
      blind_name = "Small Blind",
      blind_key = "bl_small",
    },
  })

  assert_true(type(signature) == "string", "signature should be a string")
  assert_true(#signature > 0, "signature should not be empty")
end

local function test_missing_item_keys_do_not_crash()
  local signature = Signature.make({
    state = {
      jokers = {
        { name = "Joker" },
        { name = nil },
      },
      vouchers = {
        { key = nil },
      },
      consumables_inventory = {
        { key = "c_fool", kind = "tarot" },
      },
    },
  })

  assert_true(type(signature) == "string", "signature should be a string for partial item data")
end

local function test_distinct_real_values_change_signature()
  local first = Signature.make({
    state = {
      phase = "shop",
      money = 4,
      jokers = {
        { name = "Joker" },
      },
    },
  })

  local second = Signature.make({
    state = {
      phase = "shop",
      money = 5,
      jokers = {
        { name = "Joker" },
      },
    },
  })

  assert_not_equal(first, second, "signature should change when gameplay-relevant state changes")
end

test_missing_scalar_fields_still_produce_signature()
test_missing_item_keys_do_not_crash()
test_distinct_real_values_change_signature()
