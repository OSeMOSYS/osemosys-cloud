module Ec2
  class InstanceParams
    def initialize(instance_type:, run_id:)
      @instance_type = instance_type
      @run_id = run_id
    end

    def to_h
      {
        image_id: 'ami-06ad5a06d5412374e', # Large server v6 AMI
        min_count: 1,
        max_count: 1,
        key_name: 'yboulkaid_osemosys_2023',
        user_data: encoded_user_data,
        security_group_ids: ['sg-43911f25'],
        instance_type: instance_type,
        iam_instance_profile: {
          name: 'OsemosysEC2Role',
        },
        instance_initiated_shutdown_behavior: 'terminate',
      }
    end

    private

    attr_reader :instance_type, :run_id

    def encoded_user_data
      UserData.new(run_id: run_id).to_base64_encoded
    end
  end
end
