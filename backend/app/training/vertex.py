"""Stub for offloading training to Vertex AI Custom Training Jobs instead of
running Keras in-process (recommended for real datasets / GPU training).

from google.cloud import aiplatform

def submit_vertex_training_job(display_name, container_uri, args, machine_type="n1-standard-4"):
    aiplatform.init(project=settings.gcp_project_id, location="europe-west1")
    job = aiplatform.CustomContainerTrainingJob(
        display_name=display_name,
        container_uri=container_uri,
    )
    job.run(args=args, machine_type=machine_type, replica_count=1, sync=False)
    return job
"""
