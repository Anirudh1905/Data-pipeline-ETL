load("ext://helm_remote", "helm_remote")

docker_build("dag", ".", dockerfile="Dockerfile-airflow", platform="linux/amd64")
docker_build("app", ".", dockerfile="Dockerfile-app", platform="linux/amd64")

helm_remote(
  "airflow",
  repo_name="apache-airflow",
  repo_url="https://airflow.apache.org",
  values="manifests/values.yaml",
  namespace="airflow",
  create_namespace=True
)

k8s_yaml("manifests/deployment.yaml")

k8s_resource("app", port_forwards=["8000:8000"])
k8s_resource("airflow-webserver", port_forwards=["8080:8080"])