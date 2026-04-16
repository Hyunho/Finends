require "test_helper"

class StrategyCatalogTest < ActiveSupport::TestCase
  test "lists strategies from the repository" do
    catalog = StrategyCatalog.new

    strategies = catalog.strategies

    assert_includes strategies.map(&:name), "box_range"
    refute_includes strategies.map(&:name), "__pycache__"
  end

  test "finds a history document by slug" do
    catalog = StrategyCatalog.new

    document = catalog.fetch_document("box_range", "history/2026-04-16-box-range-v2-attempt-failed")

    assert document
    assert_equal true, document.history?
    assert_includes document.body, "v2"
  end
end
