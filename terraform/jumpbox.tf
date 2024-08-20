resource "aws_security_group" "jumpbox_sg" {
  vpc_id = aws_vpc.vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "tls_private_key" "jumpbox_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "local_file" "jumpbox_pem" {
  content  = tls_private_key.jumpbox_key.private_key_pem
  filename = "${path.module}/jumpbox_key.pem"

  provisioner "local-exec" {
    command = "chmod 400 ${path.module}/jumpbox_key.pem"
  }
}

resource "aws_key_pair" "jumpbox_key" {
  key_name   = "jumpbox_key"
  public_key = tls_private_key.jumpbox_key.public_key_openssh
}

resource "aws_instance" "jumpbox" {
  ami             = "ami-0ae8f15ae66fe8cda"
  instance_type   = "t2.micro"
  subnet_id       = aws_subnet.public-us-east-1a.id
  security_groups = [aws_security_group.jumpbox_sg.id]
  key_name        = aws_key_pair.jumpbox_key.key_name


  connection {
    type        = "ssh"
    user        = "ec2-user"
    private_key = tls_private_key.jumpbox_key.private_key_pem
    host        = self.public_ip
  }
}

output "jumpbox_public_ip" {
  value = aws_instance.jumpbox.public_ip
}

output "private_key_path" {
  value = local_file.jumpbox_pem.filename
}