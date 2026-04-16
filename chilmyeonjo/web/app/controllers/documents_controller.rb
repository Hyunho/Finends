class DocumentsController < ApplicationController
  def show
    @strategy = catalog.fetch_strategy(params[:strategy_name])
    raise NotFoundError unless @strategy

    @document = catalog.fetch_document(@strategy.name, params[:doc_path])
    raise NotFoundError unless @document

    @rendered_document = MarkdownRenderer.new.render(@document.body)
  end

  private

  def catalog
    @catalog ||= StrategyCatalog.new
  end
end
