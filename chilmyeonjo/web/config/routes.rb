Rails.application.routes.draw do
  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check

  root "strategies#index"
  get "strategies/:strategy_name", to: "strategies#show", as: :strategy
  get "strategies/:strategy_name/docs/*doc_path", to: "documents#show", as: :strategy_document
end
