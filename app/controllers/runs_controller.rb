class RunsController < ApplicationController
  def new
    @run = Run.new(version_id: params[:version_id])
  end

  def show
    if request.xhr?
      run = Run.find(params[:id])
      run.broadcast_update!
      head :ok
    else
      head :not_found
    end
  end

  def create
    @run = current_user.runs.create(run_params)

    if @run.valid?
      flash.notice = t('flash.run.created')
      redirect_to version_path(@run.version)
    else
      flash.now.alert = @run.errors.full_messages.to_sentence
      render :new
    end
  end

  def start
    run = Run.find(params[:id])
    if run.transition_to(:queued)
      EnqueueRunSolverJob.perform_later(run_id: run.id)
      flash.notice = t('flash.run.started')
    end
    redirect_to version_path(run.version)
  end

  def stop
    run = Run.find(params[:id])
    Ec2::StopInstance.call(aws_id: run.ec2_instance.aws_id)
    flash.notice = t('flash.run.stopped')
    redirect_to version_path(run.version)
  end

  def edit
    @run = current_user.runs.kept.find_by(id: params[:id])
    redirect_to :not_found and return unless @run
  end

  def update
    @run = current_user.runs.kept.find_by(id: params[:id])
    redirect_to :not_found and return unless @run

    if @run.update(run_params)
      flash.notice = t('flash.run.updated')
      redirect_to version_path(@run.version)
    else
      flash.now.alert = @run.errors.full_messages.to_sentence
      render :edit
    end
  end

  def destroy
    @run = current_user.runs.kept.find_by(id: params[:id])
    redirect_to :not_found and return unless @run

    if @run.discard
      flash.notice = t('flash.run.deleted')
      redirect_to version_path(@run.version)
    end
  end

  private

  def run_params
    params.require(:run).permit(
      :name, :model_file, :data_file, :description,
      :notify_when_finished, :version_id, :server_type, :language,
      :pre_process, :post_process
    )
  end

  def ensure_logged_in_user
    redirect_to root_path and return unless current_user
  end
end
