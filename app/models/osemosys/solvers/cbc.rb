module Osemosys
  module Solvers
    class Cbc
      def initialize(local_model_path:, local_data_path:, run:, logger:)
        @local_data_path = local_data_path
        @local_model_path = local_model_path
        @run = run
        @logger = logger
      end

      def call
        preprocess_data_file if pre_process?
        generate_input_file
        find_solution
        prepare_results
        if postprocess_results?
          postprocess_results
          generate_figures
          zip_csv_folder
        end
        print_summary

        SolvedFiles.new(
          solved_file_path: zipped_output_path,
          csv_file_path: zipped_csv_path,
          feasible: feasible?,
        )
      end

      private

      attr_reader :local_data_path, :local_model_path, :run, :logger

      def pre_process?
        run.pre_process?
      end

      def postprocess_results?
        run.post_process?
      end

      def preprocess_data_file
        run.transition_to!(:preprocessing_data)
        Commands::PreprocessDataFile.new(
          local_data_path: local_data_path,
          preprocessed_data_path: preprocessed_data_path,
          model_file_path: local_model_path,
          preprocessed_model_file_path: preprocessed_model_file_path,
          logger: logger,
        ).call
      end

      def generate_input_file
        data_path = pre_process? ? preprocessed_data_path : local_data_path
        model_path = pre_process? ? preprocessed_model_file_path : local_model_path
        run.transition_to!(:generating_matrix)
        Commands::GenerateInputFile.new(
          local_model_path: model_path,
          local_data_path: data_path,
          lp_path: lp_path,
          logger: logger,
          timeout: run.timeout.to_i,
        ).call
      end

      def find_solution
        run.transition_to!(:finding_solution)
        Commands::FindSolution.new(
          lp_path: lp_path,
          output_path: output_path,
          logger: logger,
          timeout: run.timeout.to_i,
        ).call
      end

      def postprocess_results
        run.transition_to!(:postprocessing)

        Commands::PostProcessResultFiles.new(
          preprocessed_data_path: preprocessed_data_path,
          solution_file_path: output_path,
          logger: logger,
        ).call
      end

      def generate_figures
        Commands::GenerateFigures.new(
          csv_path: 'csv/',
          language: run.language,
          logger: logger,
        ).call
      end

      def zip_csv_folder
        Commands::ZipFolder.new(
          folder: 'csv/',
          destination: zipped_csv_path,
          logger: logger,
        ).call
      end

      def feasible?
        File.open(output_path) do |f|
          first_line = f.first
          !first_line.match?('Infeasible')
        end
      end

      def print_summary
        logger.info 'Model solved!'
        logger.info ''
        logger.info "run_id: #{run.id}"
      end

      def preprocessed_model_file_path
        "./data/model_#{run.id}.pre.txt"
      end

      def lp_path
        "./data/input_#{run.id}.lp"
      end

      def output_path
        "./data/output_#{run.id}.txt"
      end

      def zipped_output_path
        "./data/output_#{run.id}.zip"
      end

      def zipped_csv_path
        "./data/csv_#{run.id}.zip"
      end

      def metadata_path
        @metadata_path ||= GenerateMetadata.call(run: run)
      end

      def prepare_results
        PrepareResults.call(
          output_path: output_path,
          data_path: local_data_path,
          metadata_path: metadata_path,
          destination: zipped_output_path,
          logger: logger,
        )
      end

      def preprocessed_data_path
        "#{local_data_path}.pre"
      end
    end
  end
end
