-- LangGraph Checkpoint Tables for Cortex Flow
-- This schema is created automatically by langgraph-checkpoint-postgres

-- The checkpointer will create these tables:
-- - checkpoints: stores graph state snapshots
-- - checkpoint_writes: stores pending writes
-- - checkpoint_blobs: stores large binary data

-- No manual schema needed - langgraph handles it
-- This file exists to ensure the database is ready

SELECT 'Database cortex_flow initialized successfully' AS status;
