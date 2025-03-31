require 'rails_helper'

RSpec.describe Osemosys::Solvers::Cbc do
  it 'solves the model with glpsol and cbc without preprocessing' do
    run = create(:run, :queued, pre_process: false, post_process: false)
    atlantis_model_path = "#{Rails.root}/spec/data/atlantis_model.txt"
    atlantis_data_path = "#{Rails.root}/spec/data/atlantis_data.txt"

    expect(run.state).to eq('queued')
    allow(run).to receive(:transition_to!).with(:generating_matrix).and_call_original
    allow(run).to receive(:transition_to!).with(:finding_solution).and_call_original

    output = Osemosys::Solvers::Cbc.new(
      local_model_path: atlantis_model_path,
      local_data_path: atlantis_data_path,
      run: run,
      logger: Logger.new($stdout),
    ).call

    expect(output.solved_file_path).to match(%r{\.\/data\/output.+\.zip})
    expect(run.state).to eq('finding_solution')
    expect(run).to have_received(:transition_to!).with(:generating_matrix)
    expect(run).to have_received(:transition_to!).with(:finding_solution)
  end

  xit 'solves the model with glpsol and cbc with pre and post-processing' do
    run = create(:run, :queued)
    model_path = "#{Rails.root}/spec/data/osemosys_with_preprocessed.txt"
    atlantis_data_path = "#{Rails.root}/spec/data/atlantis_data_preprocessing.txt"

    expect(run.state).to eq('queued')
    allow(run).to receive(:transition_to!).with(:preprocessing_data).and_call_original
    allow(run).to receive(:transition_to!).with(:generating_matrix).and_call_original
    allow(run).to receive(:transition_to!).with(:finding_solution).and_call_original
    allow(run).to receive(:transition_to!).with(:postprocessing).and_call_original

    output = Osemosys::Solvers::Cbc.new(
      local_model_path: model_path,
      local_data_path: atlantis_data_path,
      run: run,
      logger: Logger.new($stdout),
    ).call

    expect(output.solved_file_path).to match(%r{\.\/data\/output.+\.zip})
    expect(run.state).to eq('postprocessing')
    expect(run).to have_received(:transition_to!).with(:generating_matrix)
    expect(run).to have_received(:transition_to!).with(:finding_solution)
  end
end
