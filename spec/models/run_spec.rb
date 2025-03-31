require 'rails_helper'

RSpec.describe Run do
  describe 'validations' do
    context 'when a run has post_processing but no pre_processing' do
      it 'is invalid' do
        run = build(:run, pre_process: false, post_process: true)

        expect(run).not_to be_valid
      end
    end

    context 'when a run has post_processing and pre_processing' do
      it 'is valid' do
        run = build(:run, pre_process: true, post_process: true)

        expect(run).to be_valid
      end
    end
  end

  describe '#ec2?' do
    it 'is true when the server type is an EC2 instance' do
      run = build(:run, :ec2)

      expect(run.ec2?).to be(true)
    end

    it 'is false when the server type is sidekiq' do
      run = build(:run, :sidekiq)

      expect(run.ec2?).to be(false)
    end
  end

  describe '#sidekiq?' do
    it 'is true when the server type is an sidekiq instance' do
      run = build(:run, :sidekiq)

      expect(run.sidekiq?).to be(true)
    end

    it 'is false when the server type is sidekiq' do
      run = build(:run, :ec2)

      expect(run.sidekiq?).to be(false)
    end
  end

  describe '#can_be_stopped?' do
    it 'is true for a running ec2 run' do
      run = create(:run, :ongoing, :ec2)

      expect(run.can_be_stopped?).to be(true)
    end

    it 'is false for a running sidekiq run' do
      run = create(:run, :ongoing, :sidekiq)

      expect(run.can_be_stopped?).to be(false)
    end

    it 'is false for finished or new ec2 runs' do
      succeeded_run = create(:run, :finished, :ec2)
      new_run = create(:run, :ec2)

      expect(succeeded_run.can_be_stopped?).to be(false)
      expect(new_run.can_be_stopped?).to be(false)
    end
  end

  describe '#timeout' do
    it 'is 1 hour for EC2 runs' do
      run = build(:run, :ec2)

      expect(run.timeout).to eq(3.hours)
    end

    it 'is 5 minutes for sidekiq runs' do
      run = build(:run, :sidekiq)

      expect(run.timeout).to eq(2.minutes)
    end
  end

  describe '#humanized_status' do
    it 'translates into a human readable state' do
      succeeded_run = create(:run, :finished)

      expect(succeeded_run.humanized_status).to eq('Succeeded')
    end

    it 'has translations for all states' do
      Run::StateMachine.states.each do |state|
        expect(I18n.exists?("run_state.#{state}", I18n.locale)).to be(true)
      end
    end
  end
end
