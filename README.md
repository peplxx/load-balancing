# Lab Report: High-Availability Web Service with Load Balancing

## Table of Contents
1. [Objective](#objective)
2. [System Architecture](#system-architecture)
3. [Prerequisites](#prerequisites)
4. [Setup and Usage](#setup-and-usage)
    - [Makefile Commands](#makefile-commands)
5. [Component Configuration Details](#component-configuration-details)
    - [HTTP Load Balancing](#http-load-balancing)
    - [Database TCP Load Balancing](#database-tcp-load-balancing)
    - [Backend Application](#backend-application)
    - [Service Orchestration](#service-orchestration)
6. [Load Testing and Resilience Experiments](#load-testing-and-resilience-experiments)
    - [Experiment 1: Baseline Performance](#experiment-1-baseline-performance)
    - [Experiment 2: Database Slave Failure](#experiment-2-database-slave-failure)
    - [Experiment 3: Application and Database Failure](#experiment-3-application-and-database-failure)
7. [Conclusion](#conclusion)

---

## Objective
The goal of this project is to gain practical skills in using load balancers to build a resilient and scalable web service. This involves implementing load balancing for both HTTP application traffic and TCP database connections, and then verifying the system's fault tolerance under simulated load.

## System Architecture

The architecture is designed in layers to ensure high availability and distribute load effectively.

1.  **Nginx (HTTP Load Balancer):** Serves as the single entry point for all incoming web traffic. It acts as a reverse proxy, distributing requests to a pool of identical backend application instances.

2.  **Backend Application Instances:** A set of containerized Python Flask applications that handle the business logic. Each application instance is stateless and can process any incoming request.

3.  **HAProxy (TCP Load Balancer):** Manages connections to the database layer. It intelligently routes database queries based on their type:
    *   **Write Operations:** Are sent directly to the primary master database.
    *   **Read Operations:** Are load-balanced across a pool of read-only slave databases.

4.  **PostgreSQL Cluster:** A replicated database setup consisting of:
    *   A single **master** node for all data writes.
    *   Multiple **slave** nodes that replicate data from the master and handle read queries.

This multi-layered approach ensures that the failure of any single application or database slave node does not bring down the entire system.

## Prerequisites

The following tools are required to build and run this project:

- [**Docker**](https://docs.docker.com/engine/install/): To build and run the containerized services.
- [**Docker Compose**](https://docs.docker.com/compose/install/): To orchestrate the multi-container application.
- [**Make**](https://www.gnu.org/software/make/): To use the provided command shortcuts for setup and testing.

## Setup and Usage

1.  **Prepare Environment:** Initialize the necessary environment variables for the project by running:
    ```sh
    make env
    ```

2.  **Run Test Scenarios:** The project includes automated presets to run different failure scenarios and generate performance reports. To run the baseline test with all services active:
    ```sh
    make run-preset1
    ```
    This command fully automates the process of starting the services, running the load test, saving the results, and cleaning up the environment.

### Makefile Commands

A `Makefile` simplifies project management. Use `make help` for a full list of commands.

| Category  | Target          | Description                                            |
|-----------|-----------------|--------------------------------------------------------|
| **Help**  | `help`          | Show a list of all available commands.                 |
| **Utils** | `env`           | Prepare the `.env` file from the example template.     |
|           | `stop-slave1`   | Stop a specific database slave container.              |
|           | `stop-app1`     | Stop a specific backend application container.         |
| **Run**   | `up-app`        | Start all application services using Docker Compose.   |
|           | `k6-load-test`  | Execute the load test script against the system.       |
| **Cleanup** | `drop-all`      | Stop and remove all Docker containers and volumes.     |
| **Presets** | `run-preset1`   | Run the baseline test (no services disabled).          |
|           | `run-preset2`   | Run test with one database slave disabled.             |
|           | `run-preset3`   | Run test with one application and one slave disabled.  |

## Component Configuration Details

### HTTP Load Balancing
Nginx is configured to perform Layer 7 (HTTP) load balancing. It maintains an `upstream` group of backend application servers and distributes incoming requests among them using the `least_conn` algorithm. This strategy directs new requests to the server with the fewest active connections, ensuring an even load distribution.

### Database TCP Load Balancing
HAProxy is configured for Layer 4 (TCP) load balancing to manage the PostgreSQL cluster. It exposes two distinct ports: one for write operations that directs traffic exclusively to the master database, and another for read operations. The read endpoint uses a `roundrobin` algorithm to distribute connections across all available slave nodes. Crucially, HAProxy is configured with health checks to automatically detect and remove unresponsive database nodes from the load-balancing pool, ensuring high availability.

### Backend Application
The backend is a lightweight Python Flask application. Its primary function is to process incoming requests by performing a read operation on the database via HAProxy's read-only endpoint. It then returns a JSON response containing details about the container that processed the request and the specific database node that fulfilled the data query. This provides real-time insight into the behavior of both the Nginx and HAProxy load balancers.

### Service Orchestration
The entire multi-service application is defined and orchestrated using Docker Compose. The configuration specifies all services (Nginx, applications, HAProxy, PostgreSQL master/slaves), their build instructions, networking, dependencies, and environment variables. YAML anchors are used to keep the configuration DRY (Don't Repeat Yourself) by defining common service properties once.

## Load Testing and Resilience Experiments

Load testing was performed using `k6` to simulate user traffic. The test script runs in stages (ramp-up, sustained load, ramp-down) and validates that the system responds correctly and performs within latency thresholds. We conducted three experiments to test the system's resilience.

### Experiment 1: Baseline Performance
- **Scenario:** All services are running optimally. Nginx balances load across two application instances, and HAProxy balances reads across two database slaves.
- **Report:** A full performance report for this scenario is available at [results/k6_disabled[none].html](./results/k6_disabled%5Bnone%5D.html).

### Experiment 2: Database Slave Failure
- **Scenario:** One of the PostgreSQL slave nodes was intentionally stopped to simulate a database failure.
- **Report:** A full performance report for this scenario is available at [results/k6_disabled[slave1].html](./results/k6_disabled%5Bslave1%5D.html).

### Experiment 3: Application and Database Failure
- **Scenario:** A more severe failure was simulated by stopping both one application instance and one database slave.
- **Report:** A full performance report for this scenario is available at [results/k6_disabled[slave1,app1].html](./results/k6_disabled%5Bslave1,app1%5D.html).

## Conclusion

This project successfully demonstrates the design and implementation of a fault-tolerant, high-availability web architecture. By layering load balancers for different protocols—Nginx for HTTP and HAProxy for TCP—we built a system resilient to component failures. The experiments confirmed that the failure of individual application or database slave nodes does not lead to service downtime. Instead, the load balancers automatically adapt to the changing topology, ensuring continuous availability and a robust user experience.