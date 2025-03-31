require 'rails_helper'
require 'rake'

RSpec.describe 'Running a run' do
  xit 'Solves a valid run with pre and post processing' do
    run = create(:run, :queued, :atlantis_preprocessed)
    expect(run.state).to eq('queued')

    OsemosysCloud::Application.load_tasks if Rake::Task.tasks.empty?
    Rake::Task['solve_cbc_run'].invoke(run.id)
    Rake::Task['solve_cbc_run'].reenable

    run.reload
    expect(run.state).to eq('succeeded')

    expect(run.log_file).to be_present
    expect(run.run_result).to be_present
    expect(run.run_result.result_file.attached?).to be true
    expect(run.run_result.csv_results.attached?).to be true
  end

  it 'Handles a faulty run' do
    run = create(:run, :queued, :faulty)
    expect(run.state).to eq('queued')

    OsemosysCloud::Application.load_tasks if Rake::Task.tasks.empty?
    expect { Rake::Task['solve_cbc_run'].invoke(run.id) }.to raise_error(TTY::Command::ExitError)

    Rake::Task['solve_cbc_run'].reenable

    run.reload
    expect(run.state).to eq('failed')

    expect(run.log_file).to be_present
    log_path = run.local_log_path
    File.open(log_path) do |f|
      log_content = f.read
      expect(log_content).to include('Preprocessing data file')
    end
    expect(run.run_result).to be(nil)
  end
end
