class StrategiesController < ApplicationController
  def index
    @strategies = catalog.strategies
  end

  def show
    @strategy = catalog.fetch_strategy(params[:strategy_name])
    raise NotFoundError unless @strategy
  end

  private

  def catalog
    @catalog ||= StrategyCatalog.new
  end
end
