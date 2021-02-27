module Admin
  class UsersController < AdminController
    def index
      @all_users = User.includes(:runs).order(:id).page(params[:page])
    end

    def show
      @user = User.find(params[:id])
      @run_count_by_state = @user.runs.group(:state).count
      @user_runs = @user.runs.order(id: :asc)
      @last_run = @user_runs.last
    end
  end
end
