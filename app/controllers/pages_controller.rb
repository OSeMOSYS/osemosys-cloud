class PagesController < ApplicationController
  skip_before_action :ensure_logged_in_user

  def home
    redirect_to versions_path and return if current_user
  end
end
