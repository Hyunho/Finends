require "test_helper"

class StrategyViewerFlowTest < ActionDispatch::IntegrationTest
  test "strategy index renders known strategy" do
    get root_path

    assert_response :success
    assert_includes @response.body, "box_range"
    assert_includes @response.body, "Strategy documents, backtests, and history in one place."
  end

  test "strategy detail renders grouped documents" do
    get strategy_path("box_range")

    assert_response :success
    assert_includes @response.body, "Documents"
    assert_includes @response.body, "History"
    assert_includes @response.body, "src/analysis.py"
  end

  test "document page renders markdown content" do
    get strategy_document_path("box_range", "2026-04-16-box-range-strategy")

    assert_response :success
    assert_includes @response.body, "박스권 매매 전략"
    assert_includes @response.body, "현재 채택 전략은 v1입니다."
  end

  test "missing document returns not found" do
    get strategy_document_path("box_range", "does-not-exist")

    assert_response :not_found
    assert_includes @response.body, "Requested strategy or document was not found."
  end
end
