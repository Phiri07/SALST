-- SALST: non-destructive emergency configuration migration
ALTER TABLE owners ADD COLUMN IF NOT EXISTS emergency_banner_seconds INTEGER NOT NULL DEFAULT 120;
-- Emergency reset attribution already stored in emergencies.resolved_by and events.
