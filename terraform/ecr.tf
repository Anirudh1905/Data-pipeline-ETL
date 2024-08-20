resource "aws_ecr_repository" "ecr_app" {
  name = "data-repo/app"

  image_scanning_configuration {
    scan_on_push = true
  }
}