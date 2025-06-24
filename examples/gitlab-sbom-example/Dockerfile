# Use Alpine Linux 3.18 as the base image
FROM alpine:3.18
#
## Set the working directory
WORKDIR /app
#
## Copy requirements.txt if needed (uncomment if using Python/Ansible)
COPY ./requirements.txt .
#
## Install Python3, pip, and Ansible
RUN apk update && \
 apk add --no-cache python3 py3-pip ansible
#
## (Optional) Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt
#
## Default command (prints Ansible version)
CMD ["ansible", "--version"]