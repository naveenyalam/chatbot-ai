# NOVA AI — Infrastructure Capacity Planning Guide

This document presents hardware sizing, replica scaling, storage projections, and estimated cloud hosting costs for scaling NOVA AI from 100 to 100,000 daily active users.

---

## Capacity Matrix by User Tier

> [!NOTE]
> Resource requirements are based on measured local benchmarks (310 req/sec per backend node). Cloud hosting costs are **estimates**.

| Tier (Daily Active Users) | Backend Replicas | PostgreSQL Instance | Redis Instance | Vector Storage | Monthly Hosting Estimate ($) |
| --- | --- | --- | --- | --- | --- |
| **100 DAU** | 1 container (1 vCPU, 2GB) | Single DB (2 vCPU, 4GB) | Shared 1GB Redis | 10 GB SSD | **$35 / month** |
| **1,000 DAU** | 2 containers (2 vCPU, 4GB) | Primary DB (4 vCPU, 8GB) | Dedicated 2GB Redis | 50 GB SSD | **$120 / month** |
| **10,000 DAU** | 4 containers + Nginx LB | Primary + 1 Read Replica | Redis Cluster (8GB) | 250 GB NVMe | **$480 / month** |
| **100,000 DAU** | 12 containers + AWS ALB | Managed DB Cluster (16 vCPU, 64GB) | Redis Cluster (32GB) | 2 TB NVMe | **$2,400 / month** |
