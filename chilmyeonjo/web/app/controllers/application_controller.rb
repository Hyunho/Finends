class ApplicationController < ActionController::Base
  class NotFoundError < StandardError; end

  rescue_from NotFoundError, with: :render_not_found

  private

  def render_not_found
    render "errors/not_found", status: :not_found
  end
end
