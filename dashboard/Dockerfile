# Start from the official Grafana image
FROM grafana/grafana:latest

# Copy your dashboard JSON into provisioning folder
# Grafana looks for dashboards in /etc/grafana/provisioning/dashboards/
COPY dashboard.json /etc/grafana/provisioning/dashboards/dashboard.json

# Copy provisioning configuration file
COPY dashboards.yaml /etc/grafana/provisioning/dashboards/dashboards.yaml

# Copy data sources
COPY datasources.yaml /etc/grafana/provisioning/datasources/datasources.yaml
