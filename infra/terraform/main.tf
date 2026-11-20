terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "resource_group_name" {
  description = "Resource group that holds the PostgreSQL server."
  type        = string
}

variable "location" {
  description = "Primary Azure region for the PostgreSQL server. Geo-redundant backups are copied to the paired region."
  type        = string
}

variable "postgres_admin_login" {
  description = "Administrator login for the PostgreSQL server."
  type        = string
}

variable "postgres_admin_password" {
  description = "Administrator password for the PostgreSQL server. Supply via TF_VAR_postgres_admin_password, never commit it."
  type        = string
  sensitive   = true
}

variable "postgres_sku_name" {
  description = "Compute SKU for the PostgreSQL flexible server (geo-redundant backup requires General Purpose or Memory Optimized tiers)."
  type        = string
  default     = "GP_Standard_D2s_v3"
}

variable "postgres_storage_mb" {
  description = "Storage size in MB for the PostgreSQL flexible server."
  type        = number
  default     = 32768
}

variable "postgres_db_name" {
  description = "Application database name (matches POSTGRES_DB / DB_NAME)."
  type        = string
  default     = "leave_tracker"
}

# Azure Database for PostgreSQL flexible server.
# - Automated daily backups with 35-day retention (>= 30-day requirement, Azure maximum).
# - Geo-redundant backup storage: backups are replicated to the Azure paired region,
#   i.e. stored in a separate region from the primary database.
# - Point-in-time recovery (PITR) is available to any second within the retention window
#   (continuous WAL archiving is built into flexible server backups).
# Restore procedure: see docs/restore-runbook.md.
resource "azurerm_postgresql_flexible_server" "main" {
  name                = "psql-employeeleavetrack-44834"
  resource_group_name = var.resource_group_name
  location            = var.location
  version             = "16"

  administrator_login    = var.postgres_admin_login
  administrator_password = var.postgres_admin_password

  sku_name   = var.postgres_sku_name
  storage_mb = var.postgres_storage_mb

  backup_retention_days        = 35
  geo_redundant_backup_enabled = true

  lifecycle {
    # Geo-redundant backup can only be set at creation time; prevent accidental
    # destruction of the server and its backups.
    prevent_destroy = true
    ignore_changes  = [zone]
  }
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = var.postgres_db_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

output "postgres_server_name" {
  value = azurerm_postgresql_flexible_server.main.name
}

output "postgres_server_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "postgres_backup_retention_days" {
  value = azurerm_postgresql_flexible_server.main.backup_retention_days
}

output "postgres_geo_redundant_backup_enabled" {
  value = azurerm_postgresql_flexible_server.main.geo_redundant_backup_enabled
}
