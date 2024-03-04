[![Docker Image CI](https://github.com/atcomputing/moodledb-exporter/actions/workflows/docker-image.yml/badge.svg?branch=main)](https://github.com/atcomputing/moodledb-exporter/actions/workflows/docker-image.yml)

# Moodle Metrics Collector

This project provides a Prometheus metrics collector for Moodle, designed to run in a Docker container. It collects various metrics from a Moodle database, such as active users, online users, total users, database size, number of enrolled users per course, average time spent on the site, number of failed login attempts, and number of assignments submitted.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Docker and Docker Compose installed on your machine
- Access to a Moodle database

## Requirements

The tool uses `prometheus-client` and `mysql-connector-python` to fetch and serve metrics. It has been tested and confirmed to work on Python 3.11.

## Configuration

Configuration is handled through environment variables set in a `.env` file. A template `.env` file is included as `.env.example`. Copy this file to `.env` and adjust the variables according to your Moodle database configuration:

```
DB_HOST=db_host_here
DB_USER=db_user_here
DB_PASSWORD=db_password_here
DB_NAME=moodle_database_name_here
SLEEP_INTERVAL=60
SERVER_PORT=8899
```

## Building and Running

To build and run the Moodle Metrics Collector, use the following commands:

```sh
# Build the Docker image and start the container
docker-compose up --build
```

This command builds the Docker image based on the `Dockerfile`, starts a container with the configuration specified in `docker-compose.yml`, and uses the environment variables defined in the `.env` file.

## Metrics

The collector exposes the following metrics on `http://localhost:8899` (or the port you configured):

- Active Moodle users in the last 5 minutes
- Online Moodle users in the last 5 minutes
- All Moodle users
- Moodle database size in MB
- Average time spent on site by users
- Number of failed login attempts
- Number of assignments submitted
- Number of users enrolled per course
- Course completion rate
- Number of quiz attempts
- Quiz success rate
- Number of certifications achieved
- Grades distribution
- Number of issued badges in Moodle

## Stopping the Container

To stop and remove the container, use the following command:

```sh
docker-compose down
```

## Security

To secure the metrics exported by the service, you should have a reverse proxy setup. The reverse proxy should provide Transport Layer Security (TLS) for secure data transmission over the network and include an authentication mechanism to restrict unauthorized access.

## Contributing

Contributions to this project are welcome. Please ensure you update tests as appropriate.
