import subprocess
import uuid

from kloudia.config import HOST_DATA_DIR, HOST_CONFIG_DIR
from orchestra.celery import celery


@celery.task
def cloudscan_aws_inventory_scan_task(**kwargs):
    # launch a docker container with the cloudscan image
    image_name = "fmlabs/cloudscan:latest"

    aws_profile = kwargs.get("aws_profile", "")
    aws_account_id = kwargs.get("aws_account_id", "")
    aws_region_name = kwargs.get("aws_region_name", "us-east-1")
    aws_service_names = kwargs.get("aws_service_names", "s3")

    try:
        if not aws_account_id:
            raise Exception("aws_account_id is required")
        if not aws_profile:
            raise Exception("aws_profile is required")
        if not aws_region_name:
            raise Exception("aws_region_name is required")
        if not aws_service_names:
            raise Exception("aws_service_names is required")

        if not HOST_DATA_DIR:
            raise Exception("HOST_DATA_DIR is not set in environment variables")
        if not HOST_CONFIG_DIR:
            raise Exception("HOST_CONFIG_DIR is not set in environment variables")

        random_container_suffix = uuid.uuid4().hex[:8]
        container_name = f"cloudscan-{random_container_suffix}"

        cmd = ["docker", "run", "--rm",
               "--name", container_name,
               "-e", f"DATA_DIR=/data",
               "-e", f"AWS_PROFILE={aws_profile}",
               "-e", f"AWS_CONFIG_FILE=/aws/config",
               "-v", f"{HOST_CONFIG_DIR}/aws:/aws:ro",
               "-v", f"{HOST_DATA_DIR}:/data",
               image_name,
               "aws",
               "scan",
               aws_account_id,
               aws_region_name,
               aws_service_names
               ]

        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Command finished with return code {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")

        if result.returncode != 0:
            raise Exception(f"Cloudscan inventory command failed with return code {result.returncode}")

        return {"output": result.stdout}

    except Exception as e:
        return {"error": str(e)}