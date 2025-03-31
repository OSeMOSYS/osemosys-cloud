class Run < ApplicationRecord
  extend Statesman::Adapters::ActiveRecordQueries[transition_class: RunTransition, initial_state: :new]
  include Discard::Model

  delegate :current_state, :history, :transition_to, :transition_to!,
    :can_transition_to?, :last_transition, to: :state_machine

  has_many :run_transitions, autosave: false
  has_one :ec2_instance, class_name: 'Ec2::Instance'

  after_commit :generate_res_file, on: :create

  belongs_to :user
  belongs_to :version
  has_one_attached :model_file
  has_one_attached :data_file
  has_one_attached :log_file
  has_one_attached :res_file
  has_one :run_result

  validates :name, presence: true
  validates :model_file, attached: true
  validates :data_file, attached: true

  validate :only_postprocess_preprocessed_runs

  enum server_type: ServerType.to_enum_definition
  enum language: Language.to_enum_definition

  scope :ordered, -> { order(id: :desc) }

  def self.for_index_view(page)
    order(id: :desc)
      .page(page)
      .with_attached_model_file
      .with_attached_data_file
      .with_attached_log_file
      .with_attached_res_file
      .includes(
        :run_transitions,
        run_result: { result_file_attachment: :blob, csv_results_attachment: :blob },
      )
  end

  def model
    version.model
  end

  def local_log_path
    "/tmp/run-#{id}.log"
  end

  def can_be_queued?
    can_transition_to? :queued
  end

  def can_be_stopped?
    ec2? && can_transition_to?(:failed)
  end

  def in_progress?
    return false unless last_transition.present?

    !last_transition.final?
  end

  def state_machine
    @state_machine ||= StateMachine.new(
      self, transition_class: RunTransition
    )
  end

  def humanized_status
    if unfeasible?
      I18n.t('run_state.unfeasible')
    else
      I18n.t("run_state.#{state}")
    end
  end

  def finished?
    finished_in.present?
  end

  def ec2?
    !sidekiq?
  end

  def sidekiq?
    server_type == 'sidekiq'
  end

  def timeout
    if ec2?
      3.hours
    else
      2.minutes
    end
  end

  def broadcast_update!
    ActionCable.server.broadcast('runs', { run_id: id, partial: to_card })
  end

  def res_file_thumbnail_url
    if cached_res_thumbnail_url.present?
      cached_res_thumbnail_url
    elsif res_file.previewable?
      cache_res_file_thumbnail
      res_file.preview(resize_to_limit: [100, 100]).processed.url
    end
  end

  def failed?
    current_state == 'failed'
  end

  def unfeasible?
    return false if run_result.blank?

    !run_result.feasible?
  end

  def run_card_css_class
    if unfeasible?
      'run-card__title-bar--unfeasible'
    else
      "run-card__title-bar--#{state}"
    end
  end

  private

  def only_postprocess_preprocessed_runs
    if post_process.present? && pre_process.blank?
      errors.add(:post_process, 'can only be enabled if pre-processing is enabled')
    end
  end

  def generate_res_file
    GenerateResJob.perform_later(id)
  end

  def to_card
    ApplicationRenderer.render(
      partial: 'runs/card',
      locals: { run: Run.find(id), view_as_admin: false },
    )
  end

  def cache_res_file_thumbnail
    update(cached_res_thumbnail_url: res_file.preview(resize_to_limit: [100, 100]).processed.url)
  end
end
